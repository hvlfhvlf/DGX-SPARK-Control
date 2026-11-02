const {test}=require('node:test');
const assert=require('node:assert/strict');
const D=require('../web/telemetry-detail-data.js');

test('zero is a measured value; null, NaN and absent values are not',()=>{
 const rows=[{gpu:null},{gpu:0},{gpu:20},{gpu:NaN},{}];
 assert.deepEqual(D.stats(rows,'gpu'),{count:2,mean:10,peak:20});
 assert.deepEqual(D.stats([{network:[null,0]}],'network',1),{count:1,mean:0,peak:0});
 assert.deepEqual(D.stats(rows,'missing'),{count:0,mean:null,peak:null});
});
test('range selection filters both boundaries and does not mutate history',()=>{
 const rows=[{timestamp:105},{timestamp:39},{timestamp:100},{timestamp:40}];
 assert.deepEqual(D.windowRows(rows,1,100).map(r=>r.timestamp),[40,100]);
 assert.equal(rows[0].timestamp,105);
});
test('charts break at null readings and collection gaps; isolated points remain',()=>{
 const rows=[{timestamp:0,gpu:0},{timestamp:5,gpu:50},{timestamp:10,gpu:null},{timestamp:15,gpu:25},{timestamp:40,gpu:100}];
 assert.deepEqual(D.segments(rows,'gpu',0,0,40,100),[[[0,0],[.125,.5]],[[.375,.25]],[[1,1]]]);
});
test('utilization and capacity axes use real ceilings, including a 64 GiB system',()=>{
 const rows=[{gpu:3,memory:8,disk:1}];
 assert.equal(D.scale('gpu',{},rows),100);
 assert.equal(D.scale('memory',{memory_total_gib:60.8},rows),60.8);
 assert.equal(D.scale('disk',{disk_total_tib:3.6},rows),3.6);
});
test('I/O channels share a tiered axis that holds after a peak falls out',()=>{
 assert.equal(D.scale('network',{},[{network:[4,37]}]),50);
 assert.equal(D.scale('network',{},[{network:[0,0]}],50),50);
 assert.equal(D.scale('network',{},[{network:[70,10]}],50),100);
 assert.equal(D.scale('network',{},[{network:[null,null]}]),1);
});
test('composition preserves available and reserved space, without treating unknown as zero',()=>{
 assert.deepEqual(D.composition([20,70,10],100),[20,70,10]);
 assert.equal(D.composition([20,null],100),null);
 assert.equal(D.composition([60,50],100),null);
 assert.equal(D.composition([0,0],0),null);
});
test('clock flags distinguish thermal, power, idle and unknown causes',()=>{
 assert.equal(D.clockEvents(null),null);
 assert.equal(D.clockEvents(1).thermal,false);
 assert.equal(D.clockEvents(8).thermal,false);
 assert.equal(D.clockEvents(4).power,true);
 assert.equal(D.clockEvents(32+64).thermal,true);
 assert.equal(D.clockEvents(128).power,true);
 assert.deepEqual(D.clockEvents(0).active,[]);
 assert.equal(D.clockEvents(2**40+32).unknown,2**40);
 assert.equal(D.clockEvents(Number.MAX_SAFE_INTEGER+1),null);
});
