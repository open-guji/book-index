"""故宫一号多书（合刻／叢書一册）Book 按 K19 处理：不拆 Book、不建 Work，只在 Book 的故宫资源上加 note
「合刻本：同册另含《某》《某》（K19，只挂主书）」。主书＝Book 现题名（导入时按书名卷数挑定）。
用法：python3 .claude/qa/dedup-4c/npm/k19/k19.py <故宫 library json> <npm Book 路径清单> [--apply]
输出到本目录：plan.tsv（写 note 的）、skip.tsv（同书多条或认不出主书，不写）。"""
import json, os, re, sys, glob, hashlib, datetime, collections
ROOT = os.path.abspath(os.path.dirname(__file__) + '/../../../../..')
sys.path.insert(0, ROOT + '/scripts')
from importlib import import_module
import opencc
norm0 = import_module('dedup-census').norm
CC = opencc.OpenCC('t2s')


def norm(t):
    return CC.convert(norm0(t).replace('杨', '楊'))


def near(a, b):
    return len(a) == len(b) and len(a) >= 3 and sum(x != y for x, y in zip(a, b)) <= 1
HERE = os.path.dirname(os.path.abspath(__file__))
LIB, LST, APPLY = sys.argv[1], sys.argv[2], '--apply' in sys.argv
TODAY = datetime.date.today().isoformat()
NUM = '一二三四五六七八九十百千〇零兩廿卅'
CUT = re.compile(r'([%s]+卷|不分卷|殘存|存[%s]+卷|附[^　 ]*$).*' % (NUM, NUM))


def base(t):
    t = re.sub(r'\s+', '', t or '')
    return CUT.sub('', t) or t


lib = collections.defaultdict(list)
for r in json.load(open(LIB, encoding='utf-8')):
    lib[r['id']].append(r)
plan, skip = [], []
for p in open(LST).read().split():
    p = os.path.join(ROOT, p) if not p.startswith('/') else p
    b = json.load(open(p, encoding='utf-8'))
    hid = (b.get('metadata') or {}).get('npm_item_id')
    rs = lib.get(hid, [])
    if len(rs) < 2:
        continue
    titles = []
    for r in rs:
        t = base(r['bookName'])
        if t not in titles:
            titles.append(t)
    bt = norm(base(b.get('title')))
    mine = [t for t in titles if norm(t) == bt]
    if not mine:  # 退一步：互含（僧寶傳／禪林僧寶傳）、同长差一字（辨／辯），须唯一
        cand = [t for t in titles if len(bt) >= 2 and (bt in norm(t) or norm(t) in bt)] or [t for t in titles if near(norm(t), bt)]
        mine = cand if len(cand) == 1 else []
    others = [t for t in titles if t not in mine]
    if not others:
        skip.append([b['id'], hid, b.get('title'), '同书多条', '；'.join(titles)]); continue
    if not mine:
        skip.append([b['id'], hid, b.get('title'), '认不出主书', '；'.join(titles)]); continue
    note = '合刻本：同册另含%s（K19，只挂主书）' % ''.join('《%s》' % t for t in others)
    res = [x for x in b.get('resources') or [] if x.get('id') == 'npm-rarebooks' and (x.get('metadata') or {}).get('item_id') == hid]
    if len(res) != 1:
        skip.append([b['id'], hid, b.get('title'), '故宫资源条数 %d' % len(res), '；'.join(titles)]); continue
    pre = hashlib.sha256(open(p, 'rb').read()).hexdigest()
    plan.append([b['id'], hid, b.get('title'), b.get('work_id') or '', note, pre])
    if APPLY:
        r0 = res[0]
        if r0.get('note') == note:
            continue
        r0['note'] = (r0['note'] + '；' + note) if r0.get('note') else note
        v = (b.get('revision') or '1.0.0').split('.')
        b.pop('revision', None); b.pop('revised_at', None)
        b['revision'] = '%s.%d.0' % (v[0], int(v[1]) + 1); b['revised_at'] = TODAY
        with open(p, 'w', encoding='utf-8', newline='\n') as f:
            f.write(json.dumps(b, ensure_ascii=False, indent=2) + '\n')
with open(os.path.join(HERE, 'plan.tsv'), 'w', encoding='utf-8') as f:
    f.write('book\tholding\tbook_title\twork_id\tnote\tpre_sha256\n')
    for r in plan: f.write('\t'.join(r) + '\n')
with open(os.path.join(HERE, 'skip.tsv'), 'w', encoding='utf-8') as f:
    f.write('book\tholding\tbook_title\t原因\t故宫题名\n')
    for r in skip: f.write('\t'.join(map(str, r)) + '\n')
print('写 note', len(plan), '不写', len(skip), collections.Counter(r[3] for r in skip))
