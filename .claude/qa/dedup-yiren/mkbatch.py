#!/usr/bin/env python3
"""新-异人登记-經未：由逐对判定（final.json）生成并条批次（apply_3a.py 格式）、keeper 责任者勘误（dedup-3c/apply_fixes.py 格式）与 dedup-judged 登记。

    python3 mkbatch.py <final.json> <clusters.json> <base sha> <批次目录>
"""
import glob, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
UNIT = '新-异人登记-經未'


def load(kind, i):
    d = {'w': 'Work', 'e': 'Entity'}[kind]
    p = glob.glob(os.path.join(ROOT, d, i[-3], i[-2], i[-1], i + '-*.json'))
    return json.load(open(p[0], encoding='utf-8')) if p else None


ENT = None
def ent_by_name(n):
    global ENT
    if ENT is None:
        ENT = {}
        for p in glob.glob(os.path.join(ROOT, 'Entity', '*', '*', '*', '*.json')):
            d = json.load(open(p, encoding='utf-8'))
            if d.get('subtype') == 'people' and not d.get('merged_into'):
                ENT.setdefault(d.get('primary_name'), []).append(d['id'])
    v = ENT.get(n) or []
    return v[0] if len(v) == 1 else None


def main():
    fin, clf, base, out = sys.argv[1:5]
    F = json.load(open(fin, encoding='utf-8'))
    CL = json.load(open(clf, encoding='utf-8'))
    groups, fixes = [], []
    for n, o in enumerate(CL, 1):
        cid = 'YJ-%04d' % n
        ids = [o['keeper']] + o['losers']
        if any(load('w', i).get('merged_into') for i in ids):
            print('跳过（成员已成墓碑）', cid, ids); continue
        ev = '；'.join(dict.fromkeys(o['whys']))
        groups.append({'case_id': cid, 'cluster_id': 'yiren-jing-' + cid, 'type': 'work', 'keeper': o['keeper'], 'losers': o['losers'],
                       'keeper_source': '去重新-异人登记-經未 首位异人同题组逐对判（book-index %s）' % base[:10],
                       'evidence': ev, 'why': ev,
                       'rule': '去重第二轮细拆 新-异人登记-經未：同题首位责任者异写／误字／占位名或编撰分署，原文自证同书，逐对判并（双盲：判定与复核分由不同子 agent）'})
        k = load('w', o['keeper']); a0 = (k.get('authors') or [{}])[0]
        for old, new in o['renames']:
            if a0.get('name') != old:
                continue
            new = new.split('、')[0]
            eid = None
            for l in o['losers']:
                la = (load('w', l).get('authors') or [{}])[0]
                if la.get('name') == new and la.get('entity_id'):
                    eid = la['entity_id']
            eid = eid or ent_by_name(new) or ''
            fixes.append({'wid': o['keeper'], 'idx': 0, 'old': old, 'new': new, 'kind': '误字／异称', 'entity_new': eid,
                          'basis': '去重 %s %s：%s' % (UNIT, cid, ev[:300])})
            break
    os.makedirs(out, exist_ok=True)
    json.dump({'groups': groups}, open(os.path.join(out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    json.dump(fixes, open(os.path.join(out, 'fixes.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    rows = []
    for k, (d, why, src) in sorted(F['J'].items()):
        if d == '并':
            continue
        a, b = k.split('|')
        rows.append('\t'.join([a, b, d, why.replace('\t', ' ').replace('\n', ' ')]))
    open(os.path.join(ROOT, '.claude', 'qa', 'dedup-judged', UNIT + '.tsv'), 'w', encoding='utf-8').write(
        '# %s（首位责任者异姓／朝代不同的同题组，經部＋未分类）判为分立 C／存疑 D 的对，不并；基线 main %s；口径与流程见 .claude/qa/dedup-yiren/README.md\n' % (UNIT, base[:10]) + '\n'.join(rows) + '\n')
    print('并 %d 组，勘误 %d 处，登记 %d 对' % (len(groups), len(fixes), len(rows)))


if __name__ == '__main__':
    main()
