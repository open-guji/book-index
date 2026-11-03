#!/usr/bin/env python3
"""S2-N：Book 计量合一。juan_count / volume_count → measures[]（真源）；measure_info 保留原文。
可重复运行；--apply 才写盘。无法结构化的原值写入 ai_note，不丢信息。
"""
import argparse, collections, json, os, re


def note(d, line):
    d['ai_note'] = (d['ai_note'] + '\n' if d.get('ai_note') else '') + line


def has(ms, number, unit):
    return any(isinstance(m, dict) and m.get('number') == number and m.get('unit') == unit for m in ms)


def migrate(d, ch):
    changed = False
    ms = d.get('measures') if isinstance(d.get('measures'), list) else None
    jc = d.get('juan_count')
    if isinstance(jc, dict):
        n, u, desc = jc.get('number'), jc.get('unit'), jc.get('description')
        extra = set(jc) - {'number', 'unit', 'description'}
        if extra:
            note(d, '原 juan_count 其他欄位：' + json.dumps({k: jc[k] for k in extra}, ensure_ascii=False)); ch['jc_extra'] += 1
        if isinstance(n, int) and u and not (isinstance(ms, list) and has(ms, n, u)):
            ms = ms if ms is not None else []
            ms.insert(0, {'number': n, 'unit': u}); ch['jc_to_measures'] += 1
        elif isinstance(n, int) and u:
            ch['jc_already_in_measures'] += 1
        elif isinstance(n, int) and not u:
            primary = ms[0] if ms else None
            if primary and primary.get('number') == n:
                ch['jc_nounit_same'] += 1
            else:
                note(d, '原 juan_count.number（無單位）：%d' % n); ch['jc_nounit_noted'] += 1
        if desc:
            mi = d.get('measure_info')
            redundant = bool(re.fullmatch(r'\d+\S', desc)) and isinstance(n, int) and desc.startswith(str(n))
            if not mi and not redundant:
                d['measure_info'] = desc; ch['desc_to_measure_info'] += 1
            elif mi == desc or redundant:
                ch['desc_dropped'] += 1
            else:
                note(d, '原 juan_count.description：' + desc); ch['desc_noted'] += 1
        del d['juan_count']; changed = True
    vc = d.get('volume_count')
    if isinstance(vc, dict):
        n, desc = vc.get('number'), vc.get('description')
        if isinstance(n, int):
            ms = ms if ms is not None else []
            if not has(ms, n, '冊'):
                ms.append({'number': n, 'unit': '冊'}); ch['vc_to_measures'] += 1
        if desc and desc != '%d冊' % (n if isinstance(n, int) else -1):
            note(d, '原 volume_count.description：' + desc); ch['vc_desc_noted'] += 1
        del d['volume_count']; changed = True
    if changed and ms is not None:
        d['measures'] = ms
    return changed


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--root', default='Book'); ap.add_argument('--apply', action='store_true')
    a = ap.parse_args(); ch = collections.Counter(); n = 0
    for r, _, fs in os.walk(a.root):
        for f in fs:
            if not f.endswith('.json'): continue
            p = os.path.join(r, f)
            d = json.load(open(p, encoding='utf8'))
            if migrate(d, ch):
                n += 1
                if a.apply:
                    open(p, 'w', encoding='utf8').write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
    print('changed', n)
    for k, v in sorted(ch.items()): print(v, k)


main()
