const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
const source=fs.readFileSync(path.join(__dirname,'../web/runtime.js'),'utf8');
const apiSource=source.slice(source.indexOf('async function api('),source.indexOf('function graph('));
function harness(fetch,extra={}){
 const removed=[];let timeoutActive=false;
 const c=vm.createContext({fetch,AbortController,liveNode:{token:'old-session'},tr:en=>en,
  setTimeout(){timeoutActive=true;return 1;},clearTimeout(){timeoutActive=false;},
  localStorage:{removeItem:k=>removed.push(k)},sessionStorage:{removeItem:k=>removed.push(k)},...extra});
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

test('a browser has at most three active API requests',async()=>{
 let active=0,peak=0;const finish=[];
 const h=harness(()=>{active++;peak=Math.max(peak,active);return new Promise(resolve=>finish.push(()=>{active--;resolve({status:200,ok:true,json:async()=>({})});}));});
 const pending=Array.from({length:9},()=>h.c.api('metrics'));
 while(finish.length){finish.shift()();await new Promise(resolve=>setImmediate(resolve));}
 await Promise.all(pending);assert.equal(peak,3);assert.equal(h.c.api.active,0);
});
test('GET busy responses retry once; mutations are never replayed',async()=>{
 for(const body of [undefined,{action:'stop'}]){let calls=0;
  const h=harness(async()=>{calls++;return {status:503,ok:false,json:async()=>({error:'busy'})};},
   {setTimeout(fn,ms){if(ms<2000)queueMicrotask(fn);return 1;},clearTimeout(){}});
  await assert.rejects(h.c.api('services/action',body),/busy/);assert.equal(calls,body?1:2);assert.equal(h.c.api.active,0);
 }
});
test('queued private requests cannot run after logout',async()=>{
 const finish=[];let calls=0;const h=harness(()=>{calls++;return new Promise(resolve=>finish.push(resolve));});
 const pending=Array.from({length:4},()=>h.c.api('metrics'));const results=Promise.allSettled(pending);
 h.c.liveNode.token='';finish.forEach(resolve=>resolve({status:200,ok:true,json:async()=>({})}));
 assert.ok((await results).every(x=>x.status==='rejected'));assert.equal(calls,3);assert.equal(h.c.api.active,0);
});
