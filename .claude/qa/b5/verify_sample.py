"""B5-3 抽检：从「确定」档随机抽 N 条，回国图详情页取题名/责任者/版本，与馆档记录及本仓 Work 并列，输出人工核对表。
限速 ≥1.2s/请求；非 200 或页面疑似反爬挑战即停（03-抓取规范 §四）。
用法：[EXCLUDE=已抽样.json,...] python3 verify_sample.py 匹配表.json 输出.json [N] [seed]
"""
import sys, os, json, re, time, random, html, urllib.request
sys.path.insert(0, os.path.dirname(__file__))
from common import *

UA = 'open-guji-b5/1.0 (research sampling; contact sheldonli.dev@gmail.com)'
rows = json.load(open(sys.argv[1]))
out = sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 50
seed = int(sys.argv[4]) if len(sys.argv) > 4 else 20261005
random.seed(seed)
excl = set()
for f in os.environ.get('EXCLUDE', '').split(','):
    if f:
        excl |= {x['url'] for x in json.load(open(f))}
pick = random.sample([r for r in rows if r['tier'] == '确定' and r['url'] not in excl], N)
W = {}
need = {r['work_id'] for r in pick}
for w in iter_works():
    if w['id'] in need:
        W[w['id']] = w


def fetch(url):
    req = urllib.request.Request(url, headers={'User-Agent': UA})
    with urllib.request.urlopen(req, timeout=30) as f:
        return f.status, f.read().decode('utf-8', 'replace')


def parse(s):
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', s, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t)
    t = re.sub(r'\s+', ' ', html.unescape(t))
    m = re.search(r'资源详情\s*(.*?)\s*(?:责任者：)\s*(.*?)\s*-->', t)
    d = {}
    if m:
        d['题名'] = m.group(1).strip()
    for k in ['责任者', '出版发行项', '版本项', '四部分类号', '现有藏本附注', '丛编项', '善本书号']:
        mm = re.search(k + r'：\s*(.*?)\s*(?=-->|[一-鿿]{2,6}：|分享到)', t)
        if mm:
            d[k] = mm.group(1).strip()
    d['在线阅读'] = '在线阅读' in t
    return d


res = []
for i, r in enumerate(pick, 1):
    w = W[r['work_id']]
    try:
        code, body = fetch(r['url'])
    except Exception as e:
        print('ERR', i, e); code, body = 0, ''
    if code != 200 or re.search(r'验证码|captcha|Access Denied', body[:5000], re.I):
        print('STOP: 非 200 或疑似反爬', i, code); break
    page = parse(body)
    res.append(dict(n=i, tier=r['tier'], url=r['url'], lib_title=r['lib_title'], lib_author=r['lib_author'], lib_version=r['lib_version'], page=page,
                    work_id=w['id'], work_title=w['title'], work_authors=[(a.get('name'), a.get('dynasty')) for a in w.get('authors', [])],
                    work_dynasty=w.get('dynasty'), work_juan=(w.get('juan_count') or {}).get('number'),
                    work_desc=((w.get('description') or {}).get('text') or '')[:120]))
    time.sleep(1.2)
json.dump(res, open(out, 'w'), ensure_ascii=False, indent=1)
print('done', len(res))
