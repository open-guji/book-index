#!/usr/bin/env python3
"""3a 第三轮：由 dossier.jsonl 生成 apply_3a.py 批次规格与存疑清单。

    python3 mkbatch.py <dossier.jsonl> <base sha> <批次目录前缀>

A 档 → <前缀>-01/batch.json；B 档（逐组人工复核过，REJECT 里的退存疑）→ <前缀>-02/batch.json；
C／D 档与 REJECT → 存疑-第三轮.tsv 与 ../../dedup-judged/3a-第三轮.tsv。
keeper：优先自有著录（非继承丛书撰者）的 Work，次取 Book 多者，再取 id 小者。"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# B 档复核判不并（见 README）
REJECT = {'攝大乘論釋': '一為世親釋、一為無性釋，同題異書',
          '小兒語': '呂得勝《小兒語》與呂坤《續小兒語》等混挂，卷數一、六不一，待拆'}
# C 档复核可并（「家谱」因部类误触发、朝代相邻、撰人异名同人）
PROMOTE = {'春秋日南至譜': '成蓉鏡即成孺，非族譜', '中饋錄': '非族譜', '硯史': '非族譜', '周甲錄': '非族譜',
           '梅邊吹笛譜': '詞集，非族譜', '周公年表': '牟廷相即牟庭，非族譜', '北遊集': '宋末元初與元相容',
           '續神仙傳': '沈汾南唐人，唐／南唐相容', '異魚圖贊': '非族譜；一卷本（升菴合集）另存疑'}
# 组内剔出、另存疑的成员（丛编一卷选本不并入多卷本）
DROP = {'d59fy5ok79c0': '學海類編一卷本，夢蕉詩話原二卷，選本不並', 'd59fyivdpo8w': '總纂升菴合集一卷本，異魚圖贊原四卷，選本不並'}


def desc(w):
    a = w['authors'][0]
    return '《%s》%s(%s,%s卷,%d版本%s)' % (w['title'], a['name'], a.get('dynasty') or '?',
                                      '/'.join(map(str, w['juan'])) or '?', w['nbooks'], ',繼承叢書撰者' if w['inherited'] else '')


def main():
    src, base, pre = sys.argv[1:4]
    L = [json.loads(l) for l in open(src, encoding='utf-8')]
    out = {'A': [], 'B': []}
    hold, judged = [], []
    n = 0
    for x in L:
        n += 1
        cid = 'R3-%04d' % n
        ws = [w for w in x['works'] if w['id'] not in DROP]
        for w in x['works']:
            if w['id'] in DROP:
                hold.append('\t'.join([x['bulei'], cid, 'B-剔出', '%s《%s》' % (w['id'], w['title']), DROP[w['id']], '']))
                judged.append('\t'.join([ws[0]['id'], w['id'], 'D', '3a第三轮 %s 剔出：%s' % (cid, DROP[w['id']])]))
        t = x['tier']
        if x['key'] in PROMOTE and t == 'C':
            t = 'B'; x['why'] = x['why'] + '；复核：' + PROMOTE[x['key']]
        if t == 'X':
            continue
        if t in 'AB' and x['key'] not in REJECT:
            k = sorted(ws, key=lambda w: (w['inherited'], -w['nbooks'], w['id']))[0]
            ev = '同题同首位责任者：' + '／'.join(desc(w) for w in ws) + '；'
            if t == 'A':
                ev += '题名归一后相同（简繁异体），首位责任者同名、朝代兼容、卷数上限差≤1或一侧缺、无丛编分体子目缺卷、著作领域不冲突'
                rule = '去重方案部分3a第三轮：补撰人与国書子目对后同题同首位（含混合组内同首位子簇） A 档机械并'
            else:
                ev += 'B 档逐组复核判同一作品（flags=%s）' % x['why']
                rule = '去重方案部分3a第三轮：补撰人与国書子目对后同题同首位（含混合组内同首位子簇） B 档逐组复核并'
            out[t].append({'case_id': cid, 'cluster_id': '3a-' + cid, 'type': 'work', 'keeper': k['id'],
                           'losers': [w['id'] for w in ws if w['id'] != k['id']],
                           'keeper_source': '去重方案部分3a第三轮 同题同首位责任者普查（book-index %s）' % base[:10],
                           'evidence': ev, 'rule': rule, 'why': ev})
            continue
        why = REJECT.get(x['key']) or x['why']
        st = {'C': 'C-' + why.split(':')[0], 'D': 'D-异entity'}.get(t, 'B-复核不并')
        hold.append('\t'.join([x['bulei'], cid, st, ' ／ '.join('%s《%s》' % (w['id'], w['title']) for w in ws), why, '']))
        for w in ws[1:]:
            judged.append('\t'.join([ws[0]['id'], w['id'], 'D', '3a第三轮 %s %s：%s' % (cid, st, why)]))
    for t, d in (('A', '-01'), ('B', '-02')):
        os.makedirs(pre + d, exist_ok=True)
        json.dump({'groups': out[t]}, open(pre + d + '/batch.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(os.path.join(HERE, '..', '存疑-第三轮.tsv'), 'w', encoding='utf-8').write(
        '部\t组\t状态\t成员\t依据\t需拆分/清理\n' + '\n'.join(hold) + '\n')
    open(os.path.join(HERE, '..', '..', 'dedup-judged', '3a-第三轮.tsv'), 'w', encoding='utf-8').write(
        '# 部分3a第三轮（补撰人与国書子目对后同题同首位（含混合组内同首位子簇））存疑对；基线 main %s；明细见 .claude/qa/dedup-3a/存疑-第三轮.tsv\n' % base[:10] + '\n'.join(judged) + '\n')
    print({k: len(v) for k, v in out.items()}, 'hold', len(hold))


if __name__ == '__main__':
    main()
