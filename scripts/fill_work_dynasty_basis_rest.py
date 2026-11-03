#!/usr/bin/env python3
"""补完 dynasty_basis 缺口的余项（approx. 292 条；见 fill_work_dynasty_basis.py）。默认只报告，--apply 写入，--out 写判定清单 TSV。
判定规则（逐条可复核；判不了的也写依据，但以「存疑：」起首并入清单，不改 dynasty）：
 R1 作者朝代与 Work.dynasty 不一致：若 authors[0].dynasty 与 Work.period 相容（同朝代在库内的主流 period 相同），改 Work.dynasty 为作者朝代，
    dynasty_basis=「據 authors[0].dynasty「X」；原『Y』與作者及 period 不合，2026-11-03 改」；否则「存疑：…」不改。
 R2 作者无朝代：总目 indexed_by.author_info 以朝代起首且等于 Work.dynasty → 「據總目 author_info「…」朝代前綴「X」」；
    period_basis 写明据 Entity 传播 → 「同 period_basis（據 Entity 之 period 傳播）」；否则「存疑」。
 R3 无作者：period_basis 引用断代志「《補…志》」 → 「duandai：據《…》著錄所繫之代」；indexed_by 的 author_info/title_info 含朝代前缀等于 dynasty → 同 R2；
    否则「库内原有，未经本期复核」。"""
import json, glob, sys, re, collections as C
APPLY = '--apply' in sys.argv
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else None
# 库内 dynasty→主流 period
cnt = C.defaultdict(C.Counter); files = []
for p in glob.iglob('Work/*/*/*/*.json'):
    s = open(p, encoding='utf-8').read()
    d = json.loads(s)
    if d.get('merged_into'): continue
    if 'dynasty' in d and 'period' in d: cnt[d['dynasty']][d['period']] += 1
    if 'dynasty' in d and 'dynasty_basis' not in d: files.append((p, s, d))
dyn2per = {k: v.most_common(1)[0][0] for k, v in cnt.items()}
stat = C.Counter(); rows = []
for p, s, d in files:
    nl = '\n' if s.endswith('\n') else ''
    ind = 2
    for l in s.split('\n')[1:3]:
        if len(l) - len(l.lstrip()): ind = len(l) - len(l.lstrip()); break
    if json.dumps(d, ensure_ascii=False, indent=ind) + nl != s: stat['skip_format'] += 1; rows.append((d['id'], d['title'], 'format', '', '')); continue
    a = d.get('authors') or []; a0 = a[0] if a else {}; dyn = d['dynasty']; pb = d.get('period_basis') or ''
    ib = d.get('indexed_by') or []
    newdyn = None; basis = None; kind = None
    SYN = {'宋', '趙宋'}
    if a0.get('dynasty') and a0['dynasty'] != dyn and {a0['dynasty'], dyn} <= SYN:
        basis = f"synonym：Work.dynasty「{dyn}」與 authors[0].dynasty「{a0['dynasty']}」同指趙宋"; kind = 'R1s'
    elif a0.get('dynasty') and a0['dynasty'] != dyn:
        if d.get('period') and dyn2per.get(a0['dynasty']) == d['period'] and dyn2per.get(dyn) != d['period'] and (a0['dynasty'] in pb or (a0['dynasty'] == '三國魏' and '曹魏' in pb) or sum(cnt[dyn].values()) < 30):
            newdyn = a0['dynasty']; basis = f"據 authors[0].dynasty「{newdyn}」；原『{dyn}』與 period「{d['period']}」及作者朝代不合（2026-11-03 改）"; kind = 'R1'
        else:
            basis = f"存疑：Work.dynasty「{dyn}」與 authors[0].dynasty「{a0['dynasty']}」不一致，period「{d.get('period')}」，待複核"; kind = 'R1?'
    elif a and not a0.get('dynasty'):
        hit = next((e for e in ib if e.get('source') == '中國古籍總目' and (e.get('author_info') or '').startswith(dyn)), None)
        if hit: basis = f"據總目 author_info「{hit['author_info'][:30]}」朝代前綴「{dyn}」"; kind = 'R2'
        elif '傳播' in pb and 'Entity' in pb and dyn2per.get(dyn) == d.get('period'): basis = '同 period_basis（據撰人 Entity 之 period 傳播）'; kind = 'R2'
        else: basis = f"存疑：撰人無朝代，Work.dynasty「{dyn}」無可機械核驗之依據"; kind = 'R2?'
    elif not a and d.get('period') and dyn2per.get(dyn) != d['period']:
        basis = f"存疑：Work.dynasty「{dyn}」與 period「{d['period']}」不相容，待複核"; kind = 'R3?!'
    elif not a:
        m = re.search(r'《(補[^》]*志[^》]*)》', pb)
        hit = next((e for e in ib if any((e.get(k) or '').startswith(dyn) for k in ('author_info', 'title_info'))), None)
        if m and (dyn in pb or any(('繫' + dyn[-1] + '代') in (e.get('author_info') or '') for e in ib)): basis = f"duandai：據《{m.group(1)}》著錄所繫之代（同 period_basis）"; kind = 'R3'
        elif '出土簡帛' in pb: basis = '據出土簡帛抄本入葬之世斷代（同 period_basis）'; kind = 'R3'
        else: basis = '库内原有，未经本期复核'; kind = 'R3?'
    stat[kind] += 1; rows.append((d['id'], d['title'], kind, dyn + ('→' + newdyn if newdyn else ''), basis))
    if APPLY:
        new = {}
        for k, v in d.items():
            new[k] = newdyn if (k == 'dynasty' and newdyn) else v
            if k == 'dynasty': new['dynasty_basis'] = basis
        open(p, 'w', encoding='utf-8').write(json.dumps(new, ensure_ascii=False, indent=ind) + nl)
print(dict(stat))
if OUT:
    with open(OUT, 'w', encoding='utf-8') as f:
        f.write('work_id\ttitle\tkind\tdynasty\tbasis\n')
        for r in rows: f.write('\t'.join(r) + '\n')
