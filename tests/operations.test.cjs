const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs');
const vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../web/operations.js'),'utf8');
const context=vm.createContext({tr:(en)=>en,serviceText:s=>s,serviceBusy:s=>['queued','running'].includes(s.operation?.status),Date});
vm.runInContext(source.slice(source.indexOf('function serviceSignal('),source.indexOf('function signalMarkup(')),context);
const signal=s=>context.serviceSignal(s);
test('queued retry is loading even while the old process state is failed',()=>{
 const v=signal({state:'failed',operation:{status:'queued',action:'start'}});
 assert.equal(v.tone,'loading');assert.equal(v.width,null);
});
test('unknown progress is never invented',()=>{
 const v=signal({state:'starting'});assert.equal(v.width,null);
});
test('weights 100% is still loading until readiness is observed',()=>{
 const v=signal({state:'running',startup:{total:48,current:48,ready:false}});
 assert.equal(v.width,100);assert.equal(v.tone,'loading');assert.match(v.label,/waiting/);
});
test('ready API and process-only state are distinct',()=>{
 assert.equal(signal({state:'running',readiness:'ready'}).tone,'ready');
 assert.equal(signal({state:'running',readiness:'unsupported'}).tone,'running');
});
test('failed operation remains actionable when the process may still be running',()=>{
 assert.equal(signal({state:'running',operation:{status:'failed'}}).tone,'failed');
});
