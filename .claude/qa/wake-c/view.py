import sys,re
lo,hi=int(sys.argv[1]),int(sys.argv[2])
import glob
cur=None;seen=set();show=False
for f in sorted(glob.glob('cand_*.txt')):
    for l in open(f,encoding='utf-8'):
        if l.startswith('##'):
            n=int(l.split()[1]); show=lo<=n<hi; seen=set()
            if show: print(l.rstrip()[:200])
        elif show:
            k=re.sub(r'\[\d+\]','',l.rsplit('|',1)[0])
            if k in seen: continue
            seen.add(k); print(l.rstrip()[:200])
