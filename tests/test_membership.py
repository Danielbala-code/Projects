import pytest
from fastapi.testclient import TestClient
from studio.app import create_app


class NoModel:
    available = False


@pytest.fixture
def client():
    with TestClient(create_app(model=NoModel())) as c:
        yield c


def test_membership_baseline_excludes_inappropriate_recipients(client):
    response = client.get('/membership/api/shortlist?mode=baseline')
    assert response.status_code == 200
    result = response.json()
    excluded = {p['id']: p['reason_code'] for p in result['excluded']}
    assert excluded['paid-member'] == 'already_member'
    assert excluded['opted-out'] == 'opted_out'
    assert excluded['other-host'] == 'wrong_host'
    assert excluded['recently-contacted'] == 'cooldown'
    assert excluded['unknown-consent'] == 'needs_review'
    shortlisted = {p['id'] for p in result['shortlist']}
    assert not shortlisted.intersection(excluded)
    assert result['mode'] == 'baseline'
    assert result['fictional'] is True


def test_membership_route_and_existing_interface_coexist(client):
    assert client.get('/').status_code == 200
    response = client.get('/membership/')
    assert response.status_code == 200
    assert 'Membership Opportunity Lab' in response.text


def test_embedding_mode_does_not_silently_use_baseline(client):
    response = client.get('/membership/api/shortlist?mode=invalid')
    assert response.status_code == 422


def test_ineligible_person_cannot_receive_invitation(client):
    response = client.post('/membership/api/draft', json={'attendee_id': 'opted-out', 'mode': 'baseline'})
    assert response.status_code == 409


def test_missing_llm_has_explicit_error(client):
    response = client.post('/membership/api/draft', json={'attendee_id': 'alex', 'mode': 'baseline'})
    assert response.status_code == 503


def test_savings_cap_visits_at_plan_credit_limit(client):
    result = client.get('/membership/api/shortlist?mode=baseline').json()
    nora = next(p for p in result['shortlist'] if p['id'] == 'nora')
    assert nora['matched_visits'] == 8
    assert nora['covered_visits'] == 4
    assert nora['illustrative_saving'] == 13
    assert 'if' in nora['saving_condition'].lower()


def test_factual_template_is_explicitly_not_inference(client):
    response = client.post('/membership/api/draft', json={'attendee_id': 'alex', 'mode': 'baseline', 'generation_mode': 'template'})
    assert response.status_code == 200
    result = response.json()
    assert result['generation_mode'] == 'template'
    assert result['review_required'] is True
    assert '$59' in result['body']
    assert result['evidence_ids'] == ['pilates-4']


class MissingSearch:
    available = False


def test_missing_embeddings_are_not_reported_as_semantic_success():
    from membership.app import create_membership_app
    with TestClient(create_membership_app(NoModel(), search=MissingSearch())) as c:
        response = c.get('/api/shortlist?mode=semantic')
        assert response.status_code == 503
        assert 'unavailable' in response.json()['detail'].lower()


def test_unknown_attendee_has_no_draft(client):
    assert client.post('/membership/api/draft', json={'attendee_id':'does-not-exist','generation_mode':'template'}).status_code == 404


class DraftModel:
    available = True
    def __init__(self, body):
        self.body = body
        self.prompt = None
    def complete(self, system, prompt, schema, max_tokens):
        import json
        self.prompt = prompt
        return json.dumps({'subject':'Explore Mat Club','body':self.body})


def test_model_draft_uses_facts_without_evaluation_labels():
    from membership.app import create_membership_app
    model = DraftModel('Hi Alex, Mat Club costs $59 per month for 4 pilates visits. Extra visits are $18 each. Would you like to learn more?')
    with TestClient(create_membership_app(model, search=MissingSearch())) as c:
        result = c.post('/api/draft', json={'attendee_id':'alex'}).json()
        assert result['generation_mode'] == 'model'
        assert result['sent'] is False
        assert result['review_required'] is True
        assert 'grade' not in model.prompt
        assert 'score' not in model.prompt
        assert 'held_out' not in model.prompt
        assert 'monthly_price_usd' in model.prompt


@pytest.mark.parametrize('body', [
    'Hi Alex, your Mat Club membership includes unlimited pilates access for $59.',
    'Hi Alex, Mat Club costs $12 per month and you can attend 4 pilates visits.',
])
def test_unsupported_model_claims_block_draft(body):
    from membership.app import create_membership_app
    with TestClient(create_membership_app(DraftModel(body), search=MissingSearch())) as c:
        response = c.post('/api/draft', json={'attendee_id':'alex'})
        assert response.status_code == 502
        assert 'No invitation was sent' in response.json()['detail']


def test_shared_model_adapter_preserves_procedure_schema_and_accepts_invitation_schema():
    from studio.model import LocalModel
    class FakeInference:
        def __init__(self): self.calls=[]
        def create_chat_completion(self, **kwargs):
            self.calls.append(kwargs)
            return {'choices':[{'message':{'content':'{}'}}]}
    model=LocalModel()
    fake=FakeInference()
    model._model=fake
    model.call('[1] Read the source instruction.')
    assert 'steps' in fake.calls[0]['response_format']['schema']['properties']
    schema={'type':'object','properties':{'subject':{'type':'string'}}}
    model.complete('Invitation system','Approved facts',schema,400)
    assert fake.calls[1]['response_format']['schema'] == schema
    assert fake.calls[1]['max_tokens'] == 400


def test_harmless_feel_free_phrase_does_not_claim_free_membership():
    from membership.app import create_membership_app
    body='Hi Jordan, Flow Club costs $49 per month for 4 yoga visits; extra visits cost $20 each. Feel free to ask for details.'
    with TestClient(create_membership_app(DraftModel(body), search=MissingSearch())) as c:
        assert c.post('/api/draft', json={'attendee_id':'jordan'}).status_code == 200


def test_free_benefit_remains_blocked_after_harmless_phrase():
    from membership.app import create_membership_app
    body='Hi Alex, feel free to join: Mat Club includes free guest passes for $59 per month.'
    with TestClient(create_membership_app(DraftModel(body), search=MissingSearch())) as c:
        assert c.post('/api/draft', json={'attendee_id':'alex'}).status_code == 502


def embedding_with_padded_tokenizer():
    import numpy as np
    from tokenizers import Tokenizer
    from tokenizers.models import WordLevel
    from tokenizers.pre_tokenizers import Whitespace
    from membership.embeddings import MiniLM
    tokenizer=Tokenizer(WordLevel({'[PAD]':0,'[UNK]':1,'Yoga':2},unk_token='[UNK]'))
    tokenizer.pre_tokenizer=Whitespace()
    tokenizer.enable_padding(length=128)
    tokenizer.enable_truncation(max_length=128)
    class Session:
        inputs=None
        def get_inputs(self):
            return [type('Input',(),{'name':name})() for name in ['input_ids','attention_mask']]
        def run(self, _, inputs):
            self.inputs=inputs
            return [np.ones((*inputs['input_ids'].shape,3),dtype=np.float32)]
    search=MiniLM();search._tokenizer=tokenizer;search._session=Session()
    return search


def test_embedding_excludes_artifact_configured_padding():
    search=embedding_with_padded_tokenizer()
    search._encode(['Yoga'])
    assert search._session.inputs['input_ids'].shape == (1,1)
    assert search._session.inputs['attention_mask'].sum() == 1


def test_embedding_rejects_long_text_without_artifact_truncation():
    search=embedding_with_padded_tokenizer()
    with pytest.raises(ValueError,match='exceeds 256 tokens'):
        search._encode([' '.join(['Yoga']*300)])
