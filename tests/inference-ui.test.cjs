const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
test('switching LLM while request is pending discards old response and fetches new choice',async()=>{
 const src=fs.readFileSync(path.join(__dirname,'../web/inference.js'),'utf8');
 const pending=[],paint=[];
 const c=vm.createContext({state:{view:'overview'},liveNode:{token:'session'},document:{hidden:false},encodeURIComponent,
  api:p=>new Promise(resolve=>pending.push({p,resolve})),drawInference:()=>paint.push(vm.runInContext('inferenceData?.selected',c))});
 vm.runInContext("let inferenceData=null,inferenceChoice='a',inferenceBusy=false,inferenceError=false;"+src.slice(src.indexOf('async function refreshInference('),src.indexOf('const overviewWithoutInference')),c);
 const first=c.refreshInference();vm.runInContext("inferenceChoice='b'",c);await c.refreshInference();
 pending[0].resolve({selected:'a'});await first;
 assert.equal(paint.includes('a'),false);assert.equal(pending.length,2);assert.equal(pending[1].p,'inference?id=b');
 pending[1].resolve({selected:'b'});await new Promise(resolve=>setImmediate(resolve));
 assert.equal(vm.runInContext('inferenceData.selected',c),'b');
});
