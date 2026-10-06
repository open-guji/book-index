"""B5-2 國圖數字古籍 → 本仓 Work 匹配（试点）。
用法：python3 match_nlc.py [输出目录]
输出：匹配表.tsv、匹配表.json（含候选）、stats.json
三档：确定／存疑／无。准确率优先——任何一项不一致、不唯一、缺责任者，一律降为存疑。
"""
import sys, os, re, json, collections, csv, difflib
sys.path.insert(0, os.path.dirname(__file__))
from common import *

OUT = sys.argv[1] if len(sys.argv) > 1 else '/tmp/claude-0/b5/nlc'
SRC = os.environ.get('SRC', '_整理/數字古籍.json')

ERA = [('先秦', 0), ('周', 0), ('秦', 0), ('漢', 1), ('汉', 1), ('魏', 2), ('晉', 2), ('晋', 2), ('南北朝', 2), ('宋', 5), ('齊', 2), ('梁', 2), ('陳', 2), ('隋', 3), ('唐', 4),
       ('五代', 4.5), ('遼', 5), ('辽', 5), ('金', 5), ('元', 6), ('明', 7), ('清', 8), ('民國', 9), ('民国', 9)]
# 朝代→序（宋齐梁陈单字有歧义，下面 era_rank 只在版本串开头与作者朝代标注里取，不处理歧义字）
RANK = {'先秦': 0, '周': 0, '秦': 0, '漢': 1, '汉': 1, '西漢': 1, '東漢': 1, '前漢': 1, '後漢': 1, '三國': 2, '魏': 2, '蜀': 2, '吳': 2, '吴': 2,
        '晉': 2, '晋': 2, '南朝': 2, '北朝': 2, '劉宋': 2, '南齊': 2, '蕭梁': 2, '隋': 3, '唐': 4, '五代': 4.5, '宋': 5, '北宋': 5, '南宋': 5, '遼': 5, '辽': 5, '金': 5,
        '元': 6, '明': 7, '清': 8, '民國': 9, '民国': 9, '近代': 9, '現代': 9}
ERATOK = sorted(RANK, key=len, reverse=True)
CN = {'〇': 0, '零': 0, '一': 1, '二': 2, '三': 3, '四': 4, '五': 5, '六': 6, '七': 7, '八': 8, '九': 9}


def cn2int(s):
    s = s.replace('廿', '二十').replace('卅', '三十')
    if re.fullmatch(r'\d+', s):
        return int(s)
    tot, cur = 0, 0
    for ch in s:
        if ch in CN:
            cur = cur * 10 + CN[ch] if False else CN[ch]
        elif ch == '十':
            tot += (cur or 1) * 10; cur = 0
        elif ch == '百':
            tot += (cur or 1) * 100; cur = 0
        elif ch == '千':
            tot += (cur or 1) * 1000; cur = 0
    return tot + cur


def lead_era(s):
    """取字符串开头（可含括号）的朝代标记，返回 RANK 值或 None。"""
    s = re.sub(r'^[\s\[\(（［【〔題题]+', '', s or '')
    for t in ERATOK:
        if s.startswith(t):
            return RANK[t]
    return None


def author_era(raw):
    m = re.match(r'^[\s題题]*[\[\(（［【〔]([^\]\)）］】〕]{1,4})[\]\)）］】〕]', raw or '')
    if m:
        for t in ERATOK:
            if m.group(1).startswith(t):
                return RANK[t]
    return None


def work_era(a):
    d = a.get('dynasty') or ''
    for t in ERATOK:
        if d.startswith(t) or d.endswith(t):
            return RANK[t]
    return None


COLL = re.compile(r'叢書|丛书|全書|全书|集成|彙刻|匯刻|彙編|汇编|叢刊|丛刊|[一二三四五六七八九十百\d]+[種种編编]')
SPLIT = re.compile(r'[\s　]{2,}|\s+(?=[〇零一二三四五六七八九十百千\d]+[卷種种編编])')
PREF = re.compile(r'^(欽定|钦定|御製|御制|御纂|御選|新刻|重刻|新鐫|新镌|校刻|重訂|重订|增訂|增订|重刊|新編|新编|新刊|新鍥|新锲|精刻|增刊|增補|增补|補刻|补刻|校正|詳註|详注|纂圖|篆圖|音註|音注|繡像|绣像|批點|批点|評點|评点|足本|校訂|校订)+')


def split_title(raw):
    """返回 (core_title_raw, rest, era_hint)。"""
    t = (raw or '').strip()
    era = None
    m = re.match(r'^[\[\(（［【〔]([^\]\)）］】〕]{1,6})[\]\)）］】〕]', t)
    if m and re.search(r'志|誌|縣|县|府|州|通志|志略', t):
        era = m.group(1)
    parts = SPLIT.split(t, maxsplit=1)
    core = parts[0]
    rest = parts[1] if len(parts) > 1 else ''
    # 题名后直接粘着卷数（故宮式「元豐類稿五十卷附錄一卷」）：在第一个「N卷」前切开
    mj = re.search(r'(?<=[\u3400-\u9fff]{2})[〇零一二三四五六七八九十百千廿卅\d]+[卷巻]', core)
    if mj:
        rest = (core[mj.start():] + ' ' + rest).strip()
        core = core[:mj.start()]
    return core, rest, era


def multi_title(rest):
    """题名后还跟着别的题名（合刻/合订本）：去掉卷册数与「附…」后仍有≥2 个汉字。"""
    r = re.sub(r'[〇零一二三四五六七八九十百千廿卅\d]+', '', rest or '')
    r = re.sub(r'[卷巻冊册函帙種种編编首末上下之，,；;、\s]', '', r)
    r = re.sub(r'附.*$', '', r)
    return len(re.findall(r'[\u3400-\u9fff]', r)) >= 2


def parse_juan(rest, core):
    m = re.search(r'([〇零一二三四五六七八九十百千廿卅\d]+)[卷巻]', rest or '') or re.search(r'([〇零一二三四五六七八九十百千廿卅\d]+)[卷巻]', core or '')
    if m:
        try:
            return cn2int(m.group(1))
        except Exception:
            return None
    return None


byauth = collections.defaultdict(list)       # 归一责任者名 -> [(归一题名, work)]，供「同责任者近似题名」存疑召回


def build_work_index():
    byauth.clear()
    idx = collections.defaultdict(list)       # exact norm title -> [work]
    idx2 = collections.defaultdict(list)      # 去前缀装饰后的键
    works = {}
    for w in iter_works():
        names = set()
        eras = []
        for a in w.get('authors') or []:
            n = norm_author(a.get('name', ''))
            names.update(x for x in n.split('|') if x)
            e = work_era(a)
            if e is not None:
                eras.append(e)
        jc = (w.get('juan_count') or {}).get('number')
        info = dict(id=w['id'], title=w['title'], authors=names, eras=eras, juan=jc if isinstance(jc, int) else None,
                    juan_unit=(w.get('juan_count') or {}).get('unit'), n_books=len(w.get('books') or []))
        works[w['id']] = info
        for n in names:
            byauth[n].append((norm_title(w['title']), info))
        ts = {w['title']} | {t if isinstance(t, str) else t.get('title', '') for t in (w.get('additional_titles') or [])}
        if w.get('original_title'):
            ts.add(w['original_title'])
        for t in ts:
            k = norm_title(t)
            if k:
                if info not in idx[k]:
                    idx[k].append(info)
                k2 = PREF.sub('', k)
                if k2 and k2 != k and info not in idx2[k2]:
                    idx2[k2].append(info)
    return idx, idx2, works


def auth_relation(lib_names, w):
    """返回 'eq'（有交集）/ 'missing'（任一方缺）/ 'diff'。"""
    if not lib_names or not w['authors']:
        return 'missing'
    if lib_names & w['authors']:
        return 'eq'
    # 一方是另一方的前后缀（如「某某」vs「某某某」不算；仅允许长度≥3 的包含，如「欧阳玄」⊂「欧阳玄等」）
    for a in lib_names:
        for b in w['authors']:
            if len(a) >= 3 and len(b) >= 3 and (a in b or b in a):
                return 'eq'
    return 'diff'


def match_one(r, idx, idx2):
    title = r.get('title') or r.get('bookName') or ''
    core, rest, era_hint = split_title(title)
    key = norm_title(core)
    lib_names = set(x for x in norm_author(r.get('author')).split('|') if x)
    a_era = author_era(r.get('author'))
    v_era = lead_era(r.get('version') or r.get('edition') or '')
    juan = parse_juan(rest, core)
    reasons = []
    is_coll = bool(COLL.search(rest) or COLL.search(core))
    is_multi = multi_title(rest)
    if not key:
        return '无', None, [], ['题名为空']
    cands = list(idx.get(key, []))
    how = '题名全等'
    if not cands:
        cands = list(idx2.get(PREF.sub('', key), [])) if PREF.sub('', key) else []
        how = '去装饰词后题名全等' if cands else ''
        if not cands and key != PREF.sub('', key):
            pass
    if not cands:
        # 近似召回：同责任者 + 题名相似度≥0.8，只进存疑，不进确定
        best = None
        for n in lib_names:
            for kt, w in byauth.get(n, []):
                if abs(len(kt) - len(key)) > max(3, len(key) // 3):
                    continue
                sc = difflib.SequenceMatcher(None, key, kt).ratio()
                if sc >= 0.8 and (best is None or sc > best[0]):
                    best = (sc, w)
        if best:
            return '存疑', best[1]['id'], [best[1]['id']], [f'同责任者+近似题名({best[0]:.2f})：{best[1]["title"]}'] + (['丛书/合集'] if is_coll else [])
        return '无', None, [], ['题名未命中'] + (['丛书/合集'] if is_coll else [])
    # 打分：作者
    scored = []
    for w in cands:
        rel = auth_relation(lib_names, w)
        flags = []
        if a_era is not None and w['eras'] and all(abs(a_era - e) > 0.9 for e in w['eras']):
            flags.append('作者朝代冲突')
        if v_era is not None and w['eras'] and min(w['eras']) > v_era + 0.01:
            flags.append('版本早于作者朝代')
        if juan and w['juan'] and (w['juan_unit'] in (None, '卷')) and abs(juan - w['juan']) > max(5, 0.5 * max(juan, w['juan'])):
            flags.append(f'卷数悬殊({juan}/{w["juan"]})')
        scored.append((rel, flags, w))
    good = [x for x in scored if x[0] == 'eq' and not x[1]]
    eq_any = [x for x in scored if x[0] == 'eq']
    cand_ids = [x[2]['id'] for x in scored]
    tier, wid = '存疑', None
    if how != '题名全等':
        reasons.append(how)
        if len(good) == 1:
            reasons.append('仅去装饰词后相合，降存疑')
            wid = good[0][2]['id']
        elif eq_any:
            wid = eq_any[0][2]['id'] if len(eq_any) == 1 else None
    elif len(good) == 1 and len(eq_any) == 1 and not is_coll and not era_hint and not is_multi:
        tier, wid = '确定', good[0][2]['id']
        reasons.append('题名全等+责任者相合+唯一')
    else:
        if len(eq_any) == 1:
            wid = eq_any[0][2]['id']
        if len(good) > 1:
            reasons.append(f'多个 Work 同题同责任者({len(good)})')
        for rel, fl, w in scored[:3]:
            if rel == 'missing':
                reasons.append('责任者缺一方')
                break
        if not eq_any and all(x[0] == 'diff' for x in scored):
            reasons.append('同题名但责任者不合')
        if len(eq_any) == 1 and eq_any[0][1]:
            reasons += eq_any[0][1]
        if is_coll:
            reasons.append('丛书/合集')
        if era_hint:
            reasons.append('地方志带朝代前缀')
        if is_multi:
            reasons.append('一条记录含多个题名（合刻/合订）')
        if len(cands) > 1 and not good:
            reasons.append(f'同题多 Work({len(cands)})')
    return tier, wid, cand_ids, sorted(set(reasons), key=reasons.index)


def main():
    os.makedirs(OUT, exist_ok=True)
    idx, idx2, works = build_work_index()
    recs = load_lib(SRC)
    rows = []
    cnt = collections.Counter()
    for r in recs:
        tier, wid, cands, reasons = match_one(r, idx, idx2)
        cnt[tier] += 1
        w = works.get(wid) if wid else None
        rows.append(dict(source_record_id=r.get('source_record_id') or (r.get('url', '').split('fid=')[-1] if r.get('url') else ''), tier=tier, lib_title=r.get('title') or r.get('bookName', ''), lib_author=r.get('author', ''),
                         lib_version=r.get('version', ''), digitized=(r.get('extra') or {}).get('數位化狀態', ''), has_image_url=bool(r.get('image_url')), url=r.get('url') or r.get('source_url', ''), work_id=wid or '', work_title=w['title'] if w else '',
                         reasons='；'.join(reasons), candidates=','.join(cands[:8])))
    json.dump(rows, open(os.path.join(OUT, '匹配表.json'), 'w'), ensure_ascii=False)
    with open(os.path.join(OUT, '匹配表.tsv'), 'w', encoding='utf-8', newline='') as f:
        wr = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter='\t')
        wr.writeheader(); wr.writerows(rows)
    json.dump(dict(cnt), open(os.path.join(OUT, 'stats.json'), 'w'))
    n = len(rows)
    print({k: f'{v} ({v / n:.1%})' for k, v in cnt.items()})
    rc = collections.Counter(x for r in rows if r['tier'] == '存疑' for x in r['reasons'].split('；'))
    print(rc.most_common(12))


if __name__ == '__main__':
    main()
