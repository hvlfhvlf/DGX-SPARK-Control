const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync('web/service-updates.js','utf8');
function context(){const c=vm.createContext({serviceUserErrors:{},document:{addEventListener(){}},tr:(a,b)=>a});vm.runInContext(source,c);return c;}
test('update button distinguishes not checked, latest and available',()=>{const c=context();assert.equal(vm.runInContext('updateActionLabel({})',c),'CHECK FOR UPDATES');assert.equal(vm.runInContext('updateActionLabel({checked_at:1})',c),'CHECK AGAIN');assert.equal(vm.runInContext('updateActionLabel({available:true})',c),'UPDATE');});
test('stopped warning and recovery messages make no availability promises',()=>{const c=context();assert.match(vm.runInContext("updateMessage('update_stop_required')",c),/Stop this service/);assert.match(vm.runInContext("updateMessage('update_recovery_needs_local_review')",c),/remain blocked/);assert.match(vm.runInContext("updateMessage('update_complete_stopped')",c),/basic checks/);});
test('boot setting labels distinguish on off and unknown without changing live state',()=>{const c=context();c.escapeHTML=s=>s;for(const [enabled,label] of [[true,'ON'],[false,'OFF'],[null,'UNAVAILABLE']]){c.panel={dataset:{autostartPanel:'test'}};c.info={enabled,editable:enabled!==null,boot_ready:true};vm.runInContext('renderServiceAutostart(panel,info)',c);assert.match(c.panel.innerHTML,new RegExp('title="Start when Spark boots · '+label+'"'));if(enabled!==null)assert.match(c.panel.innerHTML,new RegExp('aria-checked="'+enabled+'"'));else assert.doesNotMatch(c.panel.innerHTML,/role="switch"/);assert.match(c.panel.innerHTML,/Does not start or stop it now/);if(enabled===null)assert.match(c.panel.innerHTML,/disabled/);}});

test('closed details and background tabs do not poll update state',async()=>{
 const c=context(),panel={isConnected:true,dataset:{updatePanel:'test'}},modal={hidden:true};let calls=0,timers=0;
 c.document.getElementById=()=>modal;c.document.querySelector=()=>panel;c.clearTimeout=()=>{};c.setTimeout=()=>++timers;c.api=async()=>{calls++;return {job:{status:'install'}};};c.renderServiceUpdate=()=>{};
 await c.loadServiceUpdate('test');assert.equal(calls,0);
 modal.hidden=false;c.document.hidden=true;await c.loadServiceUpdate('test');assert.equal(calls,0);
 c.document.hidden=false;await c.loadServiceUpdate('test');assert.equal(calls,1);assert.equal(timers,1);
});

test('a response arriving after details close does not render or reschedule',async()=>{
 const c=context(),panel={isConnected:true,dataset:{updatePanel:'test'}},modal={hidden:false};let finish,renders=0,timers=0;
 c.document.getElementById=()=>modal;c.document.querySelector=()=>panel;c.clearTimeout=()=>{};c.setTimeout=()=>++timers;c.renderServiceUpdate=()=>renders++;c.api=()=>new Promise(resolve=>finish=resolve);
 const pending=c.loadServiceUpdate('test');modal.hidden=true;finish({job:{status:'install'}});await pending;
 assert.equal(renders,0);assert.equal(timers,0);
});

test('late update-check failure cannot reopen a closed dialog',async()=>{
 const handlers=[],c=vm.createContext({serviceUserErrors:{},document:{addEventListener(name,fn){if(name==='click')handlers.push(fn);}},tr:a=>a});vm.runInContext(source,c);
 const modal={hidden:false},panel={_updateInfo:{available:false}},button={isConnected:true,dataset:{updateAction:'test'},closest:()=>panel};let reject,shown=0;
 c.document.getElementById=()=>modal;c.serviceRows=()=>[{id:'test'}];c.api=()=>new Promise((resolve,no)=>reject=no);c.showModal=()=>shown++;
 const pending=handlers[0]({target:{closest:()=>button},preventDefault(){},stopImmediatePropagation(){}});modal.hidden=true;reject(Error('update_check_failed'));await pending;assert.equal(shown,0);
});
