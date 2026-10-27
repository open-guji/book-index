# 本单元各组：现有连通分量（related 非待並條 + whitelist），并按 zupu/fangzhi 判定对标注
import csv,sys,os,glob,json,collections,pickle
S=os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ROOT='/home/user/book-index'
sys.path.insert(0,ROOT+'/.claude/qa'); import backrefs
PENDING=('待並條',)
units=[r for r in csv.reader(open(S+'/units.tsv'),delimiter='\t') if r[0]=='新-譜志余']
ids=set(i for r in units for i in r[6].split(','))
W={}; links=[]
for t,p,d in backrefs.iter_records(ROOT):
    if t!='Work' or d.get('merged_into'): continue
    for r in d.get('related_works') or []:
        if isinstance(r,dict) and r.get('id') and not any(k in (r.get('note') or '') for k in PENDING):
            links.append((d['id'],r['id']))
    if d['id'] in ids: W[d['id']]=d
for f in glob.glob(ROOT+'/.claude/qa/dedup-judged/*.tsv'):
    for line in open(f):
        if line.startswith('#'): continue
        x=line.rstrip('\n').split('\t')
        if len(x)>=2 and x[0].startswith(('d','1')): links.append((x[0],x[1]))
pickle.dump({'units':units,'W':W,'links':links},open(S+'/w/data.pkl','wb'))
print(len(units),len(W),len(links))
