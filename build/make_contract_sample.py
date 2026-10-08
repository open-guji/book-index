#!/usr/bin/env python3
"""從 build 產物抽一份固定的契約樣例包（給網站做 contract 測試，overview#458）。

用法（標準庫即可）：
    python3 build/build_derived.py --out /tmp/b                       # 先跑全量 build
    python3 build/build_derived.py --root ../book-index-draft --ref-root . --out /tmp/bd
    python3 build/make_contract_sample.py --build /tmp/b --draft-build /tmp/bd

產出 `build/contract-sample/`（進 git）：
    entry/<id>.json             抽中的頁面就緒條目（原樣拷貝）
    index/<同 _build/index 佈局>  只留抽中條目的索引行，分片名與 build 相同
    members|catalog|related/<id>/<n>.json、lineage/<id>.json   抽中條目編號最小的一頁
    _hubs.json、classific.json   原樣拷貝
    draft/entry/<id>.json        草稿庫樣例（Book 指正式 Work）
    MANIFEST.json                每條為何入選（覆蓋項）、來源 commit
抽樣規則固定（按 id 排序取第一個符合者＋幾條指名的），同一份源重跑結果逐字節相同。
"""
import argparse
import json
import os
import shutil
import subprocess

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'contract-sample')

# 指名樣例：(id, 為何)
NAMED = [
    ('d59df01avcw0', 'Work：紅樓夢——版本多（_books）、跨作品關係多（_related，含 in/out）、有版本圖'),
    ('8rlcsybg2hhf', 'Collection：叢書（武英殿聚珍版叢書），成員分頁 _members／_member_pages'),
    ('d59f2mp0flz4', 'Work：志書，_member_catalog 分頁'),
    ('hixhd2h9bdye', 'Entity：樞紐人物（他處卡片只寫 {id, h:1}），_works 多'),
]

# 條件樣例：(為何, 條件函數)；按 id 排序取第一個（或前 n 個）符合者
RULES = [
    ('Work：有 _classifications', lambda d: d['type'] == 'work' and d.get('_classifications'), 2),
    ('Work：無分類', lambda d: d['type'] == 'work' and not d.get('_classifications') and d.get('_books'), 1),
    ('Work：_related 超 200 而分頁（_related_pages）', lambda d: d['type'] == 'work' and d.get('_related_pages'), 1),
    ('Work：在叢編裡（_collections 帶 vol／group）', lambda d: d['type'] == 'work' and any('vol' in c or 'group' in c for c in d.get('_collections') or []), 1),
    ('Work：作者繫 Entity 且帶 dates', lambda d: d['type'] == 'work' and any(a.get('dates') for a in d.get('_authors') or []), 1),
    ('Work：被志書著錄（_catalogs，含樞紐 h:1）', lambda d: d['type'] == 'work' and any(c.get('h') for c in d.get('_catalogs') or []), 1),
    ('Work：有整理本（_has_collated）', lambda d: d['type'] == 'work' and d.get('_has_collated'), 1),
    ('Book：_siblings 超 40（_siblings_more／_siblings_total）', lambda d: d['type'] == 'book' and d.get('_siblings_more'), 1),
    ('Book：有源流（_lineage_refs）', lambda d: d['type'] == 'book' and d.get('_lineage_refs'), 1),
    ('Book：被別本用作底本（_derived_by）', lambda d: d['type'] == 'book' and d.get('_derived_by'), 1),
    ('Book：在叢編裡（_collections 帶 vol／sub）', lambda d: d['type'] == 'book' and any('sub' in c for c in d.get('_collections') or []), 1),
    ('Book：有影像（_has_image）', lambda d: d['type'] == 'book' and d.get('_has_image') and not d.get('_collections'), 1),
    ('Collection：合集（成員是 Work）', lambda d: d['type'] == 'collection' and d.get('_member_type') == 'Work', 1),
    ('Collection：成員混合（mixed）', lambda d: d['type'] == 'collection' and d.get('_member_type') == 'mixed', 1),
    ('Collection：有子叢編（_children）', lambda d: d['type'] == 'collection' and d.get('_children'), 1),
    ('Entity：普通人物（非樞紐）', lambda d: d['type'] == 'entity' and 0 < len(d.get('_works') or []) < 5, 2),
    # 專名派生欄（F6-5b，契約 2）
    ('Entity：人物，朝代歧義（_dynasty_candidates）', lambda d: d['type'] == 'entity' and d.get('_dynasty_candidates'), 1),
    ('Entity：朝代，有上級與年號（_ancestors／_reigns）', lambda d: d.get('subtype') == 'dynasty' and d.get('_ancestors') and d.get('_reigns'), 1),
    ('Entity：朝代，有子朝代（_children）', lambda d: d.get('subtype') == 'dynasty' and d.get('_children'), 1),
    ('Entity：年號，有同名（_dynasty／_index_in_reign／_same_name）', lambda d: d.get('subtype') == 'reign' and d.get('_same_name'), 1),
    ('Entity：官署，有下級或合稱成員（_subordinates／_members）', lambda d: d.get('collective_kind') == '官署' and (d.get('_subordinates') or d.get('_members')), 1),
]
DRAFT_RULES = [
    ('草稿 Work：新格式，有 _classifications', lambda d: d['type'] == 'work' and d.get('_classifications'), 2),
    ('草稿 Book：work_id 指正式庫 Work', lambda d: d['type'] == 'book' and (d.get('_work') or {}).get('id', '').startswith('d59'), 2),
    ('草稿 Entity：官職概念條，有各朝具體條（_children）', lambda d: d.get('subtype') == 'office' and d.get('_children'), 1),
    ('草稿 Entity：官職，有複合條（_compounds）', lambda d: d.get('subtype') == 'office' and d.get('_compounds'), 1),
    ('草稿 Entity：官署，有所屬官職（_offices）', lambda d: d.get('collective_kind') == '官署' and d.get('_offices'), 1),
    ('草稿 Entity：地名，有下轄與跨度（_children／_span）', lambda d: d.get('subtype') == 'place' and d.get('_children'), 1),
]


def load_entries(build):
    ed = os.path.join(build, 'entry')
    for f in sorted(os.listdir(ed)):
        with open(os.path.join(ed, f), encoding='utf-8') as fh:
            yield f[:-5], json.load(fh)


def pick(build, rules, named=()):
    chosen = {}
    for i, why in named:
        if os.path.exists(os.path.join(build, 'entry', i + '.json')):
            chosen[i] = [why]
    left = {r[0]: r[2] for r in rules}
    for i, d in load_entries(build):
        for why, cond, _n in rules:
            if left[why] > 0 and i not in chosen and cond(d):
                chosen.setdefault(i, []).append(why)
                left[why] -= 1
        if not any(left.values()):
            break
    missing = [w for w, n in left.items() if n > 0]
    return chosen, missing


def copy(src, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copyfile(src, dst)


def dump(obj, dst):
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'w', encoding='utf-8') as fh:
        json.dump(obj, fh, ensure_ascii=False, indent=2, sort_keys=True)
        fh.write('\n')


def sample_index(build, ids, out):
    base = os.path.join(build, 'index')
    for dp, _dn, fs in os.walk(base):
        for f in sorted(fs):
            p = os.path.join(dp, f)
            with open(p, encoding='utf-8') as fh:
                d = json.load(fh)
            keep = {k: v for k, v in d.items() if k in ids} if isinstance(d, dict) else [x for x in d if isinstance(x, dict) and x.get('id') in ids]
            if keep:
                dump(keep, os.path.join(out, 'index', os.path.relpath(p, base)))


def git_head(root):
    r = subprocess.run(['git', '-C', root, 'rev-parse', 'HEAD'], capture_output=True, text=True)
    return r.stdout.strip()


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--build', required=True, help='正式庫 build 輸出目錄')
    ap.add_argument('--draft-build', help='草稿庫 build 輸出目錄（可省）')
    ap.add_argument('--root', default=os.path.dirname(HERE), help='正式庫倉根（記 commit 用）')
    ap.add_argument('--draft-root', default=os.path.join(os.path.dirname(os.path.dirname(HERE)), 'book-index-draft'))
    a = ap.parse_args()

    chosen, missing = pick(a.build, RULES, NAMED)
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    for i in sorted(chosen):
        copy(os.path.join(a.build, 'entry', i + '.json'), os.path.join(OUT, 'entry', i + '.json'))
        for sub in ('members', 'catalog', 'related'):  # 各拷編號最小的一頁（related 的餘頁從 2 起）
            d = os.path.join(a.build, sub, i)
            if os.path.isdir(d):
                n = min(int(f[:-5]) for f in os.listdir(d) if f.endswith('.json'))
                copy(os.path.join(d, f'{n}.json'), os.path.join(OUT, sub, i, f'{n}.json'))
        p = os.path.join(a.build, 'lineage', i + '.json')
        if os.path.exists(p):
            copy(p, os.path.join(OUT, 'lineage', i + '.json'))
    sample_index(a.build, set(chosen), OUT)
    for f in ('_hubs.json', 'classific.json'):
        copy(os.path.join(a.build, f), os.path.join(OUT, f))

    manifest = {'source': {'book-index': git_head(a.root)}, 'entries': {i: chosen[i] for i in sorted(chosen)},
                'missing_rules': missing}
    if a.draft_build:
        dchosen, dmissing = pick(a.draft_build, DRAFT_RULES)
        for i in sorted(dchosen):
            copy(os.path.join(a.draft_build, 'entry', i + '.json'), os.path.join(OUT, 'draft', 'entry', i + '.json'))
        sample_index(a.draft_build, set(dchosen), os.path.join(OUT, 'draft'))
        manifest['source']['book-index-draft'] = git_head(a.draft_root)
        manifest['draft_entries'] = {i: dchosen[i] for i in sorted(dchosen)}
        manifest['missing_rules'] += dmissing
    dump(manifest, os.path.join(OUT, 'MANIFEST.json'))
    print(f"entry {len(chosen)}，draft {len(manifest.get('draft_entries', {}))}，缺 {manifest['missing_rules']}")


if __name__ == '__main__':
    main()
