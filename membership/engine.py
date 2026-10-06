"""Transparent opportunity ranking. Never reads evaluation labels."""
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).parent


def load_data():
    return json.loads((ROOT / 'data.json').read_text())


def exclusion(person, data):
    if person['host_id'] != data['host']['id']:
        return 'wrong_host', 'Attendance belongs to another host.'
    if person['membership_status'] == 'active':
        return 'already_member', 'Already has a paid membership.'
    if person['marketing_opt_in'] is False:
        return 'opted_out', 'Does not permit marketing outreach.'
    if person['marketing_opt_in'] is not True or person['membership_status'] != 'none':
        return 'needs_review', 'Consent or membership status is unknown.'
    days = person['outreach_days_ago']
    if days is not None and days < data['outreach_cooldown_days']:
        return 'cooldown', 'Contacted within the 14-day demo cooldown.'
    if not any(person['visits_30d'].get(p['activity'], 0) for p in data['plans']):
        return 'no_covered_visits', 'No recorded visits covered by the listed plans.'
    return None


def keywords(query, text):
    words = lambda s: set(re.findall(r'[a-z]+', s.lower()))
    q, d = words(query), words(text)
    return len(q & d) / max(1, len(q))


def shortlist(mode='baseline', search=None):
    if mode not in {'baseline', 'semantic'}:
        raise ValueError('Unknown ranking mode')
    if mode == 'semantic' and search is None:
        raise ValueError('Semantic model is unavailable')
    data = load_data()
    rows, excluded = [], []
    for person in data['attendees']:
        blocked = exclusion(person, data)
        if blocked:
            excluded.append({'id': person['id'], 'name': person['name'], 'reason_code': blocked[0], 'reason': blocked[1]})
            continue
        relevance = search.similarities(person['interests'], data['plans']) if mode == 'semantic' else [keywords(person['interests'], p['benefits']) for p in data['plans']]
        offers = []
        for plan, similarity in zip(data['plans'], relevance):
            visits = person['visits_30d'].get(plan['activity'], 0)
            if not visits:
                continue
            covered = min(visits, plan['credits'])
            saving = covered * plan['drop_in_rate'] - plan['monthly_price']
            components = {'frequency': min(visits / 4, 1), 'recency': max(0, 1 - person['days_since_visit'] / 30), 'text_fit': max(0, min(float(similarity), 1)), 'value': max(0, min(saving / 30, 1))}
            score = 100 * (.5 * components['frequency'] + .25 * components['recency'] + .15 * components['text_fit'] + .1 * components['value'])
            offers.append({'plan': plan, 'score': round(score, 2), 'components': components, 'matched_visits': visits, 'covered_visits': covered, 'illustrative_saving': saving})
        best = max(offers, key=lambda row: (row['score'], row['plan']['id']))
        best.update({'id': person['id'], 'name': person['name'], 'interests': person['interests'], 'days_since_visit': person['days_since_visit'], 'suggested_action': 'review_invitation' if best['matched_visits'] >= 3 else 'nurture_first', 'saving_condition': 'If the same attendance pattern continues at the stated drop-in prices; capped by plan credits, excluding taxes. Extra visits still cost the drop-in rate.', 'reason': f"{best['matched_visits']} {best['plan']['activity']} visits in 30 days; last visit {person['days_since_visit']} days ago. Plan covers {best['covered_visits']} of those visits. Consent recorded and no current paid membership."})
        rows.append(best)
    rows.sort(key=lambda row: (-row['score'], row['id']))
    return {'fictional': True, 'host': data['host'], 'mode': mode, 'shortlist': rows, 'excluded': excluded, 'score_meaning': 'Heuristic opportunity score, not a probability of buying.', 'weights': {'frequency': .5, 'recency': .25, 'text_fit': .15, 'value': .1}, 'limitations': 'Fictional snapshot and heuristic weights. No historical conversion outcomes or causal uplift measured.'}


def evaluate(result):
    """Read labels only after ranking; no data flows back to the ranker."""
    fixture = json.loads((ROOT / 'evaluation.json').read_text())
    labels = fixture['labels']
    output = {'meaning': fixture['meaning'], 'splits': {}}
    for split in ['development', 'held_out']:
        ranked = [r for r in result['shortlist'] if labels[r['id']]['split'] == split]
        population = [v for v in labels.values() if v['split'] == split]
        top = ranked[:5]
        grades = [labels[r['id']]['grade'] for r in top]
        dcg = sum((2 ** grade - 1) / math.log2(i + 2) for i, grade in enumerate(grades))
        ideal = sorted([v['grade'] for v in population], reverse=True)[:len(top)]
        idcg = sum((2 ** grade - 1) / math.log2(i + 2) for i, grade in enumerate(ideal))
        choices = [r for r in ranked if labels[r['id']]['expected_plan']]
        output['splits'][split] = {'ranked_count': len(ranked), 'top_k_denominator': len(top), 'precision_at_5': sum(g >= 2 for g in grades) / max(1, len(top)), 'ndcg_at_5': dcg / idcg if idcg else 0, 'plan_match_correct': sum(r['plan']['id'] == labels[r['id']]['expected_plan'] for r in choices), 'plan_match_denominator': len(choices), 'top_ids': [r['id'] for r in top]}
    return output


def facts_for(attendee_id, result):
    return next((row for row in result['shortlist'] if row['id'] == attendee_id), None)
