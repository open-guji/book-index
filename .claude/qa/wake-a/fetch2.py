#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""wake-a 第二輪：對 shard0 每個 Work 查 NDL OpenSearch（串行、>=2s、退避、緩存 /tmp/wa2cache）。"""
import json, os, sys, time, urllib.parse, subprocess, hashlib
S = '/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad'
CACHE = '/tmp/wa2cache'
works = json.load(open(S + '/a_works.json'))
def get(url):
    f = os.path.join(CACHE, hashlib.md5(url.encode()).hexdigest() + '.xml')
    if os.path.exists(f) and os.path.getsize(f) > 200: return open(f, encoding='utf8').read()
    delay = 4
    for _ in range(6):
        time.sleep(2.2)
        r = subprocess.run(['curl', '-sS', '-m', '40', '-A', 'Mozilla/5.0 (research; book-index)', '-w', '\n%{http_code}', url], capture_output=True)
        out = r.stdout.decode('utf8', 'ignore'); body, _, code = out.rpartition('\n')
        if code == '200' and '<rss' in body:
            open(f, 'w', encoding='utf8').write(body); return body
        print('retry', code, url[:90], file=sys.stderr); time.sleep(delay); delay *= 2
    return None
def q(title, extra=''):
    return 'https://ndlsearch.ndl.go.jp/api/opensearch?any=' + urllib.parse.quote(title + ' 和古書' + extra) + '&cnt=50'
if __name__ == '__main__':
    lo, hi = int(sys.argv[1]), int(sys.argv[2])
    for w in works[lo:hi]:
        b = get(q(w['title']))
        n = b.count('<item>') if b else -1
        print(w['i'], w['title'], n, flush=True)
