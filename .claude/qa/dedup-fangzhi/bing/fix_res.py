#!/usr/bin/env python3
"""方志-并善后：并条时随被并条搬进 keeper 的错修次影像资源，摘下改挂到所属修次的 Work（无所属 Work 的只摘下并登记）。

    python3 fix_res.py <清单.tsv> [--apply]

清单列：keeper、资源 url、应挂 Work id（空＝只摘）、依据。原值写入同目录 <清单>-原值.json。"""
import glob, json, sys, os, urllib.parse
U = lambda s: urllib.parse.unquote(s or "")
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../../..'))
TODAY = '2026-10-26'
def path(i): return glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
def bump(rev):
    a, b, c = (rev or '1.0.0').split('.'); return '%s.%s.%d' % (a, b, int(c) + 1)
rows = [l.rstrip('\n').split('\t') for l in open(sys.argv[1], encoding='utf-8') if l.strip() and not l.startswith('#')]
apply = '--apply' in sys.argv; orig = {}
print('载入 %d 条' % len(rows))
if not rows: sys.exit('载入为 0，停')
for k, url, tgt, why in rows:
    kp = path(k); kd = json.load(open(kp, encoding='utf-8'))
    hit = [r for r in kd.get('resources') or [] if U(r.get('url')) == U(url)]
    if not hit: print('keeper 上无此资源，跳过', k, url[-50:]); continue
    orig.setdefault(k, {'resources': json.loads(json.dumps(kd.get('resources')))})
    kd['resources'] = [r for r in kd['resources'] if U(r.get('url')) != U(url)]
    note = '%s 方志-并善後：資源「%s」屬另一修次（%s），自本條摘下%s。' % (TODAY, url.rsplit('/', 1)[-1][:80], why, '，改掛 ' + tgt if tgt else '；庫中未有其修次之條，暫不掛')
    kd['ai_note'] = ((kd.get('ai_note') or '') + '\n\n' + note).strip()
    kd['revision'] = bump(kd.get('revision')); kd['revised_at'] = TODAY
    if apply: open(kp, 'w', encoding='utf-8').write(json.dumps(kd, ensure_ascii=False, indent=2) + '\n')
    if tgt:
        tp = path(tgt); td = json.load(open(tp, encoding='utf-8'))
        if any(U(r.get('url')) == U(url) for r in td.get('resources') or []): print('目标已有', tgt); continue
        orig.setdefault(tgt, {'resources': json.loads(json.dumps(td.get('resources')))})
        r = dict(hit[0]); r.pop('group', None); r.pop('group_role', None)
        td.setdefault('resources', []).append(r)
        td['revision'] = bump(td.get('revision')); td['revised_at'] = TODAY
        if apply: open(tp, 'w', encoding='utf-8').write(json.dumps(td, ensure_ascii=False, indent=2) + '\n')
    print('改', k, '->', tgt or '（只摘）', url[-50:])
if apply: json.dump(orig, open(sys.argv[1].rsplit('.', 1)[0] + '-原值.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
