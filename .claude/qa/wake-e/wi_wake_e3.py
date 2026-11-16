import json,sys,subprocess
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/'
idx={}
for l in open(S+'e_w.txt'):
    p=l.rstrip('\n'); fn=p.rsplit('/',1)[-1]; idx[fn.split('-')[0]]=p
def get(w):
    r=subprocess.run(['git','show','origin/main:'+idx[w]],cwd='/home/user/book-index',capture_output=True)
    return json.loads(r.stdout)
if __name__=='__main__':
    for w in sys.argv[1:]:
        d=get(w)
        ds=d.get('description'); ds=ds.get('text') if isinstance(ds,dict) else ds
        print(w,d.get('title'),[a.get('name') for a in d.get('authors',[])],[(i.get('title_info'),i.get('section')) for i in d.get('indexed_by',[])][:2],(ds or '')[:70].replace('\n',' '))
