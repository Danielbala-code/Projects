"""Fixed predictive benchmarks and fictional campaign controls. No message delivery."""
import hashlib
import math
from collections import Counter, defaultdict
from datetime import datetime
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import roc_auc_score, average_precision_score, brier_score_loss

FEATURES=['recency_days','log_purchase_count','log_positive_purchase_value','observed_tenure_days']


def feature_matrix(rows):
    return np.array([[r['recency'],math.log1p(r['frequency']),math.log1p(r['spend']),r['observed_tenure']] for r in rows],dtype=float)


def train_model(rows):
    model=Pipeline([('scale',StandardScaler()),('logistic',LogisticRegression(C=1,solver='lbfgs',max_iter=500,random_state=17))])
    model.fit(feature_matrix(rows),[r['repeat'] for r in rows])
    if model.named_steps['logistic'].n_iter_[0]>=500:raise ValueError('Model did not converge.')
    return model


def metrics(labels,scores,identities):
    y=np.asarray(labels);s=np.asarray(scores);n=len(y)
    if n==0:raise ValueError('Empty evaluation cohort')
    k=max(1,math.ceil(n*.2))
    rank=sorted(range(n),key=lambda i:(-float(s[i]),identities[i]))[:k]
    both=len(set(labels))==2
    return {'customers':n,'positives':int(y.sum()),'prevalence':round(float(y.mean()),6),
            'roc_auc':round(float(roc_auc_score(y,s)),6) if both else None,
            'average_precision':round(float(average_precision_score(y,s)),6) if both else None,
            'top20_customers':k,'precision_top20':round(float(y[rank].mean()),6)}


def compare(model,train,rows,bootstrap=False):
    x=feature_matrix(rows);y=[r['repeat'] for r in rows];ids=[r['customer'] for r in rows]
    prevalence=float(np.mean([r['repeat'] for r in train]))
    scores={'train_prevalence':np.full(len(rows),prevalence),'recency_rule':-x[:,0],'logistic_regression':model.predict_proba(x)[:,1]}
    results={name:metrics(y,s,ids) for name,s in scores.items()}
    for name in ['train_prevalence','logistic_regression']:
        results[name]['brier']=round(float(brier_score_loss(y,scores[name])),6)
    if bootstrap:
        rng=np.random.default_rng(17);deltas=[]
        for _ in range(300):
            idx=rng.integers(0,len(rows),len(rows));sample=np.array(y)[idx]
            if len(set(sample))==2:
                deltas.append(roc_auc_score(sample,scores['logistic_regression'][idx])-roc_auc_score(sample,scores['recency_rule'][idx]))
        results['logistic_regression']['auc_gain_vs_recency_ci95']=[round(float(v),6) for v in np.quantile(deltas,[.025,.975])]
    calibration=[]
    for lower,upper in [(0,.2),(.2,.4),(.4,.6),(.6,.8),(.8,1.000001)]:
        idx=(scores['logistic_regression']>=lower)&(scores['logistic_regression']<upper)
        if idx.any():calibration.append({'bin':f'{lower:.1f}–{min(upper,1):.1f}','customers':int(idx.sum()),'predicted':round(float(scores['logistic_regression'][idx].mean()),6),'observed':round(float(np.array(y)[idx].mean()),6)})
    slices=[]
    masks={'United Kingdom':[r['country']=='United Kingdom' for r in rows],'Other countries':[r['country']!='United Kingdom' for r in rows],'One prior purchase':[r['frequency']==1 for r in rows],'Multiple prior purchases':[r['frequency']>1 for r in rows]}
    for name,mask in masks.items():
        idx=np.flatnonzero(mask)
        if len(idx):slices.append({'slice':name,'models':{n:metrics(np.array(y)[idx].tolist(),s[idx],[ids[i] for i in idx]) for n,s in scores.items()}})
    return {'models':results,'calibration':calibration,'slices':slices}


def fictional_cases():
    cases=[]
    for country in ['UK','Ireland','Italy']:
        for segment in ['recent','lapsed']:
            for i in range(4):cases.append({'id':f'fictional-{country}-{segment}-{i}','organisation':'demo','territory':country,'segment':segment,'consent':True,'last_contact':None})
    cases += [{'id':f'fictional-excluded-{i}','organisation':'other' if i==0 else 'demo','territory':'UK','segment':'recent','consent':False if i==1 else None if i==2 else True,'last_contact':'2026-10-01' if i==3 else None} for i in range(4)]
    duplicate={'id':'fictional-duplicate','organisation':'demo','territory':'UK','segment':'recent','consent':True,'last_contact':None}
    return cases+[duplicate,dict(duplicate)]


def campaign(cases,asof):
    counts=Counter(r['id'] for r in cases);excluded={};strata=defaultdict(list)
    for r in cases:
        reason=None
        if counts[r['id']]>1:reason='duplicate_identity'
        elif r['organisation']!='demo':reason='wrong_organisation'
        elif r['consent'] is False:reason='opt_out'
        elif r['consent'] is not True:reason='unknown_consent'
        elif r['last_contact'] and (asof-datetime.fromisoformat(r['last_contact'])).days<14:reason='cooldown'
        if reason:excluded[r['id']]={'id':r['id'],'reason':reason}
        else:strata[(r['territory'],r['segment'])].append(r)
    eligible=[]
    for key,records in sorted(strata.items()):
        records.sort(key=lambda r:hashlib.sha256(('experiment-17|'+r['id']).encode()).hexdigest())
        for i,r in enumerate(records):eligible.append({'id':r['id'],'territory':key[0],'segment':key[1],'group':'test' if i%2==0 else 'control','fictional':True})
    return {'asof':asof.date().isoformat(),'cooldown_days':14,'eligible':sorted(eligible,key=lambda r:r['id']),'excluded':sorted(excluded.values(),key=lambda r:r['id']),'duplicate_source_records':sum(c for c in counts.values() if c>1),'meaning':'Fictional allocation fixture only; no contacts sent, conversion outcomes or uplift measured. Stable hash ordering alternates within territory/segment; persist assignments in production.'}
