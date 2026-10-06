const $ = id => document.getElementById(id);
const state = {mode:'baseline', result:null, selected:null, busy:false, draft:null};
const esc = value => String(value).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
async function api(path, body) {
  const response = await fetch('/membership/api/' + path, body ? {method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)} : {});
  const data = await response.json();
  if (!response.ok) throw new Error(data.detail || 'Request failed.');
  return data;
}
function status(message, error=false) { $('status').textContent=message; $('status').classList.toggle('error',error); }
function setBusy(busy) { state.busy=busy; document.querySelectorAll('button').forEach(b=>b.disabled=busy); if (!busy && $('download')) $('download').disabled=!$('reviewed').checked; }
async function load(mode) {
  if(state.busy) return;
  setBusy(true); status(mode==='semantic'?'Matching interests with local MiniLM…':'Applying eligibility rules and keyword matching…');
  try { state.result=await api('shortlist?mode='+mode);state.mode=mode;state.draft=null;
    ['baseline','semantic'].forEach(m=>$(m).classList.toggle('active',m===mode));
    renderList(); select(state.result.shortlist.some(r=>r.id===state.selected)?state.selected:state.result.shortlist[0].id);
    status(`${state.result.shortlist.length} eligible attendees · ${state.result.latency_ms} ms ranking · ${mode==='semantic'?'MiniLM + FAISS':'Keyword baseline'}`);
  } catch(e) {status(e.message,true);} finally {setBusy(false);}
}
function renderList(){
  $('count').textContent=`${state.result.shortlist.length} opportunities`;
  $('shortlist').innerHTML=state.result.shortlist.map((r,i)=>`<article class="person" tabindex="0" role="button" data-id="${esc(r.id)}" aria-label="Review ${esc(r.name)}"><span class="rank">${String(i+1).padStart(2,'0')}</span><div><h3>${esc(r.name)}</h3><p>${esc(r.plan.name)} · ${r.matched_visits} ${esc(r.plan.activity)} visits</p><span class="tag ${r.suggested_action==='nurture_first'?'nurture':''}">${r.suggested_action==='nurture_first'?'Nurture first':'Review invitation'}</span></div><div class="score">${r.score.toFixed(1)}<small>OPPORTUNITY</small></div></article>`).join('');
  document.querySelectorAll('.person').forEach(el=>{el.onclick=()=>{if(!state.busy)select(el.dataset.id);};el.onkeydown=e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();el.click();}};});
  $('excluded-count').textContent=`${state.result.excluded.length} attendees excluded from outreach`;
  $('excluded').innerHTML=state.result.excluded.map(r=>`<p><strong>${esc(r.name)}</strong> — ${esc(r.reason)}</p>`).join('');
}
function select(id){
  state.selected=id;state.draft=null;
  const r=state.result.shortlist.find(r=>r.id===id), p=r.plan;
  document.querySelectorAll('.person').forEach(el=>el.classList.toggle('selected',el.dataset.id===id));
  $('detail').innerHTML=`<p class="eyebrow">EVIDENCE / ${esc(r.id.toUpperCase())}</p><h2>${esc(r.name)} → ${esc(p.name)}</h2><p>${esc(r.reason)}</p><div class="facts"><div><strong>$${p.monthly_price}</strong><span>per month · ${p.credits} visits</span></div><div><strong>${r.days_since_visit} days</strong><span>since last attendance</span></div><div><strong>${r.covered_visits} of ${r.matched_visits}</strong><span>recorded visits covered</span></div><div><strong>${r.illustrative_saving>0?'$'+r.illustrative_saving:'No'}</strong><span>illustrative monthly saving</span></div></div><p class="small">${esc(r.saving_condition)}</p><p><strong>Stated interests:</strong> “${esc(r.interests)}”</p><p><strong>Plan terms:</strong> ${esc(p.terms)}</p><p class="small">Score components: frequency ${(r.components.frequency*100).toFixed(0)}%, recency ${(r.components.recency*100).toFixed(0)}%, text fit ${(r.components.text_fit*100).toFixed(0)}%, value ${(r.components.value*100).toFixed(0)}%. These are inputs, not probabilities.</p>${r.suggested_action==='nurture_first'?'<p><strong>Lower evidence:</strong> fewer than three matching visits. Consider a helpful follow-up before a membership invitation.</p>':''}<div class="rule"><h3>Prepare a conversation</h3><p>Review the plan and attendee evidence before sharing any invitation.</p><div class="draft-actions"><button id="generate" class="primary">Generate AI invitation</button><button id="template">Use factual template</button></div><p id="draft-status" role="status" class="small"></p><div id="draft"></div></div>`;
  $('generate').onclick=()=>draft('model');$('template').onclick=()=>draft('template');
}
async function draft(generationMode){
  if(state.busy)return;setBusy(true);$('draft-status').textContent=generationMode==='model'?'Local Qwen is drafting… first use loads the model.':'Preparing the factual template…';
  try{const data=await api('draft',{attendee_id:state.selected,mode:state.mode,generation_mode:generationMode});state.draft=data;
    $('draft-status').textContent=`${generationMode==='model'?'Qwen AI draft':'Factual template · no AI inference'} · ${data.generation_seconds}s · Nothing sent`;
    $('draft').innerHTML='<label for="subject">Subject</label><input type="text" id="subject"><label for="body">Invitation</label><textarea id="body"></textarea><label class="review-label"><input type="checkbox" id="reviewed"><span>I reviewed the attendance evidence, price, visit limit and all claims in this draft.</span></label><button id="download" disabled>Download reviewed draft</button><p class="draft-note">Your review is recorded locally for this demo. It does not verify identity or authorise outreach. AI checks cover selected terms and numbers only.</p>';
    $('subject').value=data.subject;$('body').value=data.body;
    $('reviewed').onchange=()=>{$('download').disabled=!$('reviewed').checked;};
    [$('subject'),$('body')].forEach(el=>el.oninput=()=>{$('reviewed').checked=false;$('download').disabled=true;});
    $('download').onclick=()=>{if(!$('reviewed').checked)return;const record={project:'Membership Opportunity Lab',fictional:true,attendee_id:state.selected,subject:$('subject').value,body:$('body').value,evidence_ids:data.evidence_ids,generation_mode:data.generation_mode,review_acknowledged:true,sent:false,reviewed_at:new Date().toISOString()};const url=URL.createObjectURL(new Blob([JSON.stringify(record,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='reviewed-membership-invitation.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
  }catch(e){$('draft-status').textContent=e.message;}finally{setBusy(false);}
}
$('baseline').onclick=()=>load('baseline');$('semantic').onclick=()=>load('semantic');
$('compare').onclick=async()=>{if(state.busy)return;setBusy(true);status('Running both modes on the same fictional snapshot…');try{const baseline=await api('shortlist?mode=baseline'),semantic=await api('shortlist?mode=semantic');const b=baseline.evaluation.splits.held_out,s=semantic.evaluation.splits.held_out;const equal=b.precision_at_5===s.precision_at_5&&b.ndcg_at_5===s.ndcg_at_5;const row=(title,x,y)=>`<tr><td>${title}</td><td>${x}</td><td>${y}</td></tr>`;$('comparison').innerHTML=`<h3>Same data. Two approaches.</h3><table><thead><tr><th>Reserved synthetic cases</th><th>Keywords</th><th>MiniLM + FAISS</th></tr></thead><tbody>${row('Precision @ 5',b.precision_at_5.toFixed(2),s.precision_at_5.toFixed(2))}${row('NDCG @ 5',b.ndcg_at_5.toFixed(2),s.ndcg_at_5.toFixed(2))}${row('Expected plan matches',b.plan_match_correct+'/'+b.plan_match_denominator,s.plan_match_correct+'/'+s.plan_match_denominator)}${row('Ranking latency',baseline.latency_ms+' ms',semantic.latency_ms+' ms')}</tbody></table><p>${equal?'Same measured relevance on this fixture. Use latency and real validation data to justify a model.':'Relevance differs on this fixture; validate against real outcomes before drawing conclusions.'} Author-created labels; not measured signup lift or independent human validation. First-use model loading can affect latency.</p>`;$('comparison').hidden=false;status('Comparison complete. Ranking and draft selections are unchanged.');}catch(e){status(e.message,true);}finally{setBusy(false);}};
api('health').then(h=>{$('health').textContent=`MiniLM ${h.embedding_available?'files ready':'not installed'} · Qwen ${h.model_available?'file ready':'not installed'}. Artifacts verify on first use.`;}).catch(()=>{$('health').textContent='Health check unavailable; baseline can still be tried.';});
load('baseline');
