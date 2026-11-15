import subprocess, json, sys, pickle
import os
G=os.environ.get('BI_GIT', '.')
def stream(prefix):
    ls = subprocess.run(['git','-C',G,'ls-tree','-r','-z','origin/main',prefix],capture_output=True,text=True).stdout.split('\0')[:-1]
    ents=[]
    for l in ls:
        meta,path=l.split('\t',1); sha=meta.split()[2]; ents.append((sha,path))
    p=subprocess.Popen(['git','-C',G,'cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE)
    import threading
    def w():
        for s,_ in ents: p.stdin.write((s+'\n').encode())
        p.stdin.close()
    threading.Thread(target=w).start()
    for s,path in ents:
        h=p.stdout.readline().split(); n=int(h[2]); b=p.stdout.read(n); p.stdout.read(1)
        yield path,b
out={}
for t in ['Work','Book','Collection','Entity']:
    L=[]
    for path,b in stream(t):
        if not path.endswith('.json'): continue
        try: d=json.loads(b)
        except Exception: continue
        if t=='Work': L.append(dict(id=d['id'],title=d.get('title'),orig=d.get('original_title'),au=[(a.get('name'),a.get('dynasty'),a.get('role'),a.get('entity_id')) for a in d.get('authors',[])],dyn=d.get('dynasty'),mg=d.get('merged_into'),path=path,rel=[r.get('id') for r in d.get('related_works',[])],aka=d.get('aliases') or d.get('alt_titles')))
        elif t=='Book': L.append(dict(id=d['id'],title=d.get('title'),ed=d.get('edition'),wid=d.get('work_id'),ci=d.get('contained_in'),mg=d.get('merged_into'),path=path,au=[(a.get('name'),a.get('role')) for a in d.get('authors',[])] if d.get('authors') else None, res=bool(d.get('resources'))))
        elif t=='Collection': L.append(dict(id=d['id'],title=d.get('title'),path=path,mg=d.get('merged_into')))
        else: L.append(dict(id=d['id'],name=d.get('primary_name'),dyn=d.get('dynasty'),mg=d.get('merged_into')))
    out[t]=L; print(t,len(L),file=sys.stderr)
pickle.dump(out,open(sys.argv[1],'wb'))
