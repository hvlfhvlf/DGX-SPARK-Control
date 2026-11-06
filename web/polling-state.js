/* Pure bounded telemetry state; no credentials, timers or browser side effects. */
(function(root){
 'use strict';
 class ConnectionState{
  constructor(){this.lastSuccess=0;this.failures=0;this.firstFailure=0;}
  success(now){this.lastSuccess=now;this.failures=0;this.firstFailure=0;return 'online';}
  failure(now){this.failures++;if(!this.firstFailure)this.firstFailure=now;
   return this.failures>=2||now-(this.lastSuccess||this.firstFailure)>=20000?'offline':'delayed';}
 }
 function mergeHistory(previous,reply,now){
  if(!reply||typeof reply.epoch!=='string'||!Array.isArray(reply.samples))throw Error('Invalid history response');
  const rows=new Map();
  for(const row of [...(reply.reset?[]:previous),...reply.samples]){
   if(Number.isFinite(row?.timestamp)&&row.timestamp>=now-3600)rows.set(row.timestamp,row);
  }
  return [...rows.values()].sort((a,b)=>a.timestamp-b.timestamp).slice(-720);
 }
 const value={ConnectionState,mergeHistory};
 if(typeof module!=='undefined'&&module.exports)module.exports=value;else root.SparkPolling=value;
})(typeof globalThis!=='undefined'?globalThis:this);
