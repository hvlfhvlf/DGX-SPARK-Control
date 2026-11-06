'use strict';
// Browser-only interaction state. Never stores credentials or model commands.
const formDrafts=new Map();
let nameDraft=null,nameDraftDirty=false,lastSuccessfulRefresh=null,discardReturnFocus=null;
function formSignature(form){return JSON.stringify([...new FormData(form)].map(([k,v])=>[k,String(v)]));}
function resetFormDrafts(){formDrafts.clear();document.getElementById('discardDraftPrompt')?.remove();}
function trackFormDraft(id){const form=document.getElementById(id);if(!form)return;const value=formSignature(form);if(!formDrafts.has(id))formDrafts.set(id,{baseline:value,current:value});document.querySelector('.modal-card').classList.add('editing-modal');}
function updateFormDraft(form){const record=formDrafts.get(form?.id);if(record)record.current=formSignature(form);}
function hasFormDraft(id){const record=formDrafts.get(id);return !!record&&record.baseline!==record.current;}
function hasUnsavedForms(){return [...formDrafts.keys()].some(hasFormDraft);}
function clearFormDraft(id){formDrafts.delete(id);}
function allowModalClose(){
 if(!hasUnsavedForms())return true;
 if(!document.getElementById('discardDraftPrompt')){
  discardReturnFocus=document.activeElement;
  document.getElementById('modalContent').insertAdjacentHTML('beforeend',`<div id="discardDraftPrompt" class="draft-prompt" role="alertdialog" aria-modal="true" aria-labelledby="discardDraftTitle"><h3 id="discardDraftTitle">${tr('Discard unsaved changes?','저장하지 않은 변경을 버릴까요?')}</h3><p>${tr('Your edits have not been saved.','입력한 내용은 아직 저장되지 않았습니다.')}</p><div class="service-confirm-actions"><button class="button" data-draft-keep>${tr('KEEP EDITING','계속 편집')}</button><button class="button service-cancel" data-draft-discard>${tr('DISCARD','변경 버리기')}</button></div></div>`);
  document.querySelector('[data-draft-keep]').focus();
 }
 return false;
}
function keepEditing(){document.getElementById('discardDraftPrompt')?.remove();if(discardReturnFocus?.isConnected)discardReturnFocus.focus();}
function inlineFormError(message){let el=document.getElementById('editorError');if(!el){el=document.createElement('p');el.id='editorError';el.className='editor-error';el.setAttribute('role','alert');document.querySelector('#serviceEditForm .service-confirm-actions')?.before(el);}if(el){el.textContent=message;el.scrollIntoView({block:'nearest'});}}
async function finishEditorSave(section){
 clearFormDraft(section==='display'?'serviceEditForm':'connectionForm');
 await reloadServiceDisplay();
 const other=section==='display'?'connectionForm':'serviceEditForm';
 if(hasFormDraft(other)&&serviceEditorDraft){
  const s=serviceRows().find(row=>row.id===serviceEditorDraft.id);
  if(!s){toast(tr('Service changed. Your other draft is still open.','서비스가 변경되었습니다. 다른 초안은 유지됩니다.'));return;}
  if(section==='display')connectionForm({...serviceEditorDraft.connection,revision:liveNode.services.revision});
  else showServiceEditor(s,serviceEditorDraft.display||{});
  toast(tr('Saved. Review the remaining unsaved section.','저장했습니다. 다른 탭의 남은 변경을 확인하세요.'));
 }else closeModal(true);
}
function patchRetainingInteraction(el,html){
 if(!el||el.innerHTML===html)return;
 const focused=el.contains(document.activeElement)?document.activeElement:null;
 if(focused?.tagName==='SELECT')return; // Do not dismiss an open native chooser.
 const focusId=focused?.id,open=[...el.querySelectorAll('details[id]')].filter(e=>e.open).map(e=>e.id);
 el.innerHTML=html;
 open.forEach(id=>{const d=document.getElementById(id);if(d&&el.contains(d))d.open=true;});
 if(focusId)document.getElementById(focusId)?.focus({preventScroll:true});
}
function smallRate(value){return value==null?'—':value>0&&value<0.1?'<0.1':Number(value).toFixed(1);}
function syncConnectionStatus(){
 const el=document.getElementById('connectionLabel');if(!el)return;
 const delayed=!!liveNode.connectionDelayed;
 el.textContent=!liveNode.token?tr('SIGN IN REQUIRED','로그인 필요'):delayed?tr('UPDATE DELAYED','갱신 지연'):liveNode.connected?tr('NODE ONLINE','연결됨'):!liveNode.statusChecked?tr('CONNECTING','연결 확인 중'):tr('CONNECTION LOST','연결 끊김');
 el.title=lastSuccessfulRefresh?tr('Last response: ','마지막 응답: ')+new Date(lastSuccessfulRefresh).toLocaleTimeString():tr('Waiting for server','서버 응답 대기');
 document.getElementById('connectionDot')?.classList.toggle('offline',!liveNode.connected||delayed);
 const parts=[];
 if(liveNode.historyError&&typeof needsHistory==='function'&&needsHistory())parts.push(tr('Graph history','그래프 이력'));
 if(liveNode.servicesConnected===false)parts.push(tr('Service status','서비스 상태'));
 if(liveNode.eventsError&&typeof state!=='undefined'&&state.view==='logs')parts.push(tr('Activity','기록'));
 if(liveNode.settingsError)parts.push(tr('Settings','설정'));
 if(liveNode.hardwareError)parts.push(tr('Hardware identity','장치 정보'));
 if(liveNode.displayError)parts.push(tr('Screen update','화면 갱신'));
 let notice=document.getElementById('connectionNotice');
 if(!notice){notice=document.createElement('div');notice.id='connectionNotice';notice.setAttribute('role','status');document.querySelector('.context-bar')?.after(notice);}
 notice.hidden=!liveNode.token||!liveNode.statusChecked||liveNode.connected&&!delayed&&!parts.length;
 const stamp=lastSuccessfulRefresh?tr(' Last response ',' 마지막 응답 ')+new Date(lastSuccessfulRefresh).toLocaleTimeString():'';
 notice.textContent=delayed?tr('Update delayed. Retrying; controls are paused until a fresh response.','갱신이 지연됩니다. 재확인 중이며 새 응답까지 제어를 잠시 제한합니다.')+stamp:!liveNode.connected?tr('Connection lost. Retrying automatically. Unsaved edits are kept.','연결이 끊겼습니다. 자동 재연결 중이며 입력 내용은 유지됩니다.')+stamp:parts.length?parts.join(' · ')+tr(' update delayed. Node connection is available; retrying automatically.',' 갱신 지연. 서버는 연결되어 있으며 자동으로 다시 확인합니다.'):'';
}
function appAccess(s){
 if(!s.open_url)return {enabled:false,label:''};
 if(typeof liveNode!=='undefined'&&(liveNode.connected===false||liveNode.servicesConnected===false))return {enabled:false,label:tr('STATUS UNAVAILABLE','상태 확인 불가')};
 if(s.state==='unknown')return {enabled:false,label:tr('STATUS UNAVAILABLE','상태 확인 불가')};
 if(serviceBusy(s)||['starting','stopping'].includes(s.state))return {enabled:false,label:tr('PLEASE WAIT','처리 중')};
 if(s.state!=='running')return {enabled:false,label:tr('START TO OPEN','실행 후 열기')};
 if(s.readiness==='unreachable')return {enabled:false,label:tr('API NOT RESPONDING','API 응답 없음')};
 if(s.readiness==='loading')return {enabled:false,label:tr('APP NOT READY','접속 준비 중')};
 if(!['ready','unsupported'].includes(s.readiness))return {enabled:false,label:tr('CHECKING STATUS','상태 확인 중')};
 return {enabled:true,label:tr('OPEN APP','앱 열기')};
}
function appConnectionNote(s){return s.state==='running'&&s.readiness==='unsupported'?tr('Process running confirmed · Connection status not checked','프로세스 실행 확인 · 연결 상태 미검사'):'';}
function appAccessMarkup(s){const a=appAccess(s);if(!s.open_url)return '';if(a.enabled&&s.authenticated_launch)return `<button class="button secondary service-open" data-service-open data-auth-app="${escapeHTML(s.id)}">${a.label} ${arrowIcon()}</button>`;return a.enabled?`<a class="button secondary service-open" data-service-open href="${escapeHTML(s.open_url)}" target="_blank" rel="noopener noreferrer">${a.label} ${arrowIcon()}</a>`:`<span class="button secondary service-open unavailable" data-service-open aria-disabled="true">${a.label}</span>`;}
document.addEventListener('click',async event=>{
 const button=event.target.closest('[data-auth-app]');if(!button)return;
 event.preventDefault();if(button.disabled)return;
 const tab=window.open('about:blank','_blank');
 if(!tab){toast(tr('Allow pop-ups for this dashboard, then try again.','대시보드의 팝업을 허용한 뒤 다시 눌러 주세요.'));return;}
 tab.opener=null;button.disabled=true;
 try{
  const id=button.dataset.authApp,s=serviceRows().find(row=>row.id===id);
  if(!s||!appAccess(s).enabled)throw Error();
  const result=await api('services/open',{id,revision:liveNode.services.revision});
  const url=new URL(result.url),base=new URL(s.open_url);
  if(url.protocol!=='https:'||url.origin!==base.origin||url.pathname!=='/'||url.username||url.password||url.hash)throw Error();
  if(!tab.closed)tab.location.replace(url.href);
 }catch(error){tab.close();toast(tr('Cannot open the app. Check that the service is running, refresh and try again.','앱을 열 수 없습니다. 서비스 실행 상태를 확인하고 새로고침 후 다시 시도하세요.'));}
 finally{if(button.isConnected)button.disabled=false;}
});
document.addEventListener('input',event=>{updateFormDraft(event.target.form);if(event.target.id==='sparkNameInput'){nameDraft=event.target.value;nameDraftDirty=nameDraft!==preferences.sparkName;}});
document.addEventListener('change',event=>updateFormDraft(event.target.form));
document.addEventListener('click',event=>{const b=event.target.closest('button');if(!b)return;if(b.hasAttribute('data-draft-keep')){event.stopImmediatePropagation();keepEditing();}if(b.hasAttribute('data-draft-discard')){event.stopImmediatePropagation();closeModal(true);}},true);
document.addEventListener('keydown',event=>{const prompt=document.getElementById('discardDraftPrompt');if(!prompt)return;if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();keepEditing();}else if(event.key==='Tab'){const buttons=prompt.querySelectorAll('button'),first=buttons[0],last=buttons[buttons.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}},true);
window.addEventListener('beforeunload',event=>{if(hasUnsavedForms()){event.preventDefault();event.returnValue='';}});
