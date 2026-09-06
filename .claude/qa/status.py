#!/usr/bin/env python3
"""車道狀態檔讀寫：.claude/qa/status/<lane>.json，儀表板據此畫。

  python3 .claude/qa/status.py --lane song --set batch=3 focus="F 名不合 逐條裁決" \
      --count found.F=40 fixed.F=31 researched.F=6 recorded.F=3 normal.F=0 --commit $(git rev-parse --short HEAD)
  python3 .claude/qa/status.py --lane song --done      # 收工

欄位：
  lane, periods[], works(條數), state(running|done|paused), batch, focus, commit, updated_at,
  counts: {check: {found, fixed, researched, recorded, normal}}
          found=掃出，fixed=已修，researched=經網上查證後修，
          recorded=不確定而記入 known-issues，**normal=逐條讀過而判為本時期之常態（非缺陷）**
          四者之和即已處置數；normal 是進度之一部分，不記則進度條永遠走不完
  log: [{at, batch, note}]   每批一行
"""
import argparse, json, os, datetime
HERE = os.path.dirname(os.path.abspath(__file__))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--lane', required=True)
    ap.add_argument('--periods', help='逗號分隔', default=None)
    ap.add_argument('--works', type=int, default=None)
    ap.add_argument('--set', nargs='*', default=[], help='k=v：batch focus commit state')
    ap.add_argument('--count', nargs='*', default=[], help='found.F=12 fixed.F=3 …（覆寫該格）')
    ap.add_argument('--add', nargs='*', default=[], help='fixed.F=3 …（累加該格）')
    ap.add_argument('--note', default=None, help='本批一行記錄')
    ap.add_argument('--done', action='store_true')
    ap.add_argument('--commit', default=None)
    a = ap.parse_args()
    p = os.path.join(HERE, 'status', a.lane + '.json')
    s = json.load(open(p)) if os.path.exists(p) else {'lane': a.lane, 'periods': [], 'works': None, 'state': 'running',
                                                       'batch': 0, 'focus': '', 'commit': None, 'counts': {}, 'log': []}
    if a.periods: s['periods'] = a.periods.split(',')
    if a.works is not None: s['works'] = a.works
    for kv in a.set:
        k, v = kv.split('=', 1); s[k] = int(v) if v.isdigit() else v
    for kv in a.count + a.add:
        k, v = kv.split('=', 1); kind, chk = k.split('.', 1)
        cell = s['counts'].setdefault(chk, {'found': 0, 'fixed': 0, 'researched': 0, 'recorded': 0, 'normal': 0})
        cell[kind] = (cell.get(kind, 0) + int(v)) if kv in a.add else int(v)
    if a.commit: s['commit'] = a.commit
    if a.done: s['state'] = 'done'
    s['updated_at'] = datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
    if a.note: s['log'].append({'at': s['updated_at'], 'batch': s.get('batch'), 'note': a.note})
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(s, open(p, 'w'), ensure_ascii=False, indent=1)
    print(json.dumps({k: s[k] for k in ('lane', 'state', 'batch', 'focus', 'commit', 'updated_at')}, ensure_ascii=False))

if __name__ == '__main__': main()
