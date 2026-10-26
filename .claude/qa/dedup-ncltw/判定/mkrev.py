import json,sys
sys.argv=['x'];exec(open('mk.py').read().split('segs=')[0])
P=json.load(open('pairs.json'))
rows=[l.rstrip('\n').split('\t') for l in open('并.tsv',encoding='utf-8')]
extra=[('d59f2gonez9d','d59fxwojvev5'),('d59f2ht2yk8z','d59fxwycwt1c')]
out=[];k=0
for r in rows:
    n=int(r[0]);a,b,recs=P[n-1]; k+=1
    out.append(f"### 复核 {k:02d}（原对 {r[0]}）\n台湾国图藏本："+'；'.join(f"{x[0]}《{x[1]}》{x[2]}" for x in recs[:3])+f"\nWork 甲\n{desc(a)}\nWork 乙\n{desc(b)}\n")
for a,b in extra:
    k+=1; out.append(f"### 复核 {k:02d}（段外线索）\nWork 甲\n{desc(a)}\nWork 乙\n{desc(b)}\n")
open('复核.md','w',encoding='utf-8').write('\n'.join(out)); print(k)
