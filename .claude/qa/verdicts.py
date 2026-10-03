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
import json, os, sys, datetime, argparse, collections, signal

# 坑 79：`... | head` 一關管子即 BrokenPipeError，而那看起來像程式壞了。
# 本檔是給人讀的報告，天生就會被 head／less 截，故明寫預設之 SIGPIPE。
try:
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
except (AttributeError, ValueError):
    pass                      # 非 POSIX 或非主執行緒

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


def _count(text):
    seen = set()
    for line in (text or '').splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r.get('id') and r.get('check'):
            seen.add((r['id'], r['check']))
    return len(seen)


def highwater(path=PATH):
    """賬只增不減之守門。回 (今之相異鍵數, main 上之數, 是否退步)。

    **所以立此**（lane-E 2026-09-07 02:45 所報）：`pushmain.sh` 之 `--ours` 解衝突曾三度
    吞掉他道之賬，最後一次清點才發現**共遺落 492 筆**（lane-C 203、lane-D 289）——
    而那兩道之 status 自書「已落賬 288」，main 上掃出卻仍是原數，**兩邊對不上而無人對**。
    **這件事不能靠各道自覺：被吞者無聲，吞人者亦無聲，只有第三方比對才看得見。**

    **水位不存檔**（2026-09-07 lane-E 覆驗本函式所報之漏二，採其乙案）：
    原以 `verdicts.hwm` 記之，而該檔入了 git，`pushmain.sh` 對非索引檔一律 `--ours`
    ——取己方之數可能低於 main 上之數，**水位遂被悄悄下修，而那一次正是最需要它響的那一次**。
    今 `prev` 逕自 `origin/main` 之賬即時算出：**水位之真身本來就是「main 上已有多少」，
    存檔只是它的影子，而影子會被合流規則弄髒。**

    讀不到 main 之賬時**算敗不算過**——守門者查不成即應中止（同 lane-E 所報之漏一）。
    """
    import subprocess
    n = len(load(path))
    r = subprocess.run(['git', 'show', 'origin/main:.claude/qa/verdicts.jsonl'],
                       capture_output=True, text=True,
                       cwd=os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
    if r.returncode != 0:
        raise RuntimeError('讀不到 origin/main 之賬（先 git fetch origin main）：%s'
                           % (r.stderr or '').strip()[:120])
    prev = _count(r.stdout)
    return n, prev, n < prev


def clashes(path=PATH):
    """撞判之檢（lane-A 2026-09-07 22:00 所請）。

    賬之 load() 取 (id, check) 之**最後一筆**，故兩道同時判同一條時，
    後寫者**默默**蓋掉先寫者，兩造都不會收到任何提示——坑 70 是「行被刪」，
    此是「行還在而效力被蓋」，是同一類病的另一面。

    報之準：同一 (id, check) 由**相異之 `by`** 落過，且**判不同**。
    別出「後手」與「撞判」：lane-A 所指——後筆之 `why` 若**援引了前一位落判者之名**，
    是有意的接續（坑 74 那種），不算撞；否則是撞。
    回 (clashes, followups)，各為 dict：(id, check) -> 該鍵之全部筆（依序）。
    """
    seq = collections.defaultdict(list)
    for r in _iter(path):
        i, c = r.get('id'), r.get('check')
        if i and c:
            seq[(i, c)].append(r)
    clash, follow = {}, {}
    for k, rows in seq.items():
        bys = {r.get('by') for r in rows}
        if len(bys) < 2:
            continue
        if len({r.get('verdict') for r in rows}) < 2:
            continue                      # 判同者不報——重工是有的，錯沒有
        prior = {r.get('by') for r in rows[:-1]} - {rows[-1].get('by')}
        why = rows[-1].get('why') or ''
        (follow if any(b and b in why for b in prior) else clash)[k] = rows
    return clash, follow


def stats(path=PATH):
    cur = load(path)
    by_verdict = collections.Counter(v.get('verdict') for v in cur.values())
    by_rule = collections.Counter((v.get('rule'), v.get('verdict')) for v in cur.values())
    by_check = collections.Counter(k[1] for k, v in cur.items() if v.get('verdict') == 'normal')
    return cur, by_verdict, by_rule, by_check


def main():
    ap = argparse.ArgumentParser(description='裁決之賬')
    ap.add_argument('--stats', action='store_true')
    ap.add_argument('--hwm', action='store_true', help='賬只增不減之守門（水位線）')
    ap.add_argument('--rule', help='列某一 rule 之所有裁')
    ap.add_argument('--revoke', metavar='RULE', help='整批翻案某一 rule')
    ap.add_argument('--by', default='coordinator')
    ap.add_argument('--why', default='')
    ap.add_argument('--clash', action='store_true',
                    help='撞判之檢：同一 (id, check) 由二道以上落過而判不同')
    ap.add_argument('--strict', action='store_true', help='與 --clash 併用：有撞則回非零')
    a = ap.parse_args()
    if a.hwm:
        n, prev, bad = highwater()
        print('賬今 %d 筆，origin/main 上 %d 筆%s' % (n, prev, '　**退步了**' if bad else ''))
        raise SystemExit(1 if bad else 0)
    if a.clash:
        clash, follow = clashes()
        print('撞判 %d 組；有意之後手 %d 組（後筆 why 援引前一位落判者）' % (len(clash), len(follow)))
        for (i, c), rows in sorted(clash.items()):
            print('  %s / %s' % (i, c))
            for r in rows:
                print('     %-11s %-7s %s  %s' % (r.get('by'), r.get('verdict'),
                      (r.get('at') or '')[:19], (r.get('rule') or '')[:44]))
        raise SystemExit(1 if (a.strict and clash) else 0)
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
