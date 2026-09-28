#!/usr/bin/env python3
"""S2c·Book base_edition 吸收之一（overview issue #190）：由 `dating.based_on` 機械回填。

`dating.based_on` 現有 273 條，形如 `{era, reign, year?, relation}`——只記底本之年代與關係，
不記其名。本腳本把 `relation` 映成 `base_edition[].role`（翻刻／影印／傳鈔→底本，配補→配補），
`name` 則從 `Book.edition` 原文機械切出：搜該關係對應之動詞，唯一一見者取其後之文字；
「百衲本二十四史」一類（`edition` 作「百衲本·某本」）另按其固定格式切分，可同時得底本、
配補兩項。動詞不唯一、切不出、或切得結果過短（僅剩「本」字等無實質內容）者不寫，
計入候選清單（`--dry-run` 時寫 `.claude/qa/s2/base_edition-dating候选.json`，供另行併入
overview 候選 CSV，不寫本庫）。

用法：
  python3 .claude/qa/s2/backfill_base_edition_dating.py [--limit N] [--dry-run]

冪等：已有 `base_edition` 者跳過，可在合流後重跑。
"""
import argparse, collections, glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import jio

VERB_GROUPS = {
    '翻刻': ['覆刻', '覆刊', '翻刻', '翻刊', '重刊', '重刻', '重雕', '翻雕', '重摹'],
    '影印': ['影鈔', '影印', '景印', '影刊', '景鈔', '摹印'],
    '傳鈔': ['傳鈔', '傳抄'],
    '配補': ['配補'],
}
ROLE_MAP = {'翻刻': '底本', '影印': '底本', '傳鈔': '底本', '配補': '配補'}
SUPP_RE = re.compile(r'(?:闕卷|原闕[^以]*|逸[^以]*)以(.+?)配補')
JUNK = {'本', '之本', '印本', ''}


def clean(s):
    s = s.strip('，,。、()（）[]【】 \t')
    # 動詞本身或作「傳鈔本／影鈔本」之類自述複合詞，「本」字歸自述而非底本之名的起首，
    # 如「傳鈔本元皇慶壬子…刊本」实为「傳鈔本」+「元皇慶…刊本」，不切則「本」字誤入底本名。
    if len(s) > 1 and s[0] == '本':
        s = s[1:]
    return s


def split_embedded_supplement(name):
    """名內若含「(闕卷／原闕…)以Y配補」或裸「X配補Y」，拆成 (底本名, 配補名)；
    無此結構回傳 (name, None)——如「清康熙五十四年武英殿刊配補影鈔本」一類配補動詞
    後未接可用之名者，(None 由呼叫端之長度／JUNK 檢查擋下)。"""
    m = SUPP_RE.search(name)
    if m:
        return clean(name[:m.start()]), clean(m.group(1))
    if '配補' in name:
        idx = name.index('配補')
        left, right = clean(name[:idx]), clean(name[idx + 2:])
        if len(left) >= 2 and len(right) >= 2 and left not in JUNK and right not in JUNK:
            return left, right
    return name, None


def extract(edition_text, relation):
    """回傳 base_edition 項之列表（可空）：[{role, name}, ...]。"""
    verbs = VERB_GROUPS.get(relation, [])
    pat = re.compile('|'.join(re.escape(v) for v in verbs))
    matches = list(pat.finditer(edition_text))
    if len(matches) == 1:
        name = clean(edition_text[matches[0].end():])
        if len(name) >= 2 and name not in JUNK:
            base, supp = split_embedded_supplement(name)
            out = []
            if len(base) >= 2 and base not in JUNK:
                out.append({'role': ROLE_MAP[relation], 'name': base})
            if supp:
                out.append({'role': '配補', 'name': supp})
            if out:
                return out
    if edition_text.startswith('百衲本'):
        m = SUPP_RE.search(edition_text)
        if m:
            supp, base_part = clean(m.group(1)), edition_text[:m.start()]
        else:
            supp, base_part = None, edition_text
        base = clean(re.sub(r'^百衲本[·・]?', '', base_part))
        out = []
        if len(base) >= 2 and base not in JUNK:
            out.append({'role': '底本', 'name': base})
        if supp and len(supp) >= 2 and supp not in JUNK:
            out.append({'role': '配補', 'name': supp})
        if out:
            return out
    return []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--limit', type=int, default=None, help='本批最多新增幾個 Book（用於先試批）')
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    files = sorted(glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True))
    # 同 work_id 之 Book 清單，供 book_id 掛連試比對
    work_books = collections.defaultdict(list)
    for f in files:
        d = json.load(open(f, encoding='utf-8'))
        work_books[d.get('work_id')].append((d['id'], d.get('edition') or ''))

    n_total_based_on = n_skipped_done = n_added_books = n_added_items = n_failed = n_matched_id = 0
    role_dist = collections.Counter()
    fail_list = []
    touched = []

    for f in files:
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        dt = d.get('dating')
        if not (isinstance(dt, dict) and 'based_on' in dt):
            continue
        n_total_based_on += 1
        if 'base_edition' in d:
            n_skipped_done += 1
            continue
        if a.limit is not None and n_added_books >= a.limit:
            continue
        relation = (dt.get('based_on') or {}).get('relation')
        edition_text = d.get('edition') or ''
        items = extract(edition_text, relation)
        if not items:
            n_failed += 1
            fail_list.append({'id': d['id'], 'title': d.get('title'), 'work_id': d.get('work_id'),
                               'edition': edition_text, 'dating_based_on': dt.get('based_on')})
            continue
        for item in items:
            item['source'] = 'dating.based_on+edition切分'
            if len(item['name']) >= 4:
                sibs = [s for s in work_books.get(d.get('work_id'), []) if s[0] != d['id'] and s[1] == item['name']]
                if len(sibs) == 1:
                    item['book_id'] = sibs[0][0]
                    n_matched_id += 1
            role_dist[item['role']] += 1
            n_added_items += 1
        if not a.dry_run:
            dd, fmt = jio.load(rel)
            if 'base_edition' not in dd:
                dd['base_edition'] = items
                jio.save(rel, dd, fmt)
        touched.append(d['id'])
        n_added_books += 1

    print(f'dating.based_on 總數              {n_total_based_on}')
    print(f'已有 base_edition（冪等跳過）      {n_skipped_done}')
    print(f'本次新增 base_edition 之 Book 數   {n_added_books}')
    print(f'本次新增 base_edition 項數         {n_added_items}')
    for k, v in sorted(role_dist.items(), key=lambda x: -x[1]):
        print(f'  {k:6s} {v}')
    print(f'掛上 book_id 之項數                {n_matched_id}')
    print(f'切分失敗（入候選）                 {n_failed}')
    if a.dry_run:
        print('（--dry-run，未寫盤）')
        if fail_list:
            out = os.path.join(ROOT, '.claude', 'qa', 's2', 'base_edition-dating候选.json')
            json.dump(fail_list, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=2)
            print(f'候選清單已寫 {out}（{len(fail_list)} 條）')
    else:
        print(f'已寫入 {len(touched)} 個 Book 檔')


if __name__ == '__main__':
    main()
