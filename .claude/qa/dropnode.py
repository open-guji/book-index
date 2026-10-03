#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""自一條記錄撤去一個誤掛之著錄節（Y misattached 之處分）。

與 `mergework.py` 相對：**併是兩條合一，撤節是一條之中去其不屬於它的那一節**。
Y 之 misattached 型正是後者——一節著錄同時掛在二條上，而其文只點名一人。

    python3 .claude/qa/dropnode.py --id <work_id> --source-bid <bid> --why <所以然> [--apply]

不加 `--apply` 即乾跑：**印出將撤之節的每一個欄位**，並印該節在別處（keeper）是否確已存在
——坑 67 之戒，撤節前先看清楚撤的是什麼；撤了之後那一節若別處也沒有，就是把著錄丟了。
"""
import json, os, sys, glob, argparse, datetime
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jio


def wpath(wid):
    for p in glob.glob(os.path.join(ROOT, 'Work/*/*/*/%s-*.json' % wid)):
        return p
    return None


def main():
    ap = argparse.ArgumentParser(description='撤去誤掛之著錄節')
    ap.add_argument('--id', required=True)
    ap.add_argument('--source-bid', required=True)
    ap.add_argument('--why', required=True)
    ap.add_argument('--keeper', help='該節之正主，用以覈其在彼處確已存在')
    ap.add_argument('--by', default='lane-B')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()

    p = wpath(a.id)
    if not p:
        raise SystemExit('檔不存在：%s' % a.id)
    rel = os.path.relpath(p, ROOT)
    d, fmt = jio.load(rel)
    nodes = d.get('indexed_by') or []
    hit = [n for n in nodes if n.get('source_bid') == a.source_bid]
    rest = [n for n in nodes if n.get('source_bid') != a.source_bid]
    if not hit:
        raise SystemExit('本條無 source_bid=%s 之節' % a.source_bid)
    print('== 將撤之節（%s，共 %d 節撤 %d）==' % (a.id, len(nodes), len(hit)))
    for n in hit:
        print(json.dumps(n, ensure_ascii=False, indent=1))
    if not rest:
        print('\n**撤後本條將無任何著錄**——空殼之條非本工具所能處分，須改判為併或存疑。')
    if a.keeper:
        kp = wpath(a.keeper)
        if kp:
            kd = json.load(open(kp))
            same = [n for n in (kd.get('indexed_by') or []) if n.get('source_bid') == a.source_bid]
            print('\n該節在正主 %s：%s' % (a.keeper, '已有 %d 節（撤之不失著錄）' % len(same) if same
                                          else '**沒有**——撤之即失此著錄，先補入正主再撤'))
    if not a.apply:
        print('\n[乾跑] 未寫任何檔。')
        return
    if not rest:
        raise SystemExit('拒絕：撤後將無著錄。')
    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    d['indexed_by'] = rest
    jio.addnote(d, '%s %s Y misattached 處分：撤去誤掛之著錄節（source_bid=%s，題「%s」）。%s'
                % (now[:10], a.by, a.source_bid, (hit[0].get('title_info') or ''), a.why))
    jio.save(rel, d, fmt)
    print('\n已撤 %d 節，餘 %d 節。' % (len(hit), len(rest)))


if __name__ == '__main__':
    main()
