#!/usr/bin/env python3
"""people.offices[] 检查（2026-11-12，A12；方案 ai-team domain/专名/规划/任官关系-统一方案-2026-11-12.md）。
用法：python3 .claude/qa/check_offices.py [仓根]
ERROR：F01 只许 people，office_id／text／sources 非空，sources 项是带 title 的对象；
       F02 office_id 指 office、place_id 指 place、institution_id 指官署（collective_kind=官署），且都未并／未退役；
       F03 kind 在枚举内，posthumous／declined 只许 true，start／end 整数且 start≤end，未知键。
WARN： F02b institution_id 与 office 的 institution_ref 相同（多余）；F04 任职年落在生卒外（无生卒用 floruit±40）；
       F05 office 朝代与人物朝代不相容；F06 同人同 office_id 同 start 重复；F07 start 早于前面某项的 start（项序与年份打架）。
印出「扫 N 檔、含 offices M 檔、任官项 K」，防扫 0 文件假绿。有 ERROR 退出码 1。"""
import json, os, sys
ROOT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', '..')
KIND = {'兼', '權', '試', '判', '守', '行', '知', '充'}
KEYS = {'office_id', 'text', 'kind', 'posthumous', 'declined', 'place_id', 'institution_id', 'start', 'end', 'date_text', 'basis', 'sources'}
recs = {}; scanned = 0
for r, _, fs in os.walk(os.path.join(ROOT, 'Entity')):
    for f in fs:
        if not f.endswith('.json'): continue
        scanned += 1
        try: d = json.load(open(os.path.join(r, f), encoding='utf-8'))
        except Exception: continue
        recs[d.get('id')] = d
dyn_name = {i: d.get('primary_name') for i, d in recs.items() if d.get('subtype') == 'dynasty'}
def live(i): o = recs.get(i); return o if o and not o.get('merged_into') and not o.get('retired') else None
def yrs(o):
    return {dyn_name.get(x) for x in o.get('dynasty_ids') or [] if dyn_name.get(x)}
def compat(pd, ods):
    if not pd or not ods: return True
    return any(a[:1] == pd[:1] or a in pd or pd in a for a in ods)
E = []; W = []; nfile = nitem = 0
for i, d in recs.items():
    ol = d.get('offices')
    if ol is None: continue
    nfile += 1
    if d.get('subtype') != 'people': E.append((i, 'F01 非 people 不得有 offices')); continue
    if not isinstance(ol, list) or not ol: E.append((i, 'F01 offices 须为非空数组')); continue
    dt = d.get('dates') or {}
    lo = hi = None
    if dt.get('birth') or dt.get('death'):
        lo = (dt.get('birth') or dt['death'] - 90) + 10; hi = (dt.get('death') or dt['birth'] + 90) + 1
    elif dt.get('floruit'):
        fl = dt['floruit']; lo, hi = fl[0] - 40, fl[-1] + 40
    seen = set(); maxstart = None
    for x in ol:
        nitem += 1
        if not isinstance(x, dict): E.append((i, 'F01 项须为对象')); continue
        bad = set(x) - KEYS
        if bad: E.append((i, 'F03 未知键 %s' % sorted(bad)))
        for k in ('office_id', 'text'):
            if not x.get(k): E.append((i, 'F01 %s 必填' % k))
        ss = x.get('sources')
        if not ss: E.append((i, 'F01 sources 必填'))
        for s in ss or []:
            if not (isinstance(s, dict) and s.get('title')): E.append((i, 'F01 sources 项须为带 title 的引文对象'))
        o = live(x.get('office_id'))
        if x.get('office_id') and (not o or o.get('subtype') != 'office'): E.append((i, 'F02 office_id 不存在／已并／非 office：%s' % x.get('office_id')))
        if x.get('place_id'):
            p = live(x['place_id'])
            if not p or p.get('subtype') != 'place': E.append((i, 'F02 place_id 不存在／已并／非 place：%s' % x['place_id']))
        if x.get('institution_id'):
            c = live(x['institution_id'])
            if not c or c.get('subtype') != 'collective' or c.get('collective_kind') != '官署': E.append((i, 'F02 institution_id 非官署：%s' % x['institution_id']))
            elif o and o.get('institution_ref') == x['institution_id']: W.append((i, 'F02b institution_id 与官职 institution_ref 相同，多余'))
        if 'kind' in x and x['kind'] not in KIND: E.append((i, 'F03 kind 不在枚举：%r' % x['kind']))
        for k in ('posthumous', 'declined'):
            if k in x and x[k] is not True: E.append((i, 'F03 %s 只许写 true' % k))
        s0, s1 = x.get('start'), x.get('end')
        for k, v in (('start', s0), ('end', s1)):
            if v is not None and (not isinstance(v, int) or isinstance(v, bool) or v == 0): E.append((i, 'F03 %s 须为非 0 整数' % k))
        if isinstance(s0, int) and isinstance(s1, int) and s0 > s1: E.append((i, 'F03 start>end'))
        if isinstance(s0, int) and lo is not None and not x.get('posthumous') and not (lo <= s0 <= hi): W.append((i, 'F04 任职年 %d 落在生卒／活动年外' % s0))
        if o and d.get('dynasty') and not compat(d['dynasty'], yrs(o)): W.append((i, 'F05 官职朝代 %s 与人物朝代 %s 不相容' % (sorted(yrs(o)), d['dynasty'])))
        if isinstance(s0, int):
            if (x.get('office_id'), s0) in seen: W.append((i, 'F06 同官同年重复'))
            seen.add((x.get('office_id'), s0))
            if maxstart is not None and s0 < maxstart: W.append((i, 'F07 start %d 早于前项 %d' % (s0, maxstart)))
            maxstart = s0 if maxstart is None else max(maxstart, s0)
print('扫 %d 檔、含 offices %d 檔、任官项 %d；ERROR %d，WARN %d' % (scanned, nfile, nitem, len(E), len(W)))
for e in E[:30]: print('  ERROR', e)
for w in W[:30]: print('  WARN', w)
sys.exit(1 if E else 0)
