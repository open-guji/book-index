import pickle,collections,random,sys
W=pickle.load(open('works.pkl','rb')); rows=pickle.load(open('rows_t2.pkl','rb'))
exec(open('tier.py').read().split("out=[]")[0].split("W=pickle")[0])  # imports only
ERA={'漢迄隋':{'pre-qin','qin-han','three-kingdoms','jin','nanbeichao','sui-tang'},'唐五代':{'sui-tang','five-dynasties'},'宋金':{'song','liao-jin-yuan'},'宋':{'song'},'元':{'liao-jin-yuan'},'明':{'ming'},'清初期':{'qing'},'清中期':{'qing'},'清後期':{'qing'},'民國':{'modern'}}
DYN={'明':'ming','宋':'song','北宋':'song','南宋':'song','元':'liao-jin-yuan','金':'liao-jin-yuan','遼':'liao-jin-yuan','唐':'sui-tang','隋':'sui-tang','晉':'jin','東晉':'jin','西晉':'jin','漢':'qin-han','東漢':'qin-han','西漢':'qin-han','後漢':'qin-han','清':'qing','民國':'modern','五代':'five-dynasties','魏':'three-kingdoms','吳':'three-kingdoms','蜀':'three-kingdoms','南朝宋':'nanbeichao','南朝齊':'nanbeichao','南朝梁':'nanbeichao','南朝陳':'nanbeichao','北魏':'nanbeichao','北齊':'nanbeichao','北周':'nanbeichao'}
def per_of(w): return w['per'] or DYN.get(w['dyn'])
sel=[]
for r in rows:
    if r['done'] or r['tier']!='B' or r['comp'] or len(r['cands'])!=1 or len(r['main'])<=2: continue
    sec=r['sort'].split('/')
    if len(sec)<3 or sec[1]!='別集類': continue
    era=ERA.get(sec[2].replace('之屬',''))
    if not era: continue
    w=W[r['cands'][0]]
    if per_of(w) not in era: continue
    if '欽定四庫全書總目' in {a for a,b in w['ib']}: continue
    if r['juan'] is not None and w['juan'] is not None and r['juan']!=w['juan']: continue
    r['tier']='A3'; r['why']='別集類年代类目与Work时代相合'; r['pick']=r['cands'][0]; sel.append(r)
print(len(sel))
random.seed(7)
for r in random.sample(sel,min(30,len(sel))):
    w=W[r['cands'][0]]; print(r['sort'][2:12],r['name'],'||',w['t'],w['au'][:1],w['dyn'],w['per'],w['juan'])
pickle.dump(rows,open('rows_t3.pkl','wb'))
