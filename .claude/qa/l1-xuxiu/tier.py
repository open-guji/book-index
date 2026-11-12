import pickle,collections,csv,random,json
W=pickle.load(open('works.pkl','rb')); rows=pickle.load(open('rows.pkl','rb'))
LATE={'qing','modern'}
PARTS={'經部','史部','子部','集部','叢書部'}
def part_of(sort):
    p=sort.split('/')[0]
    return '史部' if p=='方志部' else p
def sig(r,w):
    s={}
    s['juan']= 'eq' if (r['juan'] is not None and w['juan'] is not None and r['juan']==w['juan']) else 'na' if (r['juan'] is None or w['juan'] is None) else 'ne'
    LD={'清','民國','中華民國','近代','朝鮮','中華人民共和國','日本','越南'}
    s['per']= 'late' if w['per'] in LATE else ('late' if (not w['per'] and w['dyn'] in LD and any(w['au'])) else 'none' if not w['per'] else 'early')
    srcs={a for a,b in w['ib']}
    s['sk']= '欽定四庫全書總目' in srcs
    parts={('叢書部' if x[:2]=='叢書' else x[:2]) for x in w['sec'] if x[:2] in ('經部','史部','子部','集部','叢書')}
    s['part']='na' if not parts else 'ok' if part_of(r['sort']) in parts else 'ne'
    return s
def good(r,w):
    s=sig(r,w)
    return s['juan']!='ne' and s['per']=='late' and not s['sk'] and s['part']!='ne'
out=[]
for r in rows:
    c=r['cands']; short=len(r['main'])<=2
    if not c: tier='C'; why='无同题'
    elif r['comp']: tier='B'; why='复合题名(含多书/附)'
    elif short: tier='B'; why='题名≤2字易撞名'
    elif len(c)==1:
        w=W[c[0]]; s=sig(r,w)
        if good(r,w): tier='A'; why='唯一同题'+('+卷数相合' if s['juan']=='eq' else '')
        else: tier='B'; why='唯一同题但冲突:'+','.join(k+'='+str(v) for k,v in s.items() if (k=='juan' and v=='ne') or (k=='per' and v!='late') or (k=='sk' and v) or (k=='part' and v=='ne'))
    else:
        g=[x for x in c if good(r,W[x])]
        tier='B'; why=f'多候选{len(c)}'+(f'，其中可用1' if len(g)==1 else '')
        if len(g)==1 and sig(r,W[g[0]])['juan']=='eq':
            tier='A2'; why=f'多候选{len(c)}，唯一朝代／部类相合且卷数相合'; r['pick']=g[0]
    r['tier']=tier; r['why']=why
cnt=collections.Counter(r['tier'] for r in rows); print(cnt)
cnt2=collections.Counter((r['sort'].split('/')[0],r['tier']) for r in rows)
for k,v in sorted(cnt2.items()): print(k,v)
print(collections.Counter(r['why'].split('=')[0][:14] for r in rows if r['tier']=='B').most_common(12))
pickle.dump(rows,open('rows_t.pkl','wb'))
with open('tier.tsv','w',newline='') as f:
    wr=csv.writer(f,delimiter='\t'); wr.writerow(['k','tier','部类','书名','页','主题','卷','候选','原因'])
    for r in rows: wr.writerow([r['k'],r['tier'],r['sort'],r['name'],r['page'],r['main'],r['juan'],' '.join(r['cands']),r['why']])
