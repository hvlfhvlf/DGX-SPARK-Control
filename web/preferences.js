'use strict';
// Browser preferences only. Discovery results are fixtures, never filesystem reads.
const preferenceDefaults = {accent:'lime',density:'comfortable',home:'overview',sparkName:'DGX_SPARK',hero:true,motion:true};
let preferences = {...preferenceDefaults};
try {
  const saved = JSON.parse(localStorage.getItem('spark.preferences.v1') || '{}');
  for (const key of ['accent','density','home']) {
    const allowed = {accent:['lime','lavender','ice'],density:['comfortable','compact'],home:['overview','models','jobs','settings']}[key];
    if (allowed.includes(saved[key])) preferences[key] = saved[key];
  }
  if(typeof saved.sparkName==='string'&&saved.sparkName.trim()) preferences.sparkName=saved.sparkName.trim().slice(0,32);
  for (const key of ['hero','motion']) if (typeof saved[key] === 'boolean') preferences[key] = saved[key];
} catch (_) { /* Private modes and corrupt storage fall back to usable defaults. */ }
let discoveryScanned = false;
function applyPreferences() {
  const name=document.getElementById('sparkDisplayName');
  if(name){name.textContent=preferences.sparkName;name.title=preferences.sparkName;}
  document.body.dataset.accent = preferences.accent;
  document.body.dataset.density = preferences.density;
  document.body.classList.toggle('hide-hero',!preferences.hero);
}
function savePreferences() {
  applyPreferences();
  try { localStorage.setItem('spark.preferences.v1',JSON.stringify(preferences)); }
  catch (_) { toast('Applied for this session. Browser storage is unavailable.'); }
}
function preferenceSelect(key,label,options) {
  return `<select data-preference="${key}" aria-label="${label}">${options.map(([v,n])=>`<option value="${v}" ${preferences[key]===v?'selected':''}>${n}</option>`).join('')}</select>`;
}
function settingsView() {
  const pending = models.some(m=>m.id==='discovered-demo');
  return pageHeading('SYSTEM SETTINGS','05','MAKE THIS SPACE YOURS.') + `<div class="settings-grid settings-primary">
  <section class="panel"><div class="panel-top"><h2 class="panel-title">PERSONALIZATION</h2><span class="tiny">THIS BROWSER</span></div>
  <form id="sparkNameForm" class="setting-row spark-name-row"><div><h3><label for="sparkNameInput">Spark name</label></h3><p>A display name for this Spark. Saved in this browser; the system hostname stays unchanged.</p></div><div class="spark-name-controls"><input id="sparkNameInput" name="sparkName" type="text" required maxlength="32" pattern=".*\\S.*" value="${escapeHTML(preferences.sparkName)}" autocomplete="off" aria-label="Spark name" placeholder="My Spark"><button type="submit" class="button secondary">SAVE NAME</button></div></form>
  <div class="setting-row"><div><h3>Accent color</h3><p>Choose the interface highlight. Hardware artwork keeps its original colors.</p></div>${preferenceSelect('accent','Accent color',[['lime','Acid lime'],['lavender','Lavender'],['ice','Ice blue']])}</div>
  <div class="setting-row"><div><h3>Layout density</h3><p>Adjust panel spacing without shrinking the text.</p></div>${preferenceSelect('density','Layout density',[['comfortable','Comfortable'],['compact','Compact']])}</div>
  <div class="setting-row"><div><h3>Start page</h3><p>Used when opening the dashboard without a page link.</p></div>${preferenceSelect('home','Start page',[['overview','Overview'],['models','Models'],['jobs','Jobs'],['settings','Settings']])}</div>
  <div class="setting-row"><div><h3>Overview artwork</h3><p>Hide the large hero to put telemetry first.</p></div>${switchInput('heroToggle',preferences.hero,'Overview artwork')}</div>
  <div class="setting-row"><div><h3>Reset preferences</h3><p>Appearance is saved on this browser, separately from the demo session.</p></div><button class="button secondary" id="resetPreferences">RESTORE</button></div></section>
  <section class="panel"><div class="panel-top"><h2 class="panel-title">MODEL DISCOVERY</h2>${badge('PREVIEW','off')}</div>
  <div class="discovery-intro"><p>Find model files, review changes, then register them. Finding weights does not mean an engine is ready to run.</p><div class="discovery-sources"><span>MODEL FOLDERS</span><span>HF CACHE</span><span>ENGINE CATALOGS</span></div><p class="tiny muted">Illustrative sources only. No directories or services are accessed.</p><button class="button" id="scanModels">${discoveryScanned?'RESCAN DEMO':'SCAN DEMO MODELS'} ${arrowIcon()}</button></div>
  ${discoveryScanned?`<div class="discovery-row"><div><strong>Qwen 3.8 Flash Next</strong><small>Matched to existing registry entry</small></div>${badge('REGISTERED','off')}</div>
  <div class="discovery-row"><div><strong>Local LLM · example.gguf</strong><small>${pending?'Registered draft · engine setup required':'New file · engine and compatibility unverified'}</small></div><button class="button secondary" id="reviewDiscovered" ${pending?'disabled':''}>${pending?'ADDED':'REVIEW'}</button></div>
  <div class="discovery-row"><div><strong>Retired model · example</strong><small>Missing file example. Retain metadata until reviewed.</small></div>${badge('MISSING','warn')}</div>`:'<div class="empty-note">Run the demo scan to preview registered, new and missing model states.</div>'}
  </section></div>
  <section class="panel maintenance-panel"><div class="panel-top"><h2 class="panel-title">LLM MAINTENANCE HANDOFF</h2><span class="tiny">INSTALL / REPLACE / REMOVE</span></div><div class="maintenance-body"><div><h3>Update the registry. Keep the dashboard.</h3><p>Give your coding LLM the maintenance guide. It should update model metadata and engine adapters, verify readiness and report the result. A new model should not require rewriting the interface.</p></div><a class="button secondary" href="MODEL-MAINTENANCE.md" download>DOWNLOAD GUIDE ↓</a></div><ol class="handoff-steps"><li>Inspect paths &amp; services</li><li>Review registry changes</li><li>Validate &amp; smoke-test</li><li>Rescan &amp; confirm status</li></ol></section>
  ${prototypeSettings()}`;
}
document.addEventListener('change',event=>{
  const el=event.target;
  if(el.dataset.preference){preferences[el.dataset.preference]=el.value;savePreferences();toast('Preference saved in this browser.');}
  if(el.id==='heroToggle'){preferences.hero=el.checked;savePreferences();}
});
document.addEventListener('click',event=>{
  const button=event.target.closest('button'); if(!button||button.disabled)return;
  if(button.id==='resetPreferences'){preferences={...preferenceDefaults};savePreferences();setMotion(preferences.motion);render(false);toast('Personal preferences restored.');}
  if(button.id==='scanModels'){discoveryScanned=true;log('Demo inventory scan: registered, new and missing fixtures. No filesystem accessed.');render(false);toast('Demo scan complete. No DGX connection.');}
  if(button.id==='reviewDiscovered')showModal(`<h2 id="modalTitle">REGISTER MODEL?</h2><p>This is a fictional GGUF discovery result. Add its metadata to the session model bay as an unverified draft. It cannot be launched until an engine adapter is configured.</p><dl><dt>MODEL</dt><dd>Local LLM example</dd><dt>FORMAT</dt><dd>GGUF (demo)</dd><dt>ENGINE / MEMORY</dt><dd>UNVERIFIED</dd><dt>ACTION</dt><dd>METADATA ONLY</dd></dl><div class="button-row"><button class="button" id="registerDiscovered">ADD DRAFT</button><button class="button secondary" data-close="true">CANCEL</button></div>`);
  if(button.id==='registerDiscovered'){
    if(!models.some(m=>m.id==='discovered-demo'))models.push({id:'discovered-demo',name:'Local LLM example',short:'Local LLM',runner:'UNCONFIGURED',type:'LLM',glyph:'+',color:'',context:'UNVERIFIED',memory:'UNVERIFIED',description:'Discovered demo file. Configure and verify an engine before use.',runnable:false});
    closeModal();log('Demo model metadata registered as a draft. No files installed.');render(false);toast('Draft added. View it in Models.');
  }
});

// Store a display label without changing the remote system hostname.
document.addEventListener('submit',event=>{
 if(event.target.id!=='sparkNameForm')return;
 event.preventDefault();
 const input=document.getElementById('sparkNameInput');
 const name=input.value.trim().slice(0,32);
 if(!name)return;
 preferences.sparkName=name;input.value=name;savePreferences();
 toast('Spark name applied.');
});
