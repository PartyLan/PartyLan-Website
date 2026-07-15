import time
class MemoryRateLimiter:
    def __init__(self, limit=5, window=600): self.limit=limit; self.window=window; self.hits={}
    def allow(self, key):
        now=time.time(); vals=[t for t in self.hits.get(key,[]) if now-t<self.window]
        if len(vals)>=self.limit: self.hits[key]=vals; return False
        vals.append(now); self.hits[key]=vals; return True
