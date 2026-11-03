#!/usr/bin/env python3
"""S2-L：Book 年代统一进 dating。
publication_info.year / year_iso、lineage.year / year_range / year_text / year_uncertain
→ dating（year / year_range / text）。可重复运行；--apply 才写盘。
冲突（已有 dating 与待并入值不一致）不覆盖，原值写入 ai_note，不丢信息。
"""
import argparse, collections, json, os, re, sys

NUM = re.compile(r'\d{1,4}')
RNG = re.compile(r'(\d{1,4})\s*[-–—~]\s*(\d{1,4})')
DASH = {'basis_num': '目錄著錄年份（原 publication_info.year）',
        'basis_rng': '目錄著錄年份區間（原 publication_info.year）',
        'basis_txt': '目錄著錄年代文本（原 publication_info.year）',
        'basis_ln': '版本傳承著錄（原 lineage.year*）'}


def parse_year(s):
    s = s.strip()
    if NUM.fullmatch(s):
        return ('year', int(s))
    m = RNG.fullmatch(s)
    if m:
        a, b = int(m.group(1)), int(m.group(2))
        if a == b:
            return ('year', a)
        if a < b:
            return ('year_range', [a, b])
    return None


def note(d, line):
    d['ai_note'] = (d['ai_note'] + '\n' if d.get('ai_note') else '') + line


def migrate(d, ch):
    pi = d.get('publication_info') if isinstance(d.get('publication_info'), dict) else None
    ln = d.get('lineage') if isinstance(d.get('lineage'), dict) else None
    dt = d.get('dating') if isinstance(d.get('dating'), dict) else None
    changed = False
    pyear = pi.get('year') if pi else None
    piso = pi.get('year_iso') if pi else None
    if isinstance(pyear, str) and not pyear.strip():
        del pi['year']; pyear = None; changed = True; ch['pi_empty_dropped'] += 1
    created = False
    # ---- publication_info.year / year_iso
    if pyear is not None or piso is not None:
        p = parse_year(pyear) if isinstance(pyear, str) else None
        iso = parse_year(piso) if isinstance(piso, str) else None
        if dt is None:
            new = {}
            if p:
                new[p[0]] = p[1]; basis = DASH['basis_rng'] if p[0] == 'year_range' else DASH['basis_num']; cert = 'inferred'
            else:
                if iso:
                    new[iso[0]] = iso[1]; cert = 'inferred'
                else:
                    cert = 'uncertain'
                if pyear is not None:
                    new['text'] = pyear
                basis = DASH['basis_txt']
            new.update({'certainty': cert, 'source': 'catalog', 'basis': basis})
            dt = new; d['dating'] = dt; created = True; ch['dating_created'] += 1
        else:
            # 并入已有 dating
            if pyear is not None:
                if p and dt.get(p[0]) == p[1]:
                    ch['pi_same_dropped'] += 1
                elif p and p[0] not in dt and not (p[0] == 'year' and 'year_range' in dt) and not (p[0] == 'year_range' and 'year' in dt):
                    dt[p[0]] = p[1]; ch['pi_filled_dating'] += 1
                elif not p and 'text' not in dt:
                    dt['text'] = pyear; ch['pi_text_to_dating'] += 1
                elif not p and dt.get('text') == pyear:
                    ch['pi_same_dropped'] += 1
                else:
                    note(d, '原 publication_info.year：' + pyear); ch['conflict_pi'] += 1
            if piso is not None:
                if iso and dt.get(iso[0]) == iso[1]:
                    pass
                elif iso and iso[0] not in dt and 'year_range' not in dt and 'year' not in dt:
                    dt[iso[0]] = iso[1]
                else:
                    note(d, '原 publication_info.year_iso：' + piso); ch['conflict_iso'] += 1
        pi.pop('year', None); pi.pop('year_iso', None); changed = True
        if not pi: del d['publication_info']
    # ---- lineage.year*
    if ln and any(k in ln for k in ('year', 'year_range', 'year_text', 'year_uncertain')):
        if dt is None:
            dt = {'certainty': 'inferred', 'source': 'catalog', 'basis': DASH['basis_ln']}
            d['dating'] = dt; ch['dating_created_from_lineage'] += 1
        v = ln.pop('year', None)
        if v is not None:
            if 'year' not in dt and 'year_range' not in dt: dt['year'] = v
            elif dt.get('year') != v: note(d, '原 lineage.year：%s' % v); ch['conflict_ln_year'] += 1
        v = ln.pop('year_range', None)
        if v is not None:
            if 'year_range' not in dt and 'year' not in dt and len(v) == 2: dt['year_range'] = v
            elif dt.get('year_range') != v: note(d, '原 lineage.year_range：%s' % json.dumps(v)); ch['conflict_ln_range'] += 1
        v = ln.pop('year_text', None)
        if v is not None:
            if 'text' not in dt: dt['text'] = v
            elif dt['text'] != v: note(d, '原 lineage.year_text：' + v); ch['conflict_ln_text'] += 1
        v = ln.pop('year_uncertain', None)
        if v is not None:
            if v is True and dt.get('certainty') != 'uncertain':
                note(d, '原 lineage.year_uncertain：true'); ch['ln_uncertain_noted'] += 1
            elif v is False: ch['ln_uncertain_false'] += 1
        changed = True
        if not ln: del d['lineage']
    return changed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='Book'); ap.add_argument('--apply', action='store_true')
    ap.add_argument('--limit', type=int, default=0)
    a = ap.parse_args()
    ch = collections.Counter(); n = 0
    for r, _, fs in os.walk(a.root):
        for f in fs:
            if not f.endswith('.json'): continue
            p = os.path.join(r, f)
            d = json.load(open(p, encoding='utf8'))
            if migrate(d, ch):
                n += 1
                if a.apply:
                    open(p, 'w', encoding='utf8').write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
                if a.limit and n >= a.limit: break
        if a.limit and n >= a.limit: break
    print('changed', n)
    for k, v in sorted(ch.items()): print(v, k)

main()
