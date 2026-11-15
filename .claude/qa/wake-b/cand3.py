import json,re,sys,collections
sys.path.insert(0,'.')
import ndl,eras
ws=json.load(open('/tmp/wb_works.json'));books=json.load(open('/tmp/wb_books.json'))
by=collections.defaultdict(list)
for b in books: by[b['work_id']].append(b)
def norm(s): return re.sub(r'[\s　]','',ndl.jp(s))
def exyears(wid):
    ys=set()
    for b in by[wid]:
        y,_=eras.era_year(b.get('edition',''))
        if y: ys.add(y)
        d=b.get('dating',{})
        if d.get('year'): ys.add(d['year'])
        m=re.search(r'\[(1[4-9]\d\d)',b.get('edition','')); 
        if m: ys.add(int(m.group(1)))
    return ys
PF={'R100000002':'NDL','R000000050':'早大','R100000092':'九大','R100000102':'東大'}
out=collections.OrderedDict()
for wid,res in json.load(open('/tmp/wb_pass3.json')):
    t=norm(ws[wid]['title']);ys=exyears(wid)
    g=collections.OrderedDict()
    for r in res:
        rid,title,cr,pub,date,vol,ext,cat=r
        p=rid.split('-')[0]
        if p not in PF or '和古書' not in cat+('和古書' if p=='R000000050' else ''): continue
        m=re.match(r'(\d{4})',date)
        if not m or not pub: continue
        y=int(m.group(1))
        tt=re.sub(r'\d+[卷巻].*$|[\[〔].*','',norm(title))
        if tt!=t: continue
        if y in ys: continue
        k=(y,pub[:20])
        g.setdefault(k,[]).append((PF[p],rid,title,cr,ext))
    if g: out[wid]=g
for wid,g in out.items():
    print('##',wid,ws[wid]['title'],[a.get('name') for a in ws[wid].get('authors',[])][:1],sorted(exyears(wid)))
    for (y,pub),l in g.items(): print('   ',y,pub,[(a,r) for a,r,*_ in l][:4],l[0][2][:20],l[0][3][:10],l[0][4][:10])
