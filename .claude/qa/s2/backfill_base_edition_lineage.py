#!/usr/bin/env python3
"""S2c·Book base_edition 吸收之二（overview issue #190）：由 `lineage.derived_from` 機械回填。

`lineage.derived_from[]` 現有 155 個 Book、164 項，形如
`{ref, ref_type, relation, confidence, evidence}`。`ref_type=="book"`（107 項）之 `ref`
即本庫 Book ID，可逕驗其存在且非自指；按 `relation` 機械對映 `role`（見 ROLE_MAP，
三類之外——`合刊`／`混裝本`——非版本源流關係不算候選，`綜合`／`同系延伸`／
`派生（剔田虎王慶+多本配補）`——關係含混判不出角色，入候選）。

`relation` 為「校改／校改後印／校改加評／批校」四種者（13 項），不逕定角色（2026-09-28
協調者驗收①訂正：原一律映成參校，13 項裡約 10 項 `evidence` 明寫是底本，如「以崇禎本…為
底本加評」「在程乙本基礎上」）——改按 `classify_editorial()` 讀 `evidence` 原文之措辭判：
明講「以此為據」（為底本／基礎上／上承／承…而／派生／下啟等）→底本；明講「取來比對」
（參校／參考／對校）→參校；兩者皆未見→判不出，入候選。

`ref_type=="hypothetical"`（57 項，`ref` 為內部假設底本代號，非本庫 ID，`evidence` 無足以
機械摘取之底本名）一律不寫，入候選（`--dry-run` 時寫 `.claude/qa/s2/base_edition-lineage候选.json`，
供另行併入 overview 候選 CSV，不寫本庫）。

用法：
  python3 .claude/qa/s2/backfill_base_edition_lineage.py [--limit N] [--dry-run]

冪等：已有 `base_edition` 者跳過（含前一腳本 backfill_base_edition_dating.py 已寫入者），
可在合流後重跑。
"""
import argparse, collections, glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import jio

ROLE_MAP = {}
for rel in ('翻刻', '同系翻刻', '翻刻補修', '翻刻+改批', '影印', '石印', '拓自', '過錄', '底本',
            '據以抄錄', '據以評', '節選', '刪節', '刪節（學界主流說）', '刪改', '修訂', '增補',
            '截斷（同板印至第百回止）'):
    ROLE_MAP[rel] = '底本'
ROLE_MAP['參校'] = '參校'  # 原始 relation 即明寫「參校」者，直接信之
ROLE_MAP['配補'] = '配補'
NOT_APPLICABLE = {'合刊', '混裝本'}  # 非版本源流關係，不算候選

# 「校改／校改後印／校改加評／批校」四種不逕定角色（協調者驗收①所指：原腳本一律映成參校，
# 十三項有評語（note）明寫底本者）——改按 evidence 原文之措辭逐項判：
# 「以X為底(本)／在X基礎上／上承X／承X而……／X下啟……／X派生……」一類明講「以此為據」者→底本；
# 只有「參校／參考／参照／對校」一類明講「取來比對」者→參校；兩者皆未見→判不出，入候選。
AMBIGUOUS_EDITORIAL_RELATIONS = {'校改', '校改後印', '校改加評', '批校'}
BASE_EVIDENCE_RE = [re.compile(p) for p in
                     (r'為底本', r'為底(?!本)', r'基礎上', r'上承', r'承[^，。]*而', r'翻自', r'祖於',
                      r'經由[^，。]*過渡', r'派生', r'下啟')]
CANJIAO_EVIDENCE_RE = [re.compile(p) for p in (r'參校', r'參考', r'参照', r'對校', r'对校')]


def classify_editorial(evidence):
    """校改類 evidence 原文判角色：回傳 '底本'／'參校'／None（判不出）。"""
    ev = evidence or ''
    if any(p.search(ev) for p in BASE_EVIDENCE_RE):
        return '底本'
    if any(p.search(ev) for p in CANJIAO_EVIDENCE_RE):
        return '參校'
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=None, help='本批最多新增幾個 Book（用於先試批）')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True))
    book_by_id = {}
    for f in files:
        d = json.load(open(f, encoding='utf-8'))
        book_by_id[d['id']] = d

    n_total_books_with_df = n_skipped_done = n_added_books = n_added_items = 0
    n_ambiguous = n_hypothetical = n_not_applicable = n_dangling = n_selfref = 0
    role_dist = collections.Counter()
    candidates = []
    touched = []

    for f in files:
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        lg = d.get('lineage')
        df = (lg or {}).get('derived_from') or []
        if not df:
            continue
        n_total_books_with_df += 1
        if 'base_edition' in d:
            n_skipped_done += 1
            continue
        if a.limit is not None and n_added_books >= a.limit:
            continue
        items = []
        for it in df:
            ref, ref_type, relation = it.get('ref'), it.get('ref_type'), it.get('relation')
            if ref_type == 'hypothetical':
                n_hypothetical += 1
                candidates.append({'id': d['id'], 'title': d.get('title'), 'ref': ref, 'ref_type': ref_type,
                                    'relation': relation, 'evidence': it.get('evidence'), 'reason': 'hypothetical無名可依'})
                continue
            if relation in NOT_APPLICABLE:
                n_not_applicable += 1
                continue
            if relation in AMBIGUOUS_EDITORIAL_RELATIONS:
                role = classify_editorial(it.get('evidence'))
                if role is None:
                    n_ambiguous += 1
                    candidates.append({'id': d['id'], 'title': d.get('title'), 'ref': ref, 'ref_type': ref_type,
                                        'relation': relation, 'evidence': it.get('evidence'),
                                        'reason': 'evidence未明寫底本或參校，判不出角色'})
                    continue
            else:
                role = ROLE_MAP.get(relation)
            if role is None:
                n_ambiguous += 1
                candidates.append({'id': d['id'], 'title': d.get('title'), 'ref': ref, 'ref_type': ref_type,
                                    'relation': relation, 'evidence': it.get('evidence'), 'reason': '關係含混判不出角色'})
                continue
            if ref not in book_by_id:
                n_dangling += 1
                candidates.append({'id': d['id'], 'title': d.get('title'), 'ref': ref, 'ref_type': ref_type,
                                    'relation': relation, 'evidence': it.get('evidence'), 'reason': 'book_id懸空'})
                continue
            if ref == d['id']:
                n_selfref += 1
                continue
            target = book_by_id[ref]
            name = target.get('edition') or target.get('title') or ref
            item = {'role': role, 'book_id': ref, 'name': name, 'source': 'lineage.derived_from'}
            if it.get('evidence'):
                item['note'] = it['evidence']
            items.append(item)
            role_dist[role] += 1
            n_added_items += 1
        if not items:
            continue
        if not a.dry_run:
            dd, fmt = jio.load(rel)
            if 'base_edition' not in dd:
                dd['base_edition'] = items
                jio.save(rel, dd, fmt)
        touched.append(d['id'])
        n_added_books += 1

    print(f'lineage.derived_from 非空之 Book 總數  {n_total_books_with_df}')
    print(f'已有 base_edition（冪等跳過）           {n_skipped_done}')
    print(f'本次新增 base_edition 之 Book 數        {n_added_books}')
    print(f'本次新增 base_edition 項數              {n_added_items}')
    for k, v in sorted(role_dist.items(), key=lambda x: -x[1]):
        print(f'  {k:6s} {v}')
    print(f'ref_type=hypothetical（入候選）         {n_hypothetical}')
    print(f'relation 含混判不出角色（入候選）       {n_ambiguous}')
    print(f'relation 非版本源流關係（不算候選）     {n_not_applicable}')
    print(f'book_id 懸空（入候選）                  {n_dangling}')
    print(f'book_id 自指（略過不寫）                {n_selfref}')
    if a.dry_run:
        print('（--dry-run，未寫盤）')
        if candidates:
            out = os.path.join(ROOT, '.claude', 'qa', 's2', 'base_edition-lineage候选.json')
            json.dump(candidates, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            print(f'候選清單已寫 {out}（{len(candidates)} 條）')
    else:
        print(f'已寫入 {len(touched)} 個 Book 檔')


if __name__ == '__main__':
    main()
