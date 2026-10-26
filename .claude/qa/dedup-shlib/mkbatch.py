#!/usr/bin/env python3
"""据人工过目后的组清单（每行：keeper loser...[ \t# 备注]）与上图 work 号生成 batch.json。
用法：mkbatch.py <清单.tsv> <输出 batch.json> <基线 sha>
清单列：上图work<TAB>keeper<TAB>losers(逗号)<TAB>判据档(A/B)<TAB>人工依据"""
import json, sys, glob, os
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
def load(i):
    return json.load(open(glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')[0], encoding='utf-8'))
def live(i, n=0):
    d = load(i)
    while d.get('merged_into') and n < 10:
        i = d['merged_into']; d = load(i); n += 1
    return i
def brief(d):
    au = '、'.join(a.get('name') or '' for a in d.get('authors') or [])
    jc = d.get('juan_count'); jc = jc.get('number') if isinstance(jc, dict) else jc
    return f"《{d['title']}》{au}({d.get('dynasty') or '-'},{jc if jc is not None else '-'}卷)"
src, out, base = sys.argv[1:4]
groups = []
for line in (l for l in open(src, encoding='utf-8') if l.strip() and not l.startswith('#')):
    wu, keeper, losers, tier, why = line.rstrip('\n').split('\t')
    losers = losers.split(',')
    # 基线之后别的单元可能已并：keeper 已成墓碑的整组跳过；已并入 keeper 的被并者剔除
    if live(keeper) != keeper:
        print('跳过（keeper 已并入他条）', keeper, '->', live(keeper)); continue
    gone = [l for l in losers if live(l) != l]
    if any(live(l) != keeper for l in gone):
        print('跳过（被并者已并入别的 keeper）', keeper, gone); continue
    if gone: print('剔除已并入 keeper 的被并者', keeper, gone)
    losers = [l for l in losers if l not in gone]
    if not losers: print('跳过（全组已由别的单元并完）', keeper); continue
    k = load(keeper); ls = {l: load(l) for l in losers}
    ev = (f"上图藏书 work_uri {wu} 与《中國古籍總目》同一 work（instanceOf），经总目 instance 落到本组各 Work；"
          + '／'.join(brief(x) for x in [k] + list(ls.values())) + '；' + why)
    groups.append({'case_id': f'SH{len(groups)+1:04d}', 'cluster_id': f'上图-并-{wu}', 'type': 'work', 'keeper': keeper, 'losers': losers,
                   'keeper_source': f'去重细拆上图-并：A6 去重线索（book_index_json A6-研究-20261025）在 book-index {base[:10]} 重算',
                   'evidence': ev, 'rule': f'去重细拆上图-并 {tier} 档：总目同一 work＋题名归一同／异写＋首位责任者同一＋卷数朝代相容',
                   'why': ev,
                   'loser_original_notes': {l: {kk: d.get(kk) for kk in ('description', 'ai_note') if d.get(kk)} for l, d in ls.items()}})
json.dump({'groups': groups}, open(out, 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('groups', len(groups))
