import json, os, glob
ROOT='/home/user/book-index'
def _fmt(raw, d):
    for ind in (2,1,4):
        for nl in ('\n',''):
            if raw==json.dumps(d,ensure_ascii=False,indent=ind)+nl: return ind,nl
    return 2,'\n'   # 未知者用主流式
def load(relpath):
    p=os.path.join(ROOT,relpath); raw=open(p).read(); d=json.loads(raw)
    return d, _fmt(raw,d)
def save(relpath, d, fmt):
    ind,nl=fmt
    with open(os.path.join(ROOT,relpath),'w') as f: f.write(json.dumps(d,ensure_ascii=False,indent=ind)+nl)
def update_index(family, key, mutate):
    for f in sorted(glob.glob(os.path.join(ROOT,'index',family,'*.json'))):
        rel=os.path.relpath(f,ROOT); d,fmt=load(rel)
        if key in d:
            mutate(d[key]); save(rel,d,fmt); return rel
    raise KeyError(key)
def addnote(d, note):
    old=(d.get('ai_note') or '')
    d['ai_note']=(old.rstrip()+'\n\n'+note) if old.strip() else note

def drop_index(family, key):
    """自索引刪去一鍵（廢條之用）。update_index 之 mutate 收到的是「值」不是「字典」，
    故刪鍵不能用它——此坑已有道踩過，別再繞。"""
    for f in sorted(glob.glob(os.path.join(ROOT,'index',family,'*.json'))):
        rel=os.path.relpath(f,ROOT); d,fmt=load(rel)
        if key in d:
            del d[key]; save(rel,d,fmt); return rel
    raise KeyError(key)
