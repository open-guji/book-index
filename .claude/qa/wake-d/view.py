import json,re,sys
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad'
d=json.load(open(S+'/shard3.json')); W=json.load(open(S+'/d_works.json')); c=json.load(open('cache_d.json'))
lo,hi=int(sys.argv[1]),int(sys.argv[2])
seen=set()
for x in d[lo:hi]:
    au=(W[x['work']]['au'] or [''])[0]
    k=x['title']+'|'+au
    print('#',x['id'],x['title'],'|',x['edition'],'|',au,'| sib:',[ (b['ed'],b['prov']) for b in W[x['work']]['books'] if not b['mine']][:4])
    if k in seen or k not in c: print('   (see above / pending)'); continue
    seen.add(k)
    v=c[k]; sn=set(); cnt=0
    for r in v.get('ndl',[]):
        if re.match(r'\d{4}',r['date']) and int(r['date'][:4])<1913 and x['title'][:2] in r['title']:
            kk=(r['title'][:12],r['pub'][:10],r['date'][:4])
            if kk in sn or cnt>7: continue
            sn.add(kk); cnt+=1
            print('  N',r['title'][:40],'|',r['creator'][:24],'|',r['pub'][:40],'|',r['date'],'|',r['link'].split('/')[-1])
    for r in v.get('cinii',[]):
        m=re.search(r'(\d{4})',r[4]) 
        if x['title'][:2] in r[1] and (('[' in r[4] or '.' in r[4] or r[4][:1].isdigit()) is False or (m and int(m.group(1))<1913)) and not re.match(r'(19[1-9]|20)',r[4]): print('  C',r[0],r[1][:24],'|',r[3][:24],'|',r[4],'|',r[5]) if (r[1][:8],r[3][:8],r[4]) not in sn and not sn.add((r[1][:8],r[3][:8],r[4])) and cnt<14 else None
