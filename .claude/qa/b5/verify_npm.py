"""B5 抽检（故宮善本）：随机抽确定档回故宮详情页取题名／责任者／版本／数位化状态。限速 1.2s；非 200 即停。
用法：[EXCLUDE=..] python3 verify_npm.py 匹配表r.json 输出.json N seed [只抽 book_agree=异 填 conflict]
"""
import sys, os, json, re, time, random, html, urllib.request, http.cookiejar
sys.path.insert(0, os.path.dirname(__file__))
from common import *
UA = 'open-guji-b5/1.0 (research sampling; contact sheldonli.dev@gmail.com)'
rows = json.load(open(sys.argv[1])); out = sys.argv[2]; N = int(sys.argv[3]); random.seed(int(sys.argv[4]))
only = sys.argv[5] if len(sys.argv) > 5 else ''
pool = [r for r in rows if r['tier'] == '确定' and (not only or r['book_agree'] == '异')]
pick = random.sample(pool, N)
W = {w['id']: w for w in iter_works() if w['id'] in {r['work_id'] for r in pick}}
op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))


def parse(s):
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', s, flags=re.S)
    t = re.sub(r'<[^>]+>', '\n', t); t = html.unescape(t)
    L = [x.strip() for x in t.split('\n') if x.strip()]
    d = {}
    for i, x in enumerate(L):
        if '訪客，您好' in x:
            d['题名'], d['版本'], d['馆藏号'] = L[i + 1], L[i + 2], L[i + 3]
            j = i + 4; a = []
            while j < len(L) and not L[j].startswith(('原題名', '副題名')) and j < i + 14:
                a.append(L[j]); j += 1
            d['责任者'] = ' '.join(a)
            break
    d['未数位化'] = any('尚未數位化' in x for x in L)
    for k in ['副題名及卷數', '原題名']:
        for i, x in enumerate(L):
            if x.startswith(k):
                d[k] = L[i + 1] if i + 1 < len(L) else ''
    return d


res = []
for i, r in enumerate(pick, 1):
    w = W[r['work_id']]
    code, body = 0, ''
    for k in range(2):   # 连接被重置时等 60 秒重试一次，仍失败即停（03-抓取规范 §四）
        try:
            req = urllib.request.Request(r['url'], headers={'User-Agent': UA}); f = op.open(req, timeout=30); code, body = f.status, f.read().decode('utf-8', 'replace'); break
        except Exception as e:
            print('ERR', i, e); time.sleep(60)
    if code != 200:
        print('STOP', i, code); break
    res.append(dict(n=i, url=r['url'], lib_title=r['lib_title'], lib_author=r['lib_author'], lib_version=r['lib_version'], page=parse(body), book_agree=r['book_agree'],
                    book_work_ids=r['book_work_ids'], work_id=w['id'], work_title=w['title'], work_authors=[(a.get('name'), a.get('dynasty')) for a in w.get('authors', [])],
                    work_dynasty=w.get('dynasty'), work_juan=(w.get('juan_count') or {}).get('number')))
    time.sleep(2.0)
json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
print('done', len(res))
