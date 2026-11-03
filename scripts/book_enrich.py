#!/usr/bin/env python3
"""Book 补全：①机械生成 description；②把 Work 上已有的影像／全文资源挂到确定对应的 Book。

只做确定匹配，其余不动。默认 dry-run，--apply 才写档。
  python3 scripts/book_enrich.py desc [--apply] [--limit N]
  python3 scripts/book_enrich.py res  [--apply] [--limit N]
两种改动都算「知识补全」，revision 升 minor、刷新 revised_at（见 schema/common.md revision 口径）。
"""
import argparse, collections, glob, json, os, re, sys, unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = '2026-11-01'  # 洛杉矶日期
DESC_SRC = '據本條著錄字段（版本名、館藏、行款、冊卷數等）機械整理，未另據他書'


def load(kind):
    out = {}
    for f in glob.glob(os.path.join(ROOT, kind, '*/*/*/*.json')):
        try:
            d = json.load(open(f, encoding='utf-8'))
        except Exception:
            continue
        if d.get('merged_into'):
            continue
        out[d['id']] = (f, d)
    return out


def save(f, d):
    with open(f, 'w', encoding='utf-8') as fh:
        fh.write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')


def bump_minor(d):
    v = d.get('revision') or '1.0.0'
    try:
        a, b, _ = v.split('.')
        d['revision'] = f'{a}.{int(b) + 1}.0'
    except Exception:
        d['revision'] = '1.1.0'
    d['revised_at'] = TODAY


# ---------- description ----------
def build_desc(b, coll_title):
    ed = (b.get('edition') or '').strip()
    et = b.get('edition_type')
    pd = b.get('physical_description') or {}
    prov = [p for p in (b.get('provenance') or []) if p.get('institution')]
    ms = [m for m in (b.get('measures') or []) if isinstance(m, dict)]
    jc = next((m for m in ms if m.get('unit') == '卷'), None) or {}
    vc = next((m for m in ms if m.get('unit') == '冊'), None) or {}
    ci = b.get('contained_in') or []
    core = 0  # 版本名之外的信息量
    parts = []
    head = f'《{b["title"]}》' + (f'，{ed}' if ed else '')
    if et and not ed.endswith('本'):
        head += f'（{et}）'
    parts.append(head + '。')
    meas = []
    if jc.get('number'):
        meas.append(f'{jc["number"]}{jc.get("unit") or "卷"}')
        core += 1
    if vc.get('number'):
        meas.append(f'{vc["number"]}冊')
        core += 1
    if meas:
        parts.append('，'.join(meas) + '。')
    ph = [pd.get(k, '').strip().rstrip('。；;') for k in ('leaf_style', 'binding', 'dimensions', 'condition')]
    ph = [x for x in ph if x]
    if ph:
        parts.append('；'.join(ph) + '。')
        core += 1
    if prov:
        s = []
        for p in prov[:3]:
            t = p['institution'] + '藏'
            if p.get('call_number'):
                t += f'（索書號：{p["call_number"]}）'
            s.append(t)
        parts.append('；'.join(s) + '。')
        core += 1
    if ci and coll_title.get(ci[0].get('id')):
        parts.append(f'收入《{coll_title[ci[0]["id"]]}》。')
        core += 1
    return ''.join(parts), core


def cmd_desc(a):
    books = load('Book')
    coll = {k: v[1].get('title') for k, v in load('Collection').items()}
    n = 0
    stats = collections.Counter()
    for bid, (f, b) in books.items():
        if b.get('description'):
            stats['已有'] += 1
            continue
        if not (b.get('edition') or '').strip():
            stats['无版本名'] += 1
            continue
        text, core = build_desc(b, coll)
        if core < a.min_core:
            stats['信息不足'] += 1
            continue
        b['description'] = {'text': text, 'sources': [DESC_SRC]}
        bump_minor(b)
        stats['补'] += 1
        if a.apply:
            save(f, b)
        elif n < 8:
            print(text)
        n += 1
        if a.limit and n >= a.limit:
            break
    print(dict(stats))


# ---------- resources ----------
DY = ['南宋', '北宋', '宋', '元', '明', '清', '唐', '金', '遼', '民國', '日本', '朝鮮', '高麗', '江戶']
REIGN = ('洪武建文永樂洪熙宣德正統景泰天順成化弘治正德嘉靖隆慶萬曆泰昌天啓崇禎順治康熙雍正乾隆嘉慶道光咸豐同治光緒宣統')
REIGNS = [REIGN[i:i + 2] for i in range(0, len(REIGN), 2)] + ['天啟', '萬歷', '万历', '嘉庆', '咸丰', '康熙', '宣统']
REIGN_NORM = {'天啟': '天啓', '萬歷': '萬曆', '万历': '萬曆', '嘉庆': '嘉慶', '咸丰': '咸豐', '宣统': '宣統'}
TYPES = [('刻', '刻本'), ('刊', '刻本'), ('抄', '抄本'), ('鈔', '抄本'), ('钞', '抄本'), ('寫', '抄本'), ('稿', '稿本'),
         ('活字', '活字本'), ('石印', '石印本'), ('鉛印', '鉛印本'), ('影印', '影印本'), ('拓', '拓本'), ('套印', '套印本')]


def nfkc(s):
    return unicodedata.normalize('NFKC', s or '')


def dyn(s):
    s = nfkc(s).replace('国', '國')
    for d in DY:
        if s.startswith(d):
            return d
    return None


def reigns(s):
    s = nfkc(s)
    return {REIGN_NORM.get(r, r) for r in REIGNS if r in s}


def etype(s):
    s = nfkc(s)
    for k, v in TYPES:
        if k in s:
            return v
    return None


def years(s):
    return [(int(x), int(y or x)) for x, y in re.findall(r'[\[(](\d{3,4})(?:\s*-\s*(\d{3,4}))?[\])]', nfkc(s))]


def norm(s):
    return re.sub(r'[\s()\[\]，、。;:]', '', nfkc(s))


def compat(re_ed, b):
    """资源 edition 与 Book 是否「确定同一本」：朝代同＋年号同（或版名全同）＋年份不冲突＋版式不冲突。返回强度或 None。"""
    bed = b.get('edition') or ''
    if not re_ed or not bed:
        return None
    if norm(re_ed) == norm(bed) and len(norm(bed)) >= 6:
        if not (len(years(bed)) == 0 and not reigns(bed) and dyn(bed) and len(norm(bed)) <= 8):
            return 'exact'
    rd, bd = dyn(re_ed), dyn(bed)
    if not rd or rd != bd:
        return None
    rr, br = reigns(re_ed), reigns(bed)
    if not rr or not (rr & br):
        return None
    t1, t2 = etype(re_ed), etype(bed)
    if t1 and t2 and t1 != t2:
        return None
    # 年份证据：同年号＋同第 N 年，或公元年相同；只有年号（无年）不算确定
    ry, by = reign_years(re_ed), reign_years(bed)
    abs_r = {y for lo, hi in years(re_ed) if lo == hi for y in [lo]}
    abs_b = set()
    if (b.get('dating') or {}).get('year'):
        abs_b.add(b['dating']['year'])
    abs_b |= {lo for lo, hi in years(bed) if lo == hi}
    if (ry & by) or (abs_r & abs_b):
        return 'reign-year'
    return None


CN = {'元': 1, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9, '十': 10, '廿': 20, '卅': 30}


def cn2n(t):
    if t.isdigit():
        return int(t)
    if t == '元':
        return 1
    n, cur = 0, 0
    for ch in t:
        v = CN.get(ch)
        if v is None:
            return None
        if v in (10, 20, 30):
            n += (cur or 1) * v if v == 10 else v
            cur = 0
        else:
            cur = cur * 10 + v if False else v
    return n + cur


def reign_years(s):
    s = nfkc(s)
    out = set()
    for r in REIGNS:
        for m in re.finditer(re.escape(r) + r'([0-9元一二三四五六七八九十廿卅]{1,4})年', s):
            n = cn2n(m.group(1))
            if n:
                out.add((REIGN_NORM.get(r, r), n))
    return out


def cmd_res(a):
    works = load('Work')
    books = load('Book')
    by_work = collections.defaultdict(list)
    for bid, (f, b) in books.items():
        by_work[b['work_id']].append((f, b))
    n = 0
    stats = collections.Counter()
    log = []
    for wid, (wf, w) in works.items():
        bl = by_work.get(wid, [])
        if not bl:
            continue
        for r in w.get('resources', []):
            if 'catalog' in (r.get('types') or []) or r.get('root_type') == 'catalog':
                continue
            e = (r.get('metadata') or {}).get('edition')
            ms = [(compat(e, b), f, b) for f, b in bl]
            ms = [m for m in ms if m[0]]
            ex = [m for m in ms if m[0] == 'exact']
            pick = ex if len(ex) == 1 else (ms if len(ms) == 1 and not ex else [])
            if len(pick) != 1:
                stats['歧义/无' if ms else '无匹配'] += 1
                continue
            lvl, f, b = pick[0]
            if any(x.get('url') == r.get('url') for x in b.get('resources', [])):
                stats['已挂'] += 1
                continue
            b.setdefault('resources', []).append(json.loads(json.dumps(r)))
            if r.get('group') and (w.get('resource_groups') or {}).get(r['group']):
                b.setdefault('resource_groups', {})[r['group']] = w['resource_groups'][r['group']]
            bump_minor(b)
            stats['挂_' + lvl] += 1
            log.append((b['id'], r['id'], lvl, e, b.get('edition')))
            n += 1
            if a.apply:
                save(f, b)
            if a.limit and n >= a.limit:
                break
        if a.limit and n >= a.limit:
            break
    print(dict(stats))
    if a.log:
        with open(a.log, 'w', encoding='utf-8') as fh:
            for row in log:
                fh.write('\t'.join(map(str, row)) + '\n')


if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('cmd', choices=['desc', 'res'])
    p.add_argument('--apply', action='store_true')
    p.add_argument('--limit', type=int, default=0)
    p.add_argument('--log')
    p.add_argument('--min-core', type=int, default=3, help='desc：版本名之外至少几类信息才写（默认 3）')
    a = p.parse_args()
    {'desc': cmd_desc, 'res': cmd_res}[a.cmd](a)
