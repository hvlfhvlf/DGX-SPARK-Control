const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
test('first load is not an inference connection failure or missing-service claim',()=>{
 const src=fs.readFileSync(path.join(__dirname,'../web/inference.js'),'utf8');let html='';
 const c=vm.createContext({liveNode:{connected:false,statusChecked:false,sample:null},document:{activeElement:null},
  $:()=>({contains:()=>false}),tr:en=>en,escapeHTML:s=>s,fmt:()=> '—',arrowIcon:()=>'',patchRetainingInteraction:(el,s)=>html=s});
 vm.runInContext(src.slice(0,src.indexOf('async function refreshInference(')),c);c.drawInference();
 assert.match(html,/Connecting/);assert.doesNotMatch(html,/Connection unavailable|Connect an LLM service/);
 c.liveNode.statusChecked=true;c.drawInference();assert.match(html,/Connection unavailable/);
 c.liveNode.connectionDelayed=true;c.drawInference();assert.match(html,/Update delayed/);
});
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
