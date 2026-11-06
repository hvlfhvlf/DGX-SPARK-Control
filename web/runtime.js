'use strict';
// Installed runtime. The original UI is retained; simulated telemetry never runs here.
const liveNode={sample:null,history:[],models:[],services:{revision:0,services:[]},servicesConnected:null,events:[],hardware:null,connected:false,statusChecked:false,busy:false,version:'—',authMode:'password',token:localStorage.getItem('spark.access')||sessionStorage.getItem('spark.access')||''};
const tr=(en,ko)=>uiLanguage==='ko'?ko:en;
const fmt=(v,places=1)=>v==null?'—':Number(v).toFixed(places);
// Fail closed if a detail asset fails to load; never fall back to prototype fixtures.
renderMetricDetailBody=function(){};
showMetricDetail=function(){metricExplorer=null;showModal(`<h2 id="modalTitle">${tr('DETAILS UNAVAILABLE','상세창을 불러올 수 없습니다')}</h2><p>${tr('Reload this page to load the detail interface.','페이지를 새로고침하여 상세 화면을 다시 불러와 주세요.')}</p>`);$('#modalKind').textContent=tr('METRIC DETAILS','지표 상세');};
function hardwareLabels(){
 const h=liveNode.hardware||{},installed=h.installed_memory_bytes,bytes=installed||h.os_memory_bytes;
 return {gpu:h.gpu_name?.replace(/^NVIDIA\s+/,'')||'—',memory:bytes?`${fmt(bytes/2**30,installed&&bytes%2**30===0?0:1)} GiB`:'—',memorySource:installed?tr('INSTALLED','설치 용량'):tr('OS USABLE','OS 가용 총량'),kind:h.memory_kind==='unified'?'UNIFIED':'SYSTEM MEMORY',arch:h.architecture||'—',cores:h.logical_cpus||'—',product:h.product?.replace(/_/g,' ')||tr('COMPUTE NODE','컴퓨트 노드')};
}
function syncHardware(){const h=hardwareLabels();$('#hardwareGpu').textContent=h.gpu;$('#hardwareMemory').textContent=h.memory;$('#hardwareKind').textContent=h.kind;$('#hardwareMemory').title=h.memorySource;}
async function api(path,body){
 const requestToken=liveNode.token;
 api.active=api.active||0;api.waiters=api.waiters||[];
 if(api.active>=3&&api.waiters.length>=24)throw Error(tr('Too many pending requests. Please try again shortly.','대기 중인 요청이 많습니다. 잠시 후 다시 시도하세요.'));
 if(api.active>=3)await new Promise(resolve=>api.waiters.push(resolve));else api.active++;
 try{
  if(!['info','login'].includes(path)&&liveNode.token!==requestToken)throw Error(tr('Session changed. Please try again.','로그인 상태가 바뀌었습니다. 다시 시도하세요.'));
  for(let attempt=0;attempt<2;attempt++){
   const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),path==='services/update/check'?45000:10000);
   let retry=false;
   try{
    const response=await fetch('/api/'+path,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+requestToken,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,signal:controller.signal});
    if(response.status===401){if(liveNode.token===requestToken){liveNode.token='';sessionStorage.removeItem('spark.access');localStorage.removeItem('spark.access');}throw Error(path==='login'?tr('Password not accepted','비밀번호가 일치하지 않습니다'):tr('Please sign in again','다시 로그인해 주세요'));}
    const value=await response.json();if(!['info','login'].includes(path)&&liveNode.token!==requestToken)throw Error(tr('Session changed. Please try again.','로그인 상태가 바뀌었습니다. 다시 시도하세요.'));
    if(response.status===503&&!body&&attempt===0)retry=true;
    else {if(!response.ok)throw Error(value.error||'Request failed');return value;}
   }finally{clearTimeout(timeout);}
   if(retry)await new Promise(resolve=>setTimeout(resolve,750+Math.random()*500));
   if(liveNode.token!==requestToken)throw Error(tr('Session changed. Please try again.','로그인 상태가 바뀌었습니다. 다시 시도하세요.'));
  }
 }finally{const next=api.waiters.shift();if(next)next();else api.active--;}
}
function graph(id,channel=0,height=64){
 const end=Date.now()/1000,start=end-5*60;
 const rows=liveNode.history.filter(row=>row.timestamp>start&&row.timestamp<=end);
 const value=row=>Array.isArray(row[id])?row[id][channel]:row[id];
 const maximum=Math.max(0.01,...rows.flatMap(row=>Array.isArray(row[id])?row[id]:[row[id]]).map(v=>v||0))*1.12;
 let paths='',segment=[];
 const flush=()=>{if(segment.length>1)paths+=`<polyline class="io-trace trace-${channel}" points="${segment.join(' ')}"/>`;segment=[];};
 rows.forEach((row,i)=>{if(value(row)==null||(i&&row.timestamp-rows[i-1].timestamp>15))flush();if(value(row)!=null)segment.push(`${((row.timestamp-start)/(end-start)*240).toFixed(1)},${(height-4-value(row)/maximum*(height-8)).toFixed(1)}`);});flush();
 return paths;
}
function livePlot(id){return `<svg viewBox="0 0 240 64" preserveAspectRatio="none" aria-label="${escapeHTML(id)}"><path class="io-grid" d="M0 16H240M0 40H240M0 63H240"/>${graph(id)}${['network','diskio'].includes(id)?graph(id,1):''}</svg>`;}
function liveCard(id,label,unit){
 const s=liveNode.sample||{},value=liveNode.connected?s[id]:null;
 if(['network','diskio'].includes(id))return `<button class="metric io-metric" data-metric="${id}"><span class="metric-top">${label}<span class="metric-arrow">${arrowIcon()}</span></span><div class="io-chart">${livePlot(id)}</div><div class="io-axis"><span>5m</span><span>NOW</span></div><div class="metric-pair">${(id==='network'?['RECEIVE','SEND']:['READ','WRITE']).map((name,c)=>`<div><span class="io-label"><i class="io-dot trace-${c}"></i>${name}</span><strong>${escapeHTML(smallRate(value?.[c]))}<small> MB/s</small></strong></div>`).join('')}</div></button>`;
 const memoryPercentage=Number.isFinite(value)&&Number.isFinite(s.memory_total_gib)&&s.memory_total_gib>0?value/s.memory_total_gib*100:null;
 const extra=id==='gpu'?`${fmt(s.gpu_clock_mhz==null?null:s.gpu_clock_mhz/1000,2)} GHz`:id==='cpu'?`${s.cpu_clock_ghz?s.cpu_clock_ghz.map(v=>fmt(v,2)).join('–'):'—'} GHz`:id==='memory'?`${fmt(memoryPercentage,1)}%`:'';
 const foot=id==='memory'?`${fmt(s.memory_total_gib)} GiB`:id==='disk'?`${fmt(s.disk_total_tib)} TiB`:id==='cpu'?`${s.cores&&Object.keys(s.cores).length?Object.keys(s.cores).length:'—'} CORES`:id==='power'?'GPU ONLY':id==='temp'?'GPU SENSOR':'NVML';
 const percentage=id==='memory'?memoryPercentage:id==='disk'?value/s.disk_total_tib*100:value;
 return `<button class="metric ${id==='temp'?'warm':''}" data-metric="${id}"><span class="metric-top">${label}<span class="metric-arrow">${arrowIcon()}</span></span><div class="metric-reading"><div class="metric-number">${fmt(value,['gpu','cpu','temp'].includes(id)?0:1)}<small>${unit}</small></div>${extra?`<div class="metric-extra">${extra}</div>`:''}</div><div class="metric-foot"><span>${tr('LIVE SENSOR','실측 센서')}</span><span>${foot}</span></div>${id!=='power'?`<div class="metric-line"><span style="width:${Math.min(100,Math.max(0,percentage||0))}%"></span></div>`:'<div class="metric-rule"></div>'}</button>`;
}
function telemetryConnectionLabel(){return !liveNode.statusChecked&&!liveNode.sample?tr('CONNECTING','연결 확인 중'):liveNode.connectionDelayed?tr('UPDATE DELAYED','갱신 지연'):liveNode.connected?tr('LIVE / 5 SEC','실측 / 5초'):tr('DISCONNECTED','연결 끊김');}
function installedOverview(){
 const h=hardwareLabels(),template=document.createElement('template');template.innerHTML=deviceArt();
 template.content.querySelector('.art-label').textContent=liveNode.hardware?.gpu_name||'—';
 const artText=template.content.querySelectorAll('svg text');artText[0].textContent=h.memory;artText[1].textContent=h.cores+' CORE';artText[2].textContent=h.arch;
 template.content.querySelector('.art-bottom').textContent=h.kind+' // SCHEMATIC';
 const hero=`<div class="hero-collapse" id="overviewHero" aria-hidden="${!preferences.hero}"><div class="hero-collapse-inner"><section class="hero"><div class="hero-copy"><div class="eyebrow muted">${escapeHTML(h.product)}</div><h2 class="hero-title">SPARK<span> /01</span></h2><p class="hero-sub">One node. Every possibility.</p><div class="hero-spec"><span>ARCH<b>${escapeHTML(h.arch)}</b></span><span>GPU<b>${escapeHTML(h.gpu)}</b></span><span>${h.memorySource}<b>${h.memory}</b></span></div></div>${template.innerHTML}</section></div></div>`;
 return pageHeading('SYSTEM OVERVIEW','01','YOUR COMPUTE. UNDER CONTROL.')+hero+`<div class="section-head"><h2>NODE TELEMETRY</h2><span>${telemetryConnectionLabel()}</span></div><section class="metric-grid">${[['gpu','GPU UTILIZATION','%'],['cpu','CPU UTILIZATION','%'],['memory','UNIFIED MEMORY','GiB'],['disk','SSD USAGE','TiB'],['temp','GPU TEMPERATURE','°C'],['power','GPU POWER','W'],['network','NETWORK TRAFFIC','MB/s'],['diskio','DISK I/O','MB/s']].map(x=>liveCard(...x)).join('')}</section>`;
}
function installedModels(){return pageHeading('MODEL BAY','02','REGISTERED SERVICES')+`<div class="model-grid">${liveNode.models.map(m=>`<article class="model-card"><div class="card-top">${badge(escapeHTML(m.state),m.state==='active'?'':'off')}</div><h2>${escapeHTML(m.name)}</h2><p>${escapeHTML(m.engine)}</p><p>${tr('Service state is not an inference readiness check.','서비스 실행 상태이며, 추론 준비 완료를 의미하지 않습니다.')}</p><div class="button-row"><button class="button" data-live-model="${escapeHTML(m.id)}" data-live-action="${m.state==='active'?'stop':'start'}" ${!m.controllable?'disabled':''}>${m.state==='active'?'STOP':'START'}</button></div></article>`).join('')||`<p class="empty-note">${tr('No services registered. Add existing user services to config.json using docs/MODELS.md.','등록된 서비스가 없습니다. docs/MODELS.md에 따라 config.json에 기존 사용자 서비스를 등록하세요.')}</p>`}</div>`;}
render=function(animate=true){
 if(state.view!=='settings'||!liveNode.token){nameDraft=null;nameDraftDirty=false;}
 let html;
 if(!liveNode.token){const password=liveNode.authMode==='password';html=pageHeading('CONNECT TO SPARK','01','DGX-SPARK-CONTROL / '+liveNode.version)+`<section class="panel auth-panel"><h2>${password?tr('Password','비밀번호'):tr('Access token','접속 토큰')}</h2><p>${password?tr('Enter your installation password. This device stays signed in until you log out or reset the password.','설치할 때 설정한 비밀번호를 입력하세요. 로그아웃하거나 비밀번호를 재설정하기 전까지 이 기기에서 유지됩니다.'):tr('Password setup is pending. Use the local access token or run scripts/set-password.py on Spark.','비밀번호 설정 전입니다. 로컬 접속 토큰을 사용하거나 Spark에서 scripts/set-password.py를 실행하세요.')}</p><form id="liveLogin"><input type="password" id="liveToken" autocomplete="${password?'current-password':'off'}" required aria-label="${password?tr('Password','비밀번호'):'Access token'}"><button class="button">${tr('SIGN IN','로그인')}</button></form><p id="liveLoginError" role="status"></p></section>`;}
 else if(state.view==='overview')html=installedOverview();
 else if(state.view==='models')html=installedModels();
 else if(state.view==='settings'){
  const template=document.createElement('template');template.innerHTML=settingsView();
  const personal=template.content.querySelector('.settings-primary > section');
  const jobsOption=personal.querySelector('option[value=jobs]');if(jobsOption){jobsOption.textContent=tr('Programs','프로그램');jobsOption.setAttribute('translate','no');}
  personal.querySelector('.panel-top .tiny').textContent=tr('Name: shared · Appearance: this browser','이름: 공용 · 화면: 현재 브라우저');
  personal.querySelector('#heroToggle').closest('.setting-row').querySelector('p').textContent=tr('Turn on to show the overview artwork; turn off to focus on telemetry.','켜면 개요 그래픽을 표시하고, 끄면 시스템 상태를 먼저 보여줍니다.');
  personal.querySelector('.spark-name-row p').textContent=tr('Shared display name saved on this Spark. The system hostname is unchanged.','이 Spark에 저장되는 공용 표시 이름입니다. 시스템 호스트명은 바뀌지 않습니다.');
  personal.querySelector('#resetPreferences').textContent=tr('RESET APPEARANCE','화면 설정 초기화');
  personal.querySelector('#resetPreferences').previousElementSibling.querySelector('p').textContent=tr('Appearance is saved in this browser. The Spark name is shared across devices.','화면 설정은 이 브라우저에 저장됩니다. Spark 이름은 기기 간 공유됩니다.');
  html=pageHeading('SYSTEM SETTINGS','05','MAKE THIS SPACE YOURS.')+personal.outerHTML+`<section class="panel runtime-panel"><h2>DGX-SPARK-Control ${liveNode.version}</h2><p>${tr('One Python process · demand-driven 5s collection · 720 history samples · 480 MiB service limit.','Python 프로세스 1개 · 요청 시 5초 간격 수집 · 최대 이력 720개 · 서비스 상한 480 MiB.')}</p><div class="setting-row"><span>Interface motion</span>${switchInput('motionToggle',state.motion,'Interface motion')}</div><button class="button secondary" id="liveDiscover">${tr('SCAN MODEL FOLDERS','모델 폴더 검색')}</button><p id="discoveryResult"></p><p>${tr('Package install: install the new .deb with apt. Settings and logins are preserved. Archive installs use their original update method.','패키지 설치판은 새 .deb를 apt로 설치하세요. 설정과 로그인은 유지됩니다. 압축판은 기존 업데이트 방식을 사용하세요.')}</p><p><a href="https://github.com/hvlfhvlf/DGX-SPARK-Control/releases" target="_blank" rel="noopener noreferrer">${tr('Releases & installation guide','배포 버전과 설치 안내')}</a></p><button class="button secondary" id="liveLogout">${tr('LOG OUT THIS DEVICE','이 기기 로그아웃')}</button></section>`;
 }else if(state.view==='logs')html=typeof activityView==='function'?activityView():'';
 else html=typeof programsView==='function'?programsView():'';
 const previousScroll=window.scrollY;$('#main').innerHTML=`<div class="view${animate?'':' no-enter'}">${html}</div>`;
 $$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===state.view));
 $('#connectionLabel').textContent=liveNode.connected?'NODE ONLINE':'NODE OFFLINE';
 const note=$('.context-note');if(note.firstChild)note.firstChild.textContent=tr('LIVE DATA / ','실시간 데이터 / ');
 $('#sparkDisplayName').textContent=preferences.sparkName;$('#runtimeVersion').textContent='V'+liveNode.version;
 if(!animate)window.scrollTo(0,previousScroll);syncHardware();translateUI();if(nameDraftDirty&&$('#sparkNameInput'))$('#sparkNameInput').value=nameDraft;if(typeof syncConnectionStatus==='function')syncConnectionStatus();if(typeof syncPowerHeader==='function')syncPowerHeader();if(state.view==='jobs'&&typeof refreshPrograms==='function')refreshPrograms();if(state.view==='models'&&typeof refreshServiceSignals==='function')refreshServiceSignals();if(typeof connectionToolbar==='function')connectionToolbar();if(typeof drawInference==='function')drawInference();
};
const connectionState=new SparkPolling.ConnectionState();
let historyEpoch='',settingsAt=0,eventsAt=0,eventsView='',pollTimer=null;
function needsHistory(){return state.view==='overview'||!!metricExplorer;}
async function refreshHistory(){
 const token=liveNode.token;
 const last=liveNode.history[liveNode.history.length-1]?.timestamp||0;
 const result=await api('history?incremental=1&since='+last+'&epoch='+encodeURIComponent(historyEpoch));
 if(liveNode.token!==token)return;
 liveNode.history=SparkPolling.mergeHistory(liveNode.history,result,Date.now()/1000);historyEpoch=result.epoch;
 liveNode.historyError=false;
}
function paintLive(){
 syncHardware();
 if(state.view==='overview'&&document.querySelector('.metric-grid')){
  const template=document.createElement('template');template.innerHTML=installedOverview();
  document.querySelectorAll('[data-metric]').forEach(card=>{const next=template.content.querySelector('[data-metric="'+card.dataset.metric+'"]');if(next)card.innerHTML=next.innerHTML;});
  document.querySelector('.section-head > span').textContent=telemetryConnectionLabel();
 }else if(state.view==='models'&&typeof refreshServiceCards==='function')refreshServiceCards();
 else if(state.view==='logs'&&typeof refreshActivity==='function')refreshActivity();
 else if(state.view==='jobs'&&typeof refreshPrograms==='function')refreshPrograms();
 $('#sparkDisplayName').textContent=preferences.sparkName;
 const input=$('#sparkNameInput');if(input&&!nameDraftDirty)input.value=preferences.sparkName;
 if(typeof refreshServiceSignals==='function')refreshServiceSignals();
 if(typeof connectionToolbar==='function')connectionToolbar();
 if(metricExplorer&&!$('#modal').hidden)renderMetricDetailBody();
 translateUI();
}
async function refreshLive(){
 if(liveNode.busy||!liveNode.token||document.hidden)return;liveNode.busy=true;
 const token=liveNode.token;
 try{
  // Only core telemetry decides node connectivity. Optional APIs and rendering
  // have independent error states; stale control state never permits actions.
  try{
   const sample=await api('metrics');if(liveNode.token!==token)return;
   liveNode.sample=sample;liveNode.connected=true;liveNode.connectionDelayed=false;
   lastSuccessfulRefresh=Date.now();connectionState.success(lastSuccessfulRefresh);
  }catch(error){
   if(liveNode.token!==token)return;
   const status=connectionState.failure(Date.now());
   liveNode.connected=status==='delayed'&&!!connectionState.lastSuccess;
   liveNode.connectionDelayed=status==='delayed';liveNode.servicesConnected=false;
   return;
  }
  const optional=async(key,work)=>{try{await work();if(liveNode.token===token)liveNode[key]=false;}catch{if(liveNode.token===token)liveNode[key]=true;}};
  const tasks=[];
  if(!settingsAt||Date.now()-settingsAt>=60000)tasks.push(optional('settingsError',async()=>{
   const settings=await api('settings');if(liveNode.token!==token)return;
   liveNode.version=settings.version;preferences.sparkName=settings.spark_name;settingsAt=Date.now();$('#runtimeVersion').textContent='V'+settings.version;
  }));
  if(!liveNode.hardware)tasks.push(optional('hardwareError',async()=>{const h=await api('hardware');if(liveNode.token===token){liveNode.hardware=h;if(state.view==='overview')render(false);}}));
  if(typeof serviceNeedsPolling==='function'?serviceNeedsPolling():['overview','models','jobs'].includes(state.view))tasks.push((async()=>{
   try{const registered=await api('services');if(liveNode.token!==token)return;liveNode.services=registered;liveNode.models=(registered.services||[]).map(s=>({...s,state:s.state==='running'?'active':s.state,engine:s.adapter}));liveNode.servicesConnected=true;}
   catch{if(liveNode.token===token)liveNode.servicesConnected=false;}
  })());
  if(state.view==='logs'&&(!eventsAt||eventsView!=='logs'||Date.now()-eventsAt>=10000))tasks.push(optional('eventsError',async()=>{const events=await api('events');if(liveNode.token===token){liveNode.events=events;eventsAt=Date.now();}}));
  eventsView=state.view;
  if(needsHistory())tasks.push(optional('historyError',refreshHistory));
  if(state.view==='jobs')tasks.push(optional('programsError',async()=>{try{programData=await api('programs');programError=false;}catch{programError=true;}}));
  await Promise.allSettled(tasks);
  if(liveNode.token===token&&typeof refreshInference==='function')refreshInference();
 }finally{
  liveNode.statusChecked=true;
  try{if(!liveNode.token)render(false);else if(liveNode.token===token){paintLive();if(typeof drawInference==='function')drawInference();}liveNode.displayError=false;}
  catch{liveNode.displayError=true;console.warn('Dashboard display update failed; connection state unchanged.');}
  try{if(typeof refreshServiceDetail==='function')refreshServiceDetail();syncConnectionStatus();if(typeof syncPowerHeader==='function')syncPowerHeader();}
  catch{liveNode.displayError=true;console.warn('Dashboard status display update failed; retry remains active.');}
  finally{liveNode.busy=false;}
 }
}
async function pollLive(){try{await refreshLive();}catch{console.warn('Dashboard refresh failed; retry remains active.');}finally{pollTimer=setTimeout(pollLive,5000+Math.random()*750);}}

document.addEventListener('submit',async event=>{
 if(!['liveLogin','sparkNameForm'].includes(event.target.id))return;event.preventDefault();event.stopImmediatePropagation();
 try{if(event.target.id==='liveLogin'){const button=event.target.querySelector('button');button.disabled=true;try{liveNode.token=liveNode.authMode==='password'?(await api('login',{password:$('#liveToken').value})).session:$('#liveToken').value.trim();await api('health');localStorage.setItem('spark.access',liveNode.token);sessionStorage.removeItem('spark.access');await refreshLive();render();}finally{button.disabled=false;}}else{const result=await api('settings',{spark_name:$('#sparkNameInput').value});preferences.sparkName=result.spark_name;nameDraft=null;nameDraftDirty=false;applyPreferences();toast(tr('Spark name saved on server.','서버에 Spark 이름을 저장했습니다.'));}}catch(error){const el=$('#liveLoginError');if(el)el.textContent=error.message;else toast(error.message);}
},true);
document.addEventListener('click',async event=>{
 const b=event.target.closest('button');if(!b)return;
 if(b.dataset.liveModel){event.stopImmediatePropagation();showModal(`<h2 id="modalTitle">${b.dataset.liveAction==='stop'?'STOP':'START'} SERVICE?</h2><p>${escapeHTML(b.dataset.liveModel)}</p><p>${tr('This controls the real registered service. Stopping interrupts its active requests.','실제 등록된 서비스를 제어합니다. 정지하면 해당 서비스의 진행 중 요청이 중단됩니다.')}</p><button class="button" data-live-confirm="${escapeHTML(b.dataset.liveModel)}" data-live-operation="${b.dataset.liveAction}">CONFIRM</button>`);}
 if(b.dataset.liveConfirm){event.stopImmediatePropagation();b.disabled=true;try{await api('models/action',{id:b.dataset.liveConfirm,action:b.dataset.liveOperation});closeModal();await refreshLive();}catch(error){b.disabled=false;toast(error.message);}}
 if(b.id==='liveDiscover'&&typeof modelFolders==='function'){event.stopImmediatePropagation();await modelFolders();return;}
 if(b.id==='liveDiscover'){event.stopImmediatePropagation();b.disabled=true;try{const result=await api('models/discover',{});$('#discoveryResult').textContent=result.roots_configured?JSON.stringify(result):tr('Configure model_roots in config.json first.','먼저 config.json에 model_roots를 등록하세요.');}catch(error){toast(error.message);}finally{b.disabled=false;}}
 if(b.id==='liveLogout'){event.stopImmediatePropagation();try{await api('logout',{});}catch{}liveNode.token='';liveNode.connected=false;liveNode.history=[];historyEpoch='';settingsAt=0;eventsAt=0;sessionStorage.removeItem('spark.access');localStorage.removeItem('spark.access');render();}
 if(b.id==='resetPreferences'){event.stopImmediatePropagation();const name=preferences.sparkName;preferences={...preferenceDefaults,sparkName:name};savePreferences();setMotion(preferences.motion);render(false);}
},true);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshLive();});
document.addEventListener('spark-language-change',()=>render(false));
state.jobs=[];state.events=[];state.model=null;
if(liveNode.token){localStorage.setItem('spark.access',liveNode.token);sessionStorage.removeItem('spark.access');}
render(false);api('info').then(info=>{liveNode.version=info.version;liveNode.authMode=info.auth_mode;render(false);refreshLive();}).catch(()=>{liveNode.statusChecked=true;syncConnectionStatus();});pollTimer=setTimeout(pollLive,5000+Math.random()*750);
