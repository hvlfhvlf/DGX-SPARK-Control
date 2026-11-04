'use strict';
// Installed runtime only. Uses the existing five-second API cache and bounded history.
// Controls remain mounted across samples to preserve focus, scroll and disclosure state.
(()=>{
 const D=TelemetryDetailData,E=escapeHTML;
 const names={gpu:['GPU utilization','GPU 사용률'],cpu:['CPU utilization','CPU 사용률'],memory:['Memory','메모리'],disk:['SSD capacity','SSD 저장 공간'],temp:['Temperature','온도'],power:['GPU power','GPU 전력'],network:['Network traffic','네트워크 트래픽'],diskio:['Disk I/O','디스크 I/O']};
 const units={gpu:'%',cpu:'%',memory:'GiB',disk:'TiB',temp:'°C',power:'W',network:'MB/s',diskio:'MB/s'};
 const source={gpu:'NVML',cpu:'/proc/stat · cpufreq',memory:'/proc/meminfo · firmware',disk:'statvfs(/)',temp:'NVML · /sys/class/hwmon',power:'NVML · nvmlDeviceGetPowerUsage',network:'/proc/net/dev · physical interfaces',diskio:'/proc/diskstats · whole physical devices'};
 const L=(en,ko)=>tr(en,ko);
 const n=(v,p=1)=>D.valid(v)?v.toFixed(p):'—';
 const val=(v,u='',p=1)=>n(v,p)+(u?' '+u:'');
 const rate=v=>n(v,D.valid(v)&&v>0&&v<1?3:1);
 const ratio=(a,b)=>D.valid(a)&&b>0?a/b*100:null;
 const divide=(v,d)=>D.valid(v)?v/d:null;
 const time=t=>D.valid(t)?new Date(t*1000).toLocaleTimeString(uiLanguage==='ko'?'ko-KR':'en-GB',{hour12:false,hour:'2-digit',minute:'2-digit',second:'2-digit'}):'—';
 const stamp=(s)=>s.timestamp?new Date(s.timestamp*1000).toLocaleString(uiLanguage==='ko'?'ko-KR':'en-GB',{hour12:false}):'—';
 const eventState=(events,key)=>events===null?L('Unavailable','확인 불가'):events[key]?L('Detected','감지됨'):L('Not detected','감지 안 됨');
 const stat=(label,value,unit='',note='',text=false)=>`<div class="td-stat${text?' td-stat-text':''}"><div class="td-stat-head"><span>${E(label)}</span>${note?`<small class="td-stat-note">${E(note)}</small>`:''}</div><strong>${E(value)}${unit?`<small>${E(unit)}</small>`:''}</strong></div>`;
 const rateStat=(label,value,note)=>stat(label,rate(value>=1000?value/1000:value),value>=1000?'GB/s':'MB/s',note);
 const rows=items=>`<dl class="td-rows">${items.map(([label,value])=>`<div><dt>${E(label)}</dt><dd>${E(String(value??'—'))}</dd></div>`).join('')}</dl>`;
 const block=(title,body)=>`<section class="td-section"><h3>${E(title)}</h3>${body}</section>`;
 const hint=text=>`<p class="td-hint">${E(text)}</p>`;
 function eventRows(events){
  if(events===null)return hint(L('Clock event reporting is unavailable on this device.','이 장치에서는 클럭 제한 원인을 확인할 수 없습니다.'));
  const list=events.active.map(([,en,ko])=>L(en,ko));
  if(events.unknown)list.push(L('Other reported flags','기타 보고된 플래그')+' · 0x'+events.unknown.toString(16));
  return `<div class="td-flags">${(list.length?list:[L('No active clock events','활성 클럭 제한 없음')]).map(label=>`<span>${E(label)}</span>`).join('')}</div>`;
 }
 function bars(labels,values,total,unit){
  const portions=D.composition(values,total);
  if(!portions)return hint(L('Capacity breakdown is unavailable.','용량 구성을 확인할 수 없습니다.'));
  return `<div class="td-capacity" role="img" aria-label="${E(labels.map((label,i)=>label+' '+val(values[i],unit)).join(', '))}">${portions.map((p,i)=>`<span class="td-tone-${i}" style="width:${p}%"></span>`).join('')}</div><div class="td-capacity-legend">${labels.map((label,i)=>`<div><span><i class="td-tone-${i}"></i>${E(label)}</span><strong>${E(val(values[i],unit))}</strong></div>`).join('')}</div>`;
 }
 function context(id,s,h){
  const gpu=h.gpu_name||L('GPU identity unavailable','GPU 정보 없음');
  if(id==='power')return gpu+' · '+L('GPU only','GPU 전력 기준');
  if(['gpu','temp'].includes(id))return gpu;
  if(id==='cpu')return `${h.architecture||'CPU'} · ${h.logical_cpus||Object.keys(s.cores||{}).length||'—'} ${L('logical CPUs','논리 코어')}`;
  if(id==='memory')return h.memory_kind==='unified'?L('Unified CPU + GPU memory','CPU + GPU 통합 메모리'):L('System memory','시스템 메모리');
  if(id==='disk')return L('Root filesystem capacity','루트 파일시스템 기준');
  if(id==='network')return L('Physical interfaces · receive / send','물리 인터페이스 · 수신 / 송신');
  return L('Physical devices · read / write','물리 장치 · 읽기 / 쓰기');
 }
 function summary(id,s,h,history){
  const current=L('Current','현재'),period=L('Selected range','선택 구간'),events=D.clockEvents(s.clock_event_reasons),st=D.stats(history,id);
  if(id==='gpu')return stat(L('Utilization','사용률'),n(s.gpu,0),'%',current)+stat(L('SM clock','SM 클럭'),n(divide(s.gpu_clock_mhz,1000),2),'GHz')+stat(L('GPU temperature','GPU 온도'),n(s.temp,0),'°C')+stat(L('GPU power','GPU 전력'),n(s.power),'W');
  if(id==='cpu')return stat(L('Total utilization','전체 사용률'),n(s.cpu),'%',current)+stat(L('Lowest core clock','최저 코어 클럭'),n(s.cpu_clock_ghz?.[0],2),'GHz')+stat(L('Highest core clock','최고 코어 클럭'),n(s.cpu_clock_ghz?.[1],2),'GHz')+stat(L('Logical CPUs','논리 코어'),n(h.logical_cpus||Object.keys(s.cores||{}).length||null,0));
  if(id==='memory')return stat(L('In use','사용 중'),n(s.memory),'GiB')+stat(L('Available','사용 가능'),n(s.memory_available_gib),'GiB')+stat(L('Utilization','사용률'),n(ratio(s.memory,s.memory_total_gib)),'%')+stat(L('Swap used','스왑 사용'),n(s.swap_used_gib),'GiB');
  if(id==='disk')return stat(L('In use','사용 중'),n(divide(s.disk_used_bytes,2**40),2),'TiB')+stat(L('Available','사용 가능'),n(divide(s.disk_available_bytes,2**40),2),'TiB')+stat(L('Used / total','전체 대비 사용률'),n(s.disk_used_percent),'%')+stat(L('Filesystem total','파일시스템 전체'),n(s.disk_total_tib,2),'TiB');
  if(id==='temp')return stat(L('GPU now','현재 GPU'),n(s.temp),'°C')+stat(L('GPU average','GPU 평균'),n(st.mean),'°C',period)+stat(L('GPU peak','GPU 최고'),n(st.peak),'°C',period)+stat(L('Thermal limiting','열 제한'),eventState(events,'thermal'),'',L('NVML event flags','NVML 플래그 기준'),true);
  if(id==='power')return stat(L('GPU draw','GPU 소비 전력'),n(s.power),'W',current)+stat(L('Average draw','평균 전력'),n(st.mean),'W',period)+stat(L('Peak draw','최고 전력'),n(st.peak),'W',period)+stat(L('Power limiting','전력 제한'),eventState(events,'power'),'',L('NVML event flags','NVML 플래그 기준'),true);
  const labels=id==='network'?[L('Receive','수신'),L('Send','송신')]:[L('Read','읽기'),L('Write','쓰기')];
  return labels.map((label,i)=>rateStat(label,s[id]?.[i],current)).join('')+labels.map((label,i)=>rateStat(label+' '+L('peak','최고'),D.stats(history,id,i).peak,period)).join('');
 }
 function sensorLabel(sensor){
  const match=(sensor.label||'').match(/^temp(\d+)(?:_input)?$/);
  if(!match)return sensor.label||sensor.id||'—';
  const family=/^acpi/.test(sensor.source||'')?'ACPI':(sensor.source||'hwmon');
  return family+' '+L('sensor','센서')+' '+match[1];
 }
 function specifics(id,s,h){
  const events=D.clockEvents(s.clock_event_reasons);
  if(id==='gpu')return block(L('Clock limiting','클럭 제한 상태'),rows([[L('Thermal limiting','열 제한'),eventState(events,'thermal')],[L('Power limiting','전력 제한'),eventState(events,'power')]])+eventRows(events));
  if(id==='cpu'){
   const cores=Object.entries(s.cores||{}).sort(([a],[b])=>a.localeCompare(b,undefined,{numeric:true}));
   return block(L('Per-core utilization','코어별 사용률'),cores.length?`<div class="td-cores">${cores.map(([name,v])=>`<div><span>${E(name.toUpperCase())}</span><strong>${n(v)}<small>%</small></strong><i><b style="width:${D.valid(v)?Math.max(0,Math.min(100,v)):0}%"></b></i></div>`).join('')}</div>`:hint(L('Waiting for per-core counters.','코어별 측정을 기다리고 있습니다.')));
  }
  if(id==='memory')return block(L('Memory composition','메모리 구성'),bars([L('In use','사용 중'),L('Available','사용 가능')],[s.memory,s.memory_available_gib],s.memory_total_gib,'GiB'))+block(L('Capacity & hardware','용량과 하드웨어'),rows([[L('Installed memory','설치 메모리'),h.installed_memory_bytes?val(h.installed_memory_bytes/2**30,'GiB'):L('Firmware value unavailable','펌웨어 값 없음')],[L('OS usable total','OS 사용 가능 총량'),val(s.memory_total_gib,'GiB')]]));
  if(id==='disk')return block(L('Storage composition','저장 공간 구성'),bars([L('Used','사용'),L('Available','가용'),L('Reserved free','예약 여유')],[s.disk_used_bytes,s.disk_available_bytes,s.disk_reserved_free_bytes].map(v=>divide(v,2**30)),divide(s.disk_total_bytes,2**30),'GiB'))+rows([[L('Mount point','마운트 위치'),s.disk_mount]]);
  if(id==='temp'){
   const sensors=Array.isArray(s.sensors)?s.sensors:[];
   return block(L('Reported sensors','센서별 온도'),`<div class="td-sensors"><div><span>${E(h.gpu_name||'GPU')}<small>NVML · GPU</small></span><strong>${val(s.temp,'°C')}</strong></div></div><details class="sensor-extra" id="additionalSensors"><summary id="additionalSensorsToggle">${L('Additional sensors','추가 센서')} · ${sensors.length}</summary><p>${L('Driver labels; ACPI does not identify the CPU or SoC.','드라이버 표기입니다. ACPI 값의 CPU·SoC 위치는 확인되지 않았습니다.')}</p><div class="td-sensors">${sensors.map(sensor=>`<div><span>${E(sensorLabel(sensor))}<small>${E(sensor.source||'hwmon')}</small></span><strong>${val(sensor.celsius,'°C')}</strong></div>`).join('')}</div></details>`)+block(L('Clock events','클럭 제한 상태'),eventRows(events));
  }
  if(id==='power')return block(L('Related GPU readings','GPU 동작 상태'),rows([[L('GPU utilization','GPU 사용률'),val(s.gpu,'%',0)],[L('GPU temperature','GPU 온도'),val(s.temp,'°C')]]))+block(L('Clock events','클럭 제한 상태'),eventRows(events));
  return '';
 }
 function technicalDetails(id,s,h){
  if(id==='disk')return diskAccounting(s);
  if(id==='gpu'||id==='memory')return rows([[L('Memory clock','메모리 클럭'),s.memory_clock_mhz==null?L('Unavailable','조회 불가'):val(s.memory_clock_mhz,'MHz',0)]]);
  if(id==='temp')return block(L('Sensor identifiers','센서 식별 정보'),rows((Array.isArray(s.sensors)?s.sensors:[]).map(sensor=>[sensorLabel(sensor),(sensor.source||'hwmon')+' · '+(sensor.id||'—')])));
  if(id!=='network'&&id!=='diskio')return '';
  const network=id==='network',devices=network?s.interfaces:s.disks;
  return block(network?L('Included interfaces','집계 인터페이스'):L('Included devices','집계 장치'),`<div class="td-flags">${Array.isArray(devices)&&devices.length?devices.map(name=>`<span>${E(name)}</span>`).join(''):E(L('No devices reported','보고된 장치 없음'))}</div>`+rows([[L('Scope','측정 범위'),network?L('All reported physical interfaces','보고된 물리 인터페이스 합계'):L('Whole physical block devices','물리 블록 장치 전체 합계')],[L('Unit','단위'),'1 MB/s = 1,000,000 B/s'],[L('Rate sampling','속도 측정'),s.rate_warming_up?L('Warming up · next sample required','준비 중 · 다음 측정 필요'):L('Counter change / elapsed seconds','누적 카운터 차이 / 경과 시간')]])+hint(network?L('Includes local-network and internet traffic. Virtual interfaces such as Tailscale are excluded to avoid double counting. Per-interface rates and cumulative totals are not collected.','LAN과 인터넷 트래픽을 포함합니다. Tailscale 등 가상 인터페이스는 중복 집계를 피하도록 제외됩니다. 인터페이스별 속도·누적 전송량은 수집하지 않습니다.'):L('Read and write rates exclude partitions already counted by their whole device. IOPS, latency and per-device rates are not collected.','전체 장치에 포함된 파티션은 중복 합산하지 않습니다. IOPS·지연시간·장치별 속도는 수집하지 않습니다.')));
 }
 function chart(id,history,s,end){
  const range=metricExplorer.range,start=end-range*60,key=id+':'+range;
  metricExplorer.scales??={};
  const max=D.scale(id,s,history,metricExplorer.scales[key]);metricExplorer.scales[key]=max;
  const dual=id==='network'||id==='diskio',unit=units[id];
  const labels=dual?(id==='network'?[L('Receive','수신'),L('Send','송신')]:[L('Read','읽기'),L('Write','쓰기')]):[id==='temp'?L('GPU temperature','GPU 온도'):L(...names[id])];
  const width=720,height=160;
  const traces=labels.map((_,channel)=>D.segments(history,id,channel,start,end,max).map(points=>{
   const p=points.map(([x,y])=>[x*width,(1-y)*height]);
   return p.length===1?`<circle class="td-point td-channel-${channel}" cx="${p[0][0]}" cy="${p[0][1]}" r="2"/>`:`<polyline class="td-trace td-channel-${channel}" points="${p.map(v=>v.map(n=>n.toFixed(2)).join(',')).join(' ')}"/>`;
  }).join('')).join('');
  const displayValue=v=>dual?rate(v)+' '+unit:val(v,unit,id==='disk'?2:1);
  const count=history.filter(row=>labels.some((_,i)=>D.valid(D.reading(row,id,i)))).length;
  const tick=v=>n(v,v!==0&&v<10?2:v%1?1:0);
  return `<div class="td-legend">${labels.map((name,i)=>`<span><i class="td-tone-${i}"></i>${E(name)}</span>`).join('')}<span class="td-axis-unit">${unit}</span></div><div class="td-plot"><div class="td-y-axis"><span>${tick(max)}</span><span>${tick(max/2)}</span><span>0</span></div><div class="td-plot-area"><svg viewBox="0 0 ${width} ${height}" preserveAspectRatio="none" role="img" aria-label="${E(L('Recorded history','실제 측정 이력')+' · '+labels.join(' / ')+' · '+unit)}"><path class="td-gridline" d="M0 1H720M0 80H720M0 159H720"/>${traces}</svg>${count?'':`<div class="td-empty">${E(L('No samples in this range','이 구간에 수집된 값이 없습니다'))}</div>`}</div></div><div class="td-x-axis"><span>${time(start)}</span><span>${time(start+(end-start)/2)}</span><span>${time(end)}</span></div>${['temp','power'].includes(id)?'':`<div class="td-range-summary">${labels.map((label,i)=>{const st=D.stats(history,id,i);return `<div><span>${E(dual?label:L('Selected range','선택 구간'))}</span><strong>${E(L('AVG','평균'))} ${displayValue(st.mean)}${dual?'':` <span>/</span> ${E(L('MAX','최고'))} ${displayValue(st.peak)}`}</strong></div>`;}).join('')}</div>`}<p class="td-chart-caption">${E(L('Collected samples','수집된 측정값'))} · ${count}</p>`;
 }
 function diskAccounting(s){
  return rows([[L('Used','사용'),val(divide(s.disk_used_bytes,2**30),'GiB')],[L('Available to user','사용자 가용 공간'),val(divide(s.disk_available_bytes,2**30),'GiB')],[L('Free but reserved','예약된 여유 공간'),val(divide(s.disk_reserved_free_bytes,2**30),'GiB')],[L('Linux df usage','Linux df 사용률'),val(s.disk_df_percent,'%',0)]]);
 }
 function sources(id){
  if(id==='disk')return `<div id="tdTechnicalDetails"></div>`+hint(L('Only the root filesystem is measured, not every SSD. Used = total − free; available excludes reserved free space. The headline percentage is used / total. Linux df uses used / (used + available), so its percentage may be higher.','루트 파일시스템만 측정하며 모든 SSD의 합계가 아닙니다. 사용량은 전체에서 여유 공간을 뺀 값이고, 가용 공간에는 예약된 여유 공간이 포함되지 않습니다. 상단 사용률은 사용량 / 전체 용량이며, Linux df는 사용량 / (사용량 + 가용 공간)으로 계산하므로 더 높을 수 있습니다.'))+`<code>${E(source[id])}</code>`+hint(L('Capacity refreshes every five seconds while clients request data. A dash means unavailable; disconnections retain the last reading and timestamp. GiB = 2³⁰ bytes; TiB = 2⁴⁰ bytes.','접속 중에는 5초 간격으로 용량을 갱신합니다. —는 조회 불가이며, 연결이 끊기면 마지막 측정값과 시각을 유지합니다. GiB는 2³⁰바이트, TiB는 2⁴⁰바이트입니다.'));
  const explanations={cpu:L('Total utilization is averaged across logical CPUs. Clock values show the lowest and highest exposed core frequencies.','전체 사용률은 논리 코어 전체의 평균입니다. 클럭은 조회 가능한 코어 주파수의 최저·최고값입니다.'),memory:L('In use = OS total − available. Available includes reclaimable memory. CPU and GPU usage cannot be separated with these counters.','사용 중 = OS 총량 − 사용 가능 용량입니다. 사용 가능에는 회수 가능한 메모리가 포함됩니다. 이 측정값으로 CPU·GPU 점유량을 분리할 수 없습니다.'),temp:L('Sensor names follow the driver. ACPI readings do not identify a CPU/SoC location. Multiple readings may describe the same component. Only GPU temperature is graphed above.','센서명은 드라이버 표기를 따릅니다. ACPI 값의 CPU·SoC 위치는 확인되지 않았으며, 여러 값이 같은 부품을 나타낼 수 있습니다. 위 그래프는 GPU 온도입니다.'),power:L('This is the NVML GPU power reading, not whole-system or wall power. Its sensor averaging period depends on the device. The chart average is the arithmetic mean of collected readings, not a separate instantaneous sensor.','시스템 전체·콘센트 전력이 아닌 NVML GPU 전력값이며 센서 내부 평균 구간은 장치에 따라 다릅니다. 구간 평균은 수집된 값의 산술평균이며 별도의 순간 전력 센서가 아닙니다.')};
  return `<div id="tdTechnicalDetails"></div>`+(explanations[id]?hint(explanations[id]):'')+(['gpu','temp','power'].includes(id)?hint(L('Idle and clock policies are not thermal throttling. Hardware slowdown alone does not identify its cause.','유휴·클럭 정책은 열 스로틀링이 아닙니다. 하드웨어 클럭 저하만으로 원인을 단정하지 않습니다.')):'')+`<code>${E(source[id])}</code>`+hint(L('Five-second collection, only while clients request data. Up to 720 shared samples in server memory; no reconstruction after downtime. Range averages include valid samples only, including zeros.','클라이언트 요청이 있을 때 5초 간격으로 수집합니다. 서버 메모리에 최대 720개를 공유하며 중단 구간은 복원하지 않습니다. 구간 평균은 0을 포함한 유효 측정값만 사용합니다.'))+hint(L('Gaps are not interpolated. Temperature, power and I/O axes do not shrink while the dialog is open.','빈 구간은 연결하지 않습니다. 온도·전력·I/O의 축은 상세창이 열린 동안 축소되지 않습니다.'))+hint(L('A dash means unavailable or warming up. When disconnected, retained readings show their original timestamp.','—는 미지원·미수집 또는 측정 준비 중을 뜻합니다. 연결이 끊기면 마지막 측정값과 시각을 유지합니다.'));
 }
 function patch(selector,html){const element=document.querySelector(selector);if(element)patchRetainingInteraction(element,html);}
 renderMetricDetailBody=function(){
  if(!metricExplorer||!document.querySelector('.td-shell'))return;
  const id=metricExplorer.id,s=liveNode.sample||{},h=liveNode.hardware||{},end=Date.now()/1000;
  const history=id==='disk'?[]:D.windowRows(liveNode.history,metricExplorer.range,end),fresh=liveNode.connected&&D.valid(s.timestamp)&&end-s.timestamp<=15;
  document.querySelector('#tdContext').textContent=context(id,s,h);
  const status=document.querySelector('#detailStreamState');status.classList.toggle('td-stale',!fresh);status.textContent=fresh?L('LIVE · 5 SEC','실시간 · 5초'):s.timestamp?L('LAST READING · NOT UPDATING','마지막 측정값 · 갱신 중단'):L('WAITING FOR DATA','데이터 대기 중');
  document.querySelector('#detailSampleTime').textContent=L('Updated ','측정 ')+time(s.timestamp);
  document.querySelector('#detailSampleTime').title=stamp(s);
  patch('#tdStats',summary(id,s,h,history));
  if(id!=='disk')patch('#tdChart',chart(id,history,s,end));
  patch('#tdSpecifics',specifics(id,s,h));
  patch('#tdTechnicalDetails',technicalDetails(id,s,h));
 };
 showMetricDetail=function(id){
  if(!names[id])return;
  metricExplorer={id,range:5,scales:{}};
  const history=id==='disk'?'':`<section class="td-history"><div class="td-chart-head"><h3>${E(L('History','시간별 추이'))}</h3><div class="td-ranges" role="group" aria-label="${E(L('History time range','추이 시간 범위'))}">${[1,5,60].map(range=>`<button type="button" data-detail-range="${range}" class="${range===5?'active':''}" aria-pressed="${range===5}">${range===60?'1h':range+'m'}</button>`).join('')}</div></div><div id="tdChart"></div></section>`;
  showModal(`<div class="td-shell" translate="no"><div class="td-heading"><h2 id="modalTitle">${E(L(...names[id]))}</h2><p id="tdContext"></p></div><div class="td-status"><span id="detailStreamState"></span><time id="detailSampleTime"></time></div><div class="td-stats" id="tdStats"></div>${history}<div id="tdSpecifics"></div><details class="td-sources"><summary>${E(id==='disk'?L('Capacity details & calculation','용량 상세 · 계산 기준'):L('Measurement notes & sources','측정 기준 · 데이터 출처'))}</summary>${sources(id)}</details></div>`);
  const card=document.querySelector('.modal-card');card.classList.add('metric-detail-modal','telemetry-detail');
  document.querySelector('#modalKind').textContent=L('METRIC DETAILS','지표 상세');
  card.scrollTop=0;renderMetricDetailBody();animateDetailMotion(true);
 };
 // Surface disconnections promptly, without fetching or creating another timer.
 document.addEventListener('visibilitychange',()=>{if(!document.hidden)renderMetricDetailBody();});
})();
