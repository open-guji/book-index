import sys,json,re
sys.path.insert(0,'.')
import spec_wake_e3 as sp
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/'
R=json.load(open(S+'e_ncidpages.json'))
def inst(d):
    seg=d['hold'].split('| 件 |',1)
    return seg[1].split('|')[0].strip() if len(seg)>1 else ''
a,b=int(sys.argv[1]),int(sys.argv[2])
for k,w,t,sels in sp.SPEC[a:b]:
    n=[]
    for s in sels: n+=sp.sel(*s)
    n=sorted(set(n))[:int(sys.argv[3]) if len(sys.argv)>3 else 12]
    print('###',k,w,t,len(n))
    seen=set()
    for x in n:
        d=R[x]
        bib=d['bib']
        note=d['note']
        nt=[p for p in note.split(' / ') if re.search(r'刊|奥|見返|識語|序|跋|蔵版|藏版|印|後|版',p) and 'Tweet' not in p][:6]
        print(' ',x,'|',bib[:110],'|',inst(d),'|',' ; '.join(nt)[:260])
