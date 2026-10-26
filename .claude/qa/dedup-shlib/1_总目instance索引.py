import json,glob,collections,re,pickle
Z='/home/user/book_index_json/library_data/上海圖書館古籍聯合目錄（中國古籍總目）/'
def iid(u): 
    m=re.search(r'/(instance|work|item)/([0-9a-z]+)',u or ''); return m.group(2) if m else None
inst={}  # zongmu instance id -> dict(work, original, held_sh)
c=collections.Counter()
for f in sorted(glob.glob(Z+'part-*.json')):
    for r in json.load(open(f)):
        w=(r.get('raw') or {}).get('work') or {}
        ins=w.get('insInfo') or {}
        held=set()
        for it in (r.get('raw') or {}).get('items') or []:
            for h in it.get('heldBy') or []: held.add(h.get('label'))
        inst[r['source_record_id']]=dict(work=iid(ins.get('instanceOf')),orig=iid(ins.get('original')),sh='上海圖書館' in held,title=r.get('title'),author=r.get('author'),edition=r.get('edition'))
        c['n']+=1; c['work']+=bool(ins.get('instanceOf')); c['orig']+=bool(ins.get('original')); c['sh']+='上海圖書館' in held
print(c)
pickle.dump(inst,open('zongmu_inst.pkl','wb'))
