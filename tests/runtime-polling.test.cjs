const {test}=require('node:test'),assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const SparkPolling=require('../web/polling-state.js');
const source=fs.readFileSync(path.join(__dirname,'../web/runtime.js'),'utf8');
test('telemetry distinguishes first load, delay and confirmed disconnection',()=>{
 const c=vm.createContext({liveNode:{statusChecked:false,sample:null,connected:false},tr:en=>en});
 vm.runInContext(source.slice(source.indexOf('function telemetryConnectionLabel('),source.indexOf('function installedOverview(')),c);
 assert.equal(c.telemetryConnectionLabel(),'CONNECTING');c.liveNode.statusChecked=true;
 assert.equal(c.telemetryConnectionLabel(),'DISCONNECTED');c.liveNode.connectionDelayed=true;
 assert.equal(c.telemetryConnectionLabel(),'UPDATE DELAYED');c.liveNode.connectionDelayed=false;c.liveNode.connected=true;
 assert.equal(c.telemetryConnectionLabel(),'LIVE / 5 SEC');
});
function harness(view='overview',fail=[]){
 const calls=[],now=Date.now()/1000;
 const c=vm.createContext({SparkPolling,Date,Promise,console,encodeURIComponent,setTimeout,clearTimeout,
  liveNode:{token:'test',busy:false,connected:true,hardware:{},history:[],services:{services:[]}},
  state:{view},document:{hidden:false},metricExplorer:null,preferences:{},lastSuccessfulRefresh:0,
  nameDraftDirty:false,tr:en=>en,$:()=>({textContent:''}),render(){},syncConnectionStatus(){},
  serviceNeedsPolling:()=>true,
  api:async p=>{calls.push(p);if(fail.includes(p.split('?')[0]))throw Error('fixture failure');
   if(p==='metrics')return {timestamp:now,cpu:3};if(p==='services')return {services:[]};
   if(p.startsWith('history'))return {epoch:'epoch-a',reset:true,samples:[{timestamp:now,cpu:3}]};
   if(p==='events')return [];return {version:'test',spark_name:'test'};}
 });
 vm.runInContext(source.slice(source.indexOf('const connectionState='),source.indexOf("document.addEventListener('submit'")),c);
 c.paintLive=()=>{};return {c,calls,fail};
}
test('optional history, events and settings failures never mark node offline',async()=>{
 for(const endpoint of ['history','events','settings']){const {c}=harness(endpoint==='events'?'logs':'overview',[endpoint]);await c.refreshLive();assert.equal(c.liveNode.connected,true);assert.equal(c.liveNode[endpoint+'Error'],true);}
});
test('service failure disables controls but leaves telemetry connection online',async()=>{
 const {c}=harness('models',['services']);await c.refreshLive();assert.equal(c.liveNode.connected,true);assert.equal(c.liveNode.servicesConnected,false);
});
test('core failure delays once, then disconnects, then recovers',async()=>{
 const {c,fail}=harness();await c.refreshLive();fail.push('metrics');await c.refreshLive();assert.equal(c.liveNode.connected,true);assert.equal(c.liveNode.connectionDelayed,true);assert.equal(c.liveNode.servicesConnected,false);
 await c.refreshLive();assert.equal(c.liveNode.connected,false);fail.length=0;await c.refreshLive();assert.equal(c.liveNode.connected,true);assert.equal(c.liveNode.connectionDelayed,false);
});
test('no history on models/settings/logs; settings cached; events only on activity',async()=>{
 for(const view of ['models','settings','logs']){const {c,calls}=harness(view);await c.refreshLive();await c.refreshLive();assert.equal(calls.filter(p=>p.startsWith('history')).length,0);assert.equal(calls.filter(p=>p==='settings').length,1);assert.equal(calls.filter(p=>p==='events').length,view==='logs'?1:0);}
});
test('rendering exceptions do not become network failures',async()=>{
 const {c}=harness();c.console={warn(){}};c.paintLive=()=>{throw Error('fixture render failure');};await c.refreshLive();assert.equal(c.liveNode.connected,true);assert.equal(c.liveNode.displayError,true);assert.equal(c.liveNode.busy,false);
});
test('history merges/deduplicates/bounds data and resets on server epoch change',()=>{
 const rows=Array.from({length:730},(_,i)=>({timestamp:1000+i,cpu:i}));
 const merged=SparkPolling.mergeHistory(rows,{epoch:'a',reset:false,samples:[{timestamp:1729,cpu:99}]},1800);
 assert.equal(merged.length,720);assert.equal(merged.at(-1).cpu,99);
 assert.deepEqual(SparkPolling.mergeHistory(rows,{epoch:'b',reset:true,samples:[{timestamp:1800,cpu:0}]},1800),[{timestamp:1800,cpu:0}]);
 assert.equal(SparkPolling.mergeHistory(rows,{epoch:'a',reset:false,samples:[]},6000).length,0);
});
test('first failed connection is delayed and elapsed failure becomes offline',()=>{
 const s=new SparkPolling.ConnectionState();assert.equal(s.failure(1000),'delayed');s.success(2000);assert.equal(s.failure(23000),'offline');
});
test('detail rendering failure releases busy and scheduler survives unexpected failure',async()=>{
 const {c}=harness();c.console={warn(){}};c.refreshServiceDetail=()=>{throw Error('fixture');};
 await c.refreshLive();assert.equal(c.liveNode.busy,false);assert.equal(c.liveNode.connected,true);
 let scheduled=0;c.setTimeout=()=>{scheduled++;return 1;};c.refreshLive=async()=>{throw Error('fixture');};
 await c.pollLive();assert.equal(scheduled,1);
});
