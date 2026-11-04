'use strict';
let connectionCandidates=[],connectionEditing=null,modelCandidates=[];
let serviceEditorDraft=null;
function serviceEditorNavigation(section){
 return `<nav class="service-editor-tabs" aria-label="${tr('Edit section','편집 항목')}">${[['display',tr('DISPLAY','표시 정보')],['connection',tr('CONNECTION','연결 설정')]].map(([id,label])=>`<button type="button" data-editor-section="${id}" aria-pressed="${section===id}" ${section===id?'disabled':''}>${label}</button>`).join('')}</nav><p class="connection-help">${tr("Each section saves separately. Other unsaved edits stay open.","탭별로 저장합니다. 다른 탭의 미저장 변경은 유지됩니다.")}</p>`;
}
function rememberEditorSection(){
 const display=$('#serviceEditForm'),connection=$('#connectionForm');
 if(display)serviceEditorDraft.display=Object.fromEntries(new FormData(display));
 if(connection){const values=Object.fromEntries(new FormData(connection));serviceEditorDraft.connection={...connectionEditing,...values,allow_control:values.allow_control==='on'};}
}
const connectionMessages={
 invalid_probe_port:['Enter a whole-number API port from 1024 to 65535.','API 포트를 1024–65535 사이의 정수로 입력하세요.'],
 invalid_open_url:['Use an http:// or https:// app address without passwords, query parameters or fragments.','http:// 또는 https:// 앱 주소를 입력하세요. 비밀번호·쿼리·# 조각은 사용할 수 없습니다.'],
 'Invalid model directory':['Choose an existing model folder on Spark, not your phone or PC. System directories cannot be scanned.','휴대폰·PC가 아닌 Spark에 존재하는 모델 폴더를 입력하세요. 시스템 폴더는 검색할 수 없습니다.'],
 'Invalid roots':['Enter up to eight model folder paths, one per line.','모델 폴더 경로를 한 줄에 하나씩 최대 8개 입력하세요.'],
 'Wait 10 seconds between scans':['Folders saved. Wait 10 seconds before scanning again.','폴더는 저장됐습니다. 검색은 10초 후 다시 시도하세요.'],
 'A scan is already running':['A folder scan is already in progress. Try again shortly.','폴더 검색이 이미 진행 중입니다. 잠시 후 다시 시도하세요.'],
 'Search again':['The file candidate has expired or changed. Scan the folders again.','파일 후보가 만료되었거나 변경되었습니다. 폴더를 다시 검색하세요.'],
 'Inventory full':['The model inventory is limited to 128 entries. Review it on Spark.','모델 목록은 최대 128개입니다. Spark에서 등록 목록을 정리하세요.'],
check_again:['Run the connection check again.','연결 검사를 다시 실행하세요.'],scan_again:['Search services again.','서비스를 다시 검색하세요.'],service_not_loaded:['The service no longer exists.','서비스가 더 이상 존재하지 않습니다.'],probe_required:['Enter the local API port.','로컬 API 포트를 입력하세요.'],stop_before_rebinding:['Stop the service before changing its API connection.','API 연결을 바꾸기 전에 서비스를 정지하세요.'],adapter_mismatch:['A profile must use the same adapter as its service.','프로필은 서비스와 동일한 연결 유형이어야 합니다.'],already_registered:['Already registered. Open its connection settings.','이미 등록되어 있습니다. 연결 설정을 여세요.']};
function connectionError(error){return connectionMessages[error.message]?tr(...connectionMessages[error.message]):serviceError(error.message);}
function connectionForm(data){
 connectionEditing=data;
 const fields=[['name',tr('Service name','서비스 이름'),data.name||''],['profile_name',tr('Profile name','프로필 이름'),data.profile_name||'Default'],['port',tr('Local API port','로컬 API 포트'),data.port||''],['open_url',tr('Open app URL (optional)','앱 접속 주소 (선택)'),data.open_url||'']];
 showModal(`<h2 id="modalTitle">${tr('CONNECT SERVICE','서비스 연결')}</h2><p class="connection-unit">${escapeHTML(data.unit||data.name||'')}</p><form id="connectionForm"><div class="connection-fields">${fields.map(([key,label,value])=>`<label>${label}<input name="${key}" value="${escapeHTML(String(value))}" ${key==='port'?'type="number" min="1024" max="65535"':`maxlength="${key==='open_url'?300:80}"`} ${['name','profile_name'].includes(key)?'required':''} autocomplete="off"></label>`).join('')}<label>${tr('Connection type','연결 유형')}<select name="adapter">${[['openai-compatible','LLM / OpenAI API'],['comfyui','ComfyUI'],['hermes','Hermes gateway'],['process',tr('Process only','프로세스만')]].map(([value,label])=>`<option value="${value}" ${data.adapter===value?'selected':''}>${label}</option>`).join('')}</select></label>${!data.service_id?`<label>${tr('Register as','등록 위치')}<select name="parent_id"><option value="">${tr('New service card','새 서비스 카드')}</option>${serviceRows().map(s=>`<option value="${escapeHTML(s.id)}">${escapeHTML(s.name)} · ${tr('new profile','새 프로필')}</option>`).join('')}</select></label>`:''}</div><label class="connection-consent"><input name="allow_control" type="checkbox" ${data.allow_control?'checked':''}>${tr('Enable start / stop control for this existing service','이 기존 서비스의 시작·정지 제어 활성화')}</label><p class="connection-help">${tr('Uses an existing user service. Registration does not start it or change its command or model files. APIs must listen on this Spark; its own Tailscale address is supported.','기존 사용자 서비스를 연결합니다. 등록만으로 실행하거나 명령·모델 파일을 변경하지 않습니다. API는 이 Spark에서 응답해야 하며, Spark 자신의 Tailscale 주소도 지원합니다.')}</p><p id="connectionResult" role="status"></p><div class="service-confirm-actions"><button type="submit" class="button">${tr('CHECK CONNECTION','연결 검사')}</button><button type="button" class="button service-cancel" data-close="true">${tr('CANCEL','취소')}</button></div></form>`);
 if(data.service_id){$('#modalTitle').textContent=tr('EDIT SERVICE','서비스 편집');$('#modalTitle').insertAdjacentHTML('afterend',serviceEditorNavigation('connection'));}
 $('#modalKind').textContent=data.service_id?tr('SERVICE SETTINGS','서비스 설정'):tr('SERVICE REGISTRATION','서비스 등록');trackFormDraft('connectionForm');
}
async function discoverConnections(){
 const result=await api('connections/discover',{});connectionCandidates=result.candidates;resetFormDrafts();serviceEditorDraft=null;
 showModal(`<h2 id="modalTitle">${tr('FIND SERVICES','서비스 찾기')}</h2><p class="connection-help">${tr('Existing user systemd services. Docker-only and terminal processes are not included. Select a service to check and register.','기존 사용자 systemd 서비스를 조회합니다. Docker 단독·터미널 프로세스는 포함되지 않습니다. 서비스를 선택해 검사·등록하세요.')}</p><input id="connectionFilter" type="search" placeholder="${tr('Filter by service name','서비스 이름 검색')}" aria-label="${tr('Filter services','서비스 검색')}"><div class="connection-list">${result.candidates.map(c=>`<div data-connection-row="${escapeHTML(c.name.toLowerCase())}"><div><strong>${escapeHTML(c.name)}</strong><small>${serviceText(c.state)}${c.registered?' · '+tr('Registered','등록됨'):''}</small></div><button class="button secondary" data-connect-candidate="${c.id}" ${c.registered?'disabled':''}>${tr('SET UP','등록 설정')}</button></div>`).join('')||`<p>${tr('No user services found.','사용자 서비스를 찾지 못했습니다.')}</p>`}</div>${result.truncated?`<p>${tr('Showing first 128 services.','최대 128개 서비스를 표시합니다.')}</p>`:''}`);
 $('#modalKind').textContent=tr('SERVICE DISCOVERY','서비스 검색');
}
async function modelFolders(){
 const value=await api('models/roots');resetFormDrafts();serviceEditorDraft=null;
 showModal(`<h2 id="modalTitle">${tr('MODEL FILES','모델 파일 조회')}</h2><p class="connection-help">${tr('Enter up to 8 existing model folders on Spark, one per line. Discovery reads filenames only; format does not guarantee engine compatibility.','Spark의 기존 모델 폴더를 한 줄에 하나씩, 최대 8개 입력하세요. 파일명 후보만 검색하며 형식만으로 엔진 호환성을 보장하지 않습니다.')}</p><form id="modelRootsForm"><label for="modelRoots">${tr('Model folders','모델 폴더')}</label><textarea id="modelRoots" name="roots" rows="3" spellcheck="false" placeholder="~/models">${escapeHTML(value.roots.join('\n'))}</textarea><button class="button" type="submit">${tr('SAVE & SCAN','저장 후 검색')}</button></form><div id="modelFilesResult" class="connection-list" role="status">${value.inventory.map(m=>`<div><strong>${escapeHTML(m.name)}</strong><span>${m.exists?tr('Inventory only · connect a service to run','파일 목록 · 실행 서비스 연결 필요'):tr('File missing','파일 없음')}</span></div>`).join('')}</div><p class="connection-help">${tr('Files are inventory only. To run one, connect an existing service configured for it. Downloads and Docker/terminal launch setup are managed on Spark.','파일 조회는 실행 등록과 다릅니다. 실행하려면 해당 파일로 구성된 기존 서비스를 연결하세요. 다운로드와 Docker·터미널 실행 설정은 Spark에서 관리합니다.')}</p><button class="button secondary" id="connectFromFiles">${tr('CONNECT AN EXISTING SERVICE','기존 실행 서비스 연결')}</button>`);trackFormDraft('modelRootsForm');$('#modalKind').textContent=tr('MODEL INVENTORY','모델 파일 목록');
}
function connectionToolbar(){
 const toolbar=$('.service-toolbar-actions');if(toolbar&&!$('#connectionAdd'))toolbar.insertAdjacentHTML('beforeend',`<button class="button" id="connectionAdd">${tr('ADD SERVICE','서비스 추가')}</button><button class="button secondary" id="modelFolders">${tr('MODEL FILES','모델 파일')}</button>`);
 const old=$('#serviceScan');if(old)old.hidden=true;
 const guide=$('.service-guide');const guideHTML=`<summary>${tr('ADD OR REPLACE A MODEL','모델 추가·교체 안내')}</summary><p>${tr('Add service finds existing user services, checks their APIs and enables control. Add another existing service as a profile, then stop → select profile → start. Model files are inventory candidates; installing engines or generating launch commands is not performed here.','서비스 추가에서 기존 사용자 서비스를 검색하고 API 검사·제어 등록을 진행합니다. 다른 기존 서비스를 프로필로 추가한 뒤 정지 → 프로필 선택 → 시작할 수 있습니다. 모델 파일은 조회 후보이며 엔진 설치나 실행 명령 생성은 수행하지 않습니다.')}</p>`;if(guide&&guide.innerHTML!==guideHTML)guide.innerHTML=guideHTML;
}
document.addEventListener('input',event=>{if(event.target.id==='connectionFilter'){const q=event.target.value.toLowerCase();document.querySelectorAll('[data-connection-row]').forEach(row=>row.hidden=!row.dataset.connectionRow.includes(q));}});
document.addEventListener('change',event=>{if(event.target.name==='parent_id'&&event.target.value){const s=serviceRows().find(s=>s.id===event.target.value);if(s){const form=event.target.form;form.elements.name.value=s.name;form.elements.adapter.value=s.adapter;}}});
document.addEventListener('click',async event=>{
 const b=event.target.closest('button');if(!b)return;
 if(!['connectionAdd','connectFromFiles','modelFolders','liveDiscover'].includes(b.id)&&!b.dataset.connectCandidate&&!b.dataset.editorSection&&!b.dataset.connectionSave&&!b.dataset.connectionBack&&!b.dataset.modelRegister)return;
 event.preventDefault();event.stopImmediatePropagation();b.disabled=true;
 try{
  if(b.dataset.modelRegister){const m=modelCandidates.find(m=>m.id===b.dataset.modelRegister);await api('models/register',{candidate_id:m.id,name:m.name});b.textContent=tr('Registered','등록됨');b.removeAttribute('data-model-register');b.dataset.registered='true';toast(tr('Added to model inventory. No launch settings changed.','모델 목록에 등록했습니다. 실행 설정은 변경되지 않습니다.'));}
  else if(b.id==='connectionAdd'||b.id==='connectFromFiles'){if(hasUnsavedForms()){toast(tr('Save the folders or discard edits before connecting a service.','폴더를 저장하거나 변경을 버린 뒤 서비스를 연결하세요.'));return;}await discoverConnections();}
  else if(['modelFolders','liveDiscover'].includes(b.id))await modelFolders();
  else if(b.dataset.connectCandidate){const c=connectionCandidates.find(c=>c.id===b.dataset.connectCandidate);connectionForm({candidate_id:c.id,name:c.name.replace(/\.service$/,''),unit:c.name,adapter:/comfy/i.test(c.name)?'comfyui':/hermes/i.test(c.name)?'hermes':'openai-compatible',revision:liveNode.services.revision});}
  else if(b.dataset.editorSection){
   rememberEditorSection();
   if(b.dataset.editorSection==='display')showServiceEditor(serviceRows().find(s=>s.id===serviceEditorDraft.id),serviceEditorDraft.display||{});
   else {
    const data=serviceEditorDraft.connection||await api('connections/settings?id='+encodeURIComponent(serviceEditorDraft.id));
    if(!b.isConnected)return;
    connectionForm(data);
   }
  }
  else if(b.dataset.connectionBack){connectionForm(connectionEditing);}
  else if(b.dataset.connectionSave){await api('connections/save',{ticket:b.dataset.connectionSave});await finishEditorSave('connection');await refreshLive();render(false);toast(tr('Service connection saved.','서비스 연결을 저장했습니다.'));}
 }catch(error){toast(connectionError(error));}finally{b.disabled=b.dataset.registered==='true';}
},true);
document.addEventListener('submit',async event=>{
 if(!['connectionForm','modelRootsForm'].includes(event.target.id))return;event.preventDefault();event.stopImmediatePropagation();const form=event.target,b=form.querySelector('button[type=submit]');b.disabled=true;
 try{
  if(form.id==='modelRootsForm'){
   await api('models/roots',{roots:$('#modelRoots').value.split('\n').map(s=>s.trim()).filter(Boolean)});clearFormDraft('modelRootsForm');trackFormDraft('modelRootsForm');
   const data=await api('models/discover',{});modelCandidates=data.matches;
   $('#modelFilesResult').innerHTML=`<p>${data.matches.length} ${tr('candidates','개 후보')}${data.truncated?' · '+tr('Scan limit reached','검색 한도 도달'):''}</p>${data.matches.map(m=>`<div><div><strong>${escapeHTML(m.name)}</strong><small>${escapeHTML(m.path)}</small></div><button class="button secondary" data-model-register="${m.id}" ${m.registered?'disabled':''}>${m.registered?tr('Registered','등록됨'):tr('REGISTER','목록 등록')}</button></div>`).join('')}<p class="connection-help">${tr('To run a candidate, first connect the existing service configured for that model using Add service. Finding a file does not create a launch profile.','후보를 실행하려면 해당 모델로 설정된 기존 서비스를 ‘서비스 추가’에서 연결하세요. 파일 발견만으로 실행 프로필이 생성되지는 않습니다.')}</p>`;
  }else{
   const f=new FormData(form),d=connectionEditing,payload={revision:d.revision,name:f.get('name'),profile_name:f.get('profile_name'),adapter:f.get('adapter'),port:f.get('port')?Number(f.get('port')):null,allow_control:f.get('allow_control')==='on',open_url:f.get('open_url')};
   if(d.service_id)payload.service_id=d.service_id;else{payload.candidate_id=d.candidate_id;if(f.get('parent_id'))payload.parent_id=f.get('parent_id');}
   connectionEditing={...d,...Object.fromEntries(f),allow_control:f.get('allow_control')==='on'};if(serviceEditorDraft)rememberEditorSection();const checked=await api('connections/check',payload);if(!form.isConnected)return;
   showModal(`<h2 id="modalTitle">${tr('REVIEW CONNECTION','연결 확인')}</h2><p class="connection-unit">${escapeHTML(checked.unit)}</p><div class="connection-review"><span>${tr('Service','서비스')}</span><b>${serviceText(checked.state)}</b><span>API</span><b>${checked.state!=='running'?tr('Not checked · service not running','미검사 · 서비스 실행 중 아님'):serviceText(checked.readiness)}</b><span>${tr('Control','제어')}</span><b>${checked.allow_control?tr('Enabled','활성화'):tr('Read only','조회 전용')}</b></div><p>${checked.readiness==='ready'?tr('API responded. This does not benchmark inference.','API 응답을 확인했습니다. 추론 성능 검증은 별도입니다.'):tr('API readiness is not confirmed. Saving only registers settings. If the service is stopped, start it; if already running, check its connection.','API 준비 상태는 확인되지 않았습니다. 저장은 설정만 등록합니다. 정지 상태면 시작하고, 이미 실행 중이면 연결 설정을 확인하세요.')}</p><div class="service-confirm-actions"><button class="button" data-connection-save="${checked.ticket}">${tr('SAVE CONNECTION','연결 저장')}</button><button class="button secondary" data-connection-back="true">${tr('BACK TO EDIT','편집으로 돌아가기')}</button></div>`);$('#modalKind').textContent=tr('CONNECTION REVIEW','연결 설정 검토');
  }
 }catch(error){const target=$('#connectionResult')||$('#modelFilesResult');if(target)target.textContent=connectionError(error);else toast(connectionError(error));}finally{b.disabled=b.dataset.registered==='true';}
},true);

render(false);
