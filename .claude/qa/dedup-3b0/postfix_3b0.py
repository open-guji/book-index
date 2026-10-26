#!/usr/bin/env python3
"""3b-0 并条后的署名善后（apply_3b0 与 postfix_common 之后跑）：
1. author_fix：keeper 首位撰人无 entity_id、簇内他条同名撰人已繫 Entity（mkbatch 已核主名／别名含规范名）：补繫；
2. alias_add：被并条的署名异写（字號形、异写、讹形）不在该 Entity 主名／alt_names 中的，补进 alt_names，
   type 按理由取 訛名／異體／別稱（字號带姓的著录形不当「字」「號」，一律 別稱），note 记来源与簇号。
   泛称（某氏、某君）、误切、衍字、省称不补；
3. postfix_common 依被并条给 keeper 同名撰人补繫的 entity：被并条原繫有误者（核验所见）撤回，列在 UNDO_COMMON。
原值写入 <batch>/postfix_3b0-原值.json。用法：postfix_3b0.py <batch 目录> [--apply]"""
import json, sys, os, glob, re, subprocess
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
TODAY = '2026-10-25'
# 被并条的同名撰人误繫他人 Entity，postfix_common 照搬到 keeper 者：撤回（簇号 → 撰人名）
UNDO_COMMON = {'3b0-029': '王畹'}
SKIP_CID = {'3b0-007', '3b0-042', '3b0-203', '3b0-293', '3b0-294', '3b0-366', '3b0-385', '3b0-435'}
def path(kind, i): return glob.glob(f'{ROOT}/{kind}/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0]
def norm(x): return x if isinstance(x, str) else x.get('name')
def bump(f, j, level):
    rel = os.path.relpath(f, ROOT)
    if not subprocess.run(['git', '-C', ROOT, 'diff', '--quiet', 'origin/main', '--', rel]).returncode:
        a, b, c = [int(x) for x in j.get('revision', '1.0.0').split('.')]
        j['revision'] = f'{a}.{b}.{c+1}' if level == 'patch' else f'{a}.{b+1}.0'
        if 'updated_at' in j and 'revised_at' not in j: j['updated_at'] = TODAY + 'T00:00:00+00:00'
        else: j['revised_at'] = TODAY
def atype(why):
    if re.search(r'讹|訛|之誤|误作', why): return '訛名'
    if re.search(r'异体|異體', why): return '異體'
    if re.search(r'避讳|避諱|唐讳', why): return '避諱'
    return '別稱'
def main():
    d = sys.argv[1]; apply = '--apply' in sys.argv
    G = json.load(open(os.path.join(d, 'batch.json'), encoding='utf-8'))['groups']
    orig, nw, ne, na = {}, 0, 0, 0
    for g in G:
        if g['cluster_id'] in UNDO_COMMON:
            f = path('Work', g['keeper']); j = json.load(open(f, encoding='utf-8'))
            for a in j.get('authors') or []:
                if a.get('name') == UNDO_COMMON[g['cluster_id']] and 'name_basis' in a and '並條善後' in a['name_basis']:
                    print(g['cluster_id'], 'work', j['id'], '撤回 postfix_common 补繫', a.pop('entity_id'), a.pop('name_basis'))
                    if apply: open(f, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
        fx = g.get('author_fix') or {}
        if fx.get('entity_id'):
            f = path('Work', g['keeper']); j = json.load(open(f, encoding='utf-8'))
            a = (j.get('authors') or [None])[0]
            if a and not a.get('entity_id'):
                orig.setdefault(j['id'], {})['authors'] = json.loads(json.dumps(j['authors']))
                a['entity_id'] = fx['entity_id']
                a['name_basis'] = f'{TODAY} 去重 3b-0 並條善後：同書署名異寫之重出條已繫此 entity，今補繫（{g["cluster_id"]}）。'
                bump(f, j, 'patch'); nw += 1
                print(g['cluster_id'], 'work', j['id'], 'entity_id <-', fx['entity_id'])
                if apply: open(f, 'w', encoding='utf-8').write(json.dumps(j, ensure_ascii=False, indent=2) + '\n')
        al = g.get('alias_add')
        if not al or g['cluster_id'] in SKIP_CID: continue
        f = path('Entity', al['entity_id']); e = json.load(open(f, encoding='utf-8'))
        known = {e.get('primary_name')} | {norm(x) for x in e.get('alt_names') or []}
        add = [x for x in al['names'] if x['name'] not in known and not re.search(r'[氏君]$', x['name'])
               and not re.search(r'误入|誤入|省|误切|衍', x['why'])]
        if not add: continue
        orig.setdefault(e['id'], {}).setdefault('alt_names', json.loads(json.dumps(e.get('alt_names'))))
        for x in add:
            e.setdefault('alt_names', []).append({'name': x['name'], 'type': atype(x['why']),
                'note': f'去重 3b-0（{g["cluster_id"]}）：同書重出條署此名，據「{x["why"]}」併條，記為著錄所見異稱。'})
            print(g['cluster_id'], 'entity', e['id'], e.get('primary_name'), '+', x['name'], atype(x['why'])); na += 1
        bump(f, e, 'patch'); ne += 1
        if apply: open(f, 'w', encoding='utf-8').write(json.dumps(e, ensure_ascii=False, indent=2) + '\n')
    if apply and orig:
        json.dump(orig, open(os.path.join(d, 'postfix_3b0-原值.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print('Work 补繫 %d，Entity 改 %d（补别名 %d）%s' % (nw, ne, na, '' if apply else '（乾跑）'))
if __name__ == '__main__': main()
