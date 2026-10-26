#!/usr/bin/env python3
"""3a 第二轮：由 dossier.jsonl 生成 apply_3a.py 批次规格与存疑清单。

    python3 mkbatch.py <dossier.jsonl> <base sha> <批次目录前缀>

A 档 → <前缀>-01/batch.json；B 档（逐组人工复核过，REJECT 里的退存疑）→ <前缀>-02/batch.json；
C／D 档与 REJECT → 存疑-第二轮.tsv 与 ../../dedup-judged/3a-第二轮.tsv。
keeper：优先自有著录（非继承丛书撰者）的 Work，次取 Book 多者，再取 id 小者。"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
# B 档复核判不并（见 README）
REJECT = {'瑜伽集要焰口施食儀': '一本有清釋受登編次，與不空譯原本當是不同儀軌本，待核'}


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
        cid = 'R2-%04d' % n
        ws = x['works']
        t = x['tier']
        if t == 'X':
            continue
        if t in 'AB' and x['key'] not in REJECT:
            k = sorted(ws, key=lambda w: (w['inherited'], -w['nbooks'], w['id']))[0]
            ev = '同题同首位责任者：' + '／'.join(desc(w) for w in ws) + '；'
            if t == 'A':
                ev += '题名归一后相同（简繁异体），首位责任者同名、朝代兼容、卷数上限差≤1或一侧缺、无丛编分体子目缺卷、著作领域不冲突'
                rule = '去重方案部分3a第二轮：獨撰子目补撰人后同题同首位 A 档机械并'
            else:
                ev += 'B 档逐组复核判同一作品（flags=%s）' % x['why']
                rule = '去重方案部分3a第二轮：獨撰子目补撰人后同题同首位 B 档逐组复核并'
            out[t].append({'case_id': cid, 'cluster_id': '3a-' + cid, 'type': 'work', 'keeper': k['id'],
                           'losers': [w['id'] for w in ws if w['id'] != k['id']],
                           'keeper_source': '去重方案部分3a第二轮 同题同首位责任者普查（book-index %s）' % base[:10],
                           'evidence': ev, 'rule': rule, 'why': ev})
            continue
        why = REJECT.get(x['key']) or x['why']
        st = {'C': 'C-' + why.split(':')[0], 'D': 'D-异entity'}.get(t, 'B-复核不并')
        hold.append('\t'.join([x['bulei'], cid, st, ' ／ '.join('%s《%s》' % (w['id'], w['title']) for w in ws), why, '']))
        for w in ws[1:]:
            judged.append('\t'.join([ws[0]['id'], w['id'], 'D', '3a第二轮 %s %s：%s' % (cid, st, why)]))
    for t, d in (('A', '-01'), ('B', '-02')):
        os.makedirs(pre + d, exist_ok=True)
        json.dump({'groups': out[t]}, open(pre + d + '/batch.json', 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(os.path.join(HERE, '..', '存疑-第二轮.tsv'), 'w', encoding='utf-8').write(
        '部\t组\t状态\t成员\t依据\t需拆分/清理\n' + '\n'.join(hold) + '\n')
    open(os.path.join(HERE, '..', '..', 'dedup-judged', '3a-第二轮.tsv'), 'w', encoding='utf-8').write(
        '# 部分3a第二轮（獨撰子目补撰人后同题同首位）存疑对；基线 main %s；明细见 .claude/qa/dedup-3a/存疑-第二轮.tsv\n' % base[:10] + '\n'.join(judged) + '\n')
    print({k: len(v) for k, v in out.items()}, 'hold', len(hold))


if __name__ == '__main__':
    main()
