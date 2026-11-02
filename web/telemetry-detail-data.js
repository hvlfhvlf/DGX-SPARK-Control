/* Pure presentation calculations. No polling, host access or generated telemetry. */
(function(root){
 'use strict';
 const valid=value=>typeof value==='number'&&Number.isFinite(value);
 const reading=(row,id,channel=0)=>{const v=row?.[id];return Array.isArray(v)?v[channel]:v;};
 function windowRows(history,minutes,end){
  return history.filter(r=>valid(r.timestamp)&&r.timestamp>=end-minutes*60&&r.timestamp<=end).slice().sort((a,b)=>a.timestamp-b.timestamp);
 }
 function stats(rows,id,channel=0){
  const values=rows.map(r=>reading(r,id,channel)).filter(valid);
  return {count:values.length,mean:values.length?values.reduce((a,b)=>a+b,0)/values.length:null,peak:values.length?Math.max(...values):null};
 }
 function segments(rows,id,channel,start,end,max){
  const result=[];let current=[],previous=null;
  for(const row of rows){
   const value=reading(row,id,channel);
   if(!valid(value)||(previous!==null&&row.timestamp-previous>15)){
    if(current.length)result.push(current);current=[];
   }
   if(valid(value))current.push([Math.max(0,Math.min(1,(row.timestamp-start)/(end-start))),Math.max(0,Math.min(1,value/max))]);
   previous=row.timestamp;
  }
  if(current.length)result.push(current);return result;
 }
 function niceCeiling(value){
  if(!(value>0))return 1;
  const base=10**Math.floor(Math.log10(value));
  return [1,2,5,10].find(n=>n*base>=value)*base;
 }
 function scale(id,sample,rows,previous=0){
  if(id==='gpu'||id==='cpu')return 100;
  if(id==='memory'&&sample.memory_total_gib>0)return sample.memory_total_gib;
  if(id==='disk'&&sample.disk_total_tib>0)return sample.disk_total_tib;
  const peak=Math.max(0,...rows.flatMap(r=>Array.isArray(r[id])?r[id]:[r[id]]).filter(valid));
  // A scale never shrinks while this dialog/range is open. Floors are chart ranges,
  // not hardware temperature limits or rated power caps.
  const floor=id==='temp'?100:id==='power'?50:1;
  return Math.max(previous,floor,niceCeiling(peak*1.1));
 }
 function composition(values,total){
  if(!valid(total)||total<=0||values.some(v=>!valid(v)||v<0))return null;
  if(values.reduce((a,b)=>a+b,0)>total*1.001)return null;
  return values.map(v=>Math.max(0,Math.min(100,v/total*100)));
 }
 const eventBits=[
  [1,'GPU idle','GPU 유휴'],[2,'Application clock policy','애플리케이션 클럭 정책'],
  [4,'Software power cap','소프트웨어 전력 제한'],[8,'Hardware slowdown','하드웨어 클럭 저하'],
  [16,'Sync boost','동기화 부스트'],[32,'Software thermal slowdown','소프트웨어 열 제한'],
  [64,'Hardware thermal slowdown','하드웨어 열 제한'],[128,'External power brake','외부 전력 제한'],
  [256,'Display clock policy','디스플레이 클럭 정책']
 ];
 function clockEvents(value){
  // Number arithmetic avoids truncating a 64-bit NVML mask to JS's 32-bit bitwise range.
  if(!Number.isSafeInteger(value)||value<0)return null;
  const active=eventBits.filter(([bit])=>Math.floor(value/bit)%2===1);
  return {active,unknown:value-active.reduce((sum,[bit])=>sum+bit,0),thermal:active.some(([bit])=>bit===32||bit===64),power:active.some(([bit])=>bit===4||bit===128)};
 }
 const api={valid,reading,windowRows,stats,segments,niceCeiling,scale,composition,clockEvents};
 if(typeof module!=='undefined'&&module.exports)module.exports=api;else root.TelemetryDetailData=api;
})(typeof globalThis!=='undefined'?globalThis:this);
