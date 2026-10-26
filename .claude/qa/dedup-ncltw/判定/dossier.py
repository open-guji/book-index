import json,glob,os,collections
from concurrent.futures import ProcessPoolExecutor
BI='/home/user/book-index'
P=json.load(open('pairs.json'))
ids=set(x for p in P for x in p[:2])
def scan(paths):
    r=[]
    for p in paths:
        s=open(p,encoding='utf-8').read()
        if '"work_id"' not in s: continue
        d=json.loads(s)
        if d.get('merged_into'): continue
        if d.get('work_id') in ids:
            r.append((d['work_id'],d.get('title'),d.get('edition') or d.get('version') or d.get('edition_name'),d.get('juan_count'),d.get('publication',{}) if isinstance(d.get('publication'),dict) else d.get('publication'),[x.get('source') for x in d.get('indexed_by') or []][:3],len(d.get('resources') or [])))
    return r
if __name__=='__main__':
    files=glob.glob(BI+'/Book/*/*/*/*.json'); ch=[files[i::32] for i in range(32)]
    books=collections.defaultdict(list)
    with ProcessPoolExecutor(16) as ex:
        for r in ex.map(scan,ch):
            for t in r: books[t[0]].append(t[1:])
    json.dump(books,open('books.json','w'),ensure_ascii=False)
    print(len(books))
