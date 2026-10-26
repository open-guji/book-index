#!/usr/bin/env python3
"""文淵閣／薈要（臺北故宮）同题 Book 挂多个 Work 的清理：先改挂错挂的 Book，再按 dedup-confirmed-163/apply_batch.py 并 Work。

    python3 apply_wy.py <plan.json> [--apply]

plan.json：{"rehang": [{"book", "from", "to", "key", "reason"}], "batch": "<同目录 batch.json>"}
改挂只动 Book.work_id，revision 升 minor，ai_note 记一行；台账写 rehang.json（含原 sha256）。
并 Work 部分直接调 apply_batch.main()（署名 A11-去重文淵閣Work），台账 merges.json。
"""
import argparse, glob, hashlib, json, os, subprocess, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(HERE, '..', 'dedup-confirmed-163'))
import apply_batch  # noqa: E402
apply_batch.BY = 'A11-去重文淵閣Work'
TODAY = apply_batch.TODAY


def book_path(i):
    h = glob.glob(os.path.join(ROOT, 'Book', *i[-3:], i + '-*.json')); assert len(h) == 1, (i, h); return h[0]


def rehang(items, apply):
    led = []
    for r in items:
        p = book_path(r['book']); raw = open(p, 'rb').read(); d = json.loads(raw)
        assert d.get('work_id') == r['from'], (r, d.get('work_id'))
        assert glob.glob(os.path.join(ROOT, 'Work', *r['to'][-3:], r['to'] + '-*.json')), r
        led.append({'book': r['book'], 'from': r['from'], 'to': r['to'], 'key': r['key'], 'reason': r['reason'],
                    'path': os.path.relpath(p, ROOT), 'sha256': hashlib.sha256(raw).hexdigest()})
        if not apply:
            print('rehang dry', r['book'], r['from'], '->', r['to']); continue
        d['work_id'] = r['to']
        d['revision'] = apply_batch.bump_minor(d.get('revision')); d['revised_at'] = TODAY
        line = '%s 去重（文淵閣／薈要同题多 Work 清理）：原挂 %s，改挂 %s。%s' % (TODAY, r['from'], r['to'], r['reason'])
        d['ai_note'] = (d['ai_note'] + '\n' + line) if d.get('ai_note') else line
        open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    return led


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('plan'); ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    plan = json.load(open(a.plan, encoding='utf-8')); out = os.path.dirname(os.path.abspath(a.plan))
    led = rehang(plan.get('rehang', []), a.apply)
    if a.apply:
        base = subprocess.check_output(['git', 'rev-parse', 'origin/main'], cwd=ROOT, text=True).strip()
        json.dump({'base': base, 'rehang': led}, open(os.path.join(out, 'rehang.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    if plan.get('batch'):
        sys.argv = ['apply_batch.py', os.path.join(out, plan['batch'])] + (['--apply'] if a.apply else [])
        apply_batch.main()


if __name__ == '__main__':
    main()
