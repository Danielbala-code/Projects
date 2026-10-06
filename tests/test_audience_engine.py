from datetime import datetime
import numpy as np
from audience.engine import campaign, metrics, train_model, feature_matrix


def test_campaign_exclusions_disjoint_and_repeatable():
    cases=[{'id':f'fictional-{i}','organisation':'demo','territory':'UK','segment':'recent','consent':True,'last_contact':None} for i in range(8)]
    cases += [{'id':'optout','organisation':'demo','territory':'UK','segment':'recent','consent':False,'last_contact':None},
              {'id':'unknown','organisation':'demo','territory':'UK','segment':'recent','consent':None,'last_contact':None},
              {'id':'wrong','organisation':'other','territory':'UK','segment':'recent','consent':True,'last_contact':None},
              {'id':'recent','organisation':'demo','territory':'UK','segment':'recent','consent':True,'last_contact':'2026-10-01'},
              {'id':'dup','organisation':'demo','territory':'UK','segment':'recent','consent':True,'last_contact':None}]*1
    cases.append(dict(cases[-1]))
    a=campaign(cases,datetime(2026,10,6));b=campaign(list(reversed(cases)),datetime(2026,10,6))
    assert a==b
    assert len(a['eligible'])==8
    assert {x['group'] for x in a['eligible']}=={'test','control'}
    assert len({x['id'] for x in a['eligible']})==8
    assert {x['reason'] for x in a['excluded']}=={'opt_out','unknown_consent','wrong_organisation','cooldown','duplicate_identity'}
    assert sum(x['group']=='test' for x in a['eligible'])==4


def test_metrics_have_honest_denominators_and_no_forced_score():
    m=metrics([1,0,1,0],[.9,.8,.7,.1],['a','b','c','d'])
    assert m['customers']==4 and m['positives']==2
    assert m['roc_auc']==.75 and m['top20_customers']==1 and m['precision_top20']==1
    single=metrics([0,0],[.1,.2],['a','b'])
    assert single['roc_auc'] is None and single['average_precision'] is None


def test_scaler_and_model_fit_only_training_rows():
    rows=[{'recency':i,'frequency':1+i%3,'spend':10+i,'observed_tenure':20+i,'repeat':i%2} for i in range(20)]
    model=train_model(rows)
    assert np.allclose(model.named_steps['scale'].mean_,feature_matrix(rows).mean(axis=0))
    before=model.named_steps['scale'].mean_.copy()
    model.predict_proba(np.full((3,4),1000000))
    assert np.array_equal(before,model.named_steps['scale'].mean_)
