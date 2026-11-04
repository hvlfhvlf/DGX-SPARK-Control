"""Demand-driven /proc sampling without command lines or environment data."""
import os
import threading
import time
from pathlib import Path


class Programs:
    def __init__(self, root='/proc'):
        self.root=Path(root);self.lock=threading.Lock();self.previous={};self.at=0;self.cached=None

    def snapshot(self):
        with self.lock:
            now=time.monotonic()
            if self.cached and now-self.at<5: return self.cached
            uptime=float((self.root/'uptime').read_text().split()[0])
            hz=os.sysconf('SC_CLK_TCK');page=os.sysconf('SC_PAGE_SIZE');cpus=os.cpu_count() or 1
            rows=[];samples={};partial=False;deadline=now+1
            for index,p in enumerate(self.root.iterdir()):
                if not p.name.isdigit(): continue
                if len(samples)>=4096 or time.monotonic()>deadline: partial=True;break
                try:
                    raw=(p/'stat').read_text()[:8192];end=raw.rindex(')');fields=raw[end+2:].split()
                    start=int(fields[19]);ticks=int(fields[11])+int(fields[12]);key=(int(p.name),start)
                    old=self.previous.get(key);samples[key]=ticks
                    cpu=max(0,min(100,100*(ticks-old)/(hz*(now-self.at)*cpus))) if old is not None and ticks>=old and 0<now-self.at<=15 else None
                    name=raw[raw.index('(')+1:end][:80]
                    group=None
                    for part in (p/'cgroup').read_text()[:4096].split('/'):
                        if part.strip().endswith('.service'): group=part.strip()
                    rows.append(dict(pid=int(p.name),name=name,group=group,state=fields[0],cpu=round(cpu,2) if cpu is not None else None,
                        memory_bytes=max(0,int(fields[21])*page),elapsed=max(0,int(uptime-start/hz)),own=p.stat().st_uid==os.getuid()))
                except (OSError,ValueError,IndexError): continue
            rows.sort(key=lambda r:(r['own'],r['memory_bytes']),reverse=True)
            self.previous=samples;self.at=now
            self.cached=dict(timestamp=time.time(),rows=rows[:512],count=len(rows),partial=partial or len(rows)>512,
                cpu_scope='host_capacity',memory_scope='rss_shared_pages_included')
            return self.cached
