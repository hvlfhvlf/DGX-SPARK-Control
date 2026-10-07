'use strict';
// Presentation-only telemetry explorer. All history and breakdowns are fixtures.
let metricExplorer = null;
let detailMotionAnimations=[],detailMotionSerial=0;
function cancelDetailMotion(){detailMotionSerial++;for(const animation of detailMotionAnimations)animation.cancel();detailMotionAnimations=[];}
function animateDetailMotion(open,done=()=>{}){
 const card=document.querySelector('.modal-card'),backdrop=document.querySelector('.modal-backdrop');
 const initial={opacity:getComputedStyle(card).opacity,transform:getComputedStyle(card).transform,backdrop:getComputedStyle(backdrop).opacity};
 cancelDetailMotion();const serial=detailMotionSerial;
 if(!state.motion||matchMedia('(prefers-reduced-motion: reduce)').matches||typeof card.animate!=='function'){done();return;}
 const duration=open?300:200;
 const options={duration,easing:open?'cubic-bezier(.16,1,.3,1)':'cubic-bezier(.4,0,1,1)',fill:'both'};
 detailMotionAnimations=[card.animate(open?[{opacity:0,transform:'translateY(16px) scale(.985)'},{opacity:1,transform:'translateY(0) scale(1)'}]:[{opacity:initial.opacity,transform:initial.transform},{opacity:0,transform:'translateY(6px) scale(.99)'}],options),backdrop.animate([{opacity:open?0:initial.backdrop},{opacity:open?1:0}],{duration,easing:'ease-in-out',fill:'both'})];
 Promise.all(detailMotionAnimations.map(a=>a.finished)).then(()=>{if(serial!==detailMotionSerial)return;done();for(const a of detailMotionAnimations)a.cancel();detailMotionAnimations=[];}).catch(()=>{});
}

const detailText = (en, ko) => uiLanguage === 'ko' ? ko : en;
const detailNames = {
 gpu:['GPU utilization','GPU 사용률'],cpu:['CPU utilization','CPU 사용률'],memory:['Unified memory','통합 메모리'],disk:['SSD usage','SSD 사용량'],
 temp:['GPU temperature','GPU 온도'],power:['GPU power','GPU 전력'],network:['Network traffic','네트워크 사용량'],diskio:['Disk I/O','디스크 I/O']
};
const detailDescriptions = {
 gpu:['Compute activity, clocks and limiting factors.','연산 부하, 클럭, 성능 제한 요인을 확인합니다.'],
 cpu:['Total CPU load and activity across 20 logical cores.','전체 CPU 부하와 20개 논리 코어의 사용률을 확인합니다.'],
 memory:['One memory pool shared by CPU and GPU.','CPU와 GPU가 공유하는 하나의 메모리 공간입니다.'],
 disk:['Capacity and a sample breakdown of stored files.','저장 공간과 파일 유형별 예시 분포를 확인합니다.'],
 temp:['Temperature trends and separately identified sensors.','온도 변화와 센서별 측정값을 구분해 확인합니다.'],
 power:['GPU power only; average and instantaneous readings differ.','GPU 전력만 표시하며 평균값과 순간값을 구분합니다.'],
 network:['Receive and send rates on one physical interface.','물리 인터페이스 하나의 수신·송신 속도를 확인합니다.'],
 diskio:['Read/write throughput and storage responsiveness.','읽기·쓰기 처리량과 저장장치 응답 상태를 확인합니다.']
};
const detailSources = {gpu:'NVML / nvidia-smi',cpu:'/proc/stat · cpufreq',memory:'/proc/meminfo',disk:'statvfs · directory inventory',temp:'NVML · /sys/class/hwmon',power:'nvidia-smi power.draw / power.draw.instant',network:'/proc/net/dev',diskio:'/proc/diskstats'};
function detailValue(n,unit='',decimals=1){return n===null?'—':Number(n).toFixed(decimals)+(unit?' '+unit:'');}
function detailStat(label,value,unit='') { return `<div class="detail-stat"><span>${label}</span><strong>${escapeHTML(value)}${unit?`<small>${unit}</small>`:''}</strong></div>`; }
function detailRows(rows){return `<div class="detail-rows">${rows.map(([a,b])=>`<div class="detail-row"><span>${a}</span><strong>${escapeHTML(b)}</strong></div>`).join('')}</div>`;}
function detailSection(title,content){return `<section class="detail-section"><h3>${title}</h3>${content}</section>`;}
function detailNotice(text){return `<p class="detail-note">${text}</p>`;}
function detailNow(id){const t=telemetry();switch(id){case 'disk':return online()?1.2:null;case 'network':case 'diskio':return online()?ioSample(id,0,state.tick):null;default:return t[id];}}
function detailSeries(id,channel=0){
 const current=detailNow(id);if(current===null)return [];
 const n=61,span={5:60,15:180,60:720}[metricExplorer.range];
 return Array.from({length:n},(_,i)=>{
  const tick=state.tick-(n-1-i)*span/(n-1);
  if(id==='network'||id==='diskio')return ioSample(id,channel,tick);
  if(id==='power'&&channel===1)return Math.max(0,current*(1+.12*Math.sin(tick*.83)));
  if(id==='disk')return Math.max(0,current-(n-1-i)*.0002);
  const scale=id==='memory'?.5:id==='temp'?3:id==='power'?2:6;
  const value=current+scale*(Math.sin(tick*.5)-Math.sin(state.tick*.5));
  return Math.max(0,Math.min(id==='gpu'||id==='cpu'?100:Infinity,value));
 });
}
function detailChart(id){
 const first=detailSeries(id),second=['network','diskio','power'].includes(id)?detailSeries(id,1):[];
 const unit={gpu:'%',cpu:'%',memory:'GiB',disk:'TiB',temp:'°C',power:'W',network:'MB/s',diskio:'MB/s'}[id];
 if(!first.length)return `<div class="detail-chart-empty">${detailText('Telemetry unavailable while offline.','연결이 끊겨 측정값을 표시할 수 없습니다.')}</div>`;
 const max=id==='gpu'||id==='cpu'?100:Math.max(...first,...second,1)*1.15;
 const points=arr=>arr.map((v,i)=>`${42+i*8.6},${(153-v/max*127).toFixed(1)}`).join(' ');
 const labelA=id==='network'?detailText('Receive','수신'):id==='diskio'?detailText('Read','읽기'):id==='power'?detailText('Average','평균'):detailText('Measured value','측정값');
 const labelB=id==='network'?detailText('Send','송신'):id==='diskio'?detailText('Write','쓰기'):detailText('Instantaneous','순간');
 return `<div class="detail-chart-legend"><span><i></i>${labelA}</span>${second.length?`<span><i class="secondary"></i>${labelB}</span>`:''}<span class="detail-unit">${unit}</span></div><svg class="detail-chart" viewBox="0 0 570 180" preserveAspectRatio="none" role="img" aria-label="${detailText('Simulated history','모의 추이')}"><path class="detail-chart-grid" d="M42 26H558M42 89H558M42 153H558"/><text x="2" y="30">${max.toFixed(max<10?1:0)}</text><text x="2" y="93">${(max/2).toFixed(max<10?1:0)}</text><text x="2" y="156">0</text><polyline class="detail-chart-line" points="${points(first)}"/>${second.length?`<polyline class="detail-chart-line secondary" points="${points(second)}"/>`:''}<text x="42" y="175">−${metricExplorer.range}m</text><text x="528" y="175">${detailText('NOW','현재')}</text></svg>`;
}
function metricDetailData(id){
 const t=telemetry(),live=online(),value=detailNow(id),engine=activeModel();
 const dash=v=>live?v:'—',L=detailText,fmt=(v,u='',d=1)=>detailValue(live?v:null,u,d);
 let stats=[],sections=[];
 const stateText=dash(L('Not active · demo','비활성 · 모의'));
 if(id==='gpu'){
  stats=[[L('GPU utilization','GPU 사용률'),fmt(t.gpu,'',0),'%'],[L('SM clock','SM 클럭'),dash('2.19'),'GHz'],[L('GPU temperature','GPU 온도'),fmt(t.temp,'',0),'°C'],[L('Average power','평균 전력'),fmt(t.power),'W']];
  sections.push(detailSection(L('Execution & limits','실행 상태와 제한'),detailRows([[L('Engine','엔진'),dash(engine?engine.name:L('No engine loaded','실행 엔진 없음'))],[L('Thermal slowdown','열 스로틀링'),stateText],['SW Power Cap',stateText],[L('Clock range','클럭 정보'),L('2.19 GHz · sample, not maximum','2.19 GHz · 예시값, 최대 클럭 아님')]])));
  sections.push(detailNotice(L('Utilization is time spent running GPU kernels, not a percentage of theoretical compute performance. The demo limit flags are fixtures, not the last live Spark measurement.','사용률은 GPU 커널이 동작한 시간의 비율이며 이론 연산 성능의 사용 비율이 아닙니다. 제한 상태는 모의값이며 앞서 측정한 실제 Spark 상태와 다릅니다.')));
 }
 if(id==='cpu'){
  stats=[[L('Total utilization','전체 사용률'),fmt(t.cpu,'',0),'%'],[L('Logical cores','논리 코어'),dash('20'),''],[L('Lowest core clock','최저 코어 클럭'),dash('2.81'),'GHz'],[L('Highest core clock','최고 코어 클럭'),dash('3.90'),'GHz']];
  // Symmetric offsets keep the mean equal to the overview CPU utilization.
  sections.push(detailSection(L('Per-core activity · sample','코어별 사용률 · 예시'),`<div class="core-grid">${Array.from({length:20},(_,i)=>{const n=live?Math.max(0,t.cpu+((i%5)-2)*(state.scenario==='idle'?.5:2)):null;return `<div class="core-cell"><span>CPU ${String(i).padStart(2,'0')}</span><strong>${n===null?'—':n.toFixed(0)+'%'}</strong><i style="--load:${n||0}%"></i></div>`;}).join('')}</div>`));
  sections.push(detailNotice(L('Total utilization uses 100% for the whole CPU. Core numbers are illustrative; performance/efficiency cluster membership must be discovered before labelling.','전체 CPU를 100%로 계산합니다. 코어 번호는 예시이며 성능·효율 코어 소속은 실제 토폴로지를 확인한 뒤 표시합니다.')));
 }
 if(id==='memory'){
  const used=t.memory,available=live?121.6-used:null;
  stats=[[L('Used','사용'),fmt(used),'GiB'],[L('Available','여유'),fmt(available),'GiB'],[L('Total','전체'),dash('121.6'),'GiB'],[L('Utilization','사용률'),fmt(live?used/121.6*100:null),'%']];
  sections.push(detailSection(L('Shared pool','공유 메모리'),`<div class="detail-capacity"><span style="width:${live?used/121.6*100:0}%"></span></div>`+detailRows([[L('Calculation','계산 기준'),'MemTotal − MemAvailable'],[L('Swap used / total · sample','스왑 사용 / 전체 · 예시'),dash('0.0 / 8.0 GiB')],[L('Memory clock','메모리 클럭'),L('Unavailable','미지원')],[L('Active model estimate','활성 모델 예상 메모리'),dash(engine?engine.memory:'—')]])));
  sections.push(detailNotice(L('CPU and GPU share this pool: do not add separate capacities. The model estimate is registry metadata, not measured process memory. Available includes memory the OS can reclaim.','CPU와 GPU가 이 공간을 공유하므로 용량을 따로 더하지 않습니다. 모델 예상치는 레지스트리 정보이며 프로세스 실측값이 아닙니다. 여유량에는 운영체제가 회수할 수 있는 메모리가 포함됩니다.')));
 }
 if(id==='disk'){
  stats=[[L('Used','사용'),dash('1.2'),'TiB'],[L('Free','여유'),dash('2.4'),'TiB'],[L('Capacity','전체 용량'),dash('3.6'),'TiB'],[L('Utilization','사용률'),dash('33.3'),'%']];
  sections.push(detailSection(L('Stored files · sample inventory','저장 파일 · 예시 분포'),`<div class="storage-breakdown">${[[L('Model weights','모델 가중치'),.78],[L('Environments & containers','환경·컨테이너'),.18],[L('Generated outputs','생성 결과물'),.12],[L('Other files','기타 파일'),.12]].map(([name,size])=>`<div><span>${name}</span><strong>${dash(size.toFixed(2)+' TiB')}</strong><i style="width:${live?size/1.2*100:0}%"></i></div>`).join('')}</div>`));
  sections.push(detailNotice(L('Example inventory totals 1.2 TiB. Future folder scans run less often than telemetry; their timestamp will be shown separately. This view does not delete files.','예시 분포의 합계는 1.2 TiB입니다. 실제 폴더 용량은 저빈도로 수집하고 별도의 조사 시각을 표시합니다. 이 화면에서 파일을 삭제하지 않습니다.')));
 }
 if(id==='temp'){
  const max=live?Math.max(...detailSeries('temp')):null;
  stats=[[L('GPU now','현재 GPU'),fmt(t.temp,'',0),'°C'],[L('Window peak · sample','기간 최고 · 예시'),fmt(max),'°C'],[L('Thermal slowdown','열 스로틀링'),dash(L('Inactive','비활성')),''],[L('Exposed readings','표시 항목'),dash('12'),'']];
  const sensors=[...Array.from({length:7},(_,i)=>['ACPI '+(i+1),live?(t.temp+[-1,-9,-8,-7,-1,-4,-6][i]).toFixed(1)+' °C':'—',L('Location unverified','위치 미확인')]),['NVMe Composite',dash('45.9 °C'),L('Composite reading','종합값')],['NVMe Sensor 1',dash('47.9 °C'),L('Device sensor','장치 센서')],['NVMe Sensor 2',dash('45.9 °C'),L('Device sensor','장치 센서')],['Wi-Fi',dash('54.0 °C'),'mt7925']];
  sections.push(detailSection(L('Other sensors · illustrative readings','기타 센서 · 모의값'),`<div class="sensor-list">${sensors.map(([n,v,note])=>`<div><span>${n}</span><strong>${v}</strong><small>${note}</small></div>`).join('')}</div>`));
  sections.push(detailNotice(L('Twelve readings include GPU and SSD composite temperature, not twelve distinct chips. ACPI sensors are not labelled CPU/SoC until their locations are verified. Duplicate thermal-zone readings are excluded.','GPU와 SSD 종합값을 포함한 12개 항목이며 물리 칩 12개를 의미하지 않습니다. 위치가 확인되기 전 ACPI를 CPU·SoC 온도로 표기하지 않고, thermal zone 중복값도 제외합니다.')));
 }
 if(id==='power'){
  const instant=live?t.power*(1+.12*Math.sin(state.tick*.83)):null;
  stats=[[L('Average draw','평균 전력'),fmt(t.power),'W'],[L('Instantaneous draw','순간 전력'),fmt(instant),'W'],[L('Window peak · average','기간 최고 · 평균값'),fmt(live?Math.max(...detailSeries('power')):null),'W'],[L('Power cap','전력 제한'),dash(L('Inactive','비활성')),'']];
  sections.push(detailSection(L('Power scope','측정 범위'),detailRows([[L('Measured component','측정 대상'),'NVIDIA GB10 GPU'],[L('Configured power limit','설정 전력 한도'),L('Unavailable','미지원')],[L('Whole-system power','전체 시스템 전력'),L('Not connected','미연결')],[L('Wall power','콘센트 전력'),L('External meter required','외부 전력계 필요')]])));
  sections.push(detailNotice(L('Average and instantaneous readings cover different sampling windows. A power-cap flag indicates clock limiting for power; it is distinct from thermal slowdown. No energy or cost estimate is inferred from a single reading.','평균·순간 전력은 측정 구간이 다릅니다. 전력 제한은 열 스로틀링과 구분합니다. 단일 측정값으로 누적 전력량이나 전기요금을 계산하지 않습니다.')));
 }
 if(id==='network'){
  stats=[[L('Receive','수신'),fmt(live?ioSample(id,0,state.tick):null),'MB/s'],[L('Send','송신'),fmt(live?ioSample(id,1,state.tick):null),'MB/s'],[L('Received total · sample','누적 수신 · 예시'),dash('18.4'),'GB'],[L('Sent total · sample','누적 송신 · 예시'),dash('2.7'),'GB']];
  sections.push(detailSection(L('Interface & counters','인터페이스와 카운터'),detailRows([[L('Interface · fixture','인터페이스 · 예시'),'eth0'],[L('Scope','집계 범위'),L('Physical interface · LAN + internet','물리 인터페이스 · LAN + 인터넷')],[L('Counter period','누적 기준'),L('Since boot / counter reset','부팅 또는 카운터 초기화 이후')],[L('Receive / send errors · sample','수신 / 송신 오류 · 예시'),dash('0 / 0')],[L('Dropped packets · sample','누락 패킷 · 예시'),dash('0')]])));
  sections.push(detailNotice(L('MB/s uses decimal megabytes per second, not Mbps. Physical-interface traffic includes LAN. Adding a Tailscale virtual interface would double-count some traffic. Interface names and totals here are fixtures.','MB/s는 초당 십진 메가바이트이며 Mbps와 다릅니다. LAN 트래픽이 포함되며 Tailscale 가상 인터페이스를 더하면 일부 트래픽이 중복됩니다. 인터페이스 이름과 누적값은 예시입니다.')));
 }
 if(id==='diskio'){
  stats=[[L('Read','읽기'),fmt(live?ioSample(id,0,state.tick):null),'MB/s'],[L('Write','쓰기'),fmt(live?ioSample(id,1,state.tick):null),'MB/s'],[L('Read IOPS · sample','읽기 IOPS · 예시'),dash('1,240'),''],[L('Write IOPS · sample','쓰기 IOPS · 예시'),dash('320'),'']];
  sections.push(detailSection(L('Device responsiveness · sample','장치 응답 상태 · 예시'),detailRows([[L('Device · fixture','장치 · 예시'),'nvme0n1'],[L('Read average latency','평균 읽기 지연'),dash('0.8 ms')],[L('Write average latency','평균 쓰기 지연'),dash('1.2 ms')],[L('Average queue depth','평균 큐 깊이'),dash('0.4')],[L('Collection interval','수집 간격'),L('5 seconds · demo','5초 · 모의')]])));
  sections.push(detailNotice(L('Throughput is bytes transferred; IOPS counts operations. Latency and queue depth help identify storage pressure. Do not sum a whole disk with its own partitions. All device statistics here are illustrative.','처리량은 전송 바이트, IOPS는 처리 작업 수입니다. 지연시간과 큐 깊이로 저장장치 부하를 판단합니다. 디스크와 그 디스크의 파티션을 중복 합산하지 않습니다. 장치 통계는 모두 예시입니다.')));
 }
 return {stats,sections};
}
function renderMetricDetailBody(){
 if(!metricExplorer)return;
 const id=metricExplorer.id,{stats,sections}=metricDetailData(id);
 const area=document.getElementById('metricDetailBody');if(!area)return;
 area.innerHTML=`<div class="detail-stats">${stats.map(x=>detailStat(...x)).join('')}</div><section class="detail-history"><h3>${detailText('HISTORY / SIMULATED','시간별 추이 / 모의 데이터')}</h3>${detailChart(id)}</section>${sections.join('')}<div class="detail-source"><span>${detailText('PLANNED SOURCE','향후 수집원')}</span><code>${detailSources[id]}</code></div>`;
 document.getElementById('detailSampleTime').textContent=timeNow()+' KST';
 document.getElementById('detailStreamState').textContent=!online()?detailText('OFFLINE','연결 끊김'):state.live?detailText('5 SEC / SIMULATED','5초 갱신 / 모의'):detailText('PAUSED / SIMULATED','갱신 정지 / 모의');
}
function showMetricDetail(id){
 if(!detailNames[id])return;
 metricExplorer={id,range:5};
 showModal(`<div class="detail-heading"><span class="detail-kicker">SPARK / TELEMETRY</span><h2 id="modalTitle">${detailText(...detailNames[id])}</h2><p>${detailText(...detailDescriptions[id])}</p></div><div class="detail-status"><span id="detailStreamState"></span><time id="detailSampleTime"></time></div><div class="detail-controls"><div class="segments" aria-label="${detailText('History time range','추이 시간 범위')}">${[5,15,60].map(n=>`<button data-detail-range="${n}" class="${n===5?'active':''}" aria-pressed="${n===5}">${n===60?'1h':n+'m'}</button>`).join('')}</div><button class="detail-refresh" data-detail-refresh>${detailText('REFRESH SAMPLE ↻','모의값 갱신 ↻')}</button></div><p class="detail-demo-note">${detailText('Design prototype. History and breakdowns are generated examples, not recordings from your Spark.','디자인 시제품입니다. 과거 추이와 세부 분포는 예시이며 실제 Spark 기록이 아닙니다.')}</p><div id="metricDetailBody"></div>`);
 document.querySelector('.modal-card').classList.add('metric-detail-modal');
 document.getElementById('modalKind').textContent=detailText('METRIC DETAILS','지표 상세');
 document.querySelector('.modal-card').scrollTop=0;
 renderMetricDetailBody();
 animateDetailMotion(true);
}
document.addEventListener('click',event=>{
 const b=event.target.closest('button');if(!b||!metricExplorer||document.getElementById('modal').hidden)return;
 if(b.hasAttribute('data-detail-range')){metricExplorer.range=Number(b.dataset.detailRange);document.querySelectorAll('[data-detail-range]').forEach(el=>{const selected=Number(el.dataset.detailRange)===metricExplorer.range;el.classList.toggle('active',selected);el.setAttribute('aria-pressed',String(selected));});renderMetricDetailBody();}
 if(b.hasAttribute('data-detail-refresh'))renderMetricDetailBody();
});
