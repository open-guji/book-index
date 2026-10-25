"""4c 复核：国图重配「挂最接近 Work」的 Book，看是否有更准的同题候选 Work。"""
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'feat.py')).read())
import json
RX=re.compile(r'國圖數字古籍重配（[^）]*）新建；國圖著錄題名「([^」]*)」、責任者「([^」]*)」、版本項「([^」]*)」；?([^\n]*)')
bytitle=collections.defaultdict(list)
for wid,w in W.items():
    if w.get('title'): bytitle[norm(w['title'])].append(wid)
def years(s):
    return set(re.findall(r'(?<!\d)(1[0-9]{3})(?!\d)',s or ''))
def exact_year(v):
    m=re.search(r'\[(\d{4})\]',v); return m.group(1) if m else None
def pubyear(b):
    pi=b.get('publication_info') or {}
    y=str(pi.get('year') or ''); return y[:4] if re.fullmatch(r'\d{4}.*',y) else None
NAME=re.compile(r'^\s*(?:\([^)]*\)|（[^）]*）)?\s*')
def nlc_author(s):
    s=NAME.sub('',s or ''); s=re.split(r'[撰著編輯注註校纂述評選譯修等,，;；\s]',s)[0]
    return norm_name(s)
res=collections.Counter(); rows=[]
for b in B.values():
    m=RX.search(b.get('ai_note') or '')
    if not m: continue
    t,au,ver,rest=m.groups()
    kind='同題多書' if '同題多書' in rest else '前輪未定' if '前輪未能確定' in rest else '其他'
    if kind=='其他': continue
    res[kind]+=1
    wid=b.get('work_id'); cands=[c for c in bytitle.get(norm(b.get('title') or t),[]) ]
    if wid not in cands: cands=cands+[wid] if wid in W else cands
    res[kind,'候选数',min(len(cands),4)]+=1
    ey=exact_year(ver); na=nlc_author(au)
    # 各候选得分
    sc={}
    for c in cands:
        f=feat(c)
        ys={pubyear(x) for x in books_of.get(c,[]) if x['id']!=b['id']}-{None}
        s=[]
        if ey and ey in ys: s.append('同年')
        if na and f['fa'] and (na==f['fa'] or na in f['fa'] or f['fa'] in na): s.append('同作者')
        if na and f['fa'] and not s.count('同作者'): s.append('作者不合')
        sc[c]=s
    cur=sc.get(wid,[])
    better=[c for c in cands if c!=wid and (('同作者' in sc[c] and '同作者' not in cur) or ('同年' in sc[c] and '同年' not in cur and '作者不合' not in sc[c]))]
    if better:
        res[kind,'有更好候选']+=1
        rows.append(dict(book=b['id'],kind=kind,title=t,nlc_author=au,ver=ver,cur=wid,cur_score=cur,cands={c:(W[c].get('title'),feat(c)['fa'],feat(c)['dyn'],sc[c]) for c in cands}))
    elif '作者不合' in cur: res[kind,'现挂作者不合且无更好']+=1
for k in sorted(res,key=str): print(k,res[k])
json.dump(rows,open(__import__('os').environ.get('P4WORK','/tmp/p4')+'/4c_better.json','w'),ensure_ascii=False,indent=1)
