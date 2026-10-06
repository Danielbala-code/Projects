"""Rebuild private invoices and a public aggregate-only, versioned evaluation snapshot."""
import hashlib
import json
import sqlite3
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from audience.data import ingest,snapshot
from audience.engine import FEATURES,train_model,compare,campaign,fictional_cases
from scripts.download_audience import DEST,SHA256,SIZE,URL
ROOT=Path(__file__).resolve().parents[1]
OUTPUT=ROOT/'docs/audience/results.json'


def main():
    if not DEST.is_file():raise SystemExit('Run python -m scripts.download_audience first.')
    with DEST.open('rb') as f:digest=hashlib.file_digest(f,'sha256').hexdigest()
    if DEST.stat().st_size!=SIZE or digest!=SHA256:raise SystemExit('Source size/checksum mismatch; no report replaced.')
    con=sqlite3.connect(ROOT/'.runtime/audience/invoices.sqlite')
    audit=ingest(DEST,con);last=datetime.fromisoformat(audit['source_max_date'])
    dates={'train':'2011-07-01','validation':'2011-09-01','test':'2011-11-01'}
    cohorts={name:snapshot(con,datetime.fromisoformat(date),last) for name,date in dates.items()}
    model=train_model(cohorts['train'])
    results={name:compare(model,cohorts['train'],rows,bootstrap=name=='test') for name,rows in cohorts.items() if name!='train'}
    summaries={name:{'cutoff':dates[name],'lookback_days':90,'horizon_days':30,'customers':len(rows),'repeat_purchasers':sum(r['repeat'] for r in rows),'repeat_rate':round(sum(r['repeat'] for r in rows)/len(rows),6),'one_purchase_customers':sum(r['frequency']==1 for r in rows)} for name,rows in cohorts.items()}
    monthly=[{'month':r[0],'invoices':r[1],'customers':r[2],'positive_purchase_value_gbp':round(r[3],2)} for r in con.execute("SELECT substr(date,1,7),COUNT(*),COUNT(DISTINCT customer),SUM(amount) FROM invoices GROUP BY substr(date,1,7) ORDER BY 1")]
    countries=[{'country':r[0],'invoices':r[1],'customers':r[2],'positive_purchase_value_gbp':round(r[3],2)} for r in con.execute('SELECT country,COUNT(*),COUNT(DISTINCT customer),SUM(amount) FROM invoices GROUP BY country ORDER BY COUNT(*) DESC')]
    coef=model.named_steps['logistic'].coef_[0]
    test=results['test']['models'];learned=test['logistic_regression'];rule=test['recency_rule']
    factual=f"On the November holdout, {summaries['test']['customers']:,} previously active customers were evaluated. {summaries['test']['repeat_purchasers']:,} purchased again within 30 days. Logistic regression ROC-AUC was {learned['roc_auc']:.3f}, compared with {rule['roc_auc']:.3f} for the recency rule. These are observational retail results, not measured campaign lift or streaming churn."
    facts=[{'id':'F1','text':f"Source contains {audit['rows']} transaction lines; cleaning yields {audit['invoices']} positive purchase invoices from {audit['known_customers']} known customers."},
           {'id':'F2','text':f"November holdout has {summaries['test']['customers']} previously active customers and {summaries['test']['repeat_purchasers']} repeat purchasers in the next 30 days."},
           {'id':'F3','text':f"November logistic regression ROC-AUC {learned['roc_auc']:.3f}; recency-rule ROC-AUC {rule['roc_auc']:.3f}."},
           {'id':'F4','text':f"November logistic regression average precision {learned['average_precision']:.3f}; recency-rule average precision {rule['average_precision']:.3f}."},
           {'id':'F5','text':'This observational gift-retail dataset does not establish campaign lift, subscriber churn, streaming behaviour or company-specific performance.'},
           {'id':'F6','text':'Campaign consent and experiment allocation are tested only on separate fictional cases. No customer is contacted.'}]
    report={'schema_version':1,'built_at':datetime.now(timezone.utc).isoformat(),'title':'Audience Engagement & Experiment Lab',
      'source':{'name':'UCI Online Retail','url':'https://archive.ics.uci.edu/dataset/352/online+retail','download_url':URL,'doi':'10.24432/C5BW33','creator':'Daqing Chen','license':'CC BY 4.0','bytes':SIZE,'sha256':SHA256,'domain':'UK-based gift retailer, including wholesalers; December 2010 to December 2011. No streaming or first-party EXL/Sky data.','mind_status':'MIND not used: current download requires HF access (401); old Azure release returned 409.'},
      'audit':audit,'cohorts':summaries,'monthly':monthly,'countries':countries,'evaluation':results,
      'model':{'type':'StandardScaler + L2 LogisticRegression','C':1,'seed':17,'training_rows':len(cohorts['train']),'features':[{ 'name':name,'coefficient_per_standard_deviation':round(float(c),6)} for name,c in zip(FEATURES,coef)],'iterations':int(model.named_steps['logistic'].n_iter_[0]),'preprocessing_mean':[float(v) for v in model.named_steps['scale'].mean_],
        'decision':'Frozen C=1 and features before evaluation; no hyperparameter search. Train only July, inspect September separately, report November once. Coefficients describe association conditional on the other inputs, not causes.'},
      'campaign':campaign(fictional_cases(),datetime(2026,10,6)),'facts':facts,'factual_brief':factual,
      'limitations':['Repeat purchase is not churn or incremental campaign response. Only customers with a positive purchase in the preceding 90 days enter each cohort; no zero-history prediction.',
          'The same customers can appear at different dates. July training outcomes end before September validation; November is the reserved later cohort. Customer behaviour and seasonality can shift.',
          'Exact-row deduplication may remove legitimate identical items. Conflicting invoice identities/timestamps/countries are quarantined. Returns are excluded, so positive purchase values are not net revenue.',
          'Raw source timestamps have no declared timezone. December is a partial month. Source identifiers and individual predictions are private and absent from this report.',
          'ROC-AUC measures ranking across positives and negatives; average precision reflects the class balance. A recency rule is a ranking score, not a calibrated probability.',
          'A paired 300-resample customer bootstrap describes uncertainty within November only; it does not cover training or seasonal uncertainty.',
          'Country is recorded retail country, not inferred location. UK/Ireland/Italy campaign cases and consent are fictional and not joined to retail customers.',
          'Qwen drafts prose from computed facts; it does not calculate metrics, decide consent or train the predictive model. Human review remains required.'],
      'integration':{'EXL':'Adapt invoice/event SQL to approved fan event tables; report segments, quality exceptions and experiment cohorts. No fan growth or warehouse integration claimed.',
                     'Sky':'Replace purchases with approved viewing/subscription events, define retention and censoring with domain experts, validate on later markets/cohorts. No OTT performance claimed.',
                     'production':['Map approved warehouse tables and event contracts to the snapshot SQL.','Add authentication, tenant isolation, governed consent and deletion, monitoring and persisted experiment assignments.','Validate model calibration, seasonal drift and incremental lift in a randomized experiment before outreach.']}}
    OUTPUT.parent.mkdir(parents=True,exist_ok=True);part=OUTPUT.with_suffix('.part');part.write_text(json.dumps(report,indent=2,allow_nan=False));part.replace(OUTPUT)
    print(json.dumps({'audit':audit,'cohorts':summaries,'holdout_models':test,'output':str(OUTPUT)},indent=2))
    con.close()
if __name__=='__main__':main()
