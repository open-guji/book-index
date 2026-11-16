# -*- coding: utf-8 -*-
"""生成 ledger4.tsv／TODO4.tsv（讀取 build4 輸出的臨時台賬＋輸入清單）。"""
import json,os,re,sys,subprocess
HERE=os.path.dirname(os.path.abspath(__file__));BI=os.path.abspath(os.path.join(HERE,'../../..'))
sys.path.insert(0,HERE)
from b4_accept import ACC
from b4_reasons import OVR,classify
rows=[l.rstrip('\n').split('\t') for l in open(os.path.join(HERE,'cuny4_input.tsv'),encoding='utf-8')]
SC=json.load(open(os.path.join(HERE,'cuny4_scan_hits.json')))   # bid -> 掃描時是否有同年同題記錄
LED=json.load(open('/tmp/wb4_ledger_part.json'))
done={r[0]:r for r in LED}
src={}
for r in rows:
    if '/ledger' in r[0]: src.setdefault(r[1],[]).append(r[0].split('/')[0]+':'+r[0].split('/')[1].replace('.tsv',''))
# 取各 Book 當前資料
out=subprocess.run(['git','-C',BI,'-c','core.quotepath=false','ls-tree','-r','--name-only','origin/main','--','Book'],capture_output=True).stdout.decode().split('\n')
P={os.path.basename(p).split('-',1)[0]:p for p in out if p}
L=['Book id\t題名\t判定\t日本館藏\t依據URL／原因\t原台賬']
T=['Book id\t題名\t版本項\t保留原因\t原台賬']
n_ok=0;cnt={}
for bid in sorted(src):
    b=json.loads(subprocess.run(['git','-C',BI,'show','origin/main:'+P[bid]],capture_output=True).stdout.decode())
    if bid in done:
        r=done[bid];L.append('\t'.join([bid,b['title'],'補掛',r[3],r[4],';'.join(src[bid])]));n_ok+=1
    else:
        why=OVR.get(bid) or classify(b,SC.get(bid,False))
        key=re.split('[：（，]',why)[0]
        cnt[key]=cnt.get(key,0)+1
        L.append('\t'.join([bid,b['title'],'存疑',' ',why,';'.join(src[bid])]))
        T.append('\t'.join([bid,b['title'],b.get('edition',''),why,';'.join(src[bid])]))
open(os.path.join(HERE,'ledger4.tsv'),'w',encoding='utf-8').write('\n'.join(L)+'\n')
# 非 Book 台賬行（Work 層新建候選）
extra=[r for r in rows if '/ledger' not in r[0]]
EX=json.load(open(os.path.join(HERE,'cuny4_worklevel.json')))
for r in extra:
    k=r[0].split('/')[0]+':'+r[1]
    T.append('\t'.join(['—',r[1],'（Work 層候選）',EX.get(k,'保留存疑：'+(r[4] if len(r)>4 else '')),r[0]]))
open(os.path.join(HERE,'TODO4.tsv'),'w',encoding='utf-8').write('\n'.join(T)+'\n')
print(n_ok,len(src)-n_ok,json.dumps(cnt,ensure_ascii=False,indent=1))
