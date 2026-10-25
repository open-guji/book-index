import json,sys,os
S=os.environ.get('OUT','/tmp/subitem-yi')
sys.argv=[sys.argv[0]]
exec(open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'sig.py')).read().split('out=[]\nfor gi')[0])
P=json.load(open(S+'/pairs.json'))
pg={}
for p in P: pg.setdefault(p['g'],[]).append(p)
with open(S+'/review.txt','w') as f:
  for gi,g in enumerate(feat):
    f.write(f"#{gi} 【{g['key']}】{g['bulei']}·{g['cat']}\n")
    for k,w in enumerate(g['works']):
        ns,dy,src=names_of(w)
        js=[x[0] for x in juan_of(w)]
        c=col.get(w['colrec']) or {}
        ed=(c.get('edition') or '')+' '+str((c.get('publication_info') or {}).get('year') or '')
        f.write(f"  {chr(65+k)} {w['id']} 〔{w['col'][:24]}〕{ed[:20]} 名{'/'.join(ns) or '-'}{'(丛)' if src=='col' else ''} 朝{'/'.join(dy) or '-'} 卷{'|'.join(sorted(set(js)))}\n")
        for ti,ai,sec,sm in w['ib']:
            if sec and not sec.startswith('叢書部'):
                f.write(f"     ·{sec[:14]} {ti} {ai} {sm[:90]}\n")
    for p in pg.get(gi,[]):
        fl=[p['acat'],'卷矛盾' if p['jconf'] else ('卷同' if p['jsame'] else '卷?')]
        if p['hx']: fl.append('互见')
        if p['yy']: fl.append('影印')
        if len(g['works'])>2: f.write(f"   {p['a'][-4:]}-{p['b'][-4:]} {' '.join(fl)}\n")
        else: f.write(f"   => {' '.join(fl)}\n")
