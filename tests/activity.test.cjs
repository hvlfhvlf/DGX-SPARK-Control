const {test}=require('node:test');
const assert=require('node:assert/strict');
const fs=require('node:fs'),vm=require('node:vm');
const source=fs.readFileSync(require('node:path').join(__dirname,'../web/activity.js'),'utf8');
const context=vm.createContext({Date});
vm.runInContext(source.slice(source.indexOf('function activityGroups('),source.indexOf('function activityAction(')),context);
const event=(id,date)=>({id,timestamp:new Date(date).getTime()/1000});
test('calendar grouping handles midnight, newest order and retains source order',()=>{
 const rows=[event('older','2026-11-02T23:59:00'),event('newest','2026-11-03T00:01:00'),event('oldest','2026-10-31T10:00:00')];
 const groups=context.activityGroups(rows,'en-US',new Date('2026-11-03T00:02:00'));
 assert.equal(groups.length,3);assert.equal(groups[0].relative,'today');assert.equal(groups[1].relative,'yesterday');assert.equal(groups[2].relative,null);
 assert.equal(rows[0].id,'older');assert.equal(groups[0].rows[0].id,'newest');
});
test('yesterday crosses year and leap-day boundaries',()=>{
 assert.equal(context.activityGroups([event('a','2025-12-31T18:00:00')],'ko-KR',new Date('2026-01-01T01:00:00'))[0].relative,'yesterday');
 assert.equal(context.activityGroups([event('a','2024-02-29T18:00:00')],'ko-KR',new Date('2024-03-01T01:00:00'))[0].relative,'yesterday');
});
test('invalid dates are omitted, matching dates share one group',()=>{
 const groups=context.activityGroups([{timestamp:NaN},{timestamp:Infinity},event('a','2026-11-03T01:00:00'),event('b','2026-11-03T02:00:00')],'en-US');
 assert.equal(groups.length,1);assert.equal(groups[0].rows.length,2);assert.equal(groups[0].rows[0].id,'b');
});
