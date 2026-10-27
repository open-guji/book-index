"""把簇导出成人读稿（给独立复核用，不含本单元判定理由）。用法：dump.py clusters.json 输出.txt [簇序号...]"""
import json, sys, glob, os
ROOT=os.environ.get('BOOK_INDEX','.')
C=json.load(open(sys.argv[1])); sel=[int(x) for x in sys.argv[3:]] or range(len(C))
idx={os.path.basename(p)[:12]:p for p in glob.glob(ROOT+'/Work/*/*/*/*.json')}
BIDX={}
for p in glob.glob(ROOT+'/index/books/*.json'):
    for bid,b in json.load(open(p)).items():
        if b.get('work_id'): BIDX.setdefault(b['work_id'],[]).append(b)
with open(sys.argv[2],'w') as f:
    for k in sel:
        c=C[k]; f.write(f"\n===== 簇 {k}【{c['key']}】{len(c['ids'])} 条\n")
        for i in c['ids']:
            w=json.load(open(idx[i]))
            import re
            m=re.search(r'所屬叢書記錄 \S+（(.*?)）', w.get('ai_note') or '')
            f.write(f"- {i} 《{w.get('title')}》 撰人:{'；'.join((a.get('dynasty') or '')+(a.get('name') or '')+(a.get('role') or '') for a in w.get('authors',[])) or '无'} 所屬叢書:{m.group(1) if m else '（单行，非叢書子目）'}\n")
            for x in w.get('indexed_by',[])[:4]:
                f.write(f"    著录[{x.get('section','')}] {x.get('title_info','')} | {x.get('author_info','')} | {(x.get('summary') or '')[:220]}\n")
            bs=BIDX.get(i,[])
            if bs: f.write("    Book: "+'；'.join(f"{b.get('edition') or b.get('title')}" for b in bs[:6])+(f" 等{len(bs)}部" if len(bs)>6 else '')+"\n")
