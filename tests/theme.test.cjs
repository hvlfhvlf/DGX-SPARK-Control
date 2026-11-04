const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),path=require('node:path'),vm=require('node:vm');
const web=path.join(__dirname,'../web');
const read=n=>fs.readFileSync(path.join(web,n),'utf8');
function boot(raw,throws=false){const document={documentElement:{dataset:{}}};vm.runInNewContext(read('theme-init.js'),{document,localStorage:{getItem(){if(throws)throw Error('denied');return raw;}}});return document.documentElement.dataset;}
test('theme bootstrap preserves legacy accent and safely defaults corrupt or denied storage',()=>{
 assert.equal(boot('{"accent":"ice"}').theme,'black');assert.equal(boot('{"accent":"ice"}').accent,'ice');
 for(const raw of ['{','null','{}','{"theme":"invalid","accent":"invalid"}']){assert.equal(boot(raw).theme,'black');assert.equal(boot(raw).accent,'lime');}
 assert.equal(boot('',true).theme,'black');assert.equal(boot('{"theme":"white","accent":"lavender"}').theme,'white');
});
test('theme and accent changes persist without rerendering or changing other preferences',()=>{
 const handlers={},root={dataset:{},lang:'en'},button={setAttribute(k,v){this[k]=v;}};let saved;
 const document={documentElement:root,body:{dataset:{},classList:{toggle(){}}},addEventListener(k,f){(handlers[k]??=[]).push(f);},getElementById(id){return id==='themeToggle'?button:null;},querySelectorAll(){return [];},querySelector(){return null;}};
 const c=vm.createContext({document,localStorage:{getItem:()=>'{"accent":"ice","density":"compact","sparkName":"Test"}',setItem:(k,v)=>{saved=JSON.parse(v);}},toast(){}});
 vm.runInContext(read('preferences.js'),c);
 const click=b=>handlers.click.forEach(f=>f({target:{closest:()=>b}}));
 click({id:'themeToggle',dataset:{}});assert.equal(saved.theme,'white');assert.equal(saved.density,'compact');assert.equal(saved.sparkName,'Test');assert.equal(root.dataset.theme,'white');assert.equal(button['aria-label'],'Switch to black mode');
 click({id:'',dataset:{accentChoice:'lavender'}});assert.equal(saved.accent,'lavender');assert.equal(saved.theme,'white');
 root.lang='ko';handlers['spark-language-change'][0]();assert.equal(button['aria-label'],'블랙 모드로 전환');
});
test('component color literals cannot bypass the shared palette',()=>{
 for(const file of fs.readdirSync(web).filter(n=>/\.(css|js)$/.test(n)&&n!=='theme.css')){
  assert.doesNotMatch(read(file),/#[0-9a-f]{3,8}\b|rgba?\(\s*\d/i,`${file} must use theme tokens`);
 }
});
function palette(theme,accent){const values={};for(const [,sel,body]of read('theme.css').matchAll(/([^{}]+)\{([^{}]+)\}/g)){
 if(!sel.includes(':root')||!body.includes('--'))continue;
 if(sel.includes('[data-theme="white"]')&&theme!=='white')continue;
 const a=sel.match(/\[data-accent="(\w+)"\]/);if(a&&a[1]!==accent)continue;
 for(const [,k,v]of body.matchAll(/(--[\w-]+):\s*(#[0-9a-f]{6})\s*;/g))values[k]=v;
 }return values;}
function luminance(hex){return hex.slice(1).match(/../g).map(v=>parseInt(v,16)/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4).reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);}
function contrast(a,b){const x=luminance(a),y=luminance(b);return (Math.max(x,y)+.05)/(Math.min(x,y)+.05);}
test('six palettes maintain readable foregrounds, chart lines and filled buttons',()=>{
 for(const mode of ['black','white'])for(const accent of ['lime','lavender','ice']){
  const p=palette(mode,accent);
  for(const bg of ['--bg','--surface','--raised'])for(const fg of ['--text','--muted','--accent','--chart-secondary','--warning','--danger'])assert.ok(contrast(p[fg],p[bg])>=4.5,`${mode}/${accent} ${fg}/${bg}`);
  for(const [fg,bg]of [['--on-accent','--accent-fill'],['--on-danger','--danger-fill'],['--hover-text','--hover-surface'],['--hover-muted','--hover-surface'],['--hover-accent','--hover-surface'],['--hover-secondary','--hover-surface'],['--art-ink','--art-base']])assert.ok(contrast(p[fg],p[bg])>=4.5,`${mode}/${accent} ${fg}/${bg}`);
 }
});
