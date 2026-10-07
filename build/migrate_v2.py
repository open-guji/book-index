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
DEFAULT_ROLE = '撰'
ORDER_TAG = '叢編原序 '          # 叢編側 contained_works[].volume_index 與成員側不一時，記入成員 details 的前綴（build 據以排序）
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
        self.extra = {}
        self.handformatted = []
        self.head0 = git(self.root, 'rev-parse', '--short', 'HEAD').stdout.strip() or '（非 git 倉）'

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

    def put_file(self, rel, content):
        """非記錄檔（分類檔等）的寫入；content=None 為刪除。與記錄一起在 save() 時落盤。"""
        p = os.path.join(self.root, rel)
        old = open(p, encoding='utf-8').read() if os.path.exists(p) else None
        if old != content:
            self.extra[rel] = content
        else:
            self.extra.pop(rel, None)

    def save(self):
        n = 0
        for rel, content in sorted(self.extra.items()):
            p = os.path.join(self.root, rel)
            if content is None:
                if os.path.exists(p):
                    os.remove(p)
            else:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, 'w', encoding='utf-8') as f:
                    f.write(content)
            n += 1
        self.extra.clear()
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
        return sorted([self.by_id[i].path for i in self.dirty
                       if V.dump(self.by_id[i].data, self.by_id[i].fmt) != self.by_id[i].raw] + list(self.extra))


def load_promotions(root):
    p = os.path.join(root, 'promotions.json')
    if not os.path.exists(p):
        return {}
    out = {}
    for k, v in (json.load(open(p, encoding='utf-8')).get('promotions') or {}).items():
        out[k] = v if isinstance(v, str) else (v.get('to') or v.get('official_id') or v.get('id')) if isinstance(v, dict) else None
    return out


def git(root, *args, stdin=None):
    return subprocess.run(['git', '-C', root, *args], capture_output=True, text=True, input=stdin)


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
    for t, fields in V.SYMMETRIC_LISTS.items():
        for i, r in repo.recs[t].items():
            for f in fields:
                for x in chk_list(i, f'{t}.{f}', r.data.get(f)):
                    if isinstance(x, str) or (isinstance(x, dict) and (sym_id(x) or x.get('work_id'))):
                        inv[f'{t}.{f}:' + type(x).__name__] += 1
                    else:
                        bad(i, f'{t}.{f}', json.dumps(x, ensure_ascii=False)[:200])
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
                    if k == 'volume_index':
                        # 目錄總管 10-07：成員側為準；叢編側序號別丟，記進 details，build 據以排序
                        item = ci_as_dict(w, n)
                        tag = f'{ORDER_TAG}{val}'
                        if tag not in (item.get('details') or ''):
                            item['details'] = '；'.join(x for x in (item.get('details'), tag) if x)
                            repo.touch(wid)
                            A['① 叢編側序號記入 contained_in[].details'] += 1
                            ITEMS['①'].append({'id': wid, 'add': f'contained_in[{cid}].details', 'value': tag})
                    else:
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
                if why == 'Work.authors 無同名者' and not w.get('authors') and e.get('subtype', 'people') == 'people':
                    # 目錄總管 10-07：Work.authors 為空 → 按 Entity 側補入
                    au = {'name': e.get('primary_name'), 'role': role or DEFAULT_ROLE, 'entity_id': eid}
                    if e.get('dynasty'):
                        au['dynasty'] = e['dynasty']
                    au['note'] = '據 Entity.works 補入（schema-v2 遷移 M1）'
                    w['authors'] = [au]
                    repo.touch(wid)
                    A['③ Work.authors 為空、按 Entity.works 補入作者'] += 1
                    ITEMS['③'].append({'id': wid, 'add': 'authors[0]', 'value': au})
                    continue
                if why == 'Work.authors 無同名者':
                    why += '（Work.authors ' + ('非空' if w.get('authors') else f'為空，但 Entity 非人物：{e.get("subtype")}') + '）'
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
    # ②b 仍缺者機械補「撰」（目錄總管 10-07 定；build 原本即以「撰」兜底，等於把兜底落成數據）
    for wid, wr in sorted(repo.recs['Work'].items()):
        for a in wr.data.get('authors') or []:
            if isinstance(a, dict) and not a.get('role'):
                a['role'] = DEFAULT_ROLE
                repo.touch(wid)
                k = '有 entity_id、Entity 側也無' if a.get('entity_id') else '無 entity_id'
                A[f'②b Work.authors[].role 機械補「撰」（{k}）'] += 1
                ITEMS['②b'].append({'id': wid, 'add': 'authors[].role', 'value': DEFAULT_ROLE, 'name': a.get('name'),
                                    'entity': a.get('entity_id')})
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


def resolve_book(repo, row, cid, zh_index, members_of):
    """sidecar 列的 book_id 不在庫：按 zhsy_id（唯一）或「題名＋同叢編成員」（唯一）找現 id（目錄總管 10-07）。"""
    if row.get('zhsy_id') and len(zh_index.get(row['zhsy_id'], ())) == 1:
        return zh_index[row['zhsy_id']][0], 'zhsy_id'
    t = row.get('title')
    if t:
        cand = [i for i in members_of.get(cid, ()) if (repo.get('Book', i) or {}).get('title') == t]
        if len(cand) == 1:
            return cand[0], '題名＋同叢編'
    return None, None


def m1_sidecars(repo, rep):
    """⓪ sidecar 方案 B（F2-7 §六附）：併入記錄、逐項對勘；sidecar 本身 M3 才刪。"""
    A, ITEMS, ERR, MAN = rep['added'], rep['items'], rep['data_errors'], rep['manual']
    pairs = set()                       # (cid, book_id) 全部 sidecar 成員
    vols = collections.defaultdict(set)
    vol_bad = set()
    parent = {}                         # (work, parent) -> collection title
    checks = collections.Counter()
    zh_index = collections.defaultdict(list)
    members_of = collections.defaultdict(set)
    for bid_, br in sorted(repo.recs['Book'].items()):
        if br.data.get('zhsy_id'):
            zh_index[br.data['zhsy_id']].append(bid_)
        for x in br.data.get('contained_in') or []:
            if V.ref_id(x):
                members_of[V.ref_id(x)].add(bid_)
    for rel, sc in repo.sidecars():
        cid = sc.get('collection_id')
        crec = repo.get('Collection', cid)
        ctitle = (crec or {}).get('title') or cid
        rows = sc.get('books') or sc.get('mappings') or []
        name = os.path.basename(rel)
        for row in rows:
            bid = row['book_id']
            b = repo.get('Book', bid)
            if b is None:
                nb, how = resolve_book(repo, row, cid, zh_index, members_of)
                if nb is None:
                    ERR['sidecar 列了不存在的 Book'].append({'sidecar': rel, 'book_id': bid, 'title': row.get('title'),
                                                          'zhsy_id': row.get('zhsy_id')})
                    continue
                ITEMS['⓪ 改號'].append({'sidecar': rel, 'old': bid, 'new': nb, 'by': how, 'title': row.get('title')})
                A[f'⓪ sidecar 舊 book_id 改指現 id（{how}）'] += 1
                bid, b = nb, repo.get('Book', nb)
            pairs.add((cid, bid))
            if 'volumes' in row and isinstance(row['volumes'], list) and all(isinstance(v, int) for v in row['volumes']):
                vols[(cid, bid)] |= set(row['volumes'])
            elif 'volumes' in row and not (isinstance(row['volumes'], list) and all(isinstance(v, dict) for v in row['volumes'])):
                vol_bad.add((cid, bid))
            if row.get('zhsy_id') and not b.get('zhsy_id'):
                b['zhsy_id'] = row['zhsy_id']             # Book 側空 → 補（目錄總管 10-07）
                repo.touch(bid)
                A['⓪ Book.zhsy_id（自 sidecar 補）'] += 1
                ITEMS['⓪'].append({'id': bid, 'add': 'zhsy_id', 'value': row['zhsy_id']})
            elif row.get('zhsy_id') and b.get('zhsy_id') != row['zhsy_id']:
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
                wid_ = row.get('work_id')
                if repo.get('Work', wid_) is None and b.get('work_id') and repo.get('Work', b['work_id']):
                    ITEMS['⓪ 改號'].append({'sidecar': rel, 'old': wid_, 'new': b['work_id'], 'by': 'Book.work_id'})
                    A['⓪ parent_work_id 子作品改指現 id（經 Book.work_id）'] += 1
                    wid_ = b['work_id']
                parent[(wid_, row['parent_work_id'])] = ctitle
            if name == 'volume_book_mapping.json' and 'expected_volumes' in row:
                exp, found = row.get('expected_volumes'), row.get('found_volumes')
                rid = sc.get('resource_id')
                res = [r for r in b.get('resources') or [] if isinstance(r, dict) and r.get('id') == rid]
                det = ' '.join(r.get('details') or '' for r in res)
                found_vols = [{k: v for k, v in x.items() if k not in ('status', 'ntul_id')}
                              for x in row.get('volumes') or [] if isinstance(x, dict) and x.get('status') == 'found']
                if not res and found_vols:            # sidecar 有鏈接 → 生成 resource（目錄總管 10-07）
                    url = found_vols[0].get('tw_url') or found_vols[0].get('url') or found_vols[0].get('wiki_url')
                    b.setdefault('resources', []).append({
                        'id': rid, 'name': sc.get('resource_name') or rid, 'url': url,
                        'details': f'共{found}/{exp}冊（據舊叢編對照表補）', 'volumes': found_vols, 'types': ['image']})
                    repo.touch(bid)
                    A[f'⓪ Book.resources[{rid}]（自 sidecar 生成）'] += 1
                    ITEMS['⓪'].append({'id': bid, 'add': f'resources[{rid}]', 'value': url})
                elif not res:
                    MAN['⓪ 百衲本：Book 無對應 resource、sidecar 也無鏈接（交資源道）'].append(
                        {'book': bid, 'resource': rid, 'expected': exp})
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
        elif not have or have != vs:
            # 目錄總管 10-07：缺者自 sidecar 補；不一者取並集
            u = sorted(have | vs)
            n, _ = ci_entry(b, cid)
            item = ci_as_dict(b, n)
            old = item.get('volume_index')
            item['volume_index'] = u[0] if len(u) == 1 else u
            repo.touch(bid)
            k = '⓪ volume_index 自 sidecar 補' if not have else '⓪ volume_index 取 sidecar 與記錄之並集'
            A[k] += 1
            ITEMS['⓪'].append({'id': bid, 'add': f'contained_in[{cid}].volume_index', 'value': item['volume_index'],
                               'old': old})
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
    # 2b. 對稱 id 列表：related_collections 的對象轉 id 字串（type／note 等逐條列報告）；小 id 側補寫
    m2_symmetric_lists(repo, rep)
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


def sym_id(x):
    """對稱列表之項 → 對方 id（str，或 related_collections 的舊對象形）。"""
    if isinstance(x, str):
        return x
    if isinstance(x, dict):
        return x.get('collection_id') or x.get('book_id') or x.get('id')
    return None


def m2_symmetric_lists(repo, rep):
    A, ITEMS = rep['added'], rep['items']
    rep.setdefault('symmetric_object_info', [])
    rep.setdefault('symmetric_unconvertible', [])
    for t, fields in V.SYMMETRIC_LISTS.items():
        for rid, rr in sorted(repo.recs[t].items()):
            for f in fields:
                lst = rr.data.get(f)
                if not isinstance(lst, list):
                    continue
                for n, x in enumerate(list(lst)):
                    if isinstance(x, str):
                        continue
                    tid = sym_id(x)
                    if not tid:
                        rep['symmetric_unconvertible'].append({'record': rid, 'field': f, 'item': x})
                        continue
                    extra = {k: v for k, v in x.items() if k not in ('collection_id', 'book_id', 'id', 'title') and v}
                    if extra:
                        # 目錄總管 10-07：併進本叢編的 description（不增欄位），一條一行
                        tt = (repo.get(t, tid) or {}).get('title') or x.get('title') or tid
                        line = f'與《{tt}》（{tid}）關係：' + '；'.join(
                            [str(extra.pop('type'))] if 'type' in extra else []) + ''.join(
                            f'；{v}' if k == 'note' else f'；{k}={v}' for k, v in extra.items())
                        desc = rr.data.get('description')
                        if not isinstance(desc, dict):
                            desc = rr.data['description'] = {'text': desc or ''} if not isinstance(desc, dict) else desc
                        if line not in (desc.get('text') or ''):
                            desc['text'] = ((desc.get('text') or '').rstrip() + '\n' + line).lstrip('\n')
                        rep['symmetric_object_info'].append({'record': rid, 'field': f, 'target': tid,
                                                             'dropped': {k: v for k, v in x.items() if k not in
                                                                         ('collection_id', 'book_id', 'id', 'title')},
                                                             'merged_into': 'description.text', 'line': line})
                    lst[n] = tid
                    repo.touch(rid)
                    A[f'{t}.{f}：對象 → id 字串'] += 1
    # 小 id 側補寫（同型記錄才補；Collection.related_books 指 Book，非對稱同型，跳過）
    for t, fields in V.SYMMETRIC_LISTS.items():
        for f in fields:
            tgt_type = 'Collection' if f == 'related_collections' else 'Book'
            if tgt_type != t:
                continue
            for rid, rr in sorted(repo.recs[t].items()):
                for tid in list(rr.data.get(f) or []):
                    if not isinstance(tid, str) or tid >= rid:
                        continue
                    other = repo.get(t, tid)
                    if other is None:
                        rep['cannot_place'].append({'store_on': tid, 'target': rid, 'relation': f'{t}.{f}',
                                                    'why': 'not in this repo', 'from': [rid]})
                        continue
                    if rid not in [sym_id(y) for y in other.get(f) or []]:
                        if other.get(f) is None:
                            other[f] = []
                        other[f].append(rid)
                        repo.touch(tid)
                        A[f'{t}.{f}：小 id 側落筆'] += 1
                        ITEMS['place'].append({'id': tid, 'add': {f: rid}, 'from': [rid]})


def sym_pairs(repo):
    out = set()
    for t, fields in V.SYMMETRIC_LISTS.items():
        for f in fields:
            for rid, rr in repo.recs[t].items():
                for x in rr.data.get(f) or []:
                    tid = sym_id(x)
                    if tid:
                        out.add((t, f, min(rid, tid), max(rid, tid)))
    return out


# ---------- M3：刪派生與反向（F2-7 §二 M3；sidecar 留到 M6，`_has_text`／`_has_collated` 留作源欄） ----------
M3_DROP = {
    'Work': ('books', '_edition_count', '_has_image', 'has_image'),
    'Book': ('_has_image', 'has_image'),
    'Collection': ('books', 'contained_works', '_member_count', '_member_type', '_has_image', 'has_image'),
    'Entity': ('works',),
}
M3_FOLD = {'has_text': '_has_text', 'has_full_text': '_has_text',
           'has_collated': '_has_collated'}   # 無底線舊鍵併入准留之源欄


def m3(repo, args, promotions):
    rep = {'step': 'M3', 'removed': collections.Counter(), 'folded': collections.Counter(),
           'lost': collections.defaultdict(list), 'manual': collections.defaultdict(list)}
    R, LOST, MAN = rep['removed'], rep['lost'], rep['manual']
    before_edges = all_edges(repo)
    before_sym = sym_pairs(repo)
    # 刪前對勘：舊反向欄的每一項，成員側／存儲側都已有（否則即「刪了就丟」）
    for wid, wr in sorted(repo.recs['Work'].items()):
        for bid in wr.data.get('books') or []:
            b = repo.get('Book', bid)
            if b is None:
                LOST['Work.books 指向不存在的 Book（舊數據錯）'].append([wid, bid])
            elif b.get('work_id') != wid:
                LOST['Work.books 與 Book.work_id 不符'].append([wid, bid, b.get('work_id')])
    for cid, cr in sorted(repo.recs['Collection'].items()):
        for x in cr.data.get('books') or []:
            bid = V.ref_id(x, 'book_id', 'id')
            b = repo.get('Book', bid)
            if b is None:
                LOST['Collection.books 指向不存在的 Book（舊數據錯）'].append([cid, bid])
            elif ci_entry(b, cid)[0] is None:
                LOST['Collection.books 成員側無 contained_in'].append([cid, bid])
        for x in cr.data.get('contained_works') or []:
            wid = V.ref_id(x, 'id', 'work_id')
            w = repo.get('Work', wid)
            if w is None:
                LOST['Collection.contained_works 指向不存在的 Work（舊數據錯）'].append([cid, wid])
            elif ci_entry(w, cid)[0] is None:
                LOST['Collection.contained_works 成員側無 contained_in'].append([cid, wid])
    for eid, er in sorted(repo.recs['Entity'].items()):
        for x in er.data.get('works') or []:
            wid = x.get('work_id') if isinstance(x, dict) else None
            w = repo.get('Work', wid)
            if w is None:
                LOST['Entity.works 指向不存在的 Work（舊數據錯）'].append([eid, wid])
            elif eid not in {a.get('entity_id') for a in w.get('authors') or [] if isinstance(a, dict)}:
                LOST['Entity.works 有而 Work.authors 無（M1③ 人工核清單）'].append([eid, wid])
    # 刪
    for t, keys in M3_DROP.items():
        for rid, rr in sorted(repo.recs[t].items()):
            d = rr.data
            for old, new in M3_FOLD.items():
                if old in d:
                    if d[old] and not d.get(new):
                        d[new] = True
                        rep['folded'][f'{t}.{old} → {new}'] += 1
                    del d[old]
                    repo.touch(rid)
                    R[f'{t}.{old}'] += 1
            for k in keys:
                if k in d:
                    del d[k]
                    repo.touch(rid)
                    R[f'{t}.{k}'] += 1
            if 'has_digitalization' in d:      # 舊鍵：有影像。resources 推得出才刪，否則交人工
                if not d['has_digitalization'] or any(
                        'image' in (r.get('types') or [r.get('type')]) for r in d.get('resources') or []
                        if isinstance(r, dict)):
                    del d['has_digitalization']
                    repo.touch(rid)
                    R[f'{t}.has_digitalization'] += 1
                else:
                    MAN['has_digitalization 為真而 resources 無影像（未刪）'].append(rid)
            for k in ('_promoted_to', 'promoted_to', '_promoted_at', 'promoted_at'):
                if k in d:
                    if k.endswith('_to') and promotions.get(rid) != d[k]:
                        MAN['promoted_to 與 promotions.json 不符（未刪）'].append({'id': rid, 'record': d[k],
                                                                              'promotions': promotions.get(rid)})
                        continue
                    del d[k]
                    repo.touch(rid)
                    R[f'{t}.{k}'] += 1
    # 反向詞項、related 在大 id 側者
    for wid, wr in sorted(repo.recs['Work'].items()):
        lst = wr.data.get('related_works')
        if not isinstance(lst, list):
            continue
        keep = [r for r in lst if not (V.rel_target(r) and not V.is_stored_form(wid, V.rel_target(r), r.get('relation')))]
        if len(keep) != len(lst):
            for r in lst:
                if r not in keep:
                    R[f'Work.related_works[{r.get("relation")}]（非存儲形）'] += 1
            wr.data['related_works'] = keep
            repo.touch(wid)
    # 對稱 id 列表：刪大 id 側
    for t, fields in V.SYMMETRIC_LISTS.items():
        for f in fields:
            for rid, rr in sorted(repo.recs[t].items()):
                lst = rr.data.get(f)
                if not isinstance(lst, list):
                    continue
                tgt_type = 'Collection' if f == 'related_collections' else 'Book'
                if tgt_type != t:
                    continue          # Collection.related_books 指 Book，不是同型對稱，不動

                def stored_on_smaller(x):
                    other = repo.get(t, x) if isinstance(x, str) and x < rid else None
                    return other is not None and rid in [sym_id(y) for y in other.get(f) or []]
                keep = [x for x in lst if not stored_on_smaller(x)]
                if len(keep) != len(lst):
                    R[f'{t}.{f}（大 id 側）'] += len(lst) - len(keep)
                    rr.data[f] = keep
                    repo.touch(rid)
    # 斷言
    built = set()
    for e in stored_edges(repo):
        built |= V.expand_edge(*e)
    lost_edges = sorted(before_edges - built)
    after_sym = sym_pairs(repo)
    lost_sym = sorted(before_sym - after_sym)
    rep['edge_conservation'] = {'edges_before_M3': len(before_edges), 'entries_after_M3': len(all_edges(repo)),
                                'built_edges': len(built), 'old_not_rebuilt': len(lost_edges),
                                'sample': lost_edges[:50], 'symmetric_pairs_before': len(before_sym),
                                'symmetric_pairs_after': len(after_sym), 'symmetric_lost': lost_sym[:50]}
    hard = {k: v for k, v in LOST.items() if '舊數據錯' not in k and 'M1③' not in k}
    rep['removed'] = dict(sorted(R.items()))
    rep['folded'] = dict(rep['folded'])
    rep['lost'] = {k: v for k, v in sorted(LOST.items())}
    rep['manual'] = {k: v for k, v in sorted(MAN.items())}
    rep['ok'] = not lost_edges and not lost_sym and not any(hard.values())
    if hard:
        rep['fail_reason'] = {k: len(v) for k, v in hard.items() if v}
    return rep


# ---------- M4：分類抽出（F3-2 §六；用戶 10-07 定：取消「未分類」占位、Collection 不分類、basis 不遷入） ----------
SCHEME = {'id': 'zongmu', 'name': '中國古籍總目', 'primary': True, 'exclusive': True, 'tree': 'zongmu/tree.json'}
CLS_DIR = 'classification'
UNCLS = '未分類'


def jdump2(o):
    return json.dumps(o, ensure_ascii=False, indent=2) + '\n'


def members_dump(node, rows):
    """成員檔：一行一條，按 work_id 排序（便於 git 逐行合併）。"""
    body = ',\n'.join('    ' + json.dumps(r, ensure_ascii=False) for r in sorted(rows))
    return '{\n  "node": %s,\n  "members": [\n%s\n  ]\n}\n' % (json.dumps(node), body)


def tree_from_vocab(vocab):
    """classific.json（葉子路徑表）→ 節點表：數組順序＝classific.json 首見順序；不含「未分類」占位節點；
    id 依此順序 zm0001 起確定性分配（正式庫、草稿庫由同一詞表得同一組 id）。"""
    paths, seen = [], set()
    for v in vocab:
        p = tuple(v[k] for k in ('cata_l1', 'cata_l2', 'cata_l3', 'cata_l4') if v.get(k))
        for i in range(1, len(p) + 1):
            q = p[:i]
            if q[-1] == UNCLS or q in seen:
                continue
            seen.add(q)
            paths.append(q)
    ids = {q: 'zm%04d' % (n + 1) for n, q in enumerate(paths)}
    return {'scheme': SCHEME['id'], 'name': SCHEME['name'],
            'nodes': [{'id': ids[q], 'label': q[-1], 'parent': ids.get(q[:-1]), 'level': len(q)} for q in paths]}


def tree_paths(tree):
    nodes = {n['id']: n for n in tree['nodes']}

    def path(i):
        out = []
        while i:
            out.append(nodes[i]['label'])
            i = nodes[i].get('parent')
        return tuple(out[::-1])
    return {i: path(i) for i in nodes if not nodes[i].get('retired')}


def load_cls(repo, vocab_path):
    base = os.path.join(repo.root, CLS_DIR, SCHEME['id'])
    tp = os.path.join(base, 'tree.json')
    if os.path.exists(tp):
        tree = json.load(open(tp, encoding='utf-8'))
        src = 'existing'
    else:
        vp = vocab_path or os.path.join(repo.root, 'classific.json')
        if not os.path.exists(vp):
            raise SystemExit(f'M4：{tp} 不存在，且找不到詞表 {vp}（草稿庫請 --vocab 指正式庫的 classific.json 或 tree.json）')
        v = json.load(open(vp, encoding='utf-8'))
        tree = v if isinstance(v, dict) and 'nodes' in v else tree_from_vocab(v)
        src = vp
    assign = {}
    mdir = os.path.join(base, 'members')
    for fn in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
        m = json.load(open(os.path.join(mdir, fn), encoding='utf-8'))
        for row in m['members']:
            assign[row[0]] = (m['node'], row[1] if len(row) > 1 else '')
    return tree, assign, src


def cls_path(c):
    ls = [c.get(k) or '' for k in ('l1', 'l2', 'l3', 'l4')]
    if any(not ls[i] and any(ls[i + 1:]) for i in range(3)):
        return None
    return tuple(x for x in ls if x)


def m4a(repo, args):
    """⑴ 由 Work.classification 生成（upsert）分類檔；逐部斷言回填＝原值。可重跑：已抽走者靠成員檔保留。"""
    rep = {'step': 'M4A', 'added': collections.Counter(), 'unknown': [], 'basis_ledger': [], 'dangling_members': []}
    A = rep['added']
    tree, assign, src = load_cls(repo, args.vocab)
    rep['tree_source'] = src
    rep['tree_nodes'] = len(tree['nodes'])
    paths = tree_paths(tree)
    node_of = {p: i for i, p in paths.items()}
    for wid, wr in sorted(repo.recs['Work'].items()):
        c = wr.data.get('classification')
        if c is None:
            continue
        p = cls_path(c) if isinstance(c, dict) else None
        if p and p[-1] == UNCLS:
            p = p[:-1]                      # 挂「未分類」占位 → 上移到父節點（＝未細分）
            A['掛「未分類」占位者上移到父節點'] += 1
        if not p or p not in node_of:
            rep['unknown'].append({'id': wid, 'classification': c})
            continue
        row = (node_of[p], c.get('source') or '')
        if assign.get(wid) != row:
            A['成員行新增' if wid not in assign else '成員行改動'] += 1
            assign[wid] = row
        b = c.get('basis')
        if b and not re.fullmatch(r'[SABC]', str(b)):
            rep['basis_ledger'].append({'id': wid, 'basis': b})   # 批次說明等非枚舉文字：不遷入，留 ledger 備查
        A['basis 丟棄（不遷入）'] += 1 if b else 0
    # 斷言：每部有 classification 的 Work，回填＝原值（未分類者比父路徑）
    mismatch = []
    for wid, wr in repo.recs['Work'].items():
        c = wr.data.get('classification')
        if not isinstance(c, dict) or any(u['id'] == wid for u in rep['unknown']):
            continue
        p = cls_path(c)
        p = p[:-1] if p and p[-1] == UNCLS else p
        node, srcv = assign[wid]
        if paths[node] != p or srcv != (c.get('source') or ''):
            mismatch.append(wid)
    for wid in assign:
        if repo.get('Work', wid) is None:
            rep['dangling_members'].append(wid)
    by_node = collections.defaultdict(list)
    for wid, (node, sv) in assign.items():
        by_node[node].append([wid, sv])
    base = f'{CLS_DIR}/{SCHEME["id"]}'
    repo.put_file(f'{CLS_DIR}/schemes.json', jdump2([SCHEME]))
    repo.put_file(f'{base}/tree.json', jdump2(tree))
    mdir = os.path.join(repo.root, base, 'members')
    for fn in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
        if fn[:-5] not in by_node:
            repo.put_file(f'{base}/members/{fn}', None)
    for node, rows in sorted(by_node.items()):
        repo.put_file(f'{base}/members/{node}.json', members_dump(node, rows))
    rep['members_total'] = len(assign)
    rep['member_files'] = len(by_node)
    rep['works_with_classification'] = sum(1 for r in repo.recs['Work'].values() if r.data.get('classification') is not None)
    rep['backfill_mismatch'] = mismatch[:50]
    rep['backfill_mismatch_count'] = len(mismatch)
    rep['added'] = dict(A)
    rep['ok'] = not rep['unknown'] and not mismatch
    return rep


def m4b(repo, args):
    """⑶ 剝離：從 Work 刪 classification（不 bump revision）。刪前逐部核成員檔已有等值行，否則不刪。"""
    rep = {'step': 'M4B', 'removed': collections.Counter(), 'not_covered': []}
    tree, assign, _ = load_cls(repo, args.vocab)
    paths = tree_paths(tree)
    for wid, wr in sorted(repo.recs['Work'].items()):
        c = wr.data.get('classification')
        if c is None:
            continue
        p = cls_path(c) if isinstance(c, dict) else None
        p = p[:-1] if p and p[-1] == UNCLS else p
        row = assign.get(wid)
        if not row or paths.get(row[0]) != p or row[1] != (c.get('source') or ''):
            rep['not_covered'].append(wid)
            continue
        del wr.data['classification']
        repo.touch(wid)
        rep['removed']['Work.classification'] += 1
    rep['removed'] = dict(rep['removed'])
    rep['ok'] = not rep['not_covered']
    return rep


# ---------- M5：build 全量＋自校驗；M6：重生 index/、刪 sidecar（F2-7 §二；sidecar 改到 M6 刪，目錄總管 10-07） ----------
def m5(repo, args):
    """不改數據：跑 build（--strict、--hub-check），寫 <root>/_build/（不進 git）。
    有 --baseline（遷移前 build 的 report.json）時，懸空引用各類只許減不許增。"""
    import build_derived as BD
    report, _ = BD.run(repo.root, args.ref_root or (), None, check_only=args.dry_run, strict=True,
                       do_hub_check=True, quiet=True)
    rep = {'step': 'M5', 'build_fatal': report['fatal'], 'entries': report['entries'],
           'files_total': report['files_total'], 'hubs': report['hubs'],
           'hub_check': [{k: x[k] for k in ('type', 'id', 'changed', 'ok')} for x in report.get('hub_check') or []],
           'dangling': {k: v['count'] for k, v in report['dangling'].items()},
           'classification': {k: v for k, v in (report.get('classification') or {}).items() if k != 'problems'},
           'index_entries': report['index']['entries'], 'index_drift_vs_repo': report['index']['drift_vs_repo_index']}
    worse = {}
    if args.baseline:
        base = json.load(open(args.baseline, encoding='utf-8'))
        bd = {k: (v['count'] if isinstance(v, dict) else v) for k, v in (base.get('dangling') or {}).items()}
        rep['dangling_baseline'] = bd
        worse = {k: [bd.get(k, 0), n] for k, n in rep['dangling'].items() if n > bd.get(k, 0)}
    rep['dangling_increased'] = worse
    rep['ok'] = not report['fatal'] and not worse
    return rep


def m6(repo, args, done):
    """⑴ 前查：人工核處置都已落完＝再跑 M1 改動為 0；⑵ 重生 index/（沿用各分片格式）；⑶ 刪 sidecar。"""
    import build_derived as BD
    rep = {'step': 'M6', 'precheck': None, 'index_files_changed': [], 'sidecars_deleted': []}
    chk = m1(repo, args)
    pending = repo.changed_paths()
    rep['precheck'] = {'M1_rerun_changes': len(pending), 'sample': pending[:20]}
    done['M1'] = chk                                   # 用它重生剩餘人工核清單
    if pending:
        repo.dirty.clear()
        repo.extra.clear()
        rep['ok'] = False
        rep['fail_reason'] = {'M1 重跑仍有改動（人工核處置或 M1 未落完／未提交）': len(pending)}
        return rep
    shards = BD.build_index(repo.recs, BD.load_promotions(repo.root))
    for rel, data in shards.items():
        raw, new = BD.index_file_content(repo.root, rel, data)
        if new != raw:
            repo.put_file(rel, new)
            rep['index_files_changed'].append(rel)
    idx = os.path.join(repo.root, 'index')
    for dp, _, fns in os.walk(idx):
        for fn in fns:
            rel = os.path.relpath(os.path.join(dp, fn), repo.root).replace(os.sep, '/')
            if rel.endswith('.json') and rel not in shards and rel.count('/') <= 2 and \
                    rel.split('/')[1] in ('works', 'books', 'entities', 'collections.json'):
                repo.put_file(rel, None)              # 舊分片多出的檔（不在重生集合內）
                rep['index_files_changed'].append(rel + '（刪）')
    # 頂層資訊尚未定去處的 sidecar（武英殿；目錄總管 10-07「先留著，不併入」）不刪，留待定案
    hold = {x['sidecar'] for x in (chk.get('manual') or {}).get('⓪ sidecar 頂層資訊（記錄未見，待定去處）', [])}
    rep['sidecars_kept'] = sorted(hold)
    for rel in repo.sidecar_paths:
        if rel in hold:
            continue
        repo.put_file(rel.replace(os.sep, '/'), None)
        rep['sidecars_deleted'].append(rel)
    repo.sidecar_paths = sorted(hold)                # 已刪者之後的步驟不再讀
    rep['index_entries'] = sum(len(v) for v in shards.values())
    rep['ok'] = True
    return rep


# ---------- 人工核清單（目錄總管 10-07：M1 的「要人工核的清單」整理成一份 md） ----------
def _t(repo, i):
    r = repo.by_id.get(i)
    if not r:
        return f'`{i}`（庫中無）'
    return f"`{i}`《{r.data.get('title') or r.data.get('primary_name') or ''}》"


def write_manual_md(repo, rep_dir, reps):
    m1r, m2r, m3r = reps.get('M1'), reps.get('M2'), reps.get('M3')
    if not (m1r or m2r or m3r):
        return None
    L = ['# 人工核清單（schema-v2 遷移 M1–M3）', '',
         f'> 由 `build/migrate_v2.py` 生成；源：遷移前 HEAD `{repo.head0}` 的副本。'
         '重跑腳本即重生本檔，請勿手改；核完的結論寫回卡上或直接改數據後重跑。', '']

    def sec(title, rows, fmt, note=None):
        if not rows:
            return
        L.append(f'## {title}（{len(rows)}）')
        L.append('')
        if note:
            L.extend([note, ''])
        for x in rows:
            L.append('- ' + fmt(x))
        L.append('')
    if m1r:
        M, E = m1r.get('manual', {}), m1r.get('data_errors', {})
        sec('冊號不一：sidecar 冊號並集 vs Book.contained_in[].volume_index', M.get('⓪ 冊號不一（sidecar 並集 vs volume_index）'),
            lambda x: f"{_t(repo, x['book'])} 叢編 `{x['collection']}`：sidecar {x['sidecar']}／記錄 {x['volume_index']}")
        sec('Book 沒寫 volume_index、sidecar 有冊號', M.get('⓪ Book 無 volume_index、sidecar 有冊號'),
            lambda x: f"{_t(repo, x['book'])} 叢編 `{x['collection']}`：sidecar {x['sidecar']}")
        sec('zhsy_id：sidecar 有、Book 側空或不同', M.get('⓪ zhsy_id 與 Book.zhsy_id 不一'),
            lambda x: f"{_t(repo, x['book'])}：sidecar `{x['sidecar']}`／Book `{x['book_side']}`")
        sec('百衲本：Book 無對應 resource、sidecar 也無鏈接（交資源道）',
            M.get('⓪ 百衲本：Book 無對應 resource、sidecar 也無鏈接（交資源道）'),
            lambda x: f"{_t(repo, x['book'])} 缺 `{x['resource']}`（應 {x['expected']} 冊）")
        sec('百衲本：details 冊數與 sidecar 不一', M.get('⓪ 百衲本：details 與 sidecar 冊數不一'),
            lambda x: f"{_t(repo, x['book'])} `{x['resource']}`：sidecar {x['found']}/{x['expected']}，details「{x['details']}」")
        sec('sidecar 頂層資訊，記錄未見（目錄總管 10-07：先留著，不併入）', M.get('⓪ sidecar 頂層資訊（記錄未見，待定去處）'),
            lambda x: f"`{x['sidecar']}` → 叢編 {_t(repo, x['collection'])}：{', '.join(x['fields'])}")
        sec('叢編側與成員側 volume_index 不一（語義不同，未動）', M.get('① contained_in 與 contained_works 屬性不一'),
            lambda x: f"{_t(repo, x['work'])} 叢編 `{x['collection']}`：叢編側 {x['collection_side']}／成員側 {x['member_side']}")
        sec('contained_works.period 與 Work.period 不一', M.get('① contained_works.period 與 Work.period 不一'),
            lambda x: f"{_t(repo, x['work'])} 叢編 `{x['collection']}`：{x['collection_side']}／{x['work_side']}")
        dup = [x for x in M.get('③ Entity.works 有而 Work.authors 無、按名補不了') or [] if x.get('other_entity')]
        rest = [x for x in M.get('③ Entity.works 有而 Work.authors 無、按名補不了') or [] if not x.get('other_entity')]
        if dup:
            L.append(f'## 疑重複人物（{len(dup)}）：M3 照刪 Entity.works，不補 authors；清單另存 `人物道-疑重複人物.md`')
            L.append('')
            write_dup_people(repo, rep_dir, dup)
        sec('Entity.works 有而 Work.authors 無、不屬疑重複人物（請目錄總管看）', rest,
            lambda x: f"人物 {_t(repo, x['entity'])} ↔ 作品 {_t(repo, x['work'])}：{x['why']}；作品作者 {x['authors']}")
        sec('parent_work_id：子母皆在、但兩者間無 related 關係（說明無處可附，請目錄總管定）',
            M.get('⓪ parent_work_id 對無 related 關係'),
            lambda x: f"子 {_t(repo, x['work'])} ／ 母 {_t(repo, x['parent'])}")
        sec('sidecar 舊 id 已改指現 id（按 zhsy_id／題名＋同叢編／Book.work_id 唯一對上；sidecar 原樣不改）',
            (m1r.get('items') or {}).get('⓪ 改號'),
            lambda x: f"`{x['old']}` → {_t(repo, x['new'])}（{x['by']}；{x['sidecar']}）")
        sec('數據錯：sidecar 列了不存在的 Book、對不上現 id（作廢，不併入；sidecar 原樣保留）', E.get('sidecar 列了不存在的 Book'),
            lambda x: f"`{x['book_id']}`《{x.get('title') or ''}》"
                      + (f" zhsy_id `{x['zhsy_id']}`" if x.get('zhsy_id') else '') + f"（{x['sidecar']}）")
        sec('數據錯：parent_work_id 子或母作品不存在、對不上現 id（不併入）', E.get('parent_work_id：子或母作品不存在'),
            lambda x: f"子 {_t(repo, x['work'])} ／ 母 {_t(repo, x['parent'])}")
        for k in ('Collection.books 指向不存在的 Book', 'Collection.contained_works 指向不存在的 Work', 'Entity.works 指向不存在的 Work'):
            sec('數據錯：' + k, E.get(k), lambda x: ' → '.join(f'`{y}`' for y in x))
    if m2r:
        sec('related_collections 對象轉 id 字串：附加資訊已併入本叢編 description.text（備查）', m2r.get('symmetric_object_info'),
            lambda x: f"{_t(repo, x['record'])}.{x['field']} → `{x['target']}`：「{x.get('line', '')}」")
        sec('related_collections 無法轉 id 字串（指向非叢編，原樣保留）', m2r.get('symmetric_unconvertible'),
            lambda x: f"{_t(repo, x['record'])}.{x['field']}：{json.dumps(x['item'], ensure_ascii=False)}")
    if m3r:
        for k, v in (m3r.get('manual') or {}).items():
            sec('M3：' + k, v, lambda x: json.dumps(x, ensure_ascii=False) if not isinstance(x, str) else _t(repo, x))
    p = os.path.join(rep_dir, '人工核清單.md')
    os.makedirs(rep_dir, exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write('\n'.join(L).rstrip() + '\n')
    return p


def write_dup_people(repo, rep_dir, rows):
    """目錄總管 10-07：94 條「同名作者已繫另一 Entity」另存一份交人物道。"""
    L = ['# 人物道：疑重複人物（schema-v2 遷移 M1③ 產出）', '',
         f'> 由 `build/migrate_v2.py` 生成；源：遷移前 HEAD `{repo.head0}`。每行：Entity.works 有此作品、而作品作者已繫另一 Entity。'
         'M3 刪 Entity.works 後，左邊這個人物頁不再列該作品；作品側不動。', '',
         '| 人物（Entity.works 側） | 作品 | 作品作者已繫 |', '|---|---|---|']
    for x in sorted(rows, key=lambda r: (r['entity'], r['work'])):
        L.append(f"| {_t(repo, x['entity'])} | {_t(repo, x['work'])} | {_t(repo, x['other_entity'][0])} |")
    with open(os.path.join(rep_dir, '人物道-疑重複人物.md'), 'w', encoding='utf-8') as f:
        f.write('\n'.join(L) + '\n')


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
    for k in ('records', 'precheck', 'build_fatal', 'entries', 'hubs', 'hub_check', 'dangling', 'dangling_increased',
              'classification', 'index_entries', 'tree_source', 'tree_nodes', 'members_total', 'member_files', 'works_with_classification',
              'backfill_mismatch_count', 'added', 'removed', 'folded', 'fail_reason', 'sidecar_checks', 'removed_title',
              'edge_conservation', 'records_changed',
              'files_written', 'protected_violations', 'head', 'tag_command'):
        if k in rep:
            v = rep[k]
            if k == 'edge_conservation':
                v = {a: b for a, b in v.items() if not a.startswith('sample')}
            s[k] = v
    for k in ('unknown_shapes', 'cannot_place', 'symmetric_object_info', 'symmetric_unconvertible', 'unknown',
              'basis_ledger', 'dangling_members', 'not_covered', 'index_files_changed', 'sidecars_deleted',
              'sidecars_kept'):
        if k in rep:
            s[k + '_count'] = len(rep[k])
    for k in ('data_errors', 'manual', 'lost'):
        if k in rep:
            s[k] = {a: len(b) for a, b in rep[k].items()}
    return s


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--root', required=True, help='數據倉根（正式庫或草稿庫）')
    ap.add_argument('--steps', default='M0', help='逗號分隔：M0,M1,M2,M3,M4（＝M4a 生成分類檔＋M4b 剝離，各一提交）,M5,M6')
    ap.add_argument('--ref-root', action='append', help='M5：只讀參照倉（草稿庫指正式庫）')
    ap.add_argument('--baseline', help='M5：遷移前 build 的 report.json，懸空引用只許減')
    ap.add_argument('--vocab', help='M4 首次生成分類樹的詞表（classific.json 或已有的 tree.json；預設 <root>/classific.json）')
    ap.add_argument('--dry-run', action='store_true', help='不寫回數據檔（報告照寫）')
    ap.add_argument('--report-dir', help='報告目錄（預設 <root>/migrate_report）')
    ap.add_argument('--tag', action='store_true', help='M0 時真的打 tag pre-schema-v2（預設只印命令）')
    ap.add_argument('--git-commit', action='store_true', help='每步寫回後在 root 倉提交一次（只 add 改過的記錄檔）')
    a = ap.parse_args(argv)
    steps = [x for s in a.steps.split(',') if s.strip()
             for x in (('M4A', 'M4B') if s.strip().upper() == 'M4' else (s.strip().upper(),))]
    rep_dir = a.report_dir or os.path.join(a.root, 'migrate_report')
    repo = Repo(a.root)
    original_edges = all_edges(repo)
    status = 0
    done = {}
    for st in steps:
        if st == 'M0':
            rep = m0(repo, a)
        elif st == 'M1':
            rep = m1(repo, a)
        elif st == 'M2':
            rep = m2(repo, a, original_edges)
        elif st == 'M3':
            rep = m3(repo, a, load_promotions(repo.root))
        elif st == 'M4A':
            rep = m4a(repo, a)
        elif st == 'M4B':
            rep = m4b(repo, a)
        elif st == 'M5':
            rep = m5(repo, a)
        elif st == 'M6':
            rep = m6(repo, a, done)
        else:
            ap.error(f'unknown step {st}')
        if st not in ('M0', 'M5'):
            bad = repo.check_protected()
            rep['protected_violations'] = bad
            if bad:
                rep['ok'] = False
            paths = repo.changed_paths()
            rep['records_changed'] = len(paths)
            if rep['ok'] and not a.dry_run:
                rep['files_written'] = repo.save()
                if a.git_commit and paths:
                    # 只 add 改過的記錄檔；檔數可上萬，走 stdin 免撞命令列長度上限
                    git(repo.root, 'add', '-A', '--pathspec-from-file=-', '--pathspec-file-nul', stdin='\0'.join(paths))
                    git(repo.root, 'commit', '-q', '-m', f'schema-v2 {rep["step"]}（migrate_v2.py）')
            elif a.dry_run:
                repo.dirty.clear()
                repo.extra.clear()
        write_report(rep_dir, rep)
        done[st] = rep
        print(json.dumps(summarise(rep), ensure_ascii=False, indent=1, default=list))
        if not rep.get('ok'):
            print(f'FAIL at {st}; stop.', file=sys.stderr)
            status = 1
            break
    # dry-run 時記憶體已改不寫回，後一步在此基礎上跑：報告反映「依次跑」的結果
    write_manual_md(repo, rep_dir, done)
    return status


if __name__ == '__main__':
    sys.exit(main())
