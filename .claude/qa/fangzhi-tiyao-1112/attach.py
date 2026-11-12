"""A 类（总目内唯一、库内方志 Work 唯一）追加 indexed_by[source=中國地方志總目提要]。
用法：python3 attach.py <classified.json> [--apply] [--limit N]。已有同 source 的 Work 跳过；revision minor+1；写法 indent=2。"""
import sys,json,os,glob,datetime
SRC='中國地方志總目提要'
res=json.load(open(sys.argv[1])); apply='--apply' in sys.argv
lim=int(sys.argv[sys.argv.index('--limit')+1]) if '--limit' in sys.argv else 10**9
today=datetime.date.today().isoformat(); n=skip=0
paths={}
for f in glob.glob('Work/*/*/*/*.json'): paths.setdefault(os.path.basename(f).split('-')[0],[]).append(f)
for r in res:
    if r['cls']!='A唯一对唯一': continue
    if n>=lim: break
    wid=r['ids'][0]; fs=paths.get(wid,[])
    if len(fs)!=1: print('?',wid,fs); continue
    d=json.load(open(fs[0]))
    if any(i.get('source')==SRC for i in d.get('indexed_by',[])): skip+=1; continue
    e={'source':SRC,'title_info':r['bookName'],'section':r['sort']}
    if r.get('page'): e['page']=r['page']
    d.setdefault('indexed_by',[]).append(e)
    a,b,c=map(int,d['revision'].split('.')); d['revision']=f'{a}.{b+1}.0'; d['revised_at']=today
    n+=1
    if apply: open(fs[0],'w').write(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
print('追加',n,'已有跳过',skip,'apply' if apply else 'dry')
