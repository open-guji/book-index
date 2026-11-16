import sys,re,json,collections
sys.path.insert(0,'/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3')
from g3_cl import nz,tcore,pubs
from g3_wshow import load,names
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3/'
TV=str.maketrans('寳真寶删増','寶眞寶刪增')
def tn(t): return nz(t).translate(TV)
widx=collections.defaultdict(list)
for wid,t in names.items(): widx[tn(t)].append(wid)
jp=json.load(open(S+'jpbooks.json'))
jpby=collections.defaultdict(list)
for b in jp: jpby[b['work']].append(b)
_ac={}
def auth(wid):
    if wid in _ac: return _ac[wid]
    try: j=load(wid); r=[a.get('name') for a in j.get('authors',[]) if isinstance(a,dict)]
    except Exception: r=[]
    _ac[wid]=r; return r
def yr(s):
    m=re.search(r'\[(\d{4})',s) or re.search(r'\((\d{4})',s)
    return int(m.group(1)) if m else None
def ov(a,b):
    for x in a:
        for y in b:
            if x==y or (len(x)>=4 and len(y)>=4 and (x in y or y in x)): return True
    return False
def clusters(scanfiles):
    items={}
    for sf in scanfiles:
        for q,v in json.load(open(sf)).items():
            for i in v['jp']: items[i['ncid']]=i
    cl=[]
    for i in items.values():
        tc=tn(tcore(i['title'])); y=yr(i['yr']); ps=set(pubs([i['pub']]))
        for c in cl:
            if c['tc']==tc and c['y']==y and (ov(c['ps'],ps) or (not ps and not c['ps'])):
                c['recs'].append(i); c['ps']|=ps; break
        else: cl.append(dict(tc=tc,y=y,ps=set(ps),recs=[i]))
    ch=True
    while ch:
        ch=False
        for a in range(len(cl)):
            for b in range(a+1,len(cl)):
                A,B=cl[a],cl[b]
                if A['tc']==B['tc'] and A['y']==B['y'] and ov(A['ps'],B['ps']):
                    A['recs']+=B['recs'];A['ps']|=B['ps'];del cl[b];ch=True;break
            if ch:break
    return sorted(cl,key=lambda c:(c['tc'],c['y'] or 0))
if __name__=='__main__':
    cl=clusters(sys.argv[1].split(','))
    out=[]
    for c in cl:
        wids=widx.get(c['tc'],[])
        ws=[(w,auth(w),len(jpby.get(w,[]))) for w in wids[:5]]
        out.append(dict(tc=c['tc'],y=c['y'],ps=sorted(c['ps']),ncids=[r['ncid'] for r in c['recs']],au=c['recs'][0]['au'],pub0=c['recs'][0]['pub'],yr0=c['recs'][0]['yr'],works=ws,nw=len(wids)))
    json.dump(out,open(sys.argv[2],'w'),ensure_ascii=False)
    print(len(out),sum(1 for o in out if o['works']))
