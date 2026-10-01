#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""RH 道（overview#321／#308 B 块）：为阅读首页策展数据顺带补可读书的元数据。

可读集 ＝ book-text 里有 `<Work|Book>/<c1>/<c2>/<c3>/<id>/manifest.json` 的条目。

做两件事（均只动可读集内的条目；干跑为默认，`--apply` 落盘，冪等）：
 1. 作者朝代：`authors[i].dynasty` 为空、而 `entity_id` 指向的 Entity 已有规范 `dynasty` 者，照抄。
    不猜：Entity 无朝代、无 entity_id、朝代不在全库 Work.authors 已用的规范集合里者，只列清单不写。
 2. 分类（仅 44 部「有整理本、缺 classification」的可读 Work，用户 09-30 就此一批开例外，见 overview#321 总管补充）：
    只写有「目录书独立著录」硬依据的（详细分析经验.md §十），按总目词表 classific.json，
    basis／source 照 SCHEMA〈classification〉。依据表见下 CLASS_EVIDENCE，逐条已回查 book-text 里的整理本原文。
    不在表里的一律不填。
 另：核对可读 Book 的 `work_id` 与 Work 一侧 `books[]` 反向引用，缺者补（本轮实测 0 条缺）。

  python3 .claude/qa/rh/backfill_rh.py --text-root ../book-text            # 干跑
  python3 .claude/qa/rh/backfill_rh.py --text-root ../book-text --apply
"""
import argparse, collections, glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))

# 依据表：id → (l1,l2,l3,l4, basis, source, 依据说明)。依据＝另一部目录书对本书的独立著录（题名对得上），其类目经对照表换算。
CLASS_EVIDENCE = {
    # 清史稿藝文志（整理本 Work d59f2mp0flz4）卷 014「別史類」：「七家後漢書二十一卷。」
    # 別史→總目無此類，SCHEMA 歸屬表定「別史暫放 史部／未分類」
    'd59f2ncf8cn5': ('史部', '未分類', '', '', 'B', '清史稿藝文志/別史類',
                     '清史稿藝文志 014 卷別史類「七家後漢書二十一卷」，與本條題名、卷數同；別史類暫放史部／未分類'),
    # 清史稿藝文志卷 011「正史類」：「補晉書藝文志四卷，晉書校文五卷。丁國鈞撰。」（題名、撰人皆對）
    # 正史→史部／紀傳類（SCHEMA 歸屬表）；屬下細目不定，l3 用「未分類」承接
    'd59f2mp2xibm': ('史部', '紀傳類', '未分類', '', 'B', '清史稿藝文志/正史類',
                     '清史稿藝文志 011 卷正史類「補晉書藝文志四卷……丁國鈞撰」，題名、撰人皆合；正史類→史部／紀傳類'),
    # 清史稿藝文志卷 024「目錄類」：「四庫全書總目提要二百卷。乾隆三十七年，紀昀等奉敕撰。」
    # 目錄類與總目詞表同名（A）；屬不定，l3 用「未分類」承接
    'd59dh3vo9af4': ('史部', '目錄類', '未分類', '', 'A', '清史稿藝文志/目錄類',
                     '清史稿藝文志 024 卷目錄類「四庫全書總目提要二百卷……紀昀等奉敕撰」，題名、撰人皆合；另書目答問譜錄（目錄）同列'),
}


def _fmt(raw, d):
    """沿用原文件的缩进与结尾换行（全库个别文件是 1 格缩进），不顺手改格式。"""
    for ind in (2, 1, 4):
        for nl in ('\n', ''):
            if raw == json.dumps(d, ensure_ascii=False, indent=ind) + nl:
                return ind, nl
    return 2, '\n'


_FMT = {}


def load_json(p):
    raw = open(p, encoding='utf-8').read()
    d = json.loads(raw)
    _FMT[p] = _fmt(raw, d)
    return d


def save_json(p, d):
    ind, nl = _FMT.get(p, (2, '\n'))
    with open(p, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=ind) + nl)


def readable_ids(text_root):
    ids = {}
    for p in glob.glob(os.path.join(text_root, '*', '*', '*', '*', '*', 'manifest.json')):
        parts = p.split(os.sep)
        if parts[-6] not in ('Work', 'Book'):
            continue
        ids[parts[-2]] = (parts[-6], load_json(p))
    return ids


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--text-root', required=True)
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--report', help='把清单写到此 json 路径')
    a = ap.parse_args()
    R = readable_ids(a.text_root)
    paths = {}
    for t in ('Work', 'Book'):
        for p in glob.glob(os.path.join(ROOT, t, '*', '*', '*', '*.json')):
            paths[os.path.basename(p).split('-')[0]] = p
    ent_dyn = {}
    for p in glob.glob(os.path.join(ROOT, 'Entity', '*', '*', '*', '*.json')):
        d = load_json(p)
        if d.get('dynasty'):
            ent_dyn[d['id']] = d['dynasty']
    used = collections.Counter()
    for p in glob.glob(os.path.join(ROOT, 'Work', '*', '*', '*', '*.json')):
        for au in load_json(p).get('authors') or []:
            if au.get('dynasty'):
                used[au['dynasty']] += 1
    canon = {k for k, v in used.items() if '(' not in k and '（' not in k}
    rep = {'readable': len(R), 'dynasty_filled': [], 'dynasty_skipped': [], 'class_filled': [], 'work_id_missing': [], 'backref_added': []}
    changed = 0
    for i in sorted(R):
        p = paths[i]
        d = load_json(p)
        dirty = False
        for k, au in enumerate(d.get('authors') or []):
            if au.get('dynasty'):
                continue
            eid = au.get('entity_id')
            dy = ent_dyn.get(eid) if eid else None
            if dy and dy in canon:
                new = {}
                for key, val in au.items():
                    new[key] = val
                    if key == 'role':
                        new['dynasty'] = dy
                if 'dynasty' not in new:
                    new['dynasty'] = dy
                d['authors'][k] = new
                rep['dynasty_filled'].append([i, au.get('name'), eid, dy])
                dirty = True
            else:
                why = '无 entity_id' if not eid else ('Entity 无朝代' if eid not in ent_dyn else f'朝代「{dy}」非规范集合')
                rep['dynasty_skipped'].append([i, au.get('name'), eid, why])
        if R[i][0] == 'Work' and i in CLASS_EVIDENCE and not d.get('classification'):
            l1, l2, l3, l4, basis, source, why = CLASS_EVIDENCE[i]
            d['classification'] = {'l1': l1, 'l2': l2, 'l3': l3, 'l4': l4, 'basis': basis, 'source': source}
            rep['class_filled'].append([i, d['title'], f'{l1}/{l2}/{l3}'.rstrip('/'), basis, source, why])
            dirty = True
        if R[i][0] == 'Book':
            w = d.get('work_id')
            if not w:
                rep['work_id_missing'].append([i, d['title']])
            elif w in paths:
                wd = load_json(paths[w])
                bk = [x if isinstance(x, str) else x.get('id') for x in wd.get('books', [])]
                if i not in bk:
                    rep['backref_added'].append([w, i])
                    if a.apply:
                        wd.setdefault('books', []).append(i)
                        save_json(paths[w], wd)
        if dirty:
            changed += 1
            if a.apply:
                save_json(p, d)
    print(f"可读 {rep['readable']}；改动条目 {changed}；作者朝代补 {len(rep['dynasty_filled'])} 处、未补 {len(rep['dynasty_skipped'])} 处；"
          f"分类补 {len(rep['class_filled'])}；缺 work_id 的可读 Book {len(rep['work_id_missing'])}；补反向引用 {len(rep['backref_added'])}"
          f"（{'已落盘' if a.apply else '干跑'}）")
    if a.report:
        save_json(a.report, rep)


if __name__ == '__main__':
    main()
