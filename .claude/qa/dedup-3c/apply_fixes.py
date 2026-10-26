#!/usr/bin/env python3
"""3c：同題異作者中的責任者名誤字、異體與佔位名勘誤（只改 authors[].name／dynasty 等少數字段）。

用法：python3 .claude/qa/dedup-3c/apply_fixes.py fixes.json [--apply]
fixes.json 每項：{wid, idx, old, new, kind, basis, dyn_new?, entity_new?（"" 表示去掉）, role_new?, title_new?, drop_author?}
乾跑只列 diff；--apply 寫回，原名存 authors[idx].original_name，依據寫 name_basis，revision 補位 +1。
"""
import json, sys, os, glob, datetime
ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
TODAY = datetime.date.today().isoformat()
PERIOD = {'明': 'ming', '清': 'qing', '唐': 'sui-tang', '北宋': 'song', '南宋': 'song', '西夏': 'liao-jin-yuan', '金': 'liao-jin-yuan', '元': 'liao-jin-yuan',
          '北齊': 'nanbeichao', '南朝梁': 'nanbeichao', '南朝陳': 'nanbeichao', '東晉': 'jin', '西漢': 'qin-han', '三國吳': 'three-kingdoms', '周': 'pre-qin'}

def path_of(wid):
    m = glob.glob(os.path.join(ROOT, 'Work', '*', '*', '*', wid + '*.json'))
    assert len(m) == 1, (wid, m)
    return m[0]

def bump(rev):
    a = [int(x) for x in (rev or '1.0.0').split('.')]
    a[2] += 1
    return '.'.join(map(str, a))

def main():
    fixes = json.load(open(sys.argv[1], encoding='utf-8'))
    apply = '--apply' in sys.argv
    print('載入', len(fixes), '項', file=sys.stderr)
    assert fixes, '0 項'
    by = {}
    for f in fixes:
        by.setdefault(f['wid'], []).append(f)
    n = 0
    for wid, fs in sorted(by.items()):
        p = path_of(wid)
        d = json.load(open(p, encoding='utf-8'))
        if d.get('merged_into'):
            print('跳過（已成墓碑）', wid, d['merged_into'], file=sys.stderr); continue
        if any(len(d.get('authors') or []) <= f['idx'] or d['authors'][f['idx']].get('name') != f['old'] for f in fs):
            print('跳過（main 上作者已變）', wid, file=sys.stderr); continue
        notes = []
        for f in sorted(fs, key=lambda x: -x['idx']):
            a = d['authors'][f['idx']]
            assert a['name'] == f['old'], (wid, a['name'], f['old'])
            if f.get('drop_author'):
                d['authors'].pop(f['idx'])
                notes.append(f"刪去 authors[{f['idx']}]「{f['old']}」：{f['basis']}")
                continue
            if f['new'] != f['old']:
                a.setdefault('original_name', f['old'])
                a['name'] = f['new']
            if f.get('dyn_new'):
                old_dyn = a.get('dynasty')
                a['dynasty'] = f['dyn_new']
                # 作品朝代由此撰人傳播而來者一併改
                if f['idx'] == 0 and d.get('dynasty') == old_dyn and old_dyn:
                    d['dynasty'] = f['dyn_new']
                    d['dynasty_basis'] = 'manual：3c 勘誤，據撰人朝代改'
                    if (d.get('period_basis') or '').startswith('據 authors[0].dynasty'):
                        d['period_basis'] = f"據 authors[0].dynasty「{f['dyn_new']}」"
                        if PERIOD.get(f['dyn_new']):
                            d['period'] = PERIOD[f['dyn_new']]
            if 'entity_new' in f:
                if f['entity_new']:
                    a['entity_id'] = f['entity_new']
                else:
                    a.pop('entity_id', None)
            if f.get('role_new'):
                a['role'] = f['role_new']
            a['name_basis'] = f['basis']
            if f.get('title_new'):
                if 'original_title' not in d:
                    d['original_title'] = d['title']
                d['title'] = f['title_new']
            notes.append(f"authors[{f['idx']}]「{f['old']}」→「{f['new']}」{('，朝代→'+f['dyn_new']) if f.get('dyn_new') else ''}")
        d['revision'] = bump(d.get('revision'))
        d['revised_at'] = TODAY
        d['ai_note'] = ((d.get('ai_note') or '') + ('；' if d.get('ai_note') else '') + '3c 責任者名勘誤（' + TODAY + '）：' + '；'.join(notes))
        n += 1
        print(wid, d['title'], '｜', '；'.join(notes))
        if apply:
            open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    print(('已寫' if apply else '乾跑'), n, '個 Work', file=sys.stderr)

if __name__ == '__main__':
    main()
