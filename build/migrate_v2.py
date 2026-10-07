#!/usr/bin/env python3
"""schema-v2 遷移腳本：M0（盤點）、M1（補齊舊數據缺口，只增不刪，含 sidecar 方案 B）、M2（關係規範化）。

依據 overview `F-數據結構/F2-7-遷移方案.md` §二、§六（附 sidecar 方案 B）、§九 D。M3 以後不在本腳本。

    python3 build/migrate_v2.py --root <倉> --steps M0            # 盤點＋未識別形態清單（非空則不推進）
    python3 build/migrate_v2.py --root <倉> --steps M0,M1,M2      # 依次跑；每步寫回、出報告
    python3 build/migrate_v2.py --root <倉> --steps M1 --dry-run  # 只出報告，不寫檔

規矩：
- 冪等：已是新格式者不動，重跑零改動。
- **不改任何 `revision`／`revised_at`**（遷移不是作品變化，F2-4-5 §二）；寫回前逐條斷言。
- 保留每個檔原有的縮排與結尾換行（同 .claude/qa/jio.py 判法）。
- M0 不自己打 tag：印出命令，`--tag` 才執行（tag 應打在 main HEAD，由目錄總管定時機）。
- 報告寫到 `<root>/migrate_report/<步>.json`（`--report-dir` 可改）；未識別形態、數據錯逐條列出。
- 失敗（未識別形態非空、斷言不過）退出碼 1，且該步不寫回。
"""
import argparse
import collections
import copy
import json
import os
import re
import subprocess
import sys
import urllib.parse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import v2common as V  # noqa: E402

PROTECTED = ('revision', 'revised_at')
WIKISOURCE = 'https://zh.wikisource.org/wiki/'
WIKISOURCE_UNVERIFIED = '頁名取自舊叢編對照表，未驗證'
PARENT_NOTE = '舊叢編對照表（{coll}）列本書於《{title}》之下'   # parent_work_id 併入 related 之 note

# 已知形態（M0「未識別形態」清單以此為準；遇到新形態先補這裡與處理分支，再跑）
CI_KEYS = {'id', 'volume_index', 'details', 'sub_items', 'group'}
REL_KEYS = {'id', 'work_id', 'relation', 'title', 'note'}
CW_KEYS = {'id', 'work_id', 'title', 'volume_index', 'group', 'note', 'period'}
EW_KEYS = {'work_id', 'role', 'title'}
SIDECAR_ROW_KEYS = {
    'volume_book_mapping.json': {'title', 'book_id', 'work_id', 'volumes', 'section', 'wiki_title', 'sub_items',
                                 'parent_work_id', 'edition', 'expected_volumes', 'found_volumes', 'missing_vols',
                                 'juan_count', 'author', 'dynasty', 'note', 'toc_title'},
    'zhsy_book_mappings.json': {'zhsy_id', 'book_id', 'work_id', 'title', 'section'},
}


# ---------- 倉 ----------
class Repo:
    def __init__(self, root):
        self.root = os.path.abspath(root)
        self.recs, self.sidecar_paths, self.problems = V.load_repo(self.root, keep_raw=True)
        self.by_id = {}
        for t in V.TYPES:
            for i, r in self.recs[t].items():
                self.by_id[i] = r
        self.protected = {i: tuple(copy.deepcopy(r.data.get(k)) for k in PROTECTED) for i, r in self.by_id.items()}
        self.dirty = set()
        self.handformatted = []

    def get(self, typ, i):
        r = self.recs[typ].get(i)
        return r.data if r else None

    def touch(self, i):
        self.dirty.add(i)

    def sidecars(self):
        out = []
        for rel in self.sidecar_paths:
            d = json.load(open(os.path.join(self.root, rel), encoding='utf-8'))
            out.append((rel, d))
        return out

    def check_protected(self):
        bad = [i for i in self.dirty
               if tuple(self.by_id[i].data.get(k) for k in PROTECTED) != self.protected[i]]
        return bad

    def save(self):
        n = 0
        for i in sorted(self.dirty):
            r = self.by_id[i]
            new = V.dump(r.data, r.fmt)
            if new != r.raw:
                with open(os.path.join(self.root, r.path), 'w', encoding='utf-8') as f:
                    f.write(new)
                r.raw = new
                n += 1
        self.dirty.clear()
        return n

    def changed_paths(self):
        return sorted(self.by_id[i].path for i in self.dirty if V.dump(self.by_id[i].data, self.by_id[i].fmt) != self.by_id[i].raw)


def git(root, *args):
    return subprocess.run(['git', '-C', root, *args], capture_output=True, text=True)


# ---------- M0：盤點 ----------
def shape_inventory(repo):
    """逐欄量形態。回傳 (counter, unknown[])。unknown 非空則不推進（F2-7 §八）。"""
    inv = collections.Counter()
    unknown = []

    def bad(i, field, why):
        unknown.append({'id': i, 'field': field, 'shape': why})

    def chk_list(i, field, v):
        if v is None:
            return []
        if not isinstance(v, list):
            bad(i, field, 'not list: ' + type(v).__name__)
            return []
        return v

    for t in V.TYPES:
        for i, r in repo.recs[t].items():
            d = r.data
            if r.dup_keys:
                bad(i, '(file)', 'duplicate keys (rewrite would drop data): ' + ', '.join(sorted(set(r.dup_keys))))
            elif r.fmt is None:
                inv['file: hand-formatted (reformatted to indent 2 if touched)'] += 1
                repo.handformatted.append(r.path)
            for f in ('contained_in',):
                for x in chk_list(i, f'{t}.{f}', d.get(f)):
                    if isinstance(x, str):
                        inv[f'{t}.{f}:str'] += 1
                    elif isinstance(x, dict) and isinstance(x.get('id'), str) and set(x) <= CI_KEYS:
                        inv[f'{t}.{f}:dict'] += 1
                    else:
                        bad(i, f'{t}.{f}', json.dumps(x, ensure_ascii=False)[:200])
            if t == 'Work':
                for x in chk_list(i, 'Work.related_works', d.get('related_works')):
                    if (isinstance(x, dict) and isinstance(V.rel_target(x), str) and set(x) <= REL_KEYS
                            and x.get('relation') in V.KNOWN_RELATIONS):
                        inv['Work.related_works:' + ('id' if 'id' in x else 'work_id')] += 1
                        inv['relation:' + x['relation']] += 1
                    else:
                        bad(i, 'Work.related_works', json.dumps(x, ensure_ascii=False)[:200])
                for x in chk_list(i, 'Work.books', d.get('books')):
                    if isinstance(x, str):
                        inv['Work.books:str'] += 1
                    else:
                        bad(i, 'Work.books', json.dumps(x, ensure_ascii=False)[:200])
                if 'books' in d and d['books'] is None:
                    inv['Work.books:null'] += 1
                for x in chk_list(i, 'Work.authors', d.get('authors')):
                    if not isinstance(x, dict):
                        bad(i, 'Work.authors', json.dumps(x, ensure_ascii=False)[:200])
                    elif x.get('entity_id') is not None and not isinstance(x.get('entity_id'), str):
                        bad(i, 'Work.authors.entity_id', repr(x.get('entity_id')))
                    else:
                        inv['Work.authors:' + ('role' if x.get('role') else 'norole')] += 1
            if t == 'Collection':
                for x in chk_list(i, 'Collection.books', d.get('books')):
                    if isinstance(x, str) or (isinstance(x, dict) and V.ref_id(x, 'book_id', 'id')):
                        inv['Collection.books:' + type(x).__name__] += 1
                    else:
                        bad(i, 'Collection.books', json.dumps(x, ensure_ascii=False)[:200])
                for x in chk_list(i, 'Collection.contained_works', d.get('contained_works')):
                    if isinstance(x, dict) and V.ref_id(x, 'id', 'work_id') and set(x) <= CW_KEYS:
                        inv['Collection.contained_works:dict'] += 1
                    else:
                        bad(i, 'Collection.contained_works', json.dumps(x, ensure_ascii=False)[:200])
            if t == 'Entity':
                for x in chk_list(i, 'Entity.works', d.get('works')):
                    if isinstance(x, dict) and isinstance(x.get('work_id'), str) and set(x) <= EW_KEYS:
                        inv['Entity.works:dict'] += 1
                    else:
                        bad(i, 'Entity.works', json.dumps(x, ensure_ascii=False)[:200])
    for rel, d in repo.sidecars():
        name = os.path.basename(rel)
        keys = SIDECAR_ROW_KEYS.get(name)
        rows = (d.get('books') or d.get('mappings') or []) if isinstance(d, dict) else None
        if keys is None or rows is None:
            bad(rel, '(sidecar)', 'unknown sidecar file')
            continue
        inv['sidecar:' + name] += 1
        for x in rows:
            if not isinstance(x, dict) or not isinstance(x.get('book_id'), str) or not set(x) <= keys:
                bad(rel, '(sidecar row)', json.dumps(x, ensure_ascii=False)[:200])
    for p in repo.problems:
        bad(p['path'], '(load)', p['problem'])
    return dict(sorted(inv.items())), unknown


def m0(repo, args):
    inv, unknown = shape_inventory(repo)
    head = git(repo.root, 'rev-parse', 'HEAD').stdout.strip() or None
    rep = {
        'step': 'M0', 'head': head, 'hand_formatted_files': repo.handformatted,
        'records': {t: len(repo.recs[t]) for t in V.TYPES},
        'sidecars': repo.sidecar_paths,
        'shape_inventory': inv,
        'unknown_shapes': unknown,
        'tag_command': f'git -C {repo.root} tag pre-schema-v2 {head}' if head else None,
    }
    if args.tag and head:
        if git(repo.root, 'rev-parse', '-q', '--verify', 'refs/tags/pre-schema-v2').returncode == 0:
            rep['tag'] = 'exists (not moved)'
        else:
            rep['tag'] = 'created' if git(repo.root, 'tag', 'pre-schema-v2', head).returncode == 0 else 'failed'
    rep['ok'] = not unknown
    return rep


# ---------- 共用 ----------
def volset(v):
    """volume_index／volumes → 冊號集合；不識別者回 None。"""
    if v is None:
        return set()
    if isinstance(v, bool):
        return None
    if isinstance(v, int):
        return {v}
    if isinstance(v, list):
        out = set()
        for x in v:
            s = volset(x)
            if s is None:
                return None
            out |= s
        return out
    if isinstance(v, str):
        out = set()
        for part in re.split(r'[,，、\s]+', v.strip()):
            if not part:
                continue
            part = re.sub(r'\s*[卷冊册]$', '', re.sub(r'^第\s*', '', part))
            m = re.fullmatch(r'(\d+)\s*[-–~～至]\s*(\d+)', part)
            if m:
                out |= set(range(int(m.group(1)), int(m.group(2)) + 1))
            elif part.isdigit():
                out.add(int(part))
            else:
                return None
        return out
    return None


def ci_entry(d, cid):
    """取 d.contained_in 裡指向 cid 的項（及其下標）；str 形回 (idx, None)。"""
    for n, x in enumerate(d.get('contained_in') or []):
        if V.ref_id(x) == cid:
            return n, (x if isinstance(x, dict) else None)
    return None, None


def ci_as_dict(rec_data, idx):
    """把 contained_in[idx] 的 str 形就地升成 dict 形（要往上加屬性時用）。"""
    x = rec_data['contained_in'][idx]
    if isinstance(x, str):
        rec_data['contained_in'][idx] = {'id': x}
    return rec_data['contained_in'][idx]


def add_ci(repo, typ, i, cid, attrs, log, why):
    d = repo.get(typ, i)
    d.setdefault('contained_in', [])
    if d['contained_in'] is None:
        d['contained_in'] = []
    item = {'id': cid}
    item.update(attrs)
    d['contained_in'].append(item)
    repo.touch(i)
    log.append({'id': i, 'add': f'{typ}.contained_in', 'value': item, 'why': why})


# ---------- M1：補齊（只增不刪） ----------
def m1(repo, args):
    rep = {'step': 'M1', 'added': collections.Counter(), 'items': collections.defaultdict(list),
           'data_errors': collections.defaultdict(list), 'manual': collections.defaultdict(list)}
    A, ITEMS, ERR, MAN = rep['added'], rep['items'], rep['data_errors'], rep['manual']
    m1_sidecars(repo, rep)
    # ① 叢編側獨有之成員 → 成員側 contained_in
    for cid, cr in sorted(repo.recs['Collection'].items()):
        c = cr.data
        for x in c.get('books') or []:
            bid = V.ref_id(x, 'book_id', 'id')
            b = repo.get('Book', bid)
            if b is None:
                ERR['Collection.books 指向不存在的 Book'].append([cid, bid])
                continue
            n, _ = ci_entry(b, cid)
            if n is None:
                add_ci(repo, 'Book', bid, cid, {}, ITEMS['①'], 'Collection.books')
                A['① Book.contained_in（叢編側獨有）'] += 1
        for x in c.get('contained_works') or []:
            wid = V.ref_id(x, 'id', 'work_id')
            w = repo.get('Work', wid)
            if w is None:
                ERR['Collection.contained_works 指向不存在的 Work'].append([cid, wid])
                continue
            attrs = {k: x[k] for k in ('volume_index', 'group') if isinstance(x, dict) and x.get(k) not in (None, '')}
            if isinstance(x, dict) and x.get('note'):
                attrs['details'] = x['note']      # 成員關係之附注 → contained_in[].details（與 Book 側同名）
            if isinstance(x, dict) and x.get('period') and x['period'] != w.get('period'):
                MAN['① contained_works.period 與 Work.period 不一'].append(
                    {'work': wid, 'collection': cid, 'collection_side': x['period'], 'work_side': w.get('period')})
            n, item = ci_entry(w, cid)
            if n is None:
                add_ci(repo, 'Work', wid, cid, attrs, ITEMS['①'], 'Collection.contained_works')
                A['① Work.contained_in（叢編側獨有）'] += 1
                continue
            for k, val in attrs.items():
                cur = (item or {}).get(k)
                if cur in (None, ''):
                    item = ci_as_dict(w, n)
                    item[k] = val
                    repo.touch(wid)
                    A[f'① Work.contained_in[].{k}（自 contained_works 補）'] += 1
                    ITEMS['①'].append({'id': wid, 'add': f'Work.contained_in[{cid}].{k}', 'value': val})
                elif cur != val and not (k == 'volume_index' and volset(cur) == volset(val)):
                    MAN['① contained_in 與 contained_works 屬性不一'].append(
                        {'work': wid, 'collection': cid, 'field': k, 'member_side': cur, 'collection_side': val})
    # ③ 按名補 entity_id（Entity.works 有、Work.authors 無）
    ent_works = collections.defaultdict(dict)
    for eid, er in sorted(repo.recs['Entity'].items()):
        for x in er.data.get('works') or []:
            if isinstance(x, dict) and x.get('work_id'):
                ent_works[x['work_id']].setdefault(eid, x.get('role'))
    for wid, ents in sorted(ent_works.items()):
        w = repo.get('Work', wid)
        if w is None:
            for eid in ents:
                ERR['Entity.works 指向不存在的 Work'].append([eid, wid])
            continue
        have = {a.get('entity_id') for a in w.get('authors') or [] if isinstance(a, dict)}
        for eid, role in sorted(ents.items()):
            if eid in have:
                continue
            e = repo.get('Entity', eid)
            names = {e.get('primary_name')} | {n.get('name') if isinstance(n, dict) else n
                                               for n in (e.get('alt_names') or [])}
            names.discard(None)
            cand = [a for a in w.get('authors') or []
                    if isinstance(a, dict) and not a.get('entity_id') and a.get('name') in names]
            if len(cand) == 1:
                cand[0]['entity_id'] = eid
                repo.touch(wid)
                A['③ Work.authors[].entity_id（按名補）'] += 1
                ITEMS['③'].append({'id': wid, 'add': 'authors[].entity_id', 'value': eid, 'name': cand[0].get('name')})
            else:
                same = [a.get('entity_id') for a in w.get('authors') or []
                        if isinstance(a, dict) and a.get('entity_id') and a.get('name') in names]
                why = ('同名作者已繫另一 Entity（疑重複人物，交人物道）' if same else
                       '同名作者不止一位' if len(cand) > 1 else 'Work.authors 無同名者')
                MAN['③ Entity.works 有而 Work.authors 無、按名補不了'].append(
                    {'entity': eid, 'work': wid, 'entity_name': e.get('primary_name'), 'why': why,
                     'authors': [a.get('name') for a in w.get('authors') or [] if isinstance(a, dict)],
                     'other_entity': same[:1] or None})
    # ② authors[].role 缺者由 Entity 側回填
    for wid, wr in sorted(repo.recs['Work'].items()):
        for a in wr.data.get('authors') or []:
            if not isinstance(a, dict) or a.get('role') or not a.get('entity_id'):
                continue
            role = ent_works.get(wid, {}).get(a['entity_id'])
            if role:
                a['role'] = role
                repo.touch(wid)
                A['② Work.authors[].role（由 Entity 回填）'] += 1
                ITEMS['②'].append({'id': wid, 'add': 'authors[].role', 'value': role, 'entity': a['entity_id']})
            else:
                MAN['② role 缺且 Entity 側也無'].append({'work': wid, 'entity': a['entity_id']})
    # ④⑤ 關係 note：規範側（related 為小 id 側）拼接兩側 note
    groups = edge_groups(repo)
    for (s, d, rel), ents in sorted(groups.items()):
        holder = [e for e in ents if e['rec'] == s and e['canon_side']]
        if not holder:
            continue           # 規範側無此項（只有反向形）：M2 落筆時帶 note
        merged = V.merge_notes([e['entry'].get('note') for e in ents if e['canon_side']]
                               + [e['entry'].get('note') for e in ents if not e['canon_side']])
        tgt = holder[0]['entry']
        if merged and tgt.get('note') != merged:
            step = '⑤' if rel in V.SYMMETRIC else '④'
            old = tgt.get('note')
            tgt['note'] = merged
            repo.touch(s)
            A[f'{step} note 併到規範側' + ('（原無 note）' if not old else '（拼接）')] += 1
            ITEMS[step].append({'id': s, 'add': f'related_works[{d},{rel}].note', 'value': merged, 'old': old})
    rep['added'] = dict(sorted(A.items()))
    rep['items'] = {k: v for k, v in sorted(ITEMS.items())}
    rep['data_errors'] = {k: v for k, v in sorted(ERR.items())}
    rep['manual'] = {k: v for k, v in sorted(MAN.items())}
    rep['ok'] = True
    return rep


def edge_groups(repo):
    """規範邊 → 指向它的全部源項（兩側都寫時是兩項）。"""
    g = collections.defaultdict(list)
    for wid, wr in sorted(repo.recs['Work'].items()):
        for r in wr.data.get('related_works') or []:
            t = V.rel_target(r)
            if not t:
                continue
            key = V.canon_edge(wid, t, r.get('relation'))
            g[key].append({'rec': wid, 'entry': r, 'canon_side': key[0] == wid and
                           V.RENAME.get(r.get('relation'), r.get('relation')) == key[2]})
    return g


def m1_sidecars(repo, rep):
    """⓪ sidecar 方案 B（F2-7 §六附）：併入記錄、逐項對勘；sidecar 本身 M3 才刪。"""
    A, ITEMS, ERR, MAN = rep['added'], rep['items'], rep['data_errors'], rep['manual']
    pairs = set()                       # (cid, book_id) 全部 sidecar 成員
    vols = collections.defaultdict(set)
    vol_bad = set()
    parent = {}                         # (work, parent) -> collection title
    checks = collections.Counter()
    for rel, sc in repo.sidecars():
        cid = sc.get('collection_id')
        crec = repo.get('Collection', cid)
        ctitle = (crec or {}).get('title') or cid
        rows = sc.get('books') or sc.get('mappings') or []
        name = os.path.basename(rel)
        for row in rows:
            bid = row['book_id']
            pairs.add((cid, bid))
            b = repo.get('Book', bid)
            if b is None:
                ERR['sidecar 列了不存在的 Book'].append({'sidecar': rel, 'book_id': bid, 'title': row.get('title')})
                continue
            if 'volumes' in row and isinstance(row['volumes'], list) and all(isinstance(v, int) for v in row['volumes']):
                vols[(cid, bid)] |= set(row['volumes'])
            elif 'volumes' in row and not (isinstance(row['volumes'], list) and all(isinstance(v, dict) for v in row['volumes'])):
                vol_bad.add((cid, bid))
            if row.get('zhsy_id') and b.get('zhsy_id') != row['zhsy_id']:
                MAN['⓪ zhsy_id 與 Book.zhsy_id 不一'].append({'book': bid, 'sidecar': row['zhsy_id'], 'book_side': b.get('zhsy_id')})
            if row.get('sub_items'):
                checks['sub_items 字串（sidecar）'] += len(row['sub_items'])
                n, _ = ci_entry(b, cid)
                if n is None:
                    add_ci(repo, 'Book', bid, cid, {}, ITEMS['⓪'], f'sidecar {name}（為放 sub_items）')
                    A['⓪ Book.contained_in（sidecar 成員，記錄側缺）'] += 1
                    n, _ = ci_entry(b, cid)
                item = ci_as_dict(b, n)
                cur = list(item.get('sub_items') or [])
                new = cur + [s for s in row['sub_items'] if isinstance(s, str) and s and s not in cur]
                if new != cur:
                    item['sub_items'] = new
                    repo.touch(bid)
                    A['⓪ Book.contained_in[].sub_items（項）'] += len(new) - len(cur)
                    ITEMS['⓪'].append({'id': bid, 'add': f'contained_in[{cid}].sub_items', 'value': new[len(cur):]})
            if row.get('wiki_title'):
                checks['wiki_title 行（sidecar）'] += 1
                url = WIKISOURCE + row['wiki_title'].strip().replace(' ', '_')
                have = {urllib.parse.unquote(r.get('url') or '') for r in b.get('resources') or [] if isinstance(r, dict)}
                if url in have:
                    checks['wiki_title 已在 resources'] += 1
                    continue
                b.setdefault('resources', [])
                res = {'id': 'wikisource', 'name': '維基文庫', 'url': url, 'types': ['text'],
                       'details': WIKISOURCE_UNVERIFIED}
                b['resources'].append(res)
                repo.touch(bid)
                A['⓪ Book.resources 維基文庫項（自 wiki_title）'] += 1
                ITEMS['⓪'].append({'id': bid, 'add': 'resources[wikisource]', 'value': url})
            if row.get('parent_work_id'):
                checks['parent_work_id 行（sidecar）'] += 1
                parent[(row.get('work_id'), row['parent_work_id'])] = ctitle
            if name == 'volume_book_mapping.json' and 'expected_volumes' in row:
                exp, found = row.get('expected_volumes'), row.get('found_volumes')
                rid = sc.get('resource_id')
                res = [r for r in b.get('resources') or [] if isinstance(r, dict) and r.get('id') == rid]
                det = ' '.join(r.get('details') or '' for r in res)
                if not res:
                    MAN['⓪ 百衲本：Book 無對應 resource'].append({'book': bid, 'resource': rid})
                elif f'{found}/{exp}' not in det:
                    MAN['⓪ 百衲本：details 與 sidecar 冊數不一'].append(
                        {'book': bid, 'resource': rid, 'found': found, 'expected': exp,
                         'missing_vols': row.get('missing_vols'), 'details': det})
                else:
                    checks['百衲本 details 冊數一致'] += 1
        if name == 'volume_book_mapping.json' and isinstance(sc.get('source'), dict) and crec is not None:
            # 武英殿 sidecar 頂層：列出記錄裡沒有的，由人定去處（F2-7 §六附「待核」）
            miss = {k: sc[k] for k in ('source', 'sections', 'stats', 'ai_note', 'total_volumes')
                    if k in sc and json.dumps(sc[k], ensure_ascii=False) not in json.dumps(crec, ensure_ascii=False)}
            if miss:
                MAN['⓪ sidecar 頂層資訊（記錄未見，待定去處）'].append({'sidecar': rel, 'collection': cid, 'fields': miss})
    # 成員對勘：sidecar 的 (叢編, Book) 是否都已在 Book.contained_in；缺者補（只增），列表
    for cid, bid in sorted(pairs):
        b = repo.get('Book', bid)
        if b is None or repo.get('Collection', cid) is None:
            continue
        n, _ = ci_entry(b, cid)
        if n is None:
            vi = sorted(vols.get((cid, bid), ()))
            attrs = {'volume_index': vi[0] if len(vi) == 1 else vi} if vi else {}
            add_ci(repo, 'Book', bid, cid, attrs, ITEMS['⓪'], 'sidecar 成員，記錄側缺')
            A['⓪ Book.contained_in（sidecar 成員，記錄側缺）'] += 1
    # 冊號對勘：只報不改（真正不一致約 2 條，人工核）
    for (cid, bid), vs in sorted(vols.items()):
        b = repo.get('Book', bid)
        _, item = ci_entry(b, cid)
        have = volset((item or {}).get('volume_index'))
        if have is None:
            MAN['⓪ volume_index 形態不識'].append({'book': bid, 'collection': cid, 'volume_index': item.get('volume_index')})
        elif not have:
            MAN['⓪ Book 無 volume_index、sidecar 有冊號'].append({'book': bid, 'collection': cid, 'sidecar': sorted(vs)})
        elif have != vs:
            MAN['⓪ 冊號不一（sidecar 並集 vs volume_index）'].append(
                {'book': bid, 'collection': cid, 'sidecar': sorted(vs), 'volume_index': item.get('volume_index')})
        else:
            checks['冊號一致'] += 1
    for k in sorted(vol_bad):
        MAN['⓪ sidecar volumes 形態不識'].append(list(k))
    # parent_work_id → 該對 related 的 note（不升為 part_of，F2-7 §六附）
    for (wid, pid), ctitle in sorted(parent.items()):
        w, p = repo.get('Work', wid), repo.get('Work', pid)
        if w is None or p is None:
            ERR['parent_work_id：子或母作品不存在'].append({'work': wid, 'parent': pid, 'work_exists': w is not None,
                                                    'parent_exists': p is not None})
            continue
        note = PARENT_NOTE.format(coll=ctitle, title=p.get('title') or pid)
        a, b_ = sorted((wid, pid))
        target = None
        for rec, other in ((a, b_), (b_, a)):
            for r in repo.get('Work', rec).get('related_works') or []:
                if V.rel_target(r) == other and V.RENAME.get(r.get('relation'), r.get('relation')) == 'related':
                    target = (rec, r)
                    break
            if target:
                break
        if not target:
            MAN['⓪ parent_work_id 對無 related 關係'].append({'work': wid, 'parent': pid})
            continue
        rec, r = target
        merged = V.merge_notes([r.get('note'), note])
        if merged != r.get('note'):
            r['note'] = merged
            repo.touch(rec)
            A['⓪ related.note（parent_work_id 說明）'] += 1
            ITEMS['⓪'].append({'id': rec, 'add': f'related_works[{r.get("id")}].note', 'value': note})
        checks['parent_work_id 對（子母皆在、有 related）'] += 1
    rep['sidecar_checks'] = dict(sorted(checks.items()))


# ---------- M2：關係規範化 ----------
def stored_edges(repo):
    """遷移後源檔該存的邊（規範形；M3 刪反向後剩下的就是這些）。"""
    out = set()
    for wid, wr in repo.recs['Work'].items():
        for r in wr.data.get('related_works') or []:
            t = V.rel_target(r)
            if t and V.is_stored_form(wid, t, r.get('relation')):
                out.add(V.canon_edge(wid, t, r.get('relation')))
    return out


def all_edges(repo):
    out = set()
    for wid, wr in repo.recs['Work'].items():
        for r in wr.data.get('related_works') or []:
            t = V.rel_target(r)
            if t:
                out.add((wid, t, V.RENAME.get(r.get('relation'), r.get('relation'))))
    return out


def m2(repo, args, original_edges=None):
    rep = {'step': 'M2', 'added': collections.Counter(), 'items': collections.defaultdict(list),
           'cannot_place': [], 'removed_title': collections.Counter()}
    A, ITEMS = rep['added'], rep['items']
    before = all_edges(repo)
    # 1. 詞表外歸併、舊 work_id 鍵改 id
    for wid, wr in sorted(repo.recs['Work'].items()):
        for r in wr.data.get('related_works') or []:
            if 'id' not in r and r.get('work_id'):
                r['id'] = r.pop('work_id')
                repo.touch(wid)
                A['related_works[].work_id → id'] += 1
            if r.get('relation') in V.RENAME:
                old = r['relation']
                r['relation'] = V.RENAME[old]
                repo.touch(wid)
                A[f'relation {old} → {r["relation"]}'] += 1
                ITEMS['rename'].append({'id': wid, 'target': r.get('id'), 'from': old, 'to': r['relation']})
    # 2. 每條規範邊在規範側落筆（只有反向形者、related 只在大 id 側者）
    for (s, d, rel), ents in sorted(edge_groups(repo).items()):
        if any(e['rec'] == s and e['canon_side'] for e in ents):
            continue
        holder = repo.get('Work', s)
        if holder is None:
            rep['cannot_place'].append({'store_on': s, 'target': d, 'relation': rel,
                                        'why': 'Collection' if repo.get('Collection', s) else 'not in this repo',
                                        'from': sorted({e['rec'] for e in ents})})
            continue
        item = {'id': d, 'relation': rel}
        note = V.merge_notes([e['entry'].get('note') for e in ents])
        if note:
            item['note'] = note
        if holder.get('related_works') is None:
            holder['related_works'] = []
        holder['related_works'].append(item)
        repo.touch(s)
        A[f'規範側落筆：{rel}'] += 1
        ITEMS['place'].append({'id': s, 'add': item, 'from': sorted({e['rec'] for e in ents})})
    # 3. 刪展示副本 title
    for wid, wr in sorted(repo.recs['Work'].items()):
        for r in wr.data.get('related_works') or []:
            if 'title' in r:
                del r['title']
                repo.touch(wid)
                rep['removed_title']['Work.related_works[].title'] += 1
    for cid, cr in sorted(repo.recs['Collection'].items()):
        for x in cr.data.get('contained_works') or []:
            if isinstance(x, dict) and 'title' in x:
                del x['title']
                repo.touch(cid)
                rep['removed_title']['Collection.contained_works[].title'] += 1
    for eid, er in sorted(repo.recs['Entity'].items()):
        for x in er.data.get('works') or []:
            if isinstance(x, dict) and 'title' in x:
                del x['title']
                repo.touch(eid)
                rep['removed_title']['Entity.works[].title'] += 1
    # 斷言：邊集守恆（F2-6 T2「舊有而 build 無＝0」）——只留規範形、build 展開後 ⊇ 舊邊
    after = all_edges(repo)
    built = set()
    for e in stored_edges(repo):
        built |= V.expand_edge(*e)
    placed_out = {(c['store_on'], c['target'], c['relation']) for c in rep['cannot_place']}
    out_expanded = set()
    for e in placed_out:
        out_expanded |= V.expand_edge(*e)
    lost_vs_before = sorted(before - built - out_expanded)
    lost_vs_orig = sorted((original_edges or set()) - built - out_expanded) if original_edges is not None else None
    rep['edge_conservation'] = {
        'edges_before_M2': len(before), 'edges_after_M2_all_entries': len(after),
        'stored_canonical_edges': len(stored_edges(repo)), 'built_edges': len(built),
        'canonical_outside_repo': len(placed_out),
        'old_not_rebuilt_vs_M2_input': len(lost_vs_before), 'sample_vs_M2_input': lost_vs_before[:50],
        'build_adds_missing_reverse': len(built - after),
    }
    if lost_vs_orig is not None:
        rep['edge_conservation']['old_not_rebuilt_vs_M0'] = len(lost_vs_orig)
        rep['edge_conservation']['sample_vs_M0'] = lost_vs_orig[:50]
    rep['added'] = dict(sorted(A.items()))
    rep['items'] = dict(sorted(ITEMS.items()))
    rep['removed_title'] = dict(rep['removed_title'])
    rep['ok'] = not lost_vs_before and not lost_vs_orig
    return rep


# ---------- 主程序 ----------
def write_report(rep_dir, rep):
    os.makedirs(rep_dir, exist_ok=True)
    p = os.path.join(rep_dir, f"{rep['step']}.json")
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(rep, f, ensure_ascii=False, indent=1, sort_keys=True, default=list)
        f.write('\n')
    return p


def summarise(rep):
    s = {'step': rep['step'], 'ok': rep.get('ok')}
    for k in ('records', 'added', 'sidecar_checks', 'removed_title', 'edge_conservation', 'records_changed',
              'files_written', 'protected_violations', 'head', 'tag_command'):
        if k in rep:
            v = rep[k]
            if k == 'edge_conservation':
                v = {a: b for a, b in v.items() if not a.startswith('sample')}
            s[k] = v
    for k in ('unknown_shapes', 'cannot_place'):
        if k in rep:
            s[k + '_count'] = len(rep[k])
    for k in ('data_errors', 'manual'):
        if k in rep:
            s[k] = {a: len(b) for a, b in rep[k].items()}
    return s


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', required=True, help='數據倉根（正式庫或草稿庫）')
    ap.add_argument('--steps', default='M0', help='逗號分隔：M0,M1,M2')
    ap.add_argument('--dry-run', action='store_true', help='不寫回數據檔（報告照寫）')
    ap.add_argument('--report-dir', help='報告目錄（預設 <root>/migrate_report）')
    ap.add_argument('--tag', action='store_true', help='M0 時真的打 tag pre-schema-v2（預設只印命令）')
    ap.add_argument('--git-commit', action='store_true', help='每步寫回後在 root 倉提交一次（只 add 改過的記錄檔）')
    a = ap.parse_args(argv)
    steps = [s.strip().upper() for s in a.steps.split(',') if s.strip()]
    rep_dir = a.report_dir or os.path.join(a.root, 'migrate_report')
    repo = Repo(a.root)
    original_edges = all_edges(repo)
    status = 0
    for st in steps:
        if st == 'M0':
            rep = m0(repo, a)
        elif st == 'M1':
            rep = m1(repo, a)
        elif st == 'M2':
            rep = m2(repo, a, original_edges)
        else:
            ap.error(f'unknown step {st}')
        if st != 'M0':
            bad = repo.check_protected()
            rep['protected_violations'] = bad
            if bad:
                rep['ok'] = False
            paths = repo.changed_paths()
            rep['records_changed'] = len(paths)
            if rep['ok'] and not a.dry_run:
                rep['files_written'] = repo.save()
                if a.git_commit and paths:
                    git(repo.root, 'add', '--', *paths)
                    git(repo.root, 'commit', '-q', '-m', f'schema-v2 {st}（migrate_v2.py）')
            elif a.dry_run:
                repo.dirty.clear()
        write_report(rep_dir, rep)
        print(json.dumps(summarise(rep), ensure_ascii=False, indent=1, default=list))
        if not rep.get('ok'):
            print(f'FAIL at {st}; stop.', file=sys.stderr)
            status = 1
            break
    # dry-run 時記憶體已改不寫回，後一步在此基礎上跑：報告反映「依次跑」的結果
    return status


if __name__ == '__main__':
    sys.exit(main())
