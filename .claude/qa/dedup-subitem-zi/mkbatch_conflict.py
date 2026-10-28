#!/usr/bin/env python3
"""冲突簇（clusters.json 中 conflict 非空）人读后的并条方案 → batch.json。
人读判定写在 PLAN：键为簇序号（conflict 簇内序），值为 (keeper, 额外并入, 排除, 依据)。keeper=None 时取有玉函山房輯佚書著录者。
用法：mkbatch_conflict.py <clusters.json> <输出目录> [--base sha]"""
import glob, json, os, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../..'))
def load(i):
    p = glob.glob(f'{ROOT}/Work/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json'); assert len(p) == 1, (i, p)
    return json.load(open(p[0], encoding='utf-8'))
YUHAN = '玉函山房輯佚書本：原書所載玉函山房輯佚書本與總目馬國翰輯本同為一卷，總目另有同題一卷複本，同一輯佚本'
PLAN = {
  1: ('d59f27ywcv7m', [], [], '九章算術：同題同書，劉徽注／李淳風等注釋／李籍音義／戴震訂訛補圖各本均為九章算術一書之注本、校本、音義附本；總目無獨立書名'),
  3: ('d59ezkwuylts', ['d59fymbuwirl'], [], '呂氏春秋二十六卷：高誘注本、畢沅輯校本為同一書之注校本，題名卷數同'),
  4: ('d59f2079wt8g', [], [], '周髀算經二卷：趙爽注、甄鸞重述、李籍音義、孔繼涵校刻各本同為周髀算經之版本，題名卷數同'),
  6: ('d59fy107uxhd', [], ['d59f2evrm6f4'], '尸子二卷存疑一卷：汪繼培輯本與總目湖海樓叢書本同卷；原書尸子（尸佼）未並，因輯本各家不同'),
  15: (None, [], [], '種樹書三卷：總目單書著錄列夷門廣牘本，周履靖編為夷門廣牘編刻者'),
  21: (None, [], [], '質龜論一卷：總目單書著錄列夷門廣牘本，周履靖編為夷門廣牘編刻者'),
  22: ('d59f2ngmxsle', [], [], '食色紳言：皆春居士即龍遵敍（總目作皆春居士（龍遵敍）撰），同書'),
  24: ('d59ezaie8u80', [], [], '鶡冠子三卷：陸佃解本、朱養和訂本為同一書之注校本，題名卷數同'),
  25: ('d59f2mtnqt4w', [], [], '黃帝授三子玄女經一卷：總目單書著錄列各叢書本（夷門廣牘、津逮秘書、藝海珠塵、平津館等），孫星衍校、周履靖編、繆希雍為各叢書本題署'),
}
for k in (0,2,5,7,9,10,11,12,13,16,17,18,19,20,23,26): PLAN[k] = (None, [], [], YUHAN)
def main():
    C = [c for c in json.load(open(sys.argv[1])) if c['conflict']]
    out = sys.argv[2]; base = sys.argv[sys.argv.index('--base') + 1] if '--base' in sys.argv else ''
    groups = []
    for k, (keeper, extra, excl, why) in sorted(PLAN.items()):
        c = C[k]; ids = [i for i in c['ids'] if i not in excl] + extra
        if keeper and keeper not in ids: ids.append(keeper)
        live = {}
        for i in ids:
            d = load(i)
            if not d.get('merged_into'): live[i] = d
        if keeper is None:
            keeper = next((i for i, d in live.items() if any(e.get('source') == '玉函山房輯佚書' for e in d.get('indexed_by', []))), None) \
                or max(live, key=lambda i: (bool(live[i].get('authors')), len(live[i].get('indexed_by') or []), -int(i, 36)))
        assert keeper in live, (k, keeper)
        losers = sorted(set(live) - {keeper})
        if not losers: continue
        ev = '同題《%s》：%s' % (c['key'], why)
        notes = {l: {'ai_note': live[l].get('ai_note'), 'description': (live[l].get('description') or {}).get('text') if isinstance(live[l].get('description'), dict) else live[l].get('description')} for l in losers}
        groups.append({'case_id': keeper, 'cluster_id': 'subzi-c-%s' % keeper, 'type': 'work', 'keeper': keeper, 'losers': losers,
          'keeper_source': '去重方案新-子目异名-子 冲突簇人读判定（book-index %s，.claude/qa/dedup-subitem-zi/mkbatch_conflict.py）' % base,
          'evidence': ev, 'rule': '去重方案新-子目异名-子：冲突簇人读——A/B 档经总目互见或同叢書本相连，D 档仅因注校辑编层次或撰人署名不同；同一书的注校音义本、叢書编刻者署名、玉函山房輯佚本并入，不同辑者的辑佚本、异姓撰人不并',
          'why': ev, 'loser_original_notes': notes, 'levels': c['levels']})
    os.makedirs(out, exist_ok=True)
    json.dump({'groups': groups}, open(os.path.join(out, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    print(len(groups), '组', sum(len(g['losers']) for g in groups), '条被并')
    for g in groups: print(g['keeper'], g['evidence'][:20], len(g['losers']))
main()
