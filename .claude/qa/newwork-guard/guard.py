#!/usr/bin/env python3
"""建前查重统一入口（G1）。所有会新建 Work 的车道在 --apply 前必须过它。

用法：
  python3 .claude/qa/newwork-guard/guard.py cands.tsv [--root ROOT] [--out hits.tsv]
    cands.tsv：每行 题名<TAB>首位责任者(可空)<TAB>备注/键(可空)，# 开头为注释
  输出每行：键 题名 状态 命中 Work id 命中题名 命中责任者 理由
    状态：DUP   归一后同题（含 additional_titles，前缀相同）且责任者相合或一侧缺 → 不要建，改挂/登记
          SAMETITLE-DIFFAUTH 同题但责任者两侧都有且不合 → 人看（可能是同名异书，也可能是撰人写法不同）
          NEAR  包含关系或编辑距离≤1（题名≥5字）→ 人看
          PREFIX 同主体但 [年号] 前缀不同或一侧缺（方志同名异修）→ 人看，不当重复
          NEW   未命中 → 可建
  --fail-on-dup：存在 DUP/NEAR/SAMETITLE-DIFFAUTH 则退出 1（供车道脚本在 --apply 前调用）

库调用：
  sys.path.insert(0, '.claude/qa/newwork-guard'); import guard
  g = guard.Guard(root); g.check(title, author) -> (status, [hits])

归一：去括注（含 [年号] 前缀）、scan.VARIANTS 异体表、opencc t2s、去标点空白、末尾卷数。
只读。载入约 1～2 分钟，载入条数为 0 即报错退出。
"""
import argparse, glob, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT0 = os.path.abspath(os.path.join(HERE, '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT0, '.claude/qa'))
from scan import VARIANTS  # noqa: E402
try:
    import opencc
    _T2S = opencc.OpenCC('t2s').convert
except Exception:  # 没装 opencc 就只靠 VARIANTS，打印警告
    _T2S = lambda s: s
    print('警告：未安装 opencc，简繁归一缺失（pip install opencc-python-reimplemented）', file=sys.stderr)

BR = re.compile(r'（[^（）]*）|\([^()]*\)|〔[^〔〕]*〕|【[^【】]*】|\[[^\[\]]*\]')
PU = re.compile(r'[\s·・、，,。．.：:；;「」『』《》〈〉()（）〔〕【】\[\]]')
JUAN = re.compile(r'([〇零一二三四五六七八九十百千\d]+卷|不分卷|無卷數)[^書集]{0,6}$')
ANON = {'', '佚名', '闕名', '缺名', '無名氏', '不著撰人', '不著撰者', '不題撰人', '不詳', '撰者不詳'}


LEAD = re.compile(r'^[\[［【]([^\]］】]{1,6})[\]］】]')


def prefix(s):
    m = LEAD.match((s or '').strip())
    return _T2S(m.group(1).translate(VARIANTS)) if m else ''


def norm(s):
    s = BR.sub('', s or '').translate(VARIANTS)
    s = PU.sub('', s)
    s = JUAN.sub('', s)
    return _T2S(s)


def nauth(a):
    a = PU.sub('', (a or '')).translate(VARIANTS)
    return '' if a in ANON else _T2S(a)


class Guard:
    def __init__(self, root=ROOT0):
        self.idx = collections.defaultdict(list)   # norm title -> [(id, title, authors)]
        self.ids = {}
        n = 0
        for p in glob.glob(os.path.join(root, 'Work/*/*/*/*.json')):
            try:
                d = json.load(open(p, encoding='utf-8'))
            except Exception:
                continue
            if d.get('merged_into'):
                continue
            n += 1
            au = {nauth(a.get('name')) for a in d.get('authors') or [] if isinstance(a, dict)} - {''}
            first = nauth(((d.get('authors') or [{}])[0] or {}).get('name'))
            rec = (d['id'], d.get('title'), au, first)
            self.ids[d['id']] = rec
            for t in [d.get('title')] + [x if isinstance(x, str) else (x or {}).get('title') for x in d.get('additional_titles') or []]:
                k = norm(t)
                if k:
                    self.idx[k].append(rec + (prefix(t),))
        if n == 0:
            sys.exit('载入 Work 0 条，路径不对：' + root)
        self.n = n
        self.judged = set()
        for f in glob.glob(os.path.join(root, '.claude/qa/dedup-judged/*.tsv')):
            for ln in open(f, encoding='utf-8'):
                if ln.startswith('#'):
                    continue
                c = ln.rstrip('\n').split('\t')
                if len(c) >= 3 and c[2][:1] in 'CD':
                    self.judged.add(frozenset((c[0], c[1])))
        # 近似：按题名长度分桶
        self.keys = list(self.idx)
        self.g4 = collections.defaultdict(list)
        for kk in self.keys:
            for i in range(max(1, len(kk) - 3)):
                self.g4[kk[i:i + 4]].append(kk)

    def check(self, title, author=None):
        k, a, pf = norm(title), nauth(author), prefix(title)
        hits = []
        for rec in self.idx.get(k, ()):
            rid, t, au, first, rpf = rec
            if pf != rpf:
                hits.append(('PREFIX', rec[:4]))
            elif len(k) < 2:
                hits.append(('NEAR', rec[:4]))
            elif a and au and a not in au:
                hits.append(('SAMETITLE-DIFFAUTH', rec[:4]))
            else:
                hits.append(('DUP', rec[:4]))
        if hits:
            order = ['DUP', 'SAMETITLE-DIFFAUTH', 'PREFIX', 'NEAR']
            st = min((h[0] for h in hits), key=order.index)
            hits.sort(key=lambda h: order.index(h[0]))
            return st, hits
        if len(k) >= 5:
            near, seen = [], set()
            for kk in self.g4.get(k[:4], ()):
                if kk in seen or abs(len(kk) - len(k)) > 2 or len(kk) < 5:
                    continue
                seen.add(kk)
                if k in kk or kk in k:
                    for rec in self.idx[kk]:
                        if not (a and rec[2] and a not in rec[2]):
                            near.append(('NEAR', rec[:4]))
            if near:
                return 'NEAR', near[:5]
        return 'NEW', []


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('cands')
    ap.add_argument('--root', default=ROOT0)
    ap.add_argument('--out')
    ap.add_argument('--fail-on-dup', action='store_true')
    a = ap.parse_args()
    g = Guard(a.root)
    print('载入在世 Work %d，归一题名 %d，已判对 %d' % (g.n, len(g.keys), len(g.judged)), file=sys.stderr)
    cnt = collections.Counter()
    out = open(a.out, 'w', encoding='utf-8') if a.out else sys.stdout
    for ln in open(a.cands, encoding='utf-8'):
        if ln.startswith('#') or not ln.strip():
            continue
        c = ln.rstrip('\n').split('\t') + ['', '', '']
        st, hits = g.check(c[0], c[1])
        cnt[st] += 1
        if not hits:
            out.write('\t'.join([c[2], c[0], st, '', '', '', '']) + '\n')
        for why, (rid, t, au, first) in hits[:3]:
            out.write('\t'.join([c[2], c[0], st, rid, t or '', first, why]) + '\n')
    print(dict(cnt), file=sys.stderr)
    if a.fail_on_dup and (cnt['DUP'] or cnt['NEAR'] or cnt['SAMETITLE-DIFFAUTH']):
        sys.exit(1)


if __name__ == '__main__':
    main()
