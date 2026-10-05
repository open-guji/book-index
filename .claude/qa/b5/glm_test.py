"""B5 外部模型对照：抽存疑档 N 条，GLM 判「馆方记录与候选 Work 是否同一部书」，记录耗时与 token。
用法：python3 glm_test.py 匹配表.json 输出目录 [N] [seed]   （GLM key 由 agent proxy 注入，脚本里没有 key）
"""
import sys, os, json, random, time, re, urllib.request, concurrent.futures as cf
sys.path.insert(0, os.path.dirname(__file__))
from common import *
rows = json.load(open(sys.argv[1])); OUT = sys.argv[2]
N = int(sys.argv[3]) if len(sys.argv) > 3 else 100
random.seed(int(sys.argv[4]) if len(sys.argv) > 4 else 1005)
cand = [r for r in rows if r['tier'] == '存疑' and r['work_id']]
pick = random.sample(cand, N)
need = {r['work_id'] for r in pick}
W = {w['id']: w for w in iter_works() if w['id'] in need}
items = []
for i, r in enumerate(pick, 1):
    w = W[r['work_id']]
    items.append(dict(n=i, url=r['url'], reasons=r['reasons'], lib=dict(题名=r['lib_title'], 责任者=r['lib_author'], 版本=r['lib_version']),
                      work=dict(题名=w['title'], 别名=w.get('additional_titles') or [], 著者=[f"{a.get('name')}({a.get('dynasty') or '朝代不详'})" for a in w.get('authors', [])],
                                朝代=w.get('dynasty'), 卷数=(w.get('juan_count') or {}).get('number'), 简介=((w.get('description') or {}).get('text') or '')[:150])))
json.dump(items, open(os.path.join(OUT, 'items.json'), 'w'), ensure_ascii=False, indent=1)
PROMPT = '''你是古籍目录员。判断图书馆著录的一条记录与目录库里的一个「作品」是不是同一部书（同一内容的书，不同版本算同一部；同名但内容、作者不同的算不同）。
只依据下面给的信息判断，不确定就说不确定，不要凭记忆猜。
馆方记录：{lib}
目录库作品：{work}
只输出 JSON：{{"verdict":"同"或"异"或"不确定","reason":"一句话"}}'''


def call(it):
    body = json.dumps(dict(model='glm-4.5-flash', thinking={'type': 'disabled'}, max_tokens=200, temperature=0,
                           messages=[dict(role='user', content=PROMPT.format(lib=json.dumps(it['lib'], ensure_ascii=False), work=json.dumps(it['work'], ensure_ascii=False)))])).encode()
    for k in range(4):
        t = time.time()
        try:
            req = urllib.request.Request('https://open.bigmodel.cn/api/paas/v4/chat/completions', body, {'Content-Type': 'application/json'})
            d = json.load(urllib.request.urlopen(req, timeout=60))
            txt = d['choices'][0]['message']['content']
            m = re.search(r'\{.*\}', txt, re.S)
            v = json.loads(m.group(0)) if m else {}
            return dict(n=it['n'], verdict=v.get('verdict'), reason=v.get('reason'), sec=time.time() - t, tok=d.get('usage', {}), retries=k)
        except Exception as e:
            err = str(e)
            time.sleep(10 * (k + 1))
    return dict(n=it['n'], verdict=None, reason='ERR ' + err, sec=0, tok={}, retries=4)


t0 = time.time()
with cf.ThreadPoolExecutor(3) as ex:
    res = list(ex.map(call, items))
json.dump(dict(wall=time.time() - t0, res=res), open(os.path.join(OUT, 'glm.json'), 'w'), ensure_ascii=False, indent=1)
print('wall', round(time.time() - t0, 1), 'calls', len(res), 'err', sum(1 for r in res if r['verdict'] is None))
