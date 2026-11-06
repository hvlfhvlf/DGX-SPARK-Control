const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm'),path=require('node:path');
function fixture(){
 const handlers=[];let navigated='',closed=false,calls=0,intercepted=false;
 const row={id:'harness',open_url:'https://example.test:9443/',state:'running',readiness:'unsupported',authenticated_launch:true};
 const button={id:'',disabled:false,isConnected:true,dataset:{authApp:'harness',serviceOpen:''},hasAttribute:k=>k==='data-auth-app'};
 const tab={opener:{},closed:false,location:{replace:u=>{navigated=u;}},close:()=>{closed=true;}};
 const context=vm.createContext({Map,URL,document:{addEventListener:(type,fn)=>{if(type==='click')handlers.push(fn);}},window:{addEventListener(){},open:()=>tab},tr:e=>e,serviceBusy:()=>false,serviceRows:()=>[row],liveNode:{connected:true,servicesConnected:true,services:{revision:8}},toast(){},escapeHTML:s=>s,arrowIcon:()=>'',api:async(p,d)=>{calls++;assert.equal(p,'services/open');assert.equal(d.revision,8);return {url:'https://example.test:9443/?token=fixture'};}});
 // Actual script registration order includes the service button capture handler.
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../web/service-controls.js'),'utf8'),context);
 vm.runInContext(fs.readFileSync(path.join(__dirname,'../web/usability.js'),'utf8'),context);
 context.liveNode.services.services=[row];
 return {context,row,button,tab,async click(){for(const fn of handlers){await fn({target:{closest:()=>button},preventDefault(){},stopImmediatePropagation(){intercepted=true;}});if(intercepted)break;}},result:()=>({navigated,closed,calls,intercepted})};
}
test('registered app button reaches authenticated handoff through other service handlers',async()=>{
 const f=fixture();await f.click();assert.equal(f.result().calls,1);assert.equal(f.result().navigated,'https://example.test:9443/?token=fixture');assert.equal(f.tab.opener,null);assert.equal(f.button.disabled,false);
});
test('different destination closes blank tab without navigation',async()=>{
 const f=fixture();f.context.api=async()=>({url:'https://other.test/?token=fixture'});await f.click();assert.equal(f.result().navigated,'');assert.equal(f.result().closed,true);
});
test('offline service does not request launch token',async()=>{
 const f=fixture();f.context.liveNode.connected=false;await f.click();assert.equal(f.result().calls,0);assert.equal(f.result().closed,true);
});
