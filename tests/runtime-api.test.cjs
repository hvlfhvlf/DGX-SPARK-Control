const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../web/runtime.js'),'utf8');
const apiSource=source.slice(source.indexOf('async function api('),source.indexOf('function graph('));
function harness(fetch){
 const removed=[];let timeoutActive=false;
 const c=vm.createContext({fetch,AbortController,liveNode:{token:'old-session'},tr:en=>en,
  setTimeout(){timeoutActive=true;return 1;},clearTimeout(){timeoutActive=false;},
  localStorage:{removeItem:k=>removed.push(k)},sessionStorage:{removeItem:k=>removed.push(k)}});
 vm.runInContext(apiSource,c);return {c,removed,timeoutActive:()=>timeoutActive};
}
test('API deadline remains active until response body is consumed',async()=>{
 let h;h=harness(async()=>({status:200,ok:true,json:async()=>{assert.equal(h.timeoutActive(),true);return {ok:true};}}));
 await h.c.api('health');assert.equal(h.timeoutActive(),false);
});
test('late unauthorized response from an old session cannot clear a newer login',async()=>{
 let finish;const h=harness(()=>new Promise(resolve=>finish=resolve));
 const pending=h.c.api('metrics');h.c.liveNode.token='new-session';
 finish({status:401,ok:false});await assert.rejects(pending);
 assert.equal(h.c.liveNode.token,'new-session');assert.deepEqual(h.removed,[]);
});
test('unauthorized current session is still revoked locally',async()=>{
 const h=harness(async()=>({status:401,ok:false}));await assert.rejects(h.c.api('metrics'));
 assert.equal(h.c.liveNode.token,'');assert.equal(h.removed.length,2);assert.equal(h.timeoutActive(),false);
});

test('late successful private response cannot repopulate a logged-out session',async()=>{
 let finish;const h=harness(()=>new Promise(resolve=>finish=resolve));
 const pending=h.c.api('services');h.c.liveNode.token='';
 finish({status:200,ok:true,json:async()=>({services:[{id:'private-service'}]})});
 await assert.rejects(pending,/Session changed/);
 assert.equal(h.c.liveNode.token,'');assert.equal(h.timeoutActive(),false);
});
