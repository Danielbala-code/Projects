'use strict';
const $ = id => document.getElementById(id);
let current = null;
let busy = false;
let dirty = false;

function notice(message, error = false) {
  $('notice').textContent = message;
  $('notice').className = error ? 'notice error' : 'notice';
  $('notice').hidden = !message;
}

async function api(path, options = {}) {
  const response = await fetch(path, options);
  if (!response.ok) {
    let message = 'The request failed. Please retry.';
    try { const body = await response.json(); message = typeof body.detail === 'string' ? body.detail : 'Check the instruction fields and try again.'; } catch (_) { /* retain useful fallback */ }
    throw new Error(message);
  }
  return response.json();
}

function jsonRequest(method, body) {
  return {method, headers: {'Content-Type': 'application/json'}, body: JSON.stringify(body)};
}

async function run(action, message) {
  if (busy) return;
  busy = true;
  document.querySelectorAll('button').forEach(button => button.disabled = true);
  $('file').disabled = true;
  notice(message);
  try { await action(); } catch (error) { notice(error.message, true); }
  finally {
    busy = false;
    document.querySelectorAll('button').forEach(button => button.disabled = false);
    $('file').disabled = false;
    updateApproval();
  }
}

function markDirty() {
  dirty = true;
  $('acknowledged').checked = false;
  updateApproval();
  notice('You have unsaved edits. Save them, then review and acknowledge again.');
}

function updateApproval() {
  const ready = current && current.draft && !dirty && !current.citation_errors.length;
  $('approve').disabled = busy || !ready || !$('acknowledged').checked;
  $('approve').hidden = Boolean(current?.approved && !dirty);
  $('download').hidden = !(current?.approved && !dirty);
  $('nav-download').classList.toggle('active', Boolean(current?.approved && !dirty));
}

function addStep(step, index) {
  const card = document.createElement('section'); card.className = 'step';
  const heading = document.createElement('div'); heading.className = 'step-heading';
  const number = document.createElement('span'); number.textContent = `INSTRUCTION ${String(index + 1).padStart(2, '0')}`;
  const remove = document.createElement('button'); remove.className = 'text-button'; remove.type = 'button'; remove.textContent = 'Remove';
  remove.addEventListener('click', () => {card.remove(); markDirty();});
  heading.append(number, remove); card.append(heading);
  for (const [key, label, max] of [['action', 'Instruction', 600], ['quote', 'Exact supporting quote', 1000]]) {
    const field = document.createElement('label'); field.className = 'field'; field.textContent = label;
    const input = document.createElement('textarea'); input.rows = key === 'quote' ? 3 : 2; input.dataset.key = key; input.maxLength = max; input.value = step[key];
    input.addEventListener('input', markDirty); field.append(input); card.append(field);
  }
  const label = document.createElement('label'); label.className = 'page-label'; label.textContent = 'Source page ';
  const page = document.createElement('input'); page.type = 'number'; page.min = 1; page.max = 10; page.dataset.key = 'page'; page.value = step.page; page.addEventListener('input', markDirty); label.append(page); card.append(label);
  $('steps').append(card);
}

function readDraft() {
  return {purpose: $('purpose').value, steps: [...$('steps').children].map(card => ({action: card.querySelector('[data-key=action]').value, quote: card.querySelector('[data-key=quote]').value, page: Number(card.querySelector('[data-key=page]').value)}))};
}

function render(data) {
  current = data; dirty = false;
  $('choose').hidden = true; $('workspace').hidden = false;
  $('filename').textContent = data.filename;
  $('source-kind').textContent = data.sample ? 'FICTIONAL SAMPLE · NOT COMPANY POLICY' : 'YOUR SOURCE DOCUMENT';
  $('source-meta').textContent = `${data.pages.length} source page${data.pages.length === 1 ? '' : 's'} · Session expires after one hour`;
  $('source-pages').replaceChildren();
  for (const page of data.pages) {
    const label = document.createElement('h4'); label.textContent = `PAGE ${page.page}`;
    const text = document.createElement('pre'); text.textContent = page.text;
    $('source-pages').append(label, text);
  }
  $('preview').hidden = !data.sample;
  $('empty-draft').hidden = Boolean(data.draft);
  $('draft-content').hidden = !data.draft; $('approval').hidden = !data.draft;
  $('nav-review').classList.toggle('active', Boolean(data.draft));
  $('nav-choose').classList.toggle('active', !data.draft);
  $('acknowledged').checked = false;
  if (data.draft) {
    $('purpose').value = data.draft.purpose;
    $('steps').replaceChildren(); data.draft.steps.forEach(addStep);
    $('step-count').textContent = `${data.draft.steps.length} INSTRUCTIONS`;
    $('markdown').value = data.markdown;
    $('draft-mode').textContent = data.mode === 'sample-preview' ? 'Sample preview · no model inference' : `Local Qwen draft · ${data.generation_seconds}s`;
    const errors = data.citation_errors;
    $('citation-status').textContent = errors.length ? errors.join('\n') : 'All supporting quotes were found in the source. Check their meaning and coverage before approval.';
    $('citation-status').className = errors.length ? 'citation-status error' : 'citation-status';
    $('download').href = `/api/procedures/${data.id}/download`;
  } else { $('step-count').textContent = 'AWAITING DRAFT'; $('draft-mode').textContent = 'Source ready for drafting'; }
  updateApproval();
}

$('load-sample').addEventListener('click', () => run(async () => {render(await api('/api/sample', {method: 'POST'})); notice('Fictional sample loaded. Choose live generation or the labelled preview.');}, 'Loading example…'));
$('file').addEventListener('change', () => {
  const file = $('file').files[0]; if (!file) return;
  if (file.size > 5 * 1024 * 1024) {notice('Choose a document smaller than 5 MB.', true); $('file').value = ''; return;}
  run(async () => {const form = new FormData(); form.append('file', file); render(await api('/api/procedures', {method: 'POST', body: form})); notice('Source loaded. Inspect it and generate your draft.');}, 'Reading your document…');
});
$('generate').addEventListener('click', () => run(async () => {render(await api(`/api/procedures/${current.id}/draft`, jsonRequest('POST', {mode: 'generate'}))); notice('Draft generated. Inspect every instruction and check for anything missing.');}, 'Drafting with local Qwen. The first run loads the model; this may take a minute…'));
$('preview').addEventListener('click', () => run(async () => {render(await api(`/api/procedures/${current.id}/draft`, jsonRequest('POST', {mode: 'preview'}))); notice('This is a fixed fictional sample preview. No model inference was used.');}, 'Loading sample preview…'));
$('save').addEventListener('click', () => run(async () => {render(await api(`/api/procedures/${current.id}/draft`, jsonRequest('PUT', {draft: readDraft()}))); notice('Instructions saved. The skill Markdown was rebuilt. Review and acknowledge again.');}, 'Saving reviewed instructions…'));
$('save-markdown').addEventListener('click', () => run(async () => {render(await api(`/api/procedures/${current.id}/draft`, jsonRequest('PUT', {draft: readDraft(), markdown: $('markdown').value}))); notice('Markdown edits saved. Review their meaning and acknowledge again.');}, 'Saving Markdown edits…'));
$('add-step').addEventListener('click', () => {if ($('steps').children.length >= 16) {notice('This demo supports at most 16 instructions.', true); return;} addStep({action: '', quote: '', page: 1}, $('steps').children.length); markDirty();});
$('purpose').addEventListener('input', markDirty); $('markdown').addEventListener('input', markDirty);
$('acknowledged').addEventListener('change', updateApproval);
$('approve').addEventListener('click', () => run(async () => {render(await api(`/api/procedures/${current.id}/approve`, jsonRequest('POST', {acknowledged: $('acknowledged').checked}))); notice('Review recorded. Download the skill and its source references.');}, 'Recording your review…'));
$('start-over').addEventListener('click', () => {current = null; dirty = false; $('workspace').hidden = true; $('choose').hidden = false; $('file').value = ''; $('nav-choose').classList.add('active'); $('nav-review').classList.remove('active'); $('nav-download').classList.remove('active'); notice('');});
api('/api/health').then(status => {$('model-status').textContent = status.model_available ? '● Local Qwen model ready' : '○ Sample preview ready · model not downloaded';}).catch(() => {$('model-status').textContent = 'Server unavailable';});
