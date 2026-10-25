#!/usr/bin/env python3
"""部分 7b 第二批：普查余下的善后缺口，逐条查明后机械收口。乾跑默认，--apply 才写。

1. Work 墓碑 merged_into 误写草稿 id（10 個）：草稿已晉升者經 promotions 換正式 id；未晉升而草稿自身
   merged_into 正式條者取其值。keeper 補 merged_in 一項。
2. 分類成員行指墓碑（12 行）：keeper 皆已在分類樹，按「keeper 只掛第一個節點」刪墓碑行，
   同節點者把來源併入 keeper 行；被刪行登記 分類互斥.tsv。
3. related_works 指向已併入自身之墓碑（2 處）：刪。indexed_by.in_note_of 指墓碑（1 處）：改指 keeper。
之後跑 ../../fix_tomb_refs.py 收 promotions。
"""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '../../../..'))
DRAFT = os.path.join(ROOT, '../book-index-draft')
sys.path.insert(0, os.path.join(ROOT, '.claude/qa'))
import backrefs  # noqa: E402
apply = '--apply' in sys.argv
os.chdir(ROOT)
tomb, live, path = {}, set(), {}
for t, p, d in backrefs.iter_records(ROOT):
    path[d['id']] = p
    (tomb.__setitem__(d['id'], d['merged_into']) if d.get('merged_into') else live.add(d['id']))
promos = {}
for p in glob.glob('promotions/*.json'):
    promos.update(json.load(open(p, encoding='utf-8'))['promotions'])
print('载入 墓碑 %d 活条 %d promotions %d' % (len(tomb), len(live), len(promos)))
assert tomb and live and promos


def fin(i):
    while i in tomb:
        i = tomb[i]
    return i


def load(i):
    raw = open(path[i], encoding='utf-8').read()
    return raw, json.loads(raw)


def save(i, d, raw):
    if apply:
        open(path[i], 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + ('\n' if raw.endswith('\n') else ''))


log = open(os.path.join(HERE, 'changes.tsv'), 'w', encoding='utf-8')
log.write('类别\tid\t原值\t新值\t依据\n')

# 1
for i, tgt in sorted(tomb.items()):
    if tgt in tomb or tgt in live:
        continue
    pid = (promos.get(tgt) or {}).get('production_id')
    why = 'promotions：草稿 %s 晉升為 %s' % (tgt, pid)
    if not pid:
        g = glob.glob(os.path.join(DRAFT, '*', tgt[-3], tgt[-2], tgt[-1], tgt + '-*.json'))
        pid = g and json.load(open(g[0], encoding='utf-8')).get('merged_into')
        why = '草稿 %s 自身 merged_into %s' % (tgt, pid)
    if not pid or fin(pid) not in live:
        print('无解', i, tgt)
        continue
    k = fin(pid)
    raw, d = load(i)
    d['merged_into'] = k
    save(i, d, raw)
    kraw, kd = load(k)
    if i not in {m.get('id') if isinstance(m, dict) else m for m in kd.get('merged_in') or []}:
        kd.setdefault('merged_in', []).append({'id': i, 'title': d.get('title'), 'at': '2026-10-25', 'by': '去重方案部分7b',
                                               'why': '墓碑 merged_into 原誤寫草稿 id %s；%s' % (tgt, why)})
        save(k, kd, kraw)
    log.write('墓碑\t%s\t%s\t%s\t%s\n' % (i, tgt, k, why))
    print('墓碑', i, d.get('title'), tgt, '->', k)
    tomb[i] = k

# 2
mutex = open(os.path.join(HERE, '分類互斥.tsv'), 'w', encoding='utf-8')
mutex.write('被併者\tkeeper\t原節點\t來源\tkeeper 節點\n')
rows = {}
files = sorted(glob.glob('classification/zongmu/members/*.json'))
for p in files:
    for r in json.load(open(p, encoding='utf-8'))['members']:
        rows.setdefault(r[0], []).append(os.path.basename(p)[:-5])
for p in files:
    raw = open(p, encoding='utf-8').read()
    d = json.loads(raw)
    node, out, n = d['node'], [], 0
    for r in d['members']:
        if r[0] not in tomb:
            out.append(r)
            continue
        k = fin(r[0])
        n += 1
        mutex.write('%s\t%s\t%s\t%s\t%s\n' % (r[0], k, node, r[1] if len(r) > 1 else '', ','.join(rows.get(k, []))))
        log.write('分類成員\t%s\t%s\t刪\tkeeper 已在 %s\n' % (r[0], node, ','.join(rows.get(k, []))))
        print('分類', node, r[0], '刪；keeper', k, rows.get(k))
    for r in out:   # 同節點：被併者來源併入 keeper 行
        for l in d['members']:
            if l[0] in tomb and fin(l[0]) == r[0] and len(l) > 1 and len(r) > 1:
                srcs = r[1].split(';')
                for s in l[1].split(';'):
                    if s not in srcs:
                        srcs.append(s)
                r[1] = ';'.join(srcs)
    if n and apply:   # 成員檔一行一項，按行改以保原格式
        want = {r[0]: r for r in out}
        lines = []
        for line in raw.split('\n'):
            m = re.match(r'\s*\["([0-9a-z]+)"', line)
            if m and m.group(1) not in want:
                continue
            if m:
                line = re.sub(r'\[.*\]', json.dumps(want[m.group(1)], ensure_ascii=False), line)
            lines.append(line)
        text = re.sub(r',(\n\s*\])', r'\1', '\n'.join(lines))
        assert json.loads(text)['members'] == out
        open(p, 'w', encoding='utf-8').write(text)

# 3
for i in sorted(live):
    if not path[i].startswith(os.path.join(ROOT, 'Work')):
        continue
    raw = open(path[i], encoding='utf-8').read()
    if not any(t in raw for t in ('related_works', 'in_note_of')):
        continue
    d = json.loads(raw)
    ch = False
    rel = d.get('related_works') or []
    keep = [r for r in rel if not (isinstance(r, dict) and r.get('id') in tomb and fin(r['id']) == i)]
    if len(keep) != len(rel):
        for r in rel:
            if r not in keep:
                log.write('related 自指\t%s\t%s\t刪\t所指墓碑已併入本條\n' % (i, r['id']))
                print('related 自指刪', i, r['id'])
        if keep:
            d['related_works'] = keep
        else:
            del d['related_works']
        ch = True
    for n in d.get('indexed_by') or []:
        if isinstance(n, dict) and n.get('in_note_of') in tomb and fin(n['in_note_of']) != i:
            log.write('in_note_of\t%s\t%s\t%s\t順 merged_into\n' % (i, n['in_note_of'], fin(n['in_note_of'])))
            print('in_note_of', i, n['in_note_of'], '->', fin(n['in_note_of']))
            n['in_note_of'] = fin(n['in_note_of'])
            ch = True
    if ch:
        save(i, d, raw)
