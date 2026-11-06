'use strict';
// Only the visible Details dialog polls update state. Check is explicit, never automatic.
const updateBusyStates=['queued','backup','install','validate','restoring'];
const updateMessages={
 update_stop_required:['Stop this service in Model Bay first, then return to update. No service was stopped or changed.','모델 탭에서 이 서비스를 먼저 정지한 후 업데이트하세요. 서비스를 정지하거나 변경하지 않았습니다.'],
 update_install_in_use:['Another process uses this installation. Close its other windows/profiles on Spark first.','같은 설치본을 사용하는 다른 프로세스가 있습니다. Spark에서 다른 창·프로필을 먼저 종료하세요.'],
 update_in_progress:['An app update or recovery is in progress. Service controls and system power are temporarily locked.','앱 업데이트 또는 복구 중입니다. 서비스 제어와 시스템 전원을 잠시 사용할 수 없습니다.'],
 update_check_failed:['Could not contact the official update source. Check the network and try again.','공식 업데이트 서버에 연결하지 못했습니다. 네트워크를 확인하고 다시 시도하세요.'],
 update_check_cooldown:['Wait a few seconds before checking again.','잠시 후 다시 확인하세요.'],
 update_review_expired:['The version or settings changed, or the check expired. Check for updates again.','버전·설정이 바뀌었거나 확인 시간이 만료됐습니다. 업데이트를 다시 확인하세요.'],
 update_local_changes:['Local source edits were found. Review them on Spark before updating.','소스에 직접 수정한 내용이 있습니다. Spark에서 검토한 뒤 업데이트하세요.'],
 update_channel_review_required:['This channel would downgrade or switch branches. Review the update channel on Spark.','현재 채널로 변경하면 이전 버전이나 다른 브랜치로 전환됩니다. Spark에서 업데이트 채널을 검토하세요.'],
 update_status_unavailable:['Installed version could not be verified. Check the local update configuration.','설치 버전을 확인하지 못했습니다. 로컬 업데이트 설정을 확인하세요.'],
 update_binding_changed:['The launch profile changed. Reconnect its update configuration on Spark.','실행 프로필이 변경됐습니다. Spark에서 업데이트 설정을 다시 연결하세요.'],
 update_guard_missing:['Update protection needs local setup on Spark.','Spark에서 업데이트 보호 설정이 필요합니다.'],
 update_source_changed:['The installation does not match the configured official source. Review it on Spark.','설치본이 설정된 공식 소스와 일치하지 않습니다. Spark에서 확인하세요.'],
 update_disk_space:['There is not enough free space for a backup and recovery copy.','백업과 복구 사본을 만들 디스크 공간이 부족합니다.'],
 update_backup_review_required:['A previous update needs review on Spark. Resolve its retained recovery files before another update to avoid accumulating copies.','이전 업데이트의 복구 자료를 Spark에서 검토해야 합니다. 사본이 계속 쌓이지 않도록 정리 확인 전에는 다음 업데이트를 차단합니다.'],
 update_backup_cleanup_required:['Backup cleanup needs attention on Spark. Check the retained update record before trying again.','Spark에서 이전 백업 정리를 확인해야 합니다. 다시 시도하기 전에 업데이트 기록을 확인하세요.'],
 update_failed_restored:['Update failed. The previous version, environment and app data were restored. The service remains stopped.','업데이트에 실패해 이전 버전·실행 환경·앱 데이터를 복원했습니다. 서비스는 정지 상태입니다.'],
 update_recovery_needs_local_review:['Recovery needs local attention. Backups are retained and service starts remain blocked.','복구에 로컬 확인이 필요합니다. 백업을 보존했으며 서비스 시작은 차단됩니다.'],
 update_complete_stopped:['Installed and basic checks passed. Start the service to verify app operation.','설치와 기본 검사를 통과했습니다. 서비스를 시작해 실제 앱 동작을 확인하세요.'],
 update_complete_review:['Installed, but Hermes doctor failed both before and after updating. Review local diagnostics for new or existing issues before starting; app operation is not verified.','설치는 완료됐지만 업데이트 전·후 모두 Hermes 진단을 통과하지 못했습니다. 기존·신규 문제를 로컬에서 검토한 후 시작하세요. 실제 앱 동작은 미검증입니다.'],
 update_worker_not_started:['Updater startup could not be confirmed. Starts remain blocked until the worker or local recovery resolves this.','업데이트 작업의 시작 여부를 확인하지 못했습니다. 작업 완료 또는 Spark에서 복구 확인 전까지 시작을 차단합니다.']
};
Object.assign(serviceUserErrors,updateMessages);
function updateMessage(code){return updateMessages[code]?tr(...updateMessages[code]):tr('Update was not completed. Check the private update record on Spark.','업데이트를 완료하지 못했습니다. Spark의 비공개 업데이트 기록을 확인하세요.');}
function updateActionLabel(info){return info.available?tr('UPDATE','업데이트'):info.checked_at?tr('CHECK AGAIN','다시 확인'):tr('CHECK FOR UPDATES','업데이트 확인');}
function showService(s){
 metricExplorer=null;
 const metadata=[[tr('Launch profile','실행 프로필'),s.profile_name],[tr('Quantization','양자화'),s.quantization],[tr('Inference engine','추론 엔진'),s.inference_engine],[tr('Serving engine','서빙 엔진'),s.serving_engine]];
 showModal(`<div class="service-details-layout"><h2 id="modalTitle">${escapeHTML(s.model_name||s.name)}</h2><p class="service-detail-status" data-service-detail-status="${escapeHTML(s.id)}">${serviceText(s.state)} / ${serviceReadiness(s)}</p><p class="muted" data-service-connection-note ${appConnectionNote(s)?'':'hidden'}>${appConnectionNote(s)}</p>
 <dl class="service-engine-details">${metadata.filter(x=>x[1]).map(([k,v])=>`<div><dt>${k}</dt><dd>${escapeHTML(v)}</dd></div>`).join('')}</dl>
 <section class="service-autostart-panel" data-autostart-panel="${escapeHTML(s.id)}"><p role="status">${tr("Reading boot settings…","자동 시작 설정 확인 중…")}</p></section>
 <section class="service-update-panel" data-update-panel="${escapeHTML(s.id)}" aria-label="${tr('App update','앱 업데이트')}"><p role="status">${tr('Reading installed version…','설치 버전 확인 중…')}</p></section>
 ${s.profiles.length>1?`<label class="service-select-label" for="serviceProfile">${tr('Change launch profile','실행 프로필 변경')}</label><select id="serviceProfile">${s.profiles.map(p=>`<option value="${escapeHTML(p.id)}" ${s.profile_id===p.id?'selected':''}>${escapeHTML(p.name)}</option>`).join('')}</select>`:''}
 <div class="service-detail-actions">${s.profiles.length>1?`<button class="button secondary" data-service-select="${escapeHTML(s.id)}" data-revision="${liveNode.services.revision}">${tr('SELECT PROFILE','프로필 선택')}</button>`:''}<button class="button secondary" data-service-action="${s.state==='running'?'restart':'start'}" data-service-id="${escapeHTML(s.id)}" ${serviceCanControl(s)?'':'disabled'}>${s.state==='running'?tr('RESTART…','재시작…'):tr('START…','시작…')}</button>${appAccessMarkup(s)}</div>
 <details class="service-notes"><summary>${tr('Connection & usage notes','연결·사용 안내')}</summary><p>${tr('Restart interrupts active work. Stop before changing profiles or updating. App versions and model weight versions are different.','재시작하면 진행 중 작업이 중단됩니다. 프로필 변경·업데이트 전에는 먼저 정지하세요. 앱 버전과 모델 가중치 버전은 서로 다릅니다.')}</p><p>${tr('Edit → Connection manages the API port and app URL. Launch commands, update bindings and private logs stay on Spark.','편집 → 연결 설정에서 API 포트와 앱 주소를 관리합니다. 실행 명령·업데이트 연결 설정·비공개 로그는 Spark에서 관리합니다.')}</p></details></div>`);
 $('#modalKind').textContent=tr('SERVICE DETAILS','서비스 상세');
 refreshServiceDetail();loadServiceUpdate(s.id);loadServiceAutostart(s.id);
}
let updatePoll=null;
function serviceUpdateVisible(panel){return !!panel&&panel.isConnected&&!document.hidden&&!document.getElementById('modal')?.hidden;}
function renderServiceUpdate(panel,info){
 const job=info.job||{},busy=updateBusyStates.includes(job.status),blocked=job.status==='recovery_required';
 panel._updateInfo=info;
 panel.innerHTML=`<div class="service-version-row"><span>${tr('Installed app version','현재 앱 버전')}</span><strong>${escapeHTML(info.current||tr('Not available','확인 불가'))}</strong></div>${info.supported?`<div class="service-update-summary"><span>${info.available?`${tr('Available','새 버전')} · ${escapeHTML(info.candidate)}`:info.checked_at?tr('Up to date on this channel','이 채널의 최신 버전'):tr('Check the official source when needed','필요할 때 공식 소스에서 확인')}</span><span class="tiny">${escapeHTML(info.channel==='main'?tr('Official development branch','공식 개발 브랜치'):info.channel==='latest'?tr('Official npm latest','공식 npm latest'):tr('Official stable release','공식 안정 릴리스'))}</span></div>
 <p class="update-stage ${blocked?'is-danger':job.code==='update_complete_review'||job.status==='rolled_back'||job.status==='failed'?'is-warning':''}" role="status" ${job.status?'':'hidden'}>${busy?({queued:tr('Preparing…','준비 중…'),backup:tr('Backing up app and environment…','앱·실행 환경 백업 중…'),install:tr('Installing official update…','공식 업데이트 설치 중…'),validate:tr('Validating installation…','설치 검증 중…'),restoring:tr('Restoring previous installation…','이전 설치본 복구 중…')}[job.status]):job.code?escapeHTML(updateMessage(job.code)):''}</p>
 <button class="button ${info.available?'':'secondary'}" data-update-action="${escapeHTML(panel.dataset.updatePanel)}" ${busy||blocked?'disabled':''}>${busy?tr('UPDATE IN PROGRESS','업데이트 진행 중'):blocked?tr('RECOVERY REQUIRED','복구 확인 필요'):updateActionLabel(info)}</button>
 <p class="service-update-hint">${tr('Stop before updating. Backup → install → basic checks; failures trigger recovery. Start manually afterwards. One recovery backup per service is retained after a successful update.','정지 후 업데이트합니다. 백업 → 설치 → 기본 검사 순서로 진행하며, 실패 시 복구합니다. 완료 후 직접 시작하세요. 정상 업데이트 후 서비스별 최근 복구 백업 1개만 유지합니다.')}</p>`:`<p class="service-update-hint">${tr('Updates are not connected for this profile. Configure a supported official installation on Spark.','이 프로필에는 업데이트가 연결되지 않았습니다. Spark에서 지원하는 공식 설치본을 연결하세요.')}</p>`}`;
}
async function loadServiceUpdate(id){
 clearTimeout(updatePoll);
 const panel=document.querySelector('[data-update-panel]');if(!serviceUpdateVisible(panel)||panel.dataset.updatePanel!==id)return;
 try{const info=await api('services/update?id='+encodeURIComponent(id));if(!serviceUpdateVisible(panel))return;renderServiceUpdate(panel,info);if(updateBusyStates.includes(info.job?.status))updatePoll=setTimeout(()=>loadServiceUpdate(id),2500);}
 catch(e){if(serviceUpdateVisible(panel))panel.innerHTML=`<p role="alert">${escapeHTML(updateMessage(e.message))}</p><button class="button secondary" data-update-retry="${escapeHTML(id)}">${tr('RETRY','다시 시도')}</button>`;}
}
document.addEventListener('visibilitychange',()=>{if(document.hidden){clearTimeout(updatePoll);return;}const panel=document.querySelector('[data-update-panel]');if(serviceUpdateVisible(panel))loadServiceUpdate(panel.dataset.updatePanel);});
document.addEventListener('click',async event=>{
 const b=event.target.closest('[data-update-action],[data-update-confirm],[data-update-retry],[data-update-back]');if(!b)return;
 event.preventDefault();event.stopImmediatePropagation();
 const id=b.dataset.updateAction||b.dataset.updateConfirm||b.dataset.updateRetry||b.dataset.updateBack;
 const s=serviceRows().find(row=>row.id===id);if(!s)return;
 if(b.dataset.updateRetry){loadServiceUpdate(id);return;}
 if(b.dataset.updateBack){showService(s);return;}
 b.disabled=true;
 try{
  if(b.dataset.updateConfirm){await api('services/update/apply',{id,ticket:b.dataset.ticket});if(serviceUpdateVisible(b))showService(s);return;}
  const panel=b.closest('[data-update-panel]'),info=panel._updateInfo;
  if(!info.available){b.textContent=tr('CHECKING…','확인 중…');const fresh=await api('services/update/check',{id});if(serviceUpdateVisible(panel))renderServiceUpdate(panel,fresh);return;}
  if(!['stopped','failed'].includes(s.state))throw Error('update_stop_required');
  showModal(`<h2 id="modalTitle">${tr('UPDATE APP','앱 업데이트')}</h2><p>${escapeHTML(s.name)} · ${escapeHTML(info.current)} → ${escapeHTML(info.candidate)}</p><p>${tr('The app, settings and environment will be backed up first. Updates can change app behavior; basic validation does not replace a real workflow test. The service remains stopped after completion.','앱·설정·실행 환경을 먼저 백업합니다. 업데이트로 앱 동작이 바뀔 수 있으며 기본 검사만으로 실제 워크플로 검증을 대신하지 않습니다. 완료 후에도 서비스는 정지 상태입니다.')}</p><div class="service-confirm-actions"><button class="button" data-update-confirm="${escapeHTML(id)}" data-ticket="${escapeHTML(info.ticket)}">${tr('BACK UP & UPDATE','백업 후 업데이트')}</button><button class="button service-cancel" data-update-back="${escapeHTML(id)}">${tr('CANCEL','취소')}</button></div>`);
  $('#modalKind').textContent=tr('OFFICIAL APP UPDATE','공식 앱 업데이트');
 }catch(e){if(serviceUpdateVisible(b)){showModal(`<h2 id="modalTitle">${tr('APP UPDATE NOTICE','앱 업데이트 안내')}</h2><p role="alert">${escapeHTML(updateMessage(e.message))}</p><button class="button secondary" data-update-back="${escapeHTML(id)}">${tr('BACK TO DETAILS','상세로 돌아가기')}</button>`);$('#modalKind').textContent=tr('APP UPDATE','앱 업데이트');}}
 finally{if(b.isConnected)b.disabled=false;}
},true);
const autostartMessages={
 autostart_unavailable:['Could not read boot settings. Try again.','자동 시작 설정을 읽지 못했습니다. 다시 확인하세요.'],
 autostart_unsupported:['This launch profile cannot change boot settings. Review its user service on Spark.','이 실행 프로필은 자동 시작을 변경할 수 없습니다. Spark에서 사용자 서비스 설정을 확인하세요.'],
 autostart_linger_required:['Enable user lingering on Spark before enabling boot startup.','부팅 자동 시작을 켜려면 Spark에서 사용자 linger 설정이 필요합니다.'],
 autostart_conflict:['Another profile that shares this service or resource is enabled for boot, or its setting is unknown. Turn it off or check it first.','동일 서비스·자원을 사용하는 다른 프로필이 자동 시작으로 설정되어 있거나 상태를 확인할 수 없습니다. 해당 설정을 먼저 해제·확인하세요.'],
 autostart_change_failed:['The change could not be verified. Reload boot settings before trying again.','변경 결과를 확인하지 못했습니다. 자동 시작 설정을 다시 읽은 후 시도하세요.'],
 disable_autostart_before_rebinding:['Turn off boot startup for the current profile before replacing or removing it.','실행 프로필을 교체·삭제하기 전에 현재 프로필의 부팅 자동 시작을 꺼주세요.']
};
Object.assign(serviceUserErrors,autostartMessages);
function renderServiceAutostart(panel,info,message=''){
 panel._autostart=info;
 const label=tr('Start when Spark boots','Spark 부팅 시 자동 시작');
 panel.innerHTML=`<div class="service-autostart-row"><strong>${label}</strong><button class="button secondary autostart-toggle" role="switch" aria-label="${label}" aria-checked="${info.enabled===true}" data-autostart-toggle="${escapeHTML(panel.dataset.autostartPanel)}" ${!info.editable||info.maintenance?'disabled':''}>${info.enabled===null?tr('UNAVAILABLE','확인 불가'):info.enabled?tr('ON','켜짐'):tr('OFF','꺼짐')}</button></div><p class="service-autostart-hint">${tr('Applies to this launch profile. Does not start or stop it now. Manual starts and dependencies can still start it.','이 실행 프로필에 적용됩니다. 현재 실행 상태는 바뀌지 않습니다. 꺼도 수동 실행·서비스 간 의존성으로 시작될 수 있습니다.')}</p>${!info.boot_ready?`<p class="service-autostart-hint">${tr('User lingering is not confirmed: startup may wait until local login.','사용자 linger 설정이 확인되지 않아 로컬 로그인 전에는 시작되지 않을 수 있습니다.')}</p>`:''}<p class="service-autostart-feedback" role="status">${escapeHTML(message||(!info.editable?tr('This profile requires local configuration.','이 프로필은 Spark에서 설정 확인이 필요합니다.'):info.maintenance?tr('Locked during app update or recovery.','앱 업데이트·복구 중에는 변경할 수 없습니다.') :''))}</p>`;
}
async function loadServiceAutostart(id){
 const panel=document.querySelector('[data-autostart-panel]');if(!panel||panel.dataset.autostartPanel!==id)return;
 try{const info=await api('services/autostart?id='+encodeURIComponent(id));if(panel.isConnected)renderServiceAutostart(panel,info);}
 catch(e){if(panel.isConnected)panel.innerHTML=`<p role="alert">${tr(...autostartMessages.autostart_unavailable)}</p><button class="button secondary" data-autostart-retry="${escapeHTML(id)}">${tr('RETRY','다시 확인')}</button>`;}
}
document.addEventListener('click',async event=>{
 const b=event.target.closest('[data-autostart-toggle],[data-autostart-retry]');if(!b)return;
 event.preventDefault();event.stopImmediatePropagation();if(b.disabled)return;
 const id=b.dataset.autostartToggle||b.dataset.autostartRetry;
 if(b.dataset.autostartRetry){loadServiceAutostart(id);return;}
 const panel=b.closest('[data-autostart-panel]'),info=panel._autostart;b.disabled=true;
 panel.querySelector('[role="status"]').textContent=tr('Saving…','저장 중…');
 try{const next=await api('services/autostart',{id,profile_id:info.profile_id,revision:info.revision,enabled:!info.enabled});if(panel.isConnected)renderServiceAutostart(panel,next,tr('Saved. Current running state is unchanged.','저장했습니다. 현재 실행 상태는 그대로입니다.'));}
 catch(e){if(panel.isConnected){const message=autostartMessages[e.message]||serviceUserErrors[e.message]||autostartMessages.autostart_change_failed;panel.innerHTML=`<p role="alert">${escapeHTML(tr(...message))}</p><button class="button secondary" data-autostart-retry="${escapeHTML(id)}">${tr('RELOAD SETTINGS','설정 다시 확인')}</button>`;}}
});
