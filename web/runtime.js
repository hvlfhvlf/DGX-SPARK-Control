'use strict';
// Installed runtime. The original UI is retained; simulated telemetry never runs here.
const liveNode={sample:null,history:[],models:[],events:[],connected:false,busy:false,version:'0.1.0',token:sessionStorage.getItem('spark.access')||''};
const tr=(en,ko)=>uiLanguage==='ko'?ko:en;
const fmt=(v,places=1)=>v==null?'—':Number(v).toFixed(places);
async function api(path,body){
 const controller=new AbortController(),timeout=setTimeout(()=>controller.abort(),10000);
 let response;try{response=await fetch('/api/'+path,{method:body?'POST':'GET',headers:{Authorization:'Bearer '+liveNode.token,...(body?{'Content-Type':'application/json'}:{})},body:body?JSON.stringify(body):undefined,signal:controller.signal});}finally{clearTimeout(timeout);}
 if(response.status===401){liveNode.token='';sessionStorage.removeItem('spark.access');throw Error(tr('Access token required','접속 토큰이 필요합니다'));}
 const value=await response.json();if(!response.ok)throw Error(value.error||'Request failed');return value;
}
function graph(id,channel=0,height=64){
 const rows=liveNode.history.filter(row=>row.timestamp>Date.now()/1000-((metricExplorer?.range||5)*60));
 const value=row=>Array.isArray(row[id])?row[id][channel]:row[id];
 const maximum=Math.max(0.01,...rows.flatMap(row=>Array.isArray(row[id])?row[id]:[row[id]]).map(v=>v||0))*1.12;
 const end=Date.now()/1000,start=end-(metricExplorer?.range||5)*60;
 let paths='',segment=[];
 const flush=()=>{if(segment.length>1)paths+=`<polyline class="io-trace trace-${channel}" points="${segment.join(' ')}"/>`;segment=[];};
 rows.forEach((row,i)=>{if(value(row)==null||(i&&row.timestamp-rows[i-1].timestamp>15))flush();if(value(row)!=null)segment.push(`${((row.timestamp-start)/(end-start)*240).toFixed(1)},${(height-4-value(row)/maximum*(height-8)).toFixed(1)}`);});flush();
 return paths;
}
function livePlot(id){return `<svg viewBox="0 0 240 64" preserveAspectRatio="none" aria-label="${escapeHTML(id)}"><path class="io-grid" d="M0 16H240M0 40H240M0 63H240"/>${graph(id)}${['network','diskio'].includes(id)?graph(id,1):''}</svg>`;}
function liveCard(id,label,unit){
 const s=liveNode.sample||{},value=liveNode.connected?s[id]:null;
 if(['network','diskio'].includes(id))return `<button class="metric io-metric" data-metric="${id}"><span class="metric-top">${label}<span>↗</span></span><div class="io-chart">${livePlot(id)}</div><div class="io-axis"><span>5m</span><span>NOW</span></div><div class="metric-pair">${(id==='network'?['RECEIVE','SEND']:['READ','WRITE']).map((name,c)=>`<div><span class="io-label"><i class="io-dot trace-${c}"></i>${name}</span><strong>${fmt(value?.[c])}<small> MB/s</small></strong></div>`).join('')}</div></button>`;
 const extra=id==='gpu'?`${fmt(s.gpu_clock_mhz==null?null:s.gpu_clock_mhz/1000,2)} GHz`:id==='cpu'?`${s.cpu_clock_ghz?s.cpu_clock_ghz.map(v=>fmt(v,2)).join('–'):'—'} GHz`:id==='memory'?`${fmt(s.memory_clock_mhz==null?null:s.memory_clock_mhz/1000,2)} GHz`:'';
 const foot=id==='memory'?`${fmt(s.memory_total_gib)} GiB`:id==='disk'?`${fmt(s.disk_total_tib)} TiB`:id==='cpu'?`${Object.keys(s.cores||{}).length} CORES`:id==='power'?'GPU ONLY':id==='temp'?'GPU SENSOR':'NVML';
 const percentage=id==='memory'?value/s.memory_total_gib*100:id==='disk'?value/s.disk_total_tib*100:value;
 return `<button class="metric ${id==='temp'?'warm':''}" data-metric="${id}"><span class="metric-top">${label}<span>↗</span></span><div class="metric-reading"><div class="metric-number">${fmt(value,['gpu','cpu','temp'].includes(id)?0:1)}<small>${unit}</small></div>${extra?`<div class="metric-extra">${extra}</div>`:''}</div><div class="metric-foot"><span>${tr('LIVE SENSOR','실측 센서')}</span><span>${foot}</span></div>${id!=='power'?`<div class="metric-line"><span style="width:${Math.min(100,Math.max(0,percentage||0))}%"></span></div>`:'<div class="metric-rule"></div>'}</button>`;
}
function installedOverview(){
 const template=document.createElement('template');template.innerHTML=overview();
 const hero=template.content.querySelector('.hero-collapse').outerHTML;
 return pageHeading('SYSTEM OVERVIEW','01','YOUR COMPUTE. UNDER CONTROL.')+hero+`<div class="section-head"><h2>NODE TELEMETRY</h2><span>${liveNode.connected?tr('LIVE / 5 SEC','실측 / 5초'):tr('DISCONNECTED','연결 끊김')}</span></div><section class="metric-grid">${[['gpu','GPU UTILIZATION','%'],['cpu','CPU UTILIZATION','%'],['memory','UNIFIED MEMORY','GiB'],['disk','SSD USAGE','TiB'],['temp','GPU TEMPERATURE','°C'],['power','GPU POWER','W'],['network','NETWORK TRAFFIC','MB/s'],['diskio','DISK I/O','MB/s']].map(x=>liveCard(...x)).join('')}</section><p class="wide-note">${tr('0.1 · Live host telemetry. Model services are managed in Models. Inference throughput and request queues require engine adapters in a later release.','0.1 · 실제 시스템 측정값입니다. 모델 서비스는 모델 탭에서 관리합니다. 추론 속도·요청 대기열은 후속 버전의 엔진 어댑터가 필요합니다.')}</p>`;
}
function installedModels(){return pageHeading('MODEL BAY','02','REGISTERED SERVICES')+`<div class="model-grid">${liveNode.models.map(m=>`<article class="model-card"><div class="card-top">${badge(escapeHTML(m.state),m.state==='active'?'':'off')}</div><h2>${escapeHTML(m.name)}</h2><p>${escapeHTML(m.engine)}</p><p>${tr('Service state is not an inference readiness check.','서비스 실행 상태이며, 추론 준비 완료를 의미하지 않습니다.')}</p><div class="button-row"><button class="button" data-live-model="${escapeHTML(m.id)}" data-live-action="${m.state==='active'?'stop':'start'}" ${!m.controllable?'disabled':''}>${m.state==='active'?'STOP':'START'}</button></div></article>`).join('')||`<p class="empty-note">${tr('No services registered. Add existing user services to config.json using docs/MODELS.md.','등록된 서비스가 없습니다. docs/MODELS.md에 따라 config.json에 기존 사용자 서비스를 등록하세요.')}</p>`}</div>`;}
const prototypeRender=render;
render=function(animate=true){
 let html;
 if(!liveNode.token){html=pageHeading('CONNECT TO SPARK','01','DGX-SPARK-CONTROL / '+liveNode.version)+`<section class="panel auth-panel"><h2>${tr('Access token','접속 토큰')}</h2><p>${tr('Enter the token saved by the installer on your Spark. It is kept in this browser tab only.','Spark 설치 프로그램이 저장한 토큰을 입력하세요. 이 브라우저 탭에서만 보관됩니다.')}</p><form id="liveLogin"><input type="password" id="liveToken" autocomplete="off" required aria-label="Access token"><button class="button">${tr('CONNECT','연결')}</button></form><p id="liveLoginError" role="status"></p></section>`;}
 else if(state.view==='overview')html=installedOverview();
 else if(state.view==='models')html=installedModels();
 else if(state.view==='settings'){
  const template=document.createElement('template');template.innerHTML=settingsView();
  const personal=template.content.querySelector('.settings-primary > section');
  personal.querySelector('.spark-name-row p').textContent=tr('Shared display name saved on this Spark. The system hostname is unchanged.','이 Spark에 저장되는 공용 표시 이름입니다. 시스템 호스트명은 바뀌지 않습니다.');
  personal.querySelector('#resetPreferences').textContent=tr('RESET APPEARANCE','화면 설정 초기화');
  personal.querySelector('#resetPreferences').previousElementSibling.querySelector('p').textContent=tr('Appearance is saved in this browser. The Spark name is shared across devices.','화면 설정은 이 브라우저에 저장됩니다. Spark 이름은 기기 간 공유됩니다.');
  html=pageHeading('SYSTEM SETTINGS','05','MAKE THIS SPACE YOURS.')+personal.outerHTML+`<section class="panel runtime-panel"><h2>DGX-SPARK-Control ${liveNode.version}</h2><p>${tr('One Python process · demand-driven 5s collection · 720 history samples · 480 MiB service limit.','Python 프로세스 1개 · 요청 시 5초 간격 수집 · 최대 이력 720개 · 서비스 상한 480 MiB.')}</p><div class="setting-row"><span>Interface motion</span>${switchInput('motionToggle',state.motion,'Interface motion')}</div><button class="button secondary" id="liveDiscover">${tr('SCAN MODEL FOLDERS','모델 폴더 검색')}</button><p id="discoveryResult"></p><p>${tr('Versioned updates: bash update.sh X.Y.Z · See docs/UPDATES.md.','버전 지정 업데이트: bash update.sh X.Y.Z · docs/UPDATES.md 참고.')}</p><button class="button secondary" id="liveLogout">${tr('DISCONNECT THIS TAB','이 탭 연결 해제')}</button></section>`;
 }else if(state.view==='logs')html=pageHeading('ACTIVITY LOG','04','CONTROL EVENTS')+`<section class="panel">${liveNode.events.map(e=>`<div class="compact-row">${new Date(e.timestamp*1000).toLocaleTimeString()} · ${escapeHTML(e.message)}</div>`).join('')||`<p class="empty-note">${tr('No control events this session.','이번 서버 실행 중 제어 기록이 없습니다.')}</p>`}</section>`;
 else html=pageHeading('WORKLOAD QUEUE','03','ENGINE INTEGRATION')+`<section class="panel"><p class="empty-note">${tr('Request tracking is not connected in 0.1. No simulated jobs are displayed.','0.1 버전은 요청 추적이 연결되지 않았습니다. 모의 작업은 표시하지 않습니다.')}</p></section>`;
 const previousScroll=window.scrollY;$('#main').innerHTML=`<div class="view${animate?'':' no-enter'}">${html}</div>`;
 $$('.nav-item').forEach(b=>b.classList.toggle('active',b.dataset.view===state.view));
 $('#connectionLabel').textContent=liveNode.connected?'NODE ONLINE':'NODE OFFLINE';
 $('.demo-label').innerHTML='<i></i> V'+liveNode.version+' / LIVE';
 const note=$('.context-note');if(note.firstChild)note.firstChild.textContent='LIVE DATA / ';
 $('#sparkDisplayName').textContent=preferences.sparkName;
 if(!animate)window.scrollTo(0,previousScroll);translateUI();
};
renderMetricDetailBody=function(){
 if(!metricExplorer)return;const id=metricExplorer.id,s=liveNode.sample||{};
 const extra={gpu:['gpu_clock_mhz','clock_event_reasons'],cpu:['cores','cpu_clock_ghz'],memory:['memory_total_gib','memory_available_gib','swap_used_gib','memory_clock_mhz'],disk:['disk_total_tib'],temp:['sensors'],power:['clock_event_reasons'],network:['interfaces'],diskio:['disks']}[id];
 const stringify=v=>v==null?'—':typeof v==='object'?JSON.stringify(v,null,2):String(v);
 $('#metricDetailBody').innerHTML=`<div class="detail-stats">${detailStat(tr('CURRENT','현재'),Array.isArray(s[id])?s[id].map(v=>fmt(v)).join(' / '):fmt(s[id]))}</div><section class="detail-history"><h3>${tr('RECORDED SAMPLES','실제 측정 이력')}</h3><div class="detail-chart">${livePlot(id)}</div></section>${extra.map(key=>`<section class="detail-section"><h3>${escapeHTML(key)}</h3><pre class="live-details">${escapeHTML(stringify(s[key]))}</pre></section>`).join('')}<div class="detail-source">${escapeHTML(detailSources[id])}</div>`;
 $('#detailStreamState').textContent=liveNode.connected?'LIVE / 5 SEC':'DISCONNECTED';$('#detailSampleTime').textContent=s.timestamp?new Date(s.timestamp*1000).toLocaleTimeString():'—';
};
const originalDetail=showMetricDetail;
showMetricDetail=function(id){originalDetail(id);$('.detail-demo-note').textContent=tr('Actual samples only. Gaps mean no collection. Missing values mean unsupported or warming up.','실측 데이터만 표시합니다. 빈 구간은 미수집, —는 미지원 또는 측정 준비 중입니다.');$('.detail-refresh').textContent=tr('REFRESH','새로고침');};
async function refreshLive(){
 if(liveNode.busy||!liveNode.token||document.hidden)return;liveNode.busy=true;
 try{
  const [sample,settings,registered,events]=await Promise.all(['metrics','settings','models','events'].map(p=>api(p)));
  $('#runtimeVersion').textContent='V'+settings.version;
  liveNode.sample=sample;liveNode.history=await api('history');liveNode.models=registered;liveNode.events=events;liveNode.connected=true;liveNode.version=settings.version;preferences.sparkName=settings.spark_name;$('#connectionLabel').textContent='NODE ONLINE';const nameInput=$('#sparkNameInput');if(nameInput&&!document.activeElement.closest('#sparkNameForm'))nameInput.value=settings.spark_name;
  if(state.view==='overview'&&document.querySelector('.metric-grid')){const template=document.createElement('template');template.innerHTML=installedOverview();document.querySelectorAll('[data-metric]').forEach(card=>{const next=template.content.querySelector('[data-metric="'+card.dataset.metric+'"]');if(next)card.innerHTML=next.innerHTML;});document.querySelector('.section-head > span').textContent=tr('LIVE / 5 SEC','실측 / 5초');$('#connectionLabel').textContent='NODE ONLINE';$('#sparkDisplayName').textContent=preferences.sparkName;translateUI();}else if(state.view!=='settings')render(false);else $('#sparkDisplayName').textContent=preferences.sparkName;
  if(metricExplorer&&!$('#modal').hidden)renderMetricDetailBody();
 }catch(error){liveNode.connected=false;if(!liveNode.token||state.view!=='settings')render(false);const err=$('#liveLoginError');if(err)err.textContent=error.message;}
 finally{liveNode.busy=false;}
}
document.addEventListener('submit',async event=>{
 if(!['liveLogin','sparkNameForm'].includes(event.target.id))return;event.preventDefault();event.stopImmediatePropagation();
 try{if(event.target.id==='liveLogin'){liveNode.token=$('#liveToken').value.trim();await api('health');sessionStorage.setItem('spark.access',liveNode.token);await refreshLive();render();}else{const result=await api('settings',{spark_name:$('#sparkNameInput').value});preferences.sparkName=result.spark_name;applyPreferences();toast(tr('Spark name saved on server.','서버에 Spark 이름을 저장했습니다.'));}}catch(error){const el=$('#liveLoginError');if(el)el.textContent=error.message;else toast(error.message);}
},true);
document.addEventListener('click',async event=>{
 const b=event.target.closest('button');if(!b)return;
 if(b.dataset.liveModel){event.stopImmediatePropagation();showModal(`<h2 id="modalTitle">${b.dataset.liveAction==='stop'?'STOP':'START'} SERVICE?</h2><p>${escapeHTML(b.dataset.liveModel)}</p><p>${tr('This controls the real registered service. Stopping interrupts its active requests.','실제 등록된 서비스를 제어합니다. 정지하면 해당 서비스의 진행 중 요청이 중단됩니다.')}</p><button class="button" data-live-confirm="${escapeHTML(b.dataset.liveModel)}" data-live-operation="${b.dataset.liveAction}">CONFIRM</button>`);}
 if(b.dataset.liveConfirm){event.stopImmediatePropagation();b.disabled=true;try{await api('models/action',{id:b.dataset.liveConfirm,action:b.dataset.liveOperation});closeModal();await refreshLive();}catch(error){b.disabled=false;toast(error.message);}}
 if(b.id==='liveDiscover'){event.stopImmediatePropagation();b.disabled=true;try{const result=await api('models/discover',{});$('#discoveryResult').textContent=result.roots_configured?JSON.stringify(result):tr('Configure model_roots in config.json first.','먼저 config.json에 model_roots를 등록하세요.');}catch(error){toast(error.message);}finally{b.disabled=false;}}
 if(b.dataset.language)queueMicrotask(()=>render(false));
 if(b.id==='liveLogout'){event.stopImmediatePropagation();liveNode.token='';liveNode.connected=false;sessionStorage.removeItem('spark.access');render();}
 if(b.id==='resetPreferences'){event.stopImmediatePropagation();const name=preferences.sparkName;preferences={...preferenceDefaults,sparkName:name};savePreferences();setMotion(preferences.motion);render(false);}
},true);
document.addEventListener('visibilitychange',()=>{if(!document.hidden)refreshLive();});
state.jobs=[];state.events=[];state.model=null;
render(false);refreshLive();setInterval(refreshLive,5000);
