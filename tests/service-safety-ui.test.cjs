const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const read=name=>fs.readFileSync(path.join(__dirname,'../web',name),'utf8');
function harness(){
 const c=vm.createContext({tr:en=>en,Date,liveNode:{connected:true,servicesConnected:true,services:{revision:2,services:[]}},document:{addEventListener(){},getElementById(){return null;}},window:{addEventListener(){}}});
 vm.runInContext(read('usability.js'),c);
 const controls=read('service-controls.js');vm.runInContext(controls.slice(0,controls.indexOf('function serviceEditIcon')),c);
 const ops=read('operations.js');vm.runInContext(ops.slice(ops.indexOf('function serviceSignal('),ops.indexOf('function signalMarkup(')),c);
 return c;
}
test('unknown readiness and failed connection are not ready-to-open states',()=>{
 const c=harness(),s={state:'running',open_url:'http://example.test',readiness:'unknown'};
 assert.equal(c.appAccess(s).enabled,false);
 assert.notEqual(c.appAccess({...s,readiness:'unreachable'}).label,c.appAccess({...s,readiness:'loading'}).label);
 c.liveNode.servicesConnected=false;
 assert.equal(c.appAccess({...s,readiness:'ready'}).enabled,false);
});
test('recovered API is shown as current health, not permanent historic failure',()=>{
 const c=harness();assert.equal(c.serviceSignal({state:'running',readiness:'ready',operation:{status:'failed',action:'start'}}).tone,'ready');
 assert.equal(c.serviceSignal({state:'running',readiness:'unreachable'}).tone,'failed');
});
test('readiness cannot make an unknown or stopped process healthy',()=>{
 const c=harness();assert.notEqual(c.serviceSignal({state:'unknown',readiness:'ready'}).tone,'ready');
 assert.equal(c.serviceSignal({state:'stopped',readiness:'ready'}).tone,'off');
});
test('failed stop keeps stop available rather than retrying a start',()=>{
 const c=harness();assert.equal(c.serviceRetryAction({state:'running',operation:{action:'stop',status:'failed'}}),'stop');
 assert.equal(c.serviceRetryAction({state:'failed',operation:{action:'start',status:'failed'}}),'start');
 assert.equal(c.serviceRetryAction({state:'running',readiness:'unreachable',operation:{action:'stop',status:'completed'}}),'restart');
});
test('control availability rejects offline, unknown and transitioning services',()=>{
 const c=harness(),s={state:'running',controllable:true};
 assert.equal(c.serviceCanControl(s),true);
 for(const state of ['starting','stopping','unknown'])assert.equal(c.serviceCanControl({...s,state}),false);
 assert.equal(c.serviceCanControl({...s,operation:{status:'queued'}}),false);
 c.liveNode.connected=false;assert.equal(c.serviceCanControl(s),false);
});
test('confirmation binds reviewed revision and profile, not latest background snapshot',()=>{
 const c=harness(),s={id:'test',profile_id:'one',state:'running',controllable:true};c.liveNode.services.services=[s];
 assert.equal(c.serviceConfirmationValid({id:'test',profile:'one',revision:2,action:'stop'}),true);
 c.liveNode.services.revision=3;
 assert.equal(c.serviceConfirmationValid({id:'test',profile:'one',revision:2,action:'stop'}),false);
 c.liveNode.services.revision=2;s.profile_id='two';
 assert.equal(c.serviceConfirmationValid({id:'test',profile:'one',revision:2,action:'stop'}),false);
});

test('service details and confirmation continue polling from Activity or Settings',()=>{
 const c=harness();c.state={view:'logs'};const modal={hidden:false,querySelector:()=>null};c.document.getElementById=()=>modal;
 assert.equal(c.serviceNeedsPolling(),false);
 modal.querySelector=()=>({});assert.equal(c.serviceNeedsPolling(),true);
 c.state.view='settings';assert.equal(c.serviceNeedsPolling(),true);
 modal.hidden=true;assert.equal(c.serviceNeedsPolling(),false);
 c.state.view='models';assert.equal(c.serviceNeedsPolling(),true);
 c.state.view='settings';c.watchedOperations=new Set(['pending']);assert.equal(c.serviceNeedsPolling(),true);
});

test('initial connection and signed-out states are not reported as connection failures',()=>{
 const c=harness(),label={},notice={};c.document.getElementById=id=>id==='connectionLabel'?label:id==='connectionNotice'?notice:null;
 Object.assign(c.liveNode,{connected:false,token:'session',statusChecked:false});
 c.syncConnectionStatus();assert.equal(label.textContent,'CONNECTING');assert.equal(notice.hidden,true);
 c.liveNode.statusChecked=true;c.syncConnectionStatus();assert.equal(label.textContent,'CONNECTION LOST');assert.equal(notice.hidden,false);
 c.liveNode.token='';c.syncConnectionStatus();assert.equal(label.textContent,'SIGN IN REQUIRED');assert.equal(notice.hidden,true);
});
