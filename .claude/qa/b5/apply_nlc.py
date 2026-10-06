#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""B5：把國圖數字古籍「确定档」的匹配结果写进 Work.resources（overview#394，口径：总管 10-05）。

口径：
  - 只写确定档；存疑、无不写。
  - 挂在 Work 层，不分 Book。一个 Work 有多条馆方记录的，每条一个 resource，全挂。
  - resource 形状沿用本仓既有的 nlc 条目（Book 里已有）：id=nlc、types=["image"]、group=nlc-<fid>、group_role=origin；
    记录号 fid 在 group 与 metadata.nlc_fid；版本写 metadata.edition；Work 有 ≥2 条国图记录时另在 resource_groups 里
    给每组加 label（版本），好区分。
  - 幂等：Work 或其 Book 上已有同一 fid 的 nlc 条目则跳过。
  - 同时置 `_has_image: true` 与索引 `has_image: true`（派生字段，与 rematch_commons.py 同做法）。

用法：
  python3 .claude/qa/b5/apply_nlc.py --table <匹配表.tsv> --plan /tmp/plan.json            # 只出方案，不写
  python3 .claude/qa/b5/apply_nlc.py --table <匹配表.tsv> --plan /tmp/plan.json --apply    # 写
  python3 .claude/qa/b5/apply_nlc.py --table <匹配表.tsv> --plan /tmp/plan.json --audit    # 对着 git HEAD 审计只多了预期字段
匹配表在 book_index_json 仓 library_data/_匹配/國圖數字古籍/匹配表.tsv（复现：match_nlc.py 生成）。
"""
import argparse, collections, csv, glob, hashlib, json, os, re, subprocess, sys
from urllib.parse import urlsplit, parse_qs

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
NAME = '中華古籍資源庫（國家圖書館）'


def fid_of(url):
    return (parse_qs(urlsplit(url).query).get('fid') or [''])[0]


def dump(path, value):
    raw = open(path, encoding='utf-8').read()
    m = re.search(r'(?m)^([ \t]+)"', raw)
    indent = m.group(1) if m else 2
    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=indent) + '\n')


def load_index():
    shards, loc = {}, {}
    for f in sorted(glob.glob(os.path.join(ROOT, 'index/works/*.json'))):
        d = json.load(open(f, encoding='utf-8')); shards[f] = d
        for k in d: loc[k] = f
    return shards, loc


def existing_fids():
    """Work 与 Book 上已有的 nlc 记录号（read.nlc.cn 的 fid／bid）。"""
    seen = set()
    for pat in ('Work', 'Book'):
        for f in glob.iglob(os.path.join(ROOT, pat, '*/*/*/*.json')):
            raw = open(f, encoding='utf-8').read()
            if 'nlc.cn' not in raw:
                continue
            for r in json.loads(raw).get('resources') or []:
                u = r.get('url') or ''
                if 'nlc.cn' in u:
                    q = parse_qs(urlsplit(u).query)
                    for k in ('fid', 'bid'):
                        for v in q.get(k, []): seen.add(v)
    return seen


def build_plan(table):
    rows = [r for r in csv.DictReader(open(table, encoding='utf-8'), delimiter='\t') if r['tier'] == '确定']
    seen = existing_fids()
    shards, loc = load_index()
    by_work = collections.defaultdict(list)
    skipped = collections.Counter()
    for r in rows:
        fid = fid_of(r['url'])
        if not fid or r['work_id'] not in loc:
            skipped['无fid或Work不在索引'] += 1; continue
        if fid in seen:
            skipped['已有同fid'] += 1; continue
        by_work[r['work_id']].append((fid, r))
    plan = []
    for wid, items in sorted(by_work.items()):
        path = shards[loc[wid]][wid]['path']
        raw = open(os.path.join(ROOT, path), 'rb').read()
        w = json.loads(raw)
        have = {fid_of(x.get('url') or '') for x in w.get('resources') or []}
        uniq, used = [], set()
        for fid, r in items:                      # 同 fid 重复行只挂一次
            if fid in used or fid in have: continue
            used.add(fid); uniq.append((fid, r))
        if not uniq: continue
        multi = len(uniq) >= 2
        res, groups = [], {}
        for fid, r in uniq:
            ed = (r['lib_version'] or '').strip()
            md = {'nlc_fid': fid}
            if ed: md['edition'] = ed
            res.append({'id': 'nlc', 'group': f'nlc-{fid}', 'group_role': 'origin', 'name': NAME, 'short_name': '國圖',
                        'url': r['url'], 'types': ['image'], 'metadata': md})
            if multi:
                groups[f'nlc-{fid}'] = {'label': ('國圖藏本：' + ed) if ed else '國圖藏本'}
        plan.append({'work_id': wid, 'path': path, 'before_sha256': hashlib.sha256(raw).hexdigest(), 'resources': res, 'resource_groups': groups})
    return plan, skipped, len(rows)


def apply(plan):
    shards, loc = load_index()
    touched = set()
    for p in plan:
        path = os.path.join(ROOT, p['path'])
        assert hashlib.sha256(open(path, 'rb').read()).hexdigest() == p['before_sha256'], p['work_id']
    for p in plan:
        path = os.path.join(ROOT, p['path'])
        w = json.load(open(path, encoding='utf-8'))
        w.setdefault('resources', []).extend(p['resources'])
        if p['resource_groups']:
            rg = w.setdefault('resource_groups', {})
            for k, v in p['resource_groups'].items(): rg.setdefault(k, v)
        w['_has_image'] = True
        dump(path, w)
        shards[loc[p['work_id']]][p['work_id']]['has_image'] = True
        touched.add(loc[p['work_id']])
    for f in touched: dump(f, shards[f])
    print(f'写入 {len(plan)} 个 Work，更新 {len(touched)} 个索引分片')


def audit(plan):
    """对着 git HEAD：每个 Work 只多了 resources 新条目、resource_groups、_has_image；索引只多 has_image。"""
    shards, loc = load_index()
    bad = 0; nres = 0
    for p in plan:
        before = json.loads(subprocess.check_output(['git', '-C', ROOT, 'show', 'HEAD:' + p['path']]))
        now = json.load(open(os.path.join(ROOT, p['path']), encoding='utf-8'))
        exp = dict(before)
        exp['resources'] = list(before.get('resources') or []) + p['resources']
        if p['resource_groups']:
            exp['resource_groups'] = {**(before.get('resource_groups') or {}), **{k: v for k, v in p['resource_groups'].items() if k not in (before.get('resource_groups') or {})}}
        exp['_has_image'] = True
        if now != exp: bad += 1; print('意外改动', p['path'])
        if shards[loc[p['work_id']]][p['work_id']].get('has_image') is not True: bad += 1; print('索引未置', p['work_id'])
        nres += len(p['resources'])
    fids = [r['metadata']['nlc_fid'] for p in plan for r in p['resources']]
    assert len(fids) == len(set(fids)), 'fid 重复'
    print(f'审计 {len(plan)} 个 Work、{nres} 条 resource，异常 {bad}')
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--table', required=True); ap.add_argument('--plan', required=True)
    ap.add_argument('--apply', action='store_true'); ap.add_argument('--audit', action='store_true')
    a = ap.parse_args()
    if a.audit:
        audit(json.load(open(a.plan))['plan'])
    else:
        plan, skipped, nrows = build_plan(a.table)
        print(f'确定档 {nrows} 行 → 方案 {len(plan)} 个 Work、{sum(len(p["resources"]) for p in plan)} 条 resource；跳过 {dict(skipped)}')
        json.dump({'plan': plan}, open(a.plan, 'w'), ensure_ascii=False)
        if a.apply: apply(plan)
