import subprocess,json,sys,re
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3/'
names={}
for l in open(S+'works.txt'):
    m=re.match(r'(d59[a-z0-9]+)-(.*)\.json',l.strip())
    if m: names[m.group(1)]=m.group(2)
def load(wid):
    t=names[wid]; c=wid[-3:]
    p='Work/%s/%s/%s/%s-%s.json'%(c[0],c[1],c[2],wid,t)
    r=subprocess.run(['git','show','origin/main:'+p],capture_output=True,cwd='/tmp/wk-wake-g3')
    return json.loads(r.stdout)
if __name__=='__main__':
    for w in sys.argv[1:]:
        try:
            j=load(w)
        except Exception as e:
            print(w,'ERR',e); continue
        a=[(x.get('name') or x.get('entity_id')) if isinstance(x,dict) else x for x in j.get('authors',[])]
        print(w,j.get('title'),a,j.get('period'),'|',str(j.get('description') or '')[:50].replace('\n',' '))
