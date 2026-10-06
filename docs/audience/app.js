'use strict';
const $=id=>document.getElementById(id);
const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const number=value=>Number(value).toLocaleString('en-GB');
const pct=value=>value==null?'—':`${(value*100).toFixed(1)}%`;
const decimal=value=>value==null?'—':Number(value).toFixed(3);
const table=(headers,rows)=>`<table><thead><tr>${headers.map(h=>`<th scope="col">${escape(h)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${row.map(c=>`<td>${escape(c)}</td>`).join('')}</tr>`).join('')}</tbody></table>`;
const names={train_prevalence:'A · Training prevalence',recency_rule:'B · Recency rule',logistic_regression:'C · Logistic regression'};
const featureNames={recency_days:'Days since last purchase',log_purchase_count:'Log purchase count',log_positive_purchase_value:'Log positive purchase value',observed_tenure_days:'Days since first purchase in window'};
const reasonNames={wrong_organisation:'Wrong organisation',opt_out:'Opted out',unknown_consent:'Consent unknown',cooldown:'Contact inside 14-day cooldown',duplicate_identity:'Duplicate identity'};
const live=document.documentElement.dataset.mode==='live';
let report=null,draftMeta=null;
function download(filename,text,type){const url=URL.createObjectURL(new Blob([text],{type}));const link=document.createElement('a');link.href=url;link.download=filename;link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
function row(label,value){return `<div class="row"><span>${escape(label)}</span><strong>${escape(value)}</strong></div>`;}
function renderMonthly(){const field=$('monthly-measure').value;const max=Math.max(...report.monthly.map(r=>r[field]));$('monthly').innerHTML=report.monthly.map(r=>`<div class="bar-row"><span>${escape(r.month)}</span><div class="bar-track" aria-label="${escape(r.month)}: ${number(r[field])}"><div class="bar-fill" style="width:${100*r[field]/max}%"></div></div><span>${number(r[field])}</span></div>`).join('');}
function renderModels(){
 const cohort=$('cohort').value,selected=$('slice').value,evaluation=report.evaluation[cohort];
 let models=evaluation.models;
 if(selected!=='all')models=evaluation.slices.find(r=>r.slice===selected)?.models;
 if(!models){$('model-table').textContent='This slice has no eligible observations.';return;}
 const m=models.logistic_regression,rule=models.recency_rule;
 $('cohort-summary').textContent=`${number(m.customers)} customers · ${number(m.positives)} repeat purchasers · ${pct(m.prevalence)} repeat rate · ${selected==='all'?'full cohort':selected}.`;
 $('model-table').innerHTML=table(['Approach','ROC-AUC','Average precision','Top 20% precision','Top 20% customers'],Object.entries(models).map(([name,m])=>[names[name],decimal(m.roc_auc),decimal(m.average_precision),pct(m.precision_top20),number(m.top20_customers)]));
 let conclusion=m.roc_auc==null?'ROC-AUC is undefined for a single-outcome slice.':`Logistic regression ${m.roc_auc>rule.roc_auc?'outperforms':m.roc_auc<rule.roc_auc?'underperforms':'ties'} the recency rule by ${decimal(Math.abs(m.roc_auc-rule.roc_auc))} ROC-AUC in this cohort. This is a measured ranking comparison, not campaign lift.`;
 const ci=evaluation.models.logistic_regression.auc_gain_vs_recency_ci95;
 if(ci&&selected==='all')conclusion+=` Paired customer-bootstrap 95% interval for the gain: ${decimal(ci[0])} to ${decimal(ci[1])} (300 resamples).`;
 $('comparison').textContent=conclusion;
 // Calibration is intentionally cohort-wide, not accidentally presented as a selected slice.
 $('calibration').innerHTML=table(['Full-cohort probability bin','Customers','Mean predicted','Actual repeat rate'],evaluation.calibration.map(r=>[r.bin,number(r.customers),pct(r.predicted),pct(r.observed)]));
 $('brier').textContent=`Full-cohort Brier: logistic ${decimal(evaluation.models.logistic_regression.brier)}; prevalence baseline ${decimal(evaluation.models.train_prevalence.brier)}. Calibration remains cohort-wide when a ranking slice is selected.`;
}
function campaignRows(){return report.campaign.eligible.filter(r=>$('territory').value==='all'||r.territory===$('territory').value);}
function renderCampaign(){const rows=campaignRows();$('campaign-summary').textContent=`${rows.length} fictional eligible cases · ${rows.filter(r=>r.group==='test').length} test · ${rows.filter(r=>r.group==='control').length} control · allocation date ${report.campaign.asof}.`;$('campaign').innerHTML=table(['Fictional identity','Territory','Segment','Group'],rows.map(r=>[r.id,r.territory,r.segment,r.group]));}
function render(){
 $('status').textContent=`${live?'Live Python interface':'Static snapshot · works without the Codespace'} · Results built ${new Date(report.built_at).toLocaleString('en-GB',{timeZone:'UTC'})} UTC. Historical source: 2010–2011.`;
 if(live){$('live-link').textContent='GitHub Pages companion ↗';$('live-link').href='https://danielbala-code.github.io/Projects/';}
 $('stats').innerHTML=[['Source item lines',report.audit.rows],['Clean purchase invoices',report.audit.invoices],['Known source customers',report.audit.known_customers],['November holdout customers',report.cohorts.test.customers]].map(([label,value])=>`<div class="stat"><strong>${number(value)}</strong><span>${escape(label)}</span></div>`).join('');
 $('audit').innerHTML=Object.entries(report.audit.excluded).map(([reason,n])=>row(reason.replaceAll('_',' '),number(n))).join('')+row('Conflicting invoice lines',number(report.audit.conflicting_lines))+row('Remaining positive item lines',number(report.audit.kept_lines));
 $('countries').innerHTML=table(['Recorded country','Invoices','Customers','Positive purchase value (£)'],report.countries.map(r=>[r.country,number(r.invoices),number(r.customers),number(r.positive_purchase_value_gbp)]));
 $('timeline').innerHTML=Object.entries(report.cohorts).map(([name,r])=>`<article><b>${escape(name.toUpperCase())}</b><strong>${escape(r.cutoff)}</strong><span>${number(r.customers)} customers</span><span>${r.lookback_days}-day history → ${r.horizon_days}-day outcome</span><span>${pct(r.repeat_rate)} repeat-purchase rate</span></article>`).join('');
 $('coefficients').innerHTML=report.model.features.map(r=>row(featureNames[r.name],`${r.coefficient_per_standard_deviation>=0?'+':''}${decimal(r.coefficient_per_standard_deviation)}`)).join('');
 $('excluded').innerHTML=report.campaign.excluded.map(r=>row(r.id,reasonNames[r.reason])).join('');
 $('factual').textContent=report.factual_brief;
 $('facts').innerHTML=report.facts.map(f=>`<p class="fact"><strong>${escape(f.id)}</strong> ${escape(f.text)}</p>`).join('');
 $('provenance').innerHTML=`<p><a href="${escape(report.source.url)}">${escape(report.source.name)}</a> · ${escape(report.source.creator)} · ${escape(report.source.license)}<br>DOI: ${escape(report.source.doi)}<br>${number(report.source.bytes)} downloaded bytes</p><p class="hash">SHA-256: ${escape(report.source.sha256)}</p><p>${escape(report.source.domain)}</p><p class="note">${escape(report.source.mind_status)}</p>`;
 $('integration').innerHTML=`<p><strong>Fan analytics / EXL:</strong> ${escape(report.integration.EXL)}</p><p><strong>OTT data science / Sky:</strong> ${escape(report.integration.Sky)}</p>`;
 $('limitations').innerHTML=report.limitations.map(l=>`<li>${escape(l)}</li>`).join('');
 if(live){$('ai-help').textContent=report.llm?.available?'Local Qwen is available. It receives the facts shown here and drafts a referenced explanation for your review.':'Local Qwen is unavailable. Computed reports and the factual explanation still work.';$('generate').disabled=!report.llm?.available;}
 renderMonthly();renderModels();renderCampaign();
}
$('monthly-measure').addEventListener('change',renderMonthly);$('cohort').addEventListener('change',renderModels);$('slice').addEventListener('change',renderModels);$('territory').addEventListener('change',renderCampaign);
$('export-campaign').addEventListener('click',()=>{if(!report)return;const keys=['id','territory','segment','group','fictional'];const quote=value=>`"${String(value).replaceAll('"','""')}"`;const csv=[keys,...campaignRows().map(r=>keys.map(k=>r[k]))].map(r=>r.map(quote).join(',')).join('\r\n');download('fictional-experiment.csv',csv,'text/csv;charset=utf-8');});
$('generate').addEventListener('click',async()=>{
 $('generate').disabled=true;$('ai-status').textContent='Generating a local Qwen draft…';$('review').checked=false;$('review').disabled=true;$('export-brief').disabled=true;$('draft').disabled=true;$('draft').value='';draftMeta=null;
 try{const response=await fetch('api/brief',{method:'POST'});const result=await response.json();if(!response.ok)throw new Error(result.detail||'Generation failed.');draftMeta=result;$('draft').value=result.summary;$('draft').disabled=false;$('review').disabled=false;$('ai-status').textContent=`Qwen draft · ${result.seconds}s · references ${result.fact_ids.join(', ')}. Review every claim before export.`;}
 catch(error){$('ai-status').textContent=error.message;}
 finally{$('generate').disabled=false;}
});
$('draft').addEventListener('input',()=>{$('review').checked=false;$('export-brief').disabled=true;});
$('review').addEventListener('change',()=>{$('export-brief').disabled=!$('review').checked||!draftMeta;});
$('export-brief').addEventListener('click',()=>{if(!draftMeta||!$('review').checked)return;download('reviewed-stakeholder-draft.json',JSON.stringify({generation_mode:'qwen',original_draft:draftMeta.summary,reviewed_draft:$('draft').value,fact_ids:draftMeta.fact_ids,facts:draftMeta.facts,snapshot_built_at:report.built_at,review_acknowledged:true,reviewed_at:new Date().toISOString(),meaning:'Demo acknowledgement only; references are from the original AI draft and must be checked after edits. No campaign sent.'},null,2),'application/json');});
fetch(live?'api/report':'./audience/results.json').then(async response=>{if(!response.ok)throw new Error(`Snapshot request failed (${response.status}).`);report=await response.json();render();}).catch(error=>{$('status').classList.add('error');$('status').textContent=error.message;});

fetch(live?'example-brief.json':'./audience/example-brief.json').then(r=>r.ok?r.json():null).then(example=>{if(!example)return;$('saved-example').hidden=false;$('example-content').innerHTML=`<p class="fact">${escape(example.reviewed_example)}</p><p class="note">Saved local Qwen generation · ${escape(example.generation_seconds)}s · facts ${escape(example.fact_ids.join(', '))}. ${escape(example.review_notes)}</p><details><summary>Original model wording</summary><p>${escape(example.original_draft)}</p></details>`;}).catch(()=>{});
