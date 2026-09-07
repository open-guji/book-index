#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""裁決之賬（v2 之地基）。

**所以立此**：全庫 17,288 條記錄有 `ai_note`（自由文字），**零條有結構化的裁決欄位**。
於是 `scan.py` 無法把裁過的排除，數字永不下降，每一道新開都要把同一批記錄重讀一遍
——v1 九道的上下文就是這樣燒光的（ming 761k/1M 停在「awaiting coordinator rulings」）。

賬是 append-only 的 JSONL，一行一裁：

    {"id":"d59f2xxx","check":"C","verdict":"normal","rule":"C-注疏",
     "round":24,"by":"lane-C","at":"2026-09-07T…","why":"…"}

`verdict` 只三種：
  normal  是常態，不必動（scan 自此不再報）
  fixed   已改（改完之後該條通常也就不再命中，落賬是為留痕）
  open    待人裁，`why` 須指出 known-issues 檔名

**`rule` 是第一等公民**：同一條 rule 可一次落幾百條，日後要翻案只須按 rule 撈回來，
不必重掃全庫。翻案用 `revoke`——**不刪行，是再追加一行 `revoked`**，賬永遠可回溯。
"""
import json, os, sys, datetime, argparse, collections

PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'verdicts.jsonl')
VALID = ('normal', 'fixed', 'open', 'revoked')


def _iter(path=PATH):
    if not os.path.exists(path):
        return
    with open(path, encoding='utf-8') as fh:
        for ln, line in enumerate(fh, 1):
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except Exception as e:
                print('賬第 %d 行解不開，跳過：%s' % (ln, e), file=sys.stderr)


def load(path=PATH):
    """回 {(id, check): 最後一筆}。後寫的蓋先寫的——revoked 亦然，故翻案即生效。"""
    out = {}
    for r in _iter(path):
        i, c = r.get('id'), r.get('check')
        if i and c:
            out[(i, c)] = r
    return out


def normal_keys(path=PATH):
    """已判 normal 且未被翻案者。scan.py 之 --exclude-adjudicated 用此。"""
    return {k for k, v in load(path).items() if v.get('verdict') == 'normal'}


def add(entries, path=PATH):
    """追加。entries 為 dict 之列。回實際寫入之筆數。"""
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    n = 0
    with open(path, 'a', encoding='utf-8') as fh:
        for e in entries:
            if not e.get('id') or not e.get('check'):
                raise ValueError('缺 id 或 check：%r' % e)
            if e.get('verdict') not in VALID:
                raise ValueError('verdict 須為 %s，得 %r' % (VALID, e.get('verdict')))
            if not e.get('rule'):
                raise ValueError('缺 rule——判準是第一等公民，無 rule 則日後無從整批翻案：%r' % e)
            e.setdefault('at', now)
            fh.write(json.dumps(e, ensure_ascii=False, sort_keys=True) + '\n')
            n += 1
    return n


def revoke(rule, by, why, path=PATH):
    """整批翻案：把某 rule 落過的每一條再追加一行 revoked。不刪行。"""
    hit = [v for v in load(path).values() if v.get('rule') == rule and v.get('verdict') != 'revoked']
    if not hit:
        return 0
    return add([{'id': v['id'], 'check': v['check'], 'verdict': 'revoked',
                 'rule': rule, 'by': by, 'why': why,
                 'revokes_round': v.get('round')} for v in hit], path)


def stats(path=PATH):
    cur = load(path)
    by_verdict = collections.Counter(v.get('verdict') for v in cur.values())
    by_rule = collections.Counter((v.get('rule'), v.get('verdict')) for v in cur.values())
    by_check = collections.Counter(k[1] for k, v in cur.items() if v.get('verdict') == 'normal')
    return cur, by_verdict, by_rule, by_check


def main():
    ap = argparse.ArgumentParser(description='裁決之賬')
    ap.add_argument('--stats', action='store_true')
    ap.add_argument('--rule', help='列某一 rule 之所有裁')
    ap.add_argument('--revoke', metavar='RULE', help='整批翻案某一 rule')
    ap.add_argument('--by', default='coordinator')
    ap.add_argument('--why', default='')
    a = ap.parse_args()
    if a.revoke:
        if not a.why:
            raise SystemExit('翻案須說明所以然（--why）')
        print('已翻案 %d 條（rule=%s）' % (revoke(a.revoke, a.by, a.why), a.revoke))
        return
    if a.rule:
        for k, v in sorted(load().items()):
            if v.get('rule') == a.rule:
                print(json.dumps(v, ensure_ascii=False))
        return
    cur, bv, br, bc = stats()
    print('賬中相異 (id, check) 共 %d 筆' % len(cur))
    print('按 verdict:', dict(bv))
    print('按 check（僅 normal）:', dict(bc))
    print('按 rule:')
    for (rule, verdict), n in br.most_common():
        print('   %-28s %-8s %5d' % (rule, verdict, n))


if __name__ == '__main__':
    main()
