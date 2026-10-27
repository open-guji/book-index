#!/usr/bin/env python3
"""新-待並條：判为分立（C）／存疑（D）的链接改注。用法：apply_notes.py <判定.tsv> [--apply]
判定.tsv 列：序号 A B 判定 keeper 理由（A 为存 related 一侧）。只改 A.related_works 中指向 B 且注含「待並條」的那一项的 note，
C → 「同題異書：…」，D → 「存疑未并：…」，并去掉「待並條」字样；不动其他字段。"""
import csv, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, '..'))
import mergework, jio  # noqa: E402
PEND = re.compile('待[並并][條条]')
DATE = '2026-10-26'


def newnote(verdict, why):
    if verdict.startswith('C'):
        return f'同題異書：{why}（去重链接定论 {DATE} 判 C 分立）'
    return f'存疑未并：{why}（去重链接定论 {DATE} 判 D 存疑，待核）'


def main():
    tsv, apply = sys.argv[1], '--apply' in sys.argv
    rows = [r for r in csv.DictReader((l for l in open(tsv, encoding='utf-8') if not l.startswith('#')), delimiter='\t')]
    done = miss = 0
    for r in rows:
        v = r['判定']
        if not (v.startswith('C') or v.startswith('D')):
            continue
        p = mergework.find('Work', r['A'])
        rel = os.path.relpath(p, jio.ROOT)
        d, fmt = jio.load(rel)
        hit = [x for x in d.get('related_works') or [] if x.get('id') == r['B'] and PEND.search(x.get('note') or '')]
        if not hit:
            miss += 1
            print('未找到', r['序号'], r['A'], r['B'])
            continue
        for x in hit:
            x['note'] = newnote(v, r['理由'])
        done += 1
        if apply:
            jio.save(rel, d, fmt)
    print(f'改注 {done}，未找到 {miss}' + ('' if apply else '（乾跑）'))


if __name__ == '__main__':
    main()
