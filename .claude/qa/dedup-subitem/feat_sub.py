"""子目-甲：同名丛书不同版次的叢書子目 Work 互并——逐组抽特征。
用法：P4WORK=<目录> python3 feat_sub.py <sub.tsv> <部类…>   （sub.tsv 由 ai-team 细拆脚本 subitem_groups.py 产出；P4WORK 下需 cache.pkl 与 census/）"""
import os, sys, json, re, collections
exec(open(os.path.join(os.path.dirname(__file__), '..', 'dedup-part4', 'feat.py')).read())
P = re.compile(r'所屬叢書記錄 (\S+)（([^）]+)）')
NUM = re.compile(r'[一二三四五六七八九十百千〇零]+(種|卷|集|冊)|不分卷')
def parent(w):
    m = P.search(w.get('ai_note') or '')
    return (m.group(1), m.group(2), norm(NUM.sub('', m.group(2)))) if m else None
def tinfo(w):
    return [i.get('title_info') or '' for i in w.get('indexed_by') or []]
def authors(w):
    return [(a.get('name'), a.get('dynasty'), a.get('role'), a.get('entity_id')) for a in w.get('authors') or [] if isinstance(a, dict)]
def colinfo(cid):
    c = C.get(cid)
    if not c: return None
    a = [x for x in c.get('authors') or [] if isinstance(x, dict)]
    return dict(id=cid, title=c.get('title'), author=a[0].get('name') if a else '', dyn=a[0].get('dynasty') if a else '', role=a[0].get('role') if a else '')
def rows(subtsv, buleis):
    for r in open(subtsv):
        b, cat, k, key, ids, par = r.rstrip('\n').split('\t')
        if k != '同名丛书子目' or b not in buleis: continue
        yield b, cat, key, ids.split(',')
def member(i):
    w = W[i]; f = feat(i); p = parent(w)
    return dict(id=i, title=w.get('title'), authors=authors(w), juan=f['juan'], bjuan=sorted(f['bjuan']), nbooks=f['nbooks'],
                eds=f['eds'], tinfo=tinfo(w), secs=sorted(f['secs']), parent=p, col=colinfo(p[0]) if p else None,
                bookcols=[c[0] for c in f['cols']], bookcolinfo=[colinfo(c[0]) for c in f['cols']], src=sorted(f['src']), sources=sorted(x for x in f['sources'] if x))
if __name__ == '__main__':
    out = []
    for b, cat, key, ids in rows(sys.argv[1], sys.argv[2:]):
        out.append(dict(bulei=b, cat=cat, key=key, members=[member(i) for i in ids if i in W]))
    json.dump(out, open(os.environ['P4WORK'] + '/feat_sub.json', 'w'), ensure_ascii=False, indent=1)
    print(len(out), '组')
