import json,re,collections,sys,opencc
_cc=opencc.OpenCC('t2s')
S='/tmp/claude-0/-home-user/e59db2b9-8fd4-5ed9-a492-942f4a225576/scratchpad/r10'
def norm(m):
    m=_cc.convert(re.sub(r'（[^）]*）|\([^)]*\)','',m or ''))
    m=m.replace('附','').replace('别','別').replace('畧','略').replace('録','錄').replace('，','').replace('、','').replace(' ','')
    m=m.replace('首一末一卷','首一卷末一卷')
    return m
MAIN=re.compile(r'^(不分卷|[〇一二三四五六七八九十百千零]+卷)')
def compat(ms):
    """returns longest raw measure if all compatible else None, reason"""
    if len({p for m in ms for p in re.findall(r'（([^）]*本)）',m)})>0: return None,'paren-ben'
    ns=[(norm(m),m) for m in ms]
    ns=[(re.sub('^不分卷','一卷',n) if re.match('^(一卷|不分卷)',n) else n,m) for n,m in ns]
    mains={MAIN.match(n).group(1) if MAIN.match(n) else None for n,_ in ns}
    if None in mains or len(mains)>1: return None,'main-diff'
    ns.sort(key=lambda t:len(t[0]))
    for i in range(len(ns)-1):
        if not ns[i+1][0].startswith(ns[i][0]): return None,'not-prefix'
    return ns[-1][1],'ok'
if __name__=='__main__':
    r=json.load(open(S+'/rej.json'))['measure']
    C=collections.Counter()
    for x in r:
        ms={b['measure_info'] for b in x['books'] if b['measure_info']}
        lg,why=compat(ms); C[why]+=1; x['mwhy']=why; x['mlong']=lg
    print(C)
    json.dump(r,open(S+'/measure.json','w'),ensure_ascii=False)
