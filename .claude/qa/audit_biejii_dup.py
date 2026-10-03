import json, pathlib
root="/home/sheldon/book-index"
works={}
for p in pathlib.Path(root).glob("Work/*/*/*/*.json"):
    try:
        d=json.loads(p.read_text(encoding='utf-8'))
        if d.get('merged_into'): continue
        works[d['id']]=d
    except: pass
print(f"works {len(works)}")
# Broader official check: any indexed_by source contains 補 and (晉 or 魏)
def is_official(w):
    ibs=w.get('indexed_by') or []
    if not ibs: return False
    for ib in ibs:
        src=ib.get('source') or ""
        if "補" in src and ("晉" in src or "魏" in src):
            return True
    return False

by_title={}
for w in works.values():
    by_title.setdefault(w['title'], []).append(w)

offices=["散騎常侍","散骑常侍","太常","光禄勋","侍中","尚书","中书","秘书","太尉","司徒","司空","大将军","骠骑将军","车骑将军","卫将军","征西将军","安西将军","镇西将军","龙骧将军","宁朔将军","建威将军","振威将军","安北将军","冠军将军","抚军将军","辅国将军","镇军将军","征虏将军","安国将军","平西将军","太守","刺史","尚书令","中书令","侍郎","黄门侍郎","散骑侍郎","给事中","御史中丞","廷尉","大鸿胪","少府","大司农","司隶校尉","河南尹","丹阳尹","征士","处士","徵士","隠士"]
offices_sorted=sorted(offices, key=len, reverse=True)
def strip_official(title):
    for off in offices_sorted:
        if title.startswith(off):
            return title[len(off):]
    return None

auto=[]
entity_mismatch=[]
review=[]
for wid,w in works.items():
    if not is_official(w): continue
    base=strip_official(w['title'])
    if not base or base==w['title']: continue
    if base not in by_title: continue
    for cand in by_title[base]:
        if cand['id']==wid: continue
        a1=set(a.get('name') for a in (w.get('authors') or []) if a.get('name'))
        a2=set(a.get('name') for a in (cand.get('authors') or []) if a.get('name'))
        if not a1 or not a2: continue
        if a1!=a2: continue
        e1=set(a.get('entity_id') for a in (w.get('authors') or []) if a.get('entity_id'))
        e2=set(a.get('entity_id') for a in (cand.get('authors') or []) if a.get('entity_id'))
        if e1!=e2:
            entity_mismatch.append((w,cand))
            continue
        auto.append((w,cand))
        break

print(f"auto {len(auto)}, entity_mismatch {len(entity_mismatch)}")
for off,nor in auto[:10]:
    print(f"AUTO {off['title']} -> {nor['title']}")
import json as js
out={"auto": [{"drop": off['id'], "drop_title": off['title'], "keeper": nor['id']} for off,nor in auto],
     "entity_mismatch": [{"drop": off['id'], "keeper": nor['id']} for off,nor in entity_mismatch]}
pathlib.Path("/tmp/_biejii_dup2.json").write_text(js.dumps(out, ensure_ascii=False, indent=2), encoding='utf-8')
print("saved /tmp/_biejii_dup2.json")
