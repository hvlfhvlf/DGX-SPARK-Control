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
 el.textContent=liveNode.connected?tr('NODE ONLINE','연결됨'):tr('CONNECTION LOST','연결 끊김');
 el.title=lastSuccessfulRefresh?tr('Last response: ','마지막 응답: ')+new Date(lastSuccessfulRefresh).toLocaleTimeString():tr('Waiting for server','서버 응답 대기');
 document.getElementById('connectionDot')?.classList.toggle('offline',!liveNode.connected);
 let notice=document.getElementById('connectionNotice');
 if(!notice){notice=document.createElement('div');notice.id='connectionNotice';notice.setAttribute('role','status');document.querySelector('.context-bar')?.after(notice);}
 notice.hidden=liveNode.connected||!liveNode.token;
 notice.textContent=tr('Connection lost. Retrying automatically. Unsaved edits are kept. ','연결이 끊겼습니다. 자동 재연결 중이며 입력 내용은 유지됩니다. ')+(lastSuccessfulRefresh?tr('Last response ','마지막 응답 ')+new Date(lastSuccessfulRefresh).toLocaleTimeString():'');
}
function appAccess(s){
 if(!s.open_url)return {enabled:false,label:''};
 if(s.state!=='running')return {enabled:false,label:tr('START TO OPEN','실행 후 열기')};
 if(serviceBusy(s)||['loading','unreachable'].includes(s.readiness))return {enabled:false,label:tr('APP NOT READY','접속 준비 중')};
 return {enabled:true,label:s.readiness==='ready'?tr('OPEN APP','앱 열기'):tr('OPEN · UNVERIFIED','열기 · 미확인')};
}
function appAccessMarkup(s){const a=appAccess(s);if(!s.open_url)return '';return a.enabled?`<a class="button secondary service-open" data-service-open href="${escapeHTML(s.open_url)}" target="_blank" rel="noopener noreferrer">${a.label} ${arrowIcon()}</a>`:`<span class="button secondary service-open unavailable" data-service-open aria-disabled="true">${a.label}</span>`;}
document.addEventListener('input',event=>{updateFormDraft(event.target.form);if(event.target.id==='sparkNameInput'){nameDraft=event.target.value;nameDraftDirty=nameDraft!==preferences.sparkName;}});
document.addEventListener('change',event=>updateFormDraft(event.target.form));
document.addEventListener('click',event=>{const b=event.target.closest('button');if(!b)return;if(b.hasAttribute('data-draft-keep')){event.stopImmediatePropagation();keepEditing();}if(b.hasAttribute('data-draft-discard')){event.stopImmediatePropagation();closeModal(true);}if(b.id==='cancelSparkName'){nameDraftDirty=false;nameDraft=null;document.getElementById('sparkNameInput').value=preferences.sparkName;}},true);
document.addEventListener('keydown',event=>{const prompt=document.getElementById('discardDraftPrompt');if(!prompt)return;if(event.key==='Escape'){event.preventDefault();event.stopImmediatePropagation();keepEditing();}else if(event.key==='Tab'){const buttons=prompt.querySelectorAll('button'),first=buttons[0],last=buttons[buttons.length-1];if(event.shiftKey&&document.activeElement===first){event.preventDefault();last.focus();}else if(!event.shiftKey&&document.activeElement===last){event.preventDefault();first.focus();}}},true);
window.addEventListener('beforeunload',event=>{if(hasUnsavedForms()||nameDraftDirty){event.preventDefault();event.returnValue='';}});
