"""B5-1 各馆画像：条数、字段填充率、脏度，外加「题名与本仓 Work 题名精确重合率」（匹配潜力粗指标）。
用法：python3 profile.py  → 输出 profile.json 与 profile.md（路径见 OUT）
"""
import sys, json, os, re, collections, glob
sys.path.insert(0, os.path.dirname(__file__))
from common import *

LIBS = [
    ('国会图书馆NDL古典籍', '国立国会图书馆（NDL）古典籍'),
    ('国書データベース漢籍', 'kokusho'),
    ('國圖數字古籍', '中國國家圖書館 數字古籍.json'),
    ('國圖數字方志', '中國國家圖書館 數字方志.json'),
    ('國圖趙城金藏', '中國國家圖書館 趙城金藏.json'),
    ('國圖敦煌遺書', '_整理/敦煌遺書.json'),
    ('家譜(read.nlc.cn)', '家譜（read.nlc.cn 影像）.json'),
    ('臺灣故宮善本古籍', '臺灣故宮博物院善本古籍'),
    ('臺灣故宮明清輿圖', '臺灣故宮博物院明清輿圖'),
    ('牛津博德利', '牛津博德利图书馆.json'),
    ('関西大学KU-ORCAS', '関西大学KU-ORCAS.json'),
    ('全国漢籍データベース', 'kanseki'),
    ('上海圖書館藏書', '_整理/上海圖書館藏書'),
    ('国立公文書館内閣文庫', '国立公文書館内閣文庫漢籍'),
    ('早稲田古典籍', 'waseda'),
    ('古籍總目(上图)', '上海圖書館古籍聯合目錄（中國古籍總目）'),
]
FFFD = re.compile('[�〓]')
CJK = re.compile(r'[㐀-鿿\U00020000-\U0002ffff]')
KANA = re.compile(r'[぀-ヿ]')
LATIN = re.compile(r'[A-Za-z]')
YINGYIN = re.compile(r'影印|影抄|石印|鉛印|排印|縮印|复制|複製|复印|据.*影')
OUT = os.environ.get('OUT', '/tmp/b5_profile')


def stream(rel):
    p = os.path.join(LIB, rel)
    files = sorted(glob.glob(os.path.join(p, 'part-*.json'))) if os.path.isdir(p) else [p]
    for f in files:
        for r in json.load(open(f, encoding='utf-8')):
            yield r
        # 让大对象及时释放


def main():
    wtitles = set()
    nworks = 0
    for w in iter_works():
        nworks += 1
        wtitles.add(norm_title(w.get('title')))
        for t in w.get('additional_titles') or []:
            wtitles.add(norm_title(t if isinstance(t, str) else t.get('title', '')))
    wtitles.discard('')
    print('works', nworks, 'titles', len(wtitles), file=sys.stderr)
    res = []
    for name, rel in LIBS:
        n = 0
        c = collections.Counter()
        keys = collections.Counter()
        seen = collections.Counter()
        hit = 0
        samples = []
        for r in stream(rel):
            n += 1
            title = r.get('title') or r.get('bookName') or ''
            au = r.get('author') or ''
            ed = r.get('edition') or r.get('version') or ''
            if title: c['title'] += 1
            if au: c['author'] += 1
            if ed: c['version'] += 1
            if r.get('image_url'): c['image_url'] += 1
            if r.get('url') or r.get('source_url'): c['url'] += 1
            if r.get('holding_id'): c['holding_id'] += 1
            if FFFD.search(title + au + ed): c['乱码'] += 1
            if title and not CJK.search(title): c['题名无汉字'] += 1
            if KANA.search(title): c['题名含假名'] += 1
            if title and LATIN.search(title): c['题名含拉丁'] += 1
            if YINGYIN.search(ed + title): c['影印标记'] += 1
            nt = norm_title(title)
            seen[(nt, norm_author(au))] += 1
            if nt and nt in wtitles:
                hit += 1
            for k in r:
                keys[k] += 1
        dup = sum(v - 1 for v in seen.values() if v > 1)
        res.append(dict(name=name, rel=rel, n=n, fill={k: round(v / n * 100, 1) for k, v in c.items()},
                        dup_title_author=dup, distinct_title_author=len(seen), title_exact_in_work=round(hit / n * 100, 1) if n else 0,
                        keys=dict(keys.most_common(12))))
        print(name, n, res[-1]['fill'], 'exact_hit', res[-1]['title_exact_in_work'], file=sys.stderr)
    os.makedirs(OUT, exist_ok=True)
    json.dump(dict(works=nworks, libs=res), open(os.path.join(OUT, 'profile.json'), 'w'), ensure_ascii=False, indent=1)


if __name__ == '__main__':
    main()
