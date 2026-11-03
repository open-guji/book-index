#!/usr/bin/env python3
"""Work 计量合一（schema 审查 可做可不做 第 3 组）：measures[] 为真源，juan_count 并入后删除，measure_info 原文保留。
默认只报告；--apply 写入；--keep-juan 只订正 measures、保留 juan_count（过渡阶段用）；--out FILE 写人核清单。
规则（number>0；unit 缺省「卷」）：
  a. measures 已有同单位同数 → 直接删 juan_count
  b. measures 有同单位不同数 → 以 measure_info 原文为准：原文含 jc 值则改 measures；含 measures 值则保留 measures；都没有则保留 measures 并入清单
  c. measures 无该单位：measure_info 含 jc 值，或无 measure_info → 追加 {unit,number}；measure_info 存在却不含 → jc 与原文不符，丢弃并入清单
  d. number==0 是占位 → 删；description 若是计量短语（数字＋单位）且 measure_info 缺 → 迁入 measure_info，否则（说明性文字）并入 ai_note
  e. jc.description（number>0）→ 该单位 measures 项的 note（与 measure_info 相同则丢）
measures 内 number==0 且 measure_info 为「不分卷」之类：保留（0 表示不分卷，见 collection.md）。"""
import json, glob, re, sys, collections as C
APPLY = '--apply' in sys.argv; KEEP = '--keep-juan' in sys.argv
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
D = {'零': 0, '〇': 0, '一': 1, '二': 2, '两': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}
def cn(s):
    total = 0; cur = 0; sec = 0
    if not s: return None
    for ch in s:
        if ch in D: cur = D[ch]
        elif ch == '十': total += (cur or 1) * 10; cur = 0
        elif ch == '百': total += (cur or 1) * 100; cur = 0
        elif ch == '千': total += (cur or 1) * 1000; cur = 0
        elif ch == '萬': total = (total + cur) * 10000; cur = 0
        else: return None
    return total + cur
UN = '卷冊册篇回種部集章本編首則'
def pairs(mi):
    out = set()
    for m in re.finditer(r'([零〇一二三四五六七八九十百千萬两]+|\d+)([%s])' % UN, mi or ''):
        n = int(m.group(1)) if m.group(1).isdigit() else cn(m.group(1))
        u = '冊' if m.group(2) == '册' else m.group(2)
        if n is not None: out.add((n, u))
    return out
st = C.Counter(); lst = []
for p in glob.iglob('Work/*/*/*/*.json'):
    s = open(p, encoding='utf-8').read()
    if '"juan_count"' not in s: continue
    d = json.loads(s)
    jc = d.get('juan_count')
    if jc is None or d.get('merged_into'): continue
    nl = '\n' if s.endswith('\n') else ''
    ind = 2
    for l in s.split('\n')[1:3]:
        if len(l) - len(l.lstrip()): ind = len(l) - len(l.lstrip()); break
    if json.dumps(d, ensure_ascii=False, indent=ind) + nl != s: st['skip_format'] += 1; lst.append((d['id'], d['title'], 'format', '')); continue
    n = jc.get('number'); u = jc.get('unit') or '卷'; desc = jc.get('description') or ''
    ms = d.get('measures') or []; mi = d.get('measure_info') or ''; mp = pairs(mi)
    ms = [dict(m) for m in ms]
    note = None
    if n == 0 or n is None:
        if desc:
            dp = pairs(desc)
            if re.fullmatch(r'[零〇一二三四五六七八九十百千萬]+[%s]' % UN, desc) and not mi: d['measure_info'] = desc; st['zero_desc_to_mi'] += 1
            elif dp and (dp <= mp or dp <= {(m['number'], m['unit']) for m in ms}): st['zero_desc_covered'] += 1
            else:
                d['ai_note'] = (d.get('ai_note', '') + ('\n' if d.get('ai_note') else '') + '2026-11-03 計量合一：原 juan_count.description「' + desc + '」（number=0 占位已刪）'); st['zero_desc_to_ai_note'] += 1
        st['zero_drop'] += 1
    else:
        same = [m for m in ms if m['unit'] == u]
        if any(m['number'] == n for m in same): st['a_agree'] += 1; target = next(m for m in same if m['number'] == n)
        elif same:
            m0 = same[0]
            if (n, u) in mp: m0['number'] = n; st['b_fix_ms'] += 1; lst.append((d['id'], d['title'], 'b_fix_ms', f'{u}:{m0["number"]}→{n} 原文「{mi}」')); target = m0
            elif (m0['number'], u) in mp: st['b_keep_ms'] += 1; target = m0
            else: st['b_unresolved'] += 1; lst.append((d['id'], d['title'], 'b_unresolved', f'jc={n}{u} ms={m0["number"]}{u} 原文「{mi}」')); target = m0
        else:
            if not mi or (n, u) in mp or not ms:
                m_new = {'unit': u, 'number': n}; ms.append(m_new); target = m_new
                st['c_add' if ms[:-1] else 'c_create'] += 1
            elif not any(m['number'] == n for m in ms):
                m_new = {'unit': u, 'number': n}; ms.append(m_new); target = m_new
                st['c_add_unverified'] += 1; lst.append((d['id'], d['title'], 'c_add_unverified', f'jc={n}{u} 原文「{mi}」未提及，measures 无同数，已按 jc 追加'))
            else:
                st['c_drop_inconsistent'] += 1; lst.append((d['id'], d['title'], 'c_drop', f'jc={n}{u} 与 measures 同数异单位（单位误标），已丢弃 jc；原文「{mi}」')); target = None
        if desc and target is not None and desc != mi:
            target['note'] = desc if not target.get('note') else target['note']; st['e_desc_to_note'] += 1
        d['measures'] = ms
    if KEEP and 'measures' in d and False: pass
    new = {}
    for k, v in d.items():
        if k == 'juan_count' and (not KEEP or n in (0, None)): continue
        new[k] = v
    if 'measures' in d and 'measures' not in new: new['measures'] = d['measures']
    # 键序：measures 紧跟原位置
    if APPLY:
        open(p, 'w', encoding='utf-8').write(json.dumps(new, ensure_ascii=False, indent=ind) + nl)
print(dict(st))
if OUT:
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('work_id\ttitle\tkind\tdetail\n')
        for r in lst: f.write('\t'.join(r) + '\n')
