'use strict';
// Central UI catalog. Model IDs, engine names, paths and API values stay unchanged.
const koCatalog = {
 'Spark name':'Spark 이름','My Spark':'나의 Spark','SAVE NAME':'이름 저장','Spark name applied.':'Spark 이름을 적용했습니다.',
 'A display name for this Spark. Saved in this browser; the system hostname stays unchanged.':'이 Spark의 표시 이름입니다. 현재 브라우저에 저장되며 시스템 호스트명은 변경하지 않습니다.',
 'Collapse overview artwork':'소개 영역 접기','Expand overview artwork':'소개 영역 펼치기',
 'AUTO SCALE':'자동 눈금','Simulated transfer rate history':'모의 전송 속도 추이',
 'Memory clock unavailable':'메모리 클럭 미지원','CPU core clock range':'CPU 코어 클럭 범위','GPU SM clock':'GPU SM 클럭',
 'GPU ONLY':'GPU 기준','AVERAGE DRAW':'평균 소비전력','GPU power':'GPU 전력','NVIDIA GPU average power':'NVIDIA GPU 평균 전력','Simulated GPU average power draw. This excludes whole-system power and adapter losses.':'모의 GPU 평균 소비전력입니다. 전체 시스템 전력이나 어댑터 손실을 포함하지 않습니다.',
 'SSD USAGE':'SSD 사용량','SYSTEM POWER':'전체 전력','NETWORK TRAFFIC':'네트워크 사용량','DISK I/O':'디스크 I/O',
 'SPACE USED':'사용 공간','3.6 TiB TOTAL':'전체 3.6 TiB','NO SENSOR':'센서 미연결','NOT CONNECTED':'미연결','SYSTEM SENSOR REQUIRED':'전체 전력 센서 필요',
 'SM CLOCK · 2.19 GHz':'SM 클럭 · 2.19 GHz','SM CLOCK · —':'SM 클럭 · —','CORE CLOCK · 2.81–3.90 GHz':'코어 클럭 · 2.81–3.90 GHz','CORE CLOCK · —':'코어 클럭 · —','MEMORY CLOCK · UNAVAILABLE':'메모리 클럭 · 미지원',
 'RECEIVE':'수신','SEND':'송신','READ':'읽기','WRITE':'쓰기','INTERFACE TOTAL':'인터페이스 트래픽','LAN + INTERNET':'LAN + 인터넷','READ / WRITE':'읽기 / 쓰기',
 'SSD usage':'SSD 사용량','System power':'전체 전력','Network traffic':'네트워크 사용량','Disk I/O':'디스크 I/O','Filesystem capacity':'파일시스템 용량','Not connected':'미연결','Network byte counters':'네트워크 전송량 카운터','Disk byte counters':'디스크 전송량 카운터',
 'Simulated filesystem space used. Disk I/O is displayed separately.':'모의 파일시스템 사용 공간입니다. 디스크 I/O는 별도로 표시합니다.',
 'No verified whole-system power source is connected. GPU power is not total system power. A validated system sensor or an external power meter is required.':'검증된 전체 전력 센서가 연결되지 않았습니다. GPU 전력과 전체 전력은 다릅니다. 검증된 시스템 센서나 외부 전력계가 필요합니다.',
 'Simulated receive and send rates for one selected physical network interface. Includes LAN and internet traffic; do not add Tailscale virtual traffic again.':'선택한 물리 네트워크 인터페이스의 모의 수신·송신 속도입니다. LAN과 인터넷 트래픽을 포함하며 Tailscale 가상 트래픽을 중복 합산하지 않습니다.',
 'Simulated NVMe read and write rates. Measures throughput, not storage capacity.':'모의 NVMe 읽기·쓰기 속도입니다. 저장 용량이 아닌 전송 속도를 표시합니다.',
 'Skip to content':'본문으로 이동','Choose language':'언어 선택','Language':'언어','LANGUAGE':'언어',
 'PERSONAL COMPUTE SYSTEM':'개인용 컴퓨팅 시스템','DESIGN PROTOTYPE':'디자인 시제품','Open settings':'설정 열기',
 'Pause interface animation':'애니메이션 정지','Resume interface animation':'애니메이션 재개',
 'OVERVIEW':'개요','MODELS':'모델','JOBS':'작업','ACTIVITY':'기록','SETTINGS':'설정','UNIFIED':'통합 메모리',
 'DEMO NODE ONLINE':'데모 노드 연결됨','DEMO NODE OFFLINE':'데모 노드 연결 끊김','SIMULATED DATA':'모의 데이터',
 'SYSTEM OVERVIEW':'시스템 개요','YOUR COMPUTE. UNDER CONTROL.':'내 컴퓨팅 환경을 한눈에.',
 'NVIDIA DGX':'NVIDIA DGX','/ PERSONAL AI SUPERCOMPUTER':'/ 개인용 AI 슈퍼컴퓨터',
 'One node. Every possibility.':'하나의 노드, 무한한 가능성.','ARCH':'아키텍처','MEMORY':'메모리',
 'NODE TELEMETRY':'시스템 상태','AUTO REFRESH / 5 SEC':'5초마다 갱신','SIMULATION PAUSED':'모의 갱신 일시 정지',
 'GPU UTILIZATION':'GPU 사용률','UNIFIED MEMORY':'통합 메모리','GPU TEMPERATURE':'GPU 온도','CPU UTILIZATION':'CPU 사용률',
 'COMPUTE LOAD':'연산 부하','SYSTEM USED':'시스템 사용량','121.6 GiB TOTAL':'전체 121.6 GiB','THERMAL STATUS':'열 상태','GPU SENSOR':'GPU 센서','TOTAL CAPACITY':'전체 CPU 기준','20 CORES':'20코어',
 'INFERENCE THROUGHPUT':'추론 처리량','ACTIVE ENGINE':'실행 중인 엔진','CONTEXT LIMIT':'컨텍스트 한도','ACTIVE REQUESTS':'진행 중인 요청','GPU POWER':'GPU 전력',
 'OUTPUT':'출력','INPUT':'입력','NOW':'현재','MANAGE MODELS':'모델 관리','STOP':'정지','START':'시작',
 'READY':'준비됨','STANDBY':'대기','BUSY':'처리 중','TRANSITIONING':'전환 중','UNREACHABLE':'연결 불가',
 'WORKLOAD QUEUE':'작업 대기열','LATEST ACTIVITY':'최근 기록','VIEW ALL ↗':'모두 보기 ↗','OPEN LOG ↗':'기록 보기 ↗',
 'RUNNING':'진행 중','COMPLETED':'완료','CANCELLED':'취소됨','ARCHIVED':'보관됨',
 'Research assistant':'리서치 지원','Code review':'코드 검토','Document summary':'문서 요약','New demo request':'새 데모 요청','Image generation':'이미지 생성',
 'MODEL BAY':'모델 관리','SELECT. INITIALIZE. CREATE.':'선택하고, 실행하고, 만들어 보세요.',
 'CREATIVE':'이미지·영상','Search model or engine…':'모델 또는 엔진 검색…','Search models':'모델 검색',
 'ENGINE':'엔진','MEMORY ESTIMATE':'예상 메모리','TYPE':'유형','MODE':'모드','LOADED':'실행 중','LOAD ENGINE':'엔진 실행','STOP ENGINE':'엔진 정지','NEEDS SETUP':'설정 필요','SETUP REQUIRED':'설정 필요',
 'UNVERIFIED':'미확인','UNCONFIGURED':'미설정','ON DEMAND':'필요 시 사용','WORKFLOWS':'워크플로',
 'Fast reasoning. Long context. Ready for your next idea.':'빠른 추론과 긴 컨텍스트로 다음 아이디어를 준비합니다.',
 'A compact multimodal model for everyday intelligence.':'일상적인 작업을 위한 경량 멀티모달 모델입니다.',
 'Your workspace for image, video and generative workflows.':'이미지·영상 생성 워크플로를 위한 작업 환경입니다.',
 'Discovered demo file. Configure and verify an engine before use.':'검색된 데모 파일입니다. 사용 전 엔진 설정과 검증이 필요합니다.',
 'No matching models. Try another name or category.':'일치하는 모델이 없습니다. 다른 이름이나 분류를 선택하세요.',
 'SIMULATION / Loading another engine replaces the active engine in this demo.':'모의 동작 / 다른 엔진을 실행하면 현재 엔진이 교체됩니다.',
 'All controls use mock data. No model is started, stopped or downloaded on your DGX.':'모든 제어는 목업입니다. 실제 DGX의 모델을 실행·정지·다운로드하지 않습니다.',
 'WORKLOADS':'작업 관리','EVERY REQUEST. IN VIEW.':'모든 요청의 진행 상황을 한눈에.',
 'SIMULATE REQUEST +':'데모 요청 추가 +','WORKLOAD / ID':'작업 / ID','STATUS':'상태','PROGRESS':'진행률','ACTION':'동작','CANCEL':'취소',
 'DEMO JOB HISTORY / Request progress and results are illustrative.':'데모 작업 기록 / 진행률과 결과는 예시입니다.',
 'ACTIVITY LOG':'활동 기록','A TRACE OF EVERY OPERATION.':'모든 동작의 기록을 확인하세요.',
 'EXPORT DEMO LOG ↓':'데모 기록 내보내기 ↓','Local prototype events only. No server logs or prompt contents are collected.':'로컬 시제품의 이벤트만 표시합니다. 서버 로그나 프롬프트 내용은 수집하지 않습니다.',
 'SYSTEM SETTINGS':'시스템 설정','MAKE THIS SPACE YOURS.':'내게 맞는 작업 환경.',
 'PERSONALIZATION':'개인화','THIS BROWSER':'현재 브라우저','Accent color':'강조색',
 'Choose the interface highlight. Hardware artwork keeps its original colors.':'화면의 강조색을 선택합니다. 하드웨어 그래픽은 원래 색상을 유지합니다.',
 'Acid lime':'라임','Lavender':'라벤더','Ice blue':'아이스 블루','Layout density':'화면 밀도',
 'Adjust panel spacing without shrinking the text.':'글자 크기를 유지하면서 패널 여백을 조절합니다.',
 'Comfortable':'여유롭게','Compact':'촘촘하게','Start page':'시작 화면',
 'Used when opening the dashboard without a page link.':'특정 페이지 링크 없이 대시보드를 열 때 표시할 화면입니다.',
 'Overview':'개요','Models':'모델','Jobs':'작업','Settings':'설정','Overview artwork':'개요 그래픽',
 'Hide the large hero to put telemetry first.':'상단 그래픽을 숨겨 시스템 상태를 먼저 표시합니다.',
 'Reset preferences':'개인화 초기화','Appearance is saved on this browser, separately from the demo session.':'화면 설정은 데모 세션과 별도로 현재 브라우저에 저장됩니다.','RESTORE':'초기화',
 'MODEL DISCOVERY':'모델 자동 검색','PREVIEW':'미리보기',
 'Find model files, review changes, then register them. Finding weights does not mean an engine is ready to run.':'모델 파일을 찾아 변경 내용을 검토한 뒤 등록합니다. 파일을 발견해도 바로 실행할 수 있는 것은 아닙니다.',
 'MODEL FOLDERS':'모델 폴더','HF CACHE':'HF 캐시','ENGINE CATALOGS':'엔진 목록',
 'Illustrative sources only. No directories or services are accessed.':'검색 대상의 예시입니다. 실제 폴더나 서비스에는 접근하지 않습니다.',
 'RESCAN DEMO':'데모 다시 검색','SCAN DEMO MODELS':'데모 모델 검색',
 'Matched to existing registry entry':'기존 등록 정보와 일치','REGISTERED':'등록됨',
 'Registered draft · engine setup required':'초안 등록됨 · 엔진 설정 필요','New file · engine and compatibility unverified':'새 파일 · 엔진과 호환성 미확인',
 'ADDED':'추가됨','REVIEW':'검토','MISSING':'파일 없음','Retired model · example':'이전 모델 · 예시',
 'Missing file example. Retain metadata until reviewed.':'파일 누락 예시입니다. 검토 전까지 등록 정보를 유지합니다.',
 'Run the demo scan to preview registered, new and missing model states.':'데모 검색으로 등록됨·신규·파일 없음 상태를 확인하세요.',
 'LLM MAINTENANCE HANDOFF':'LLM 유지보수 가이드','INSTALL / REPLACE / REMOVE':'설치 / 교체 / 제거',
 'Update the registry. Keep the dashboard.':'등록 정보는 바꾸고, 대시보드는 그대로.',
 'Give your coding LLM the maintenance guide. It should update model metadata and engine adapters, verify readiness and report the result. A new model should not require rewriting the interface.':'코딩 LLM에 가이드를 전달하세요. 모델 등록 정보와 엔진 연결 모듈을 갱신하고, 실행 준비 상태를 검증하도록 구성합니다. 모델이 바뀌어도 화면을 다시 만들 필요가 없습니다.',
 'DOWNLOAD GUIDE ↓':'가이드 다운로드 ↓','Inspect paths & services':'경로·서비스 확인','Review registry changes':'등록 정보 변경 검토','Validate & smoke-test':'검증·실행 테스트','Rescan & confirm status':'재검색·상태 확인',
 'PROTOTYPE CONTROLS':'데모 환경','LOCAL ONLY':'로컬 전용','Demo scenario':'데모 시나리오',
 'Explore a running workload, an idle node or a lost connection.':'추론 중·대기·연결 끊김 상태를 확인합니다.',
 'Inference':'추론 중','Idle':'대기','Offline':'연결 끊김','Live simulation':'실시간 모의 갱신','Update mock telemetry every five seconds.':'목업 상태를 5초마다 갱신합니다.',
 'Interface motion':'인터페이스 애니메이션','Short panel entrances and signal animation. System reduced-motion preferences take priority.':'패널 전환과 신호 애니메이션을 사용합니다. 운영체제의 모션 감소 설정이 우선합니다.',
 'Reset session':'데모 세션 초기화','Restore the initial model, jobs and demo telemetry.':'처음의 모델·작업·목업 상태로 되돌립니다.','RESET ↺':'초기화 ↺',
 'VISUAL SYSTEM':'디자인 시스템','EDITION 01':'버전 01','DISPLAY / RAJDHANI BOLD':'영문 제목 / RAJDHANI BOLD','INTERFACE / CHAKRA PETCH':'영문 UI / CHAKRA PETCH',
 'BUILT FOR':'다음 가능성을','WHAT\'S NEXT.':'위한 설계.',
 'Self-hosted SIL Open Font License typefaces.':'로컬 제공 SIL OFL 영문 폰트.',
 "Original interface inspired by Marathon's visual language.":'Marathon의 시각 표현을 참고한 오리지널 UI.',
 'LOCAL DESIGN BUILD':'로컬 시제품','NO LIVE CONNECTION':'실제 서버 미연결',
 'CONTROL TRANSACTION':'제어 확인','Close dialog':'대화상자 닫기','CLOSE':'닫기',
 'STOP ENGINE?':'엔진을 정지할까요?','SWITCH ENGINE?':'엔진을 교체할까요?','INITIALIZE ENGINE?':'엔진을 실행할까요?',
 'TARGET ENGINE':'대상 엔진','MODEL':'모델','EXECUTION':'실행 방식','SIMULATION ONLY':'모의 동작 전용','CONFIRM STOP':'정지 확인','CONFIRM LOAD':'실행 확인',
 'RUNNER':'실행 엔진','CONTEXT / MODE':'컨텍스트 / 모드','ESTIMATED MEMORY':'예상 메모리','DATA SOURCE':'데이터 출처','MOCK REGISTRY':'목업 등록 정보',
 'Registry-driven model card. Actual limits, readiness and resource requirements will be verified when a live adapter is connected.':'등록 정보로 구성된 모델 카드입니다. 실제 한도·준비 상태·리소스 요구량은 엔진 연동 시 검증합니다.',
 'REGISTER MODEL?':'모델을 등록할까요?',
 'This is a fictional GGUF discovery result. Add its metadata to the session model bay as an unverified draft. It cannot be launched until an engine adapter is configured.':'가상의 GGUF 검색 결과입니다. 현재 세션에 미검증 초안으로 등록하며, 엔진 연결 설정 전에는 실행할 수 없습니다.',
 'FORMAT':'형식','ENGINE / MEMORY':'엔진 / 메모리','METADATA ONLY':'등록 정보만 추가','ADD DRAFT':'초안 추가',
 'PLANNED SOURCE':'예정 수집원','UNIT':'단위','CURRENT DATA':'현재 데이터','SIMULATED':'모의 데이터',
 'Percentage of simulated GPU compute activity.':'모의 GPU 연산 사용률입니다.',
 'System used memory, calculated as total minus available. CPU and GPU share this pool; their capacities must not be added together.':'전체 메모리에서 사용 가능 메모리를 뺀 값입니다. CPU와 GPU가 공유하므로 두 용량을 더하지 않습니다.',
 'A simulated GPU sensor reading. CPU / SoC temperature needs a separately identified sensor.':'모의 GPU 센서 값입니다. CPU·SoC 온도는 별도 센서를 확인해야 합니다.',
 'Average utilization across all logical processors. This mock value represents the entire CPU capacity.':'전체 논리 프로세서의 평균 사용률입니다. CPU 전체 용량을 기준으로 표시합니다.',
 'Disconnected sensors will show unavailable, never a misleading zero.':'연결이 끊긴 센서는 0 대신 측정 불가로 표시합니다.',
 'NODE UNREACHABLE':'노드에 연결할 수 없음','Offline scenario. Telemetry is unavailable and model controls are disabled.':'연결 끊김 시나리오입니다. 상태 수집과 모델 제어를 사용할 수 없습니다.','RECONNECT ↗':'다시 연결 ↗',
 'TELEMETRY UNAVAILABLE':'상태 수집 불가','NO ACTIVE LANGUAGE ENGINE':'실행 중인 언어 모델 없음','Reconnect to resume the simulated stream.':'다시 연결하면 모의 상태 갱신을 재개합니다.','Load a language model to view inference telemetry.':'언어 모델을 실행하면 추론 지표를 표시합니다.',
 'Preference saved in this browser.':'현재 브라우저에 설정을 저장했습니다.','Personal preferences restored.':'개인화 설정을 초기화했습니다.',
 'Applied for this session. Browser storage is unavailable.':'현재 세션에 적용했습니다. 브라우저 저장 공간은 사용할 수 없습니다.',
 'Demo scan complete. No DGX connection.':'데모 검색 완료. 실제 DGX에는 연결하지 않았습니다.',
 'Draft added. View it in Models.':'초안을 추가했습니다. 모델 화면에서 확인하세요.',
 'Prototype session reset.':'데모 세션을 초기화했습니다.','A simulated workload has been added.':'데모 작업을 추가했습니다.',
 'Demo request cancelled.':'데모 요청을 취소했습니다.','Live simulation resumed.':'모의 갱신을 재개했습니다.','Mock telemetry paused.':'모의 갱신을 일시 정지했습니다.',
 'Demo activity log exported.':'데모 활동 기록을 내보냈습니다.','Stopping demo engine…':'데모 엔진 정지 중…','Switching demo engine…':'데모 엔진 교체 중…','Demo engine stopped.':'데모 엔진을 정지했습니다.',
 'Prototype reset. All telemetry is simulated.':'시제품 초기화. 모든 지표는 모의 데이터입니다.',
 'Demo node initialized. All telemetry is simulated.':'데모 노드 초기화. 모든 지표는 모의 데이터입니다.',
 'Qwen 3.8 is ready. Context window: 262,144 tokens.':'Qwen 3.8 준비 완료. 컨텍스트 한도: 262,144 토큰.',
 'TensorFold model weights loaded into unified memory.':'TensorFold 모델 가중치를 통합 메모리에 적재했습니다.',
 'Demo inventory scan: registered, new and missing fixtures. No filesystem accessed.':'데모 목록 검색: 등록·신규·누락 예시. 파일시스템 접근 없음.',
 'Demo model metadata registered as a draft. No files installed.':'데모 모델 정보를 초안으로 등록했습니다. 파일 설치 없음.',
 'Engine stopped. Demo node is in standby.':'엔진 정지. 데모 노드가 대기 중입니다.','Demo connection restored.':'데모 연결을 복구했습니다.',
 'Qwen 3.8 is ready':'Qwen 3.8 준비 완료','Prototype reset':'시제품 초기화','Demo node initialized':'데모 노드 초기화',
 'INFO':'정보','WARN':'주의',
 'Main navigation':'주 메뉴','Spark Control overview':'Spark Control 개요','Simulated node telemetry':'모의 시스템 상태','Chart time range':'차트 표시 기간','Filter models':'모델 분류','Simulated generation throughput history':'모의 생성 처리량 추이',
 'Black, off-white, lime, lavender, orange palette':'검정·오프화이트·라임·라벤더·주황 팔레트',
 'No engine loaded':'실행 중인 엔진 없음','SELECT A MODEL TO GET STARTED':'시작할 모델을 선택하세요',
 'NVIDIA utilization counter':'NVIDIA 사용률 지표','NVIDIA GPU temperature':'NVIDIA GPU 온도','OS CPU time counters':'운영체제 CPU 시간 지표',
 'Local LLM · example.gguf':'로컬 LLM · example.gguf','Local LLM example':'로컬 LLM 예시'
};
let uiLanguage='en';
try { const saved=localStorage.getItem('spark.language.v1'); if(saved==='ko'||saved==='en')uiLanguage=saved; } catch (_) {}
const sourceText=new WeakMap(), sourceAttrs=new WeakMap();
function translateText(text) {
  if(uiLanguage!=='ko')return text;
  const core=text.trim(); if(!core)return text;
  let translated=koCatalog[core];
  if(!translated) {
    const rules=[
      [/^(.*) details$/,(_,n)=>(koCatalog[n]||n)+' 상세'],
      [/^ALL \/ (\d+)$/,(_,n)=>'전체 / '+n],
      [/^(\d+) RUNNING \/ (\d+) TOTAL$/,(_,a,b)=>`진행 중 ${a} / 전체 ${b}`],
      [/^SESSION EVENTS \/ (\d+)$/,(_,n)=>'세션 이벤트 / '+n],
      [/^(REQ-\d+) \/ DEMO WORKLOAD$/,(_,n)=>n+' / 데모 작업'],
      [/^(REQ-\d+ \/ .+) \/ (CHAT COMPLETION|TOOL CALL|SIMULATION)$/,(_,prefix,type)=>prefix+' / '+({'CHAT COMPLETION':'대화 생성','TOOL CALL':'도구 호출','SIMULATION':'모의 동작'}[type])],
      [/^Stop the simulated (.+) engine and finish its demo workload\.$/,(_,m)=>`${m} 데모 엔진을 정지하고 데모 작업을 종료합니다.`],
      [/^(.+) will stop before (.+) loads\. The demo switches one engine at a time\.$/,(_,a,b)=>`${a} 정지 후 ${b}를 실행합니다. 데모에서는 한 번에 하나의 엔진을 사용합니다.`],
      [/^Load (.+) into the simulated compute node\.$/,(_,m)=>`${m}을 모의 노드에서 실행합니다.`],
      [/^(.+) is ready\. Simulated switch complete\.$/,(_,m)=>`${m} 준비 완료. 모의 전환을 마쳤습니다.`],
      [/^Demo scenario(?: changed to|:) (.+)\.$/,(_,s)=>'데모 시나리오: '+({inference:'추론 중',idle:'대기',offline:'연결 끊김'}[s]||s)],
      [/^(Loading|Stopping) (.+) \(simulation\)\.$/,(_,a,m)=>`${m} ${a==='Loading'?'실행':'정지'} 중 (모의 동작).`],
      [/^(.+) is ready \(simulation\)\.$/,(_,m)=>`${m} 준비 완료 (모의 동작).`],
      [/^Demo workload (.+) cancelled\.$/,(_,id)=>`데모 작업 ${id} 취소됨.`],
      [/^(.+) started on (.+) \(simulation\)\.$/,(_,id,m)=>`${m}에서 ${id} 시작 (모의 동작).`]
    ];
    for(const [pattern,fn] of rules)if(pattern.test(core)){translated=core.replace(pattern,fn);break;}
    if(!translated&&/[↗↓■+]$/.test(core)){const base=core.slice(0,-1).trim();if(koCatalog[base])translated=koCatalog[base]+' '+core.slice(-1);}
  }
  return translated?text.replace(core,translated):text;
}
function translateUI(){
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  let node;
  while((node=walker.nextNode())){
    if(node.parentElement?.closest('script,style,[translate="no"],.language-menu button,#languageCode'))continue;
    const cached=sourceText.get(node);
    const source=cached&&node.nodeValue===cached.output?cached.source:node.nodeValue;
    const output=translateText(source);
    sourceText.set(node,{source,output});if(output!==node.nodeValue)node.nodeValue=output;
  }
  document.querySelectorAll('[aria-label],[placeholder],[title]').forEach(el=>{
    if(el.closest('[translate="no"]'))return;
    const cached=sourceAttrs.get(el)||{};
    for(const attr of ['aria-label','placeholder','title'])if(el.hasAttribute(attr)){
      const current=el.getAttribute(attr), previous=cached[attr];
      const source=previous&&current===previous.output?previous.source:current;
      const output=translateText(source);cached[attr]={source,output};if(output!==current)el.setAttribute(attr,output);
    }
    sourceAttrs.set(el,cached);
  });
  const title=uiLanguage==='ko'?{overview:'개요',models:'모델',jobs:'작업',logs:'기록',settings:'설정'}[state.view]:navNames[state.view];
  document.title=`${title} / SPARK CONTROL`;
}
function closeLanguageMenu(){document.getElementById('languageMenu').hidden=true;document.getElementById('languageButton').setAttribute('aria-expanded','false');}
function setLanguage(language){
  uiLanguage=language;document.documentElement.lang=language;
  document.getElementById('languageCode').textContent=language.toUpperCase();
  document.querySelectorAll('[data-language]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.language===language)));
  translateUI();
}
document.getElementById('languageButton').addEventListener('click',()=>{
  const menu=document.getElementById('languageMenu');menu.hidden=!menu.hidden;
  document.getElementById('languageButton').setAttribute('aria-expanded',String(!menu.hidden));
  if(!menu.hidden)menu.querySelector('[data-language="'+uiLanguage+'"]').focus();
});
document.addEventListener('click',event=>{
  const choice=event.target.closest('[data-language]');
  if(choice){setLanguage(choice.dataset.language);try{localStorage.setItem('spark.language.v1',uiLanguage);}catch(_){}closeLanguageMenu();document.getElementById('languageButton').focus();}
  else if(!event.target.closest('.language-control'))closeLanguageMenu();
});
document.addEventListener('keydown',event=>{if(event.key==='Escape'&&!document.getElementById('languageMenu').hidden){closeLanguageMenu();document.getElementById('languageButton').focus();}});
const languageObserver=new MutationObserver(()=>{languageObserver.disconnect();translateUI();observeLanguage();});
function observeLanguage(){languageObserver.observe(document.body,{childList:true,subtree:true,characterData:true,attributes:true,attributeFilter:['aria-label','placeholder','title']});}
setLanguage(uiLanguage);observeLanguage();
