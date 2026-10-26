#!/usr/bin/env python3
"""3a-3 清洗：读 scan_alias.py 的 hits.tsv + works.json，按机械规则分档，产出 pairs.tsv（无序对一行）。

档：
  X-注本对原书 一方题名＝另一方题名＋注疏解说等（原书与注本层次不同，C 档）
  X-内部注  命中的是本库自动录入说明（「本著錄原繫題作」等），非原文
  X-判过    已互链或已在 dedup-judged
  X-异作者  双方首位责任者都有名且不同（姓名、entity 均不同）
  X-朝代    双方朝代相差 ≥2
  X-泛题    别名题名在库里对应 ≥4 条 Work，且双方无同一作者
  X-标记弱  只凭「即／又稱／亦稱／又作／一作／題作」等，且别名不在书名号里
  候选      其余，交逐条核
"""
import collections, csv, importlib.util, json, os, re, sys
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
spec = importlib.util.spec_from_file_location('dc', os.path.join(ROOT, 'scripts/dedup-census.py'))
dc = importlib.util.module_from_spec(spec); spec.loader.exec_module(dc)

STRONG = {'一名', '又名', '亦名', '原名', '初名', '舊名', '本名', '一題', '又題', '原題', '一稱', '改名', '更名', '易名', '或題', '蓋即'}
INTERNAL = re.compile(r'本著錄原繫|原繫題作|自動錄入|匹配檔|源記錄|并入|並入|墓碑')
DYN = ['先秦', '秦', '漢', '三國', '晉', '南北朝', '隋', '唐', '五代', '宋', '遼', '金', '元', '明', '清', '民國']
DMAP = {'周': '先秦', '春秋': '先秦', '戰國': '先秦', '西漢': '漢', '東漢': '漢', '後漢': '漢', '魏': '三國', '蜀': '三國', '吳': '三國',
        '西晉': '晉', '東晉': '晉', '南朝': '南北朝', '北朝': '南北朝', '梁': '南北朝', '陳': '南北朝', '齊': '南北朝', '北魏': '南北朝',
        '北齊': '南北朝', '北周': '南北朝', '劉宋': '南北朝', '南宋': '宋', '北宋': '宋', '後唐': '五代', '南唐': '五代', '後周': '五代',
        '中華民國': '民國', '近代': '民國', '現代': '民國'}

def dyn_idx(f):
    vals = [f.get('dynasty')] + [a[2] for a in f['authors'][:1]]
    for v in vals:
        if not v: continue
        v = str(v).strip('（）()')
        v = DMAP.get(v, v)
        for k in DYN:
            if v.startswith(k) or DMAP.get(v[:2]) == k:
                return DYN.index(k)
    return None

def first(f):
    for a in f['authors']:
        n = dc.norm_name(a[0])
        if n and n not in dc.ANONYMOUS:
            return n, a[3]
    return None, None

def all_names(f):
    return {dc.norm_name(a[0]) for a in f['authors'] if a[0]} - dc.ANONYMOUS | {a[3] for a in f['authors'] if a[3]}

SUBJ = re.compile(r'是書|是編|此書|其書|本書|此本|此編|是集|其集|是本|書|編|集|本條')

def subject_ok(h):
    # 别名须指本书：title_info／author_info 里的括注、strong 标记，或左侧同句含「是書」类主语或本书题名
    if h['field'].endswith(('title_info', 'author_info')) or h['mark'] in STRONG:
        return True
    left = h.get('left') or ''
    core = dc.norm(h['src_title'])[:2]
    return (not left.strip()) or bool(SUBJ.search(left[-12:])) or (core and core in dc.norm(left))

def main(d):
    W = json.load(open(os.path.join(d, 'works.json'), encoding='utf-8'))
    hits = list(csv.DictReader(open(os.path.join(d, 'hits.tsv'), encoding='utf-8'), delimiter='\t', quoting=csv.QUOTE_NONE))
    pairs = collections.defaultdict(list)
    for h in hits:
        pairs[tuple(sorted((h['src'], h['dst'])))].append(h)
    out, C = [], collections.Counter()
    for (a, b), hs in pairs.items():
        fa, fb = W[a], W[b]
        na, ea = first(fa); nb, eb = first(fb)
        share = bool(all_names(fa) & all_names(fb))
        good = [h for h in hs if not INTERNAL.search(h['context']) and not h['field'].startswith('additional_titles')]
        at = [h for h in hs if h['field'].startswith('additional_titles')]
        strong = [h for h in good if subject_ok(h) and (h['mark'] in STRONG or ('《' + h['alias_raw']) in h['context'] or h['field'].endswith(('title_info', 'author_info')))]
        da, db = dyn_idx(fa), dyn_idx(fb)
        ta, tb = dc.norm(fa['title']), dc.norm(fb['title'])
        short, long_ = sorted((ta, tb), key=len)
        if any(h['state'] for h in hs):
            cls = 'X-判过'
        elif short != long_ and long_.startswith(short) and re.search(r'[注註疏解傳箋釋說義述考訂補校評]|本$|篇$|圖', long_[len(short):]):
            cls = 'X-注本对原书'
        elif not good and not at:
            cls = 'X-内部注'
        elif na and nb and na != nb and not (ea and ea == eb) and not share:
            cls = 'X-异作者'
        elif da is not None and db is not None and abs(da - db) >= 2:
            cls = 'X-朝代'
        elif not strong and not at:
            cls = 'X-标记弱'
        elif min(fa['ntitle_n'], fb['ntitle_n']) >= 4 and not share:
            cls = 'X-泛题'
        elif strong:
            cls = '候选' if share else '候选-一侧无作者'
        else:
            cls = '候选-仅additional_titles' if share else 'X-仅AT无同作者'
        C[cls] += 1
        h0 = (strong or good or at or hs)[0]
        out.append([cls, a, fa['title'], '/'.join(x[0] or '' for x in fa['authors'][:2]), str(da), str(fa['juan'] or ''),
                    b, fb['title'], '/'.join(x[0] or '' for x in fb['authors'][:2]), str(db), str(fb['juan'] or ''),
                    '|'.join(sorted({h['mark'] for h in hs})), h0['src'], h0['context']])
    out.sort()
    with open(os.path.join(d, 'pairs.tsv'), 'w', encoding='utf-8') as f:
        f.write('cls\ta\ta_title\ta_auth\ta_dyn\ta_juan\tb\tb_title\tb_auth\tb_dyn\tb_juan\tmarks\tctx_src\tcontext\n')
        for r in out:
            f.write('\t'.join(x.replace('\t', ' ') for x in r) + '\n')
    for k, v in sorted(C.items()): print(k, v)

if __name__ == '__main__':
    main(sys.argv[1])
