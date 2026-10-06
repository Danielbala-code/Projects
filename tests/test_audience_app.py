import json
from pathlib import Path
from fastapi.testclient import TestClient
from audience.app import create_audience_app

REPORT=Path(__file__).resolve().parents[1]/'docs/audience/results.json'

class Missing:
    available=False

class Good:
    available=True
    def complete(self,*args):return json.dumps({'summary':'The retail findings describe repeat purchasing; no campaign uplift was measured.','fact_ids':['F5','F6']})

class Bad(Good):
    def complete(self,*args):return json.dumps({'summary':'There is guaranteed improvement of 99 percent.','fact_ids':['invented']})


def test_report_works_without_llm_and_only_exports_fiction():
    client=TestClient(create_audience_app(Missing(),REPORT))
    report=client.get('/api/report')
    assert report.status_code==200 and report.json()['audit']['rows']==541909
    assert report.json()['llm']['available'] is False
    for row in report.json()['campaign']['eligible']:assert row['id'].startswith('fictional-')
    response=client.get('/api/campaign.csv')
    assert response.status_code==200
    assert len(response.text.strip().splitlines())==25
    assert 'fictional-' in response.text
    assert client.post('/api/brief').status_code==503


def test_missing_report_returns_explicit_error(tmp_path):
    client=TestClient(create_audience_app(Missing(),tmp_path/'missing.json'))
    assert client.get('/api/report').status_code==503


def test_ai_brief_is_referenced_and_failures_are_explicit():
    good=TestClient(create_audience_app(Good(),REPORT)).post('/api/brief')
    assert good.status_code==200 and good.json()['review_required'] is True
    assert good.json()['generation_mode']=='qwen'
    assert TestClient(create_audience_app(Bad(),REPORT)).post('/api/brief').status_code==502


def test_public_report_contains_no_real_customer_keys():
    report=json.loads(REPORT.read_text())
    def walk(x):
        if isinstance(x,dict):
            assert 'customer' not in x and 'CustomerID' not in x
            for value in x.values():walk(value)
        elif isinstance(x,list):
            for value in x:walk(value)
    walk(report)
    assert report['source']['license']=='CC BY 4.0'

class Formatted(Good):
    def complete(self,*args):return json.dumps({'summary':'The November cohort includes 2,459 customers and 1,055 repeat purchasers within 30 days (F2).','fact_ids':['F2']})


def test_valid_formatted_numbers_and_inline_fact_ids_are_not_rejected():
    response=TestClient(create_audience_app(Formatted(),REPORT)).post('/api/brief')
    assert response.status_code==200

class Punctuation(Good):
    def complete(self,*args):return json.dumps({'summary':'Logistic regression ROC-AUC 0.693; recency-rule ROC-AUC 0.553; these are observational retail findings.','fact_ids':['F3','F5']})


def test_referenced_decimal_with_sentence_punctuation_is_accepted():
    assert TestClient(create_audience_app(Punctuation(),REPORT)).post('/api/brief').status_code==200
