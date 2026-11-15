#!/usr/bin/env python3
"""十三经纵向补全·老子：据嚴靈峯《無求備齋老子集成》初編＋續編書目補建库内无的独立著作 Work。用法：newwork.py [--apply] [--limit N]
依据与比对见 ai-team domain/目录与资源/设计/2026-11-十三经纵向补全/老子.md 及 老子-參照書目-無求備齋老子集成.tsv。
数据表见同目录 data.py；建前以异体归一（scan.VARIANTS＋opencc t2s）按题名查重。"""
import os, sys, json, glob, re, opencc
here = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(here, "../../.."))
sys.path.insert(0, os.path.join(BI, ".claude/qa")); sys.path.insert(0, here)
import mintid
from scan import VARIANTS
from data import R, EDO, JP
ROOT = "d59ezkx8dt6o"   # 道德經 李耳（老子原典根）
cc = opencc.OpenCC("t2s")
EX = str.maketrans({'経':'經','註':'注','徴':'徵','辨':'辯','従':'從','与':'與','対':'對','関':'關','両':'兩'})
PUNCT = re.compile(r'[\s·・、，,。．.：:；;「」『』《》〈〉()（）〔〕【】\[\]]')
BR = re.compile(r'（[^（）]*）|\([^()]*\)|〔[^〔〕]*〕|【[^【】]*】|\[[^\[\]]*\]')
def norm(s): return cc.convert(PUNCT.sub('', BR.sub('', s or '')).translate(VARIANTS).translate(EX))
TR = str.maketrans({'徳':'德','説':'說','呉':'吳','録':'錄','懐':'懷','倶':'俱','徴':'徵','絶':'絕','内':'內','戸':'戶','静':'靜','釣':'鈞','顔':'顏','増':'增'})
DYN_PERIOD = {"明":"ming","唐":"sui-tang","南宋":"song","清":"qing","民國":"modern"}
def load_titles(ROW_TSV):
    rows = [l.rstrip("\n").split("\t") for l in open(ROW_TSV, encoding="utf-8")][1:]
    return {n: r[0] for n, r in enumerate(rows, 2)}
def main():
    apply = "--apply" in sys.argv
    lim = int(sys.argv[sys.argv.index("--limit")+1]) if "--limit" in sys.argv else None
    tsv = "/home/user/ai-team/domain/目录与资源/设计/2026-11-十三经纵向补全/老子-參照書目-無求備齋老子集成.tsv"
    T = load_titles(tsv)
    W = {}; ents = {}
    for g in glob.glob(os.path.join(BI, "Work/*/*/*/*.json")):
        d = json.load(open(g, encoding="utf-8"))
        if d.get("merged_into"): continue
        W.setdefault(norm(d["title"]), []).append((d["id"], d["title"], [a.get("name","") for a in d.get("authors",[])]))
    for g in glob.glob(os.path.join(BI, "Entity/*/*/*/*.json")):
        d = json.load(open(g, encoding="utf-8"))
        if d.get("merged_into"): continue
        ents.setdefault(d.get("primary_name",""), []).append((d["id"], d.get("dynasty")))
    todo = []; held = []
    GENERIC = {norm(x) for x in ['老子道德經','老子道德真經','道德經','老子','道德真經','老子經','道德真經註']}
    for row, auth, rel, memo in R:
        t0 = T[row].translate(TR); t = t0.split('：')[0]
        hit = W.get(norm(t), [])
        same = [h for h in hit if any(n and n[:2] in "".join(h[2]) for n in [a[0] for a in auth]) and h[2]]
        if same:
            print("跳過(庫內同題同撰人):", row, t, same); held.append((row, t, "同題同撰人")); continue
        nt = norm(t)
        near = [(k, v) for k, v in W.items() if k != nt and len(k) >= 4 and len(nt) >= 4 and k not in GENERIC and (k in nt or nt in k) and min(len(k), len(nt)) / max(len(k), len(nt)) >= 0.6]
        if near:
            print("搁置(近似題名):", row, t, [(k, v[0][0], v[0][2]) for k, v in near][:3]); held.append((row, t, "近似題名")); continue
        todo.append((row, t, auth, rel, memo + (('；題名原作「%s」，附出部分不另立' % t0) if t != t0 else ''), hit))
    if lim: todo = todo[:lim]
    print("待建", len(todo), "跳過", len(R)-len(todo))
    ids = mintid.mint("Work", "a11-laozi", len(todo)) if apply else ["-"]*len(todo)
    pairs = []
    for (row, t, auth, rel, memo, hit), i in zip(todo, ids):
        pairs += [(i, h[0], '同題異撰人，另立，未辨同書') for h in hit]
        al = []
        for name, dyn, role in auth:
            a = {"name": name, "role": role}
            if dyn: a["dynasty"] = dyn
            ok = {dyn} | ({"中華民國"} if dyn == "民國" else set()) | ({"日本"} if dyn in (EDO, JP) else set()) | ({EDO} if dyn == JP else set())
            c = [e for e in ents.get(name, []) if e[1] in ok]
            if len(c) == 1 and name != "佚名": a["entity_id"] = c[0][0]
            al.append(a)
        dyn0 = auth[0][1]
        note = ("2026-11-15 十三經縱向補全（老子）：據嚴靈峯編《無求備齋老子集成》書目（CiNii 母記錄 https://ci.nii.ac.jp/ncid/BA46443739 、https://ci.nii.ac.jp/ncid/BA55202482 ；"
                "參照表 ai-team domain/目录与资源/设计/2026-11-十三經縱向補全/老子-參照書目-無求備齋老子集成.tsv 第 %d 行）著錄，庫內無同題 Work 而新建。"
                "未覆核：書名、責任者、朝代取自該目，卷數未錄；責任者未逐一考證" % row) + ("；" + memo.lstrip("；") if memo else "") + "。"
        d = {"schema_version": 1, "id": i, "type": "work", "title": t, "authors": al}
        if dyn0: d["dynasty"] = dyn0
        if memo.find("題名原作「")>=0: d["original_title"] = memo.split("題名原作「")[1].split("」")[0]
        d["related_works"] = [{"id": ROOT, "relation": rel}]
        d["ai_note"] = note; d["revision"] = "1.0.0"; d["revised_at"] = "2026-11-15"
        if dyn0 == EDO:
            d["period_upper"] = "qing"; d["period_upper_basis"] = "撰人為日本江戶時代人，與清並行；歧而未決，無論何解皆不晚於 qing"
        elif dyn0 == "朝鮮":
            d["period_upper"] = "qing"; d["period_upper_basis"] = "撰人朴世堂（1629—1703）為朝鮮人，無論何解皆不晚於 qing"
        elif dyn0 in DYN_PERIOD:
            d["period"] = DYN_PERIOD[dyn0]; d["period_basis"] = "據 authors[0].dynasty「%s」" % dyn0
        if not apply:
            print(row, t, [(a["name"], a.get("dynasty"), a.get("entity_id")) for a in al], rel); continue
        p = "Work/%s/%s/%s/%s-%s.json" % (i[-3], i[-2], i[-1], i, t)
        os.makedirs(os.path.join(BI, os.path.dirname(p)), exist_ok=True)
        open(os.path.join(BI, p), "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    bt = {}
    for (row, t, auth, rel, memo, hit), i in zip(todo, ids): bt.setdefault(norm(t), []).append((i, auth[0][0]))
    for k, v in bt.items():
        for x in range(len(v)):
            for y in range(x+1, len(v)): pairs.append((v[x][0], v[y][0], '同批同題異撰人（%s／%s）' % (v[x][1], v[y][1])))
    if apply:
        with open(os.path.join(BI, ".claude/qa/dedup-judged/老子缺口建條.tsv"), "w", encoding="utf-8") as f:
            f.write("# 十三經縱向補全·老子缺口建條：同題異撰人另立，非重出（C）\n")
            for a, b, why in pairs: f.write("%s\t%s\tC\t老子缺口建條：%s\n" % (a, b, why))
    print("新建" if apply else "（dry-run）", len(todo), "搁置/跳過", len(held), "同題異撰人對", len(pairs))
main()
