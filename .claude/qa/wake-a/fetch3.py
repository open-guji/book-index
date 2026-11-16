#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""CiNii Books OpenSearch(JSON) 查每個 Work（title=，year_to=1912，count=100），串行>=2s，緩存。"""
import json, os, sys, time, urllib.parse, subprocess, hashlib
S = '/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad'
CACHE = '/tmp/wa2cache'
def getj(url):
    f = os.path.join(CACHE, 'c_' + hashlib.md5(url.encode()).hexdigest() + '.json')
    if os.path.exists(f) and os.path.getsize(f) > 50: return json.load(open(f, encoding='utf8'))
    delay = 4
    for _ in range(6):
        time.sleep(2.0)
        r = subprocess.run(['curl', '-sS', '-m', '40', '-A', 'Mozilla/5.0 (research; book-index)', '-w', '\n%{http_code}', url], capture_output=True)
        out = r.stdout.decode('utf8', 'ignore'); body, _, code = out.rpartition('\n')
        if code == '200':
            try: j = json.loads(body)
            except Exception: j = None
            if j is not None:
                open(f, 'w', encoding='utf8').write(body); return j
        print('retry', code, url[:90], file=sys.stderr); time.sleep(delay); delay *= 2
    return None
def q(title, start=1):
    return 'https://ci.nii.ac.jp/books/opensearch/search?title=%s&format=json&count=100&year_to=1912&start=%d' % (urllib.parse.quote(title), start)
def items(j):
    try: return j['@graph'][0].get('items', [])
    except Exception: return []
if __name__ == '__main__':
    works = json.load(open(S + '/a_works.json'))
    lo, hi = int(sys.argv[1]), int(sys.argv[2])
    for w in works[lo:hi]:
        j = getj(q(w['title']))
        print(w['i'], w['title'], len(items(j)) if j else -1, j['@graph'][0].get('opensearch:totalResults') if j else '', flush=True)
