"""4c 落地：按复核定案改国图 Book 的 work_id；需要新建的 Work 先鑄 id 建档。
用法：python3 .claude/qa/dedup-4c/apply_4c.py <批目录> [--apply]
批目录下 decisions.json：[{book, verdict: MOVE|NEW, target, new_work:{title,authors}, reason}]（KEEP／UNSURE 忽略）
乾跑只打印计划；--apply 写 Book／Work、刷 index、写台账 ledger.tsv 与 new_works.json，
并把新建 Work 与原挂 Work 记为分立写进 .claude/qa/dedup-judged/4c.tsv。"""
import json, os, sys, re, glob, hashlib, collections, datetime
ROOT = os.path.abspath(os.path.dirname(__file__) + '/../../..')
sys.path.insert(0, ROOT + '/.claude/qa'); sys.path.insert(0, ROOT + '/build')
import mintid  # noqa
mintid.LANE_MACHINE['dedup-4c'] = 2035
import build_derived as BD  # noqa
os.chdir(ROOT)
D, APPLY = sys.argv[1], '--apply' in sys.argv
TODAY = datetime.date.today().isoformat()
dec = [d for d in json.load(open(os.path.join(D, 'decisions.json'))) if d['verdict'] in ('MOVE', 'NEW')]
print('载入定案', len(dec)); assert dec


def find(i, fam):
    ps = glob.glob(f'{fam}/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')
    assert len(ps) == 1, (i, ps)
    return ps[0]


def load(p): return json.load(open(p, encoding='utf-8'))


def dump(p, d):
    with open(p, 'w', encoding='utf-8', newline='\n') as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')


def bump(d):
    r = (d.get('revision') or '1.0.0').split('.')
    rev = '%s.%d.0' % (r[0], int(r[1]) + 1)
    d.pop('revision', None); d.pop('revised_at', None)
    d['revision'] = rev; d['revised_at'] = TODAY


# 新建 Work：同题同首位著者的合用一个
groups = collections.OrderedDict()
for d in dec:
    if d['verdict'] == 'NEW':
        nw = d['new_work']; a0 = (nw.get('authors') or [{}])[0].get('name', '')
        groups.setdefault((nw['title'], a0), []).append(d)
ids = mintid.mint('Work', 'dedup-4c', len(groups)) if (APPLY and groups) else ['<新id%d>' % k for k in range(len(groups))]
new_works = {}
for (key, ds), wid in zip(groups.items(), ids):
    nw = ds[0]['new_work']
    authors = [{k: v for k, v in (('name', a.get('name')), ('role', a.get('role') or '撰'), ('dynasty', a.get('dynasty'))) if v}
               for a in nw.get('authors') or []]
    w = {'schema_version': 1, 'id': wid, 'type': 'work', 'title': nw['title'], 'authors': authors}
    if authors and authors[0].get('dynasty'):
        w['dynasty'] = authors[0]['dynasty']
    olds = sorted({x['cur'] for x in ds})
    w['ai_note'] = ('2026-10-25 去重 4c 复核：據國圖著錄新建（國圖 Book %s）；同題既有 Work %s 為他書，不併。依據：%s'
                    % ('、'.join(x['book'] for x in ds), '、'.join(olds), ds[0]['reason']))
    w['revision'] = '1.0.0'; w['revised_at'] = TODAY
    new_works[wid] = (w, ds)
    for x in ds: x['target'] = wid

ledger, judged, touched = [], [], []
for d in dec:
    bp = find(d['book'], 'Book'); b = load(bp)
    old = b.get('work_id'); assert old == d['cur'], (d['book'], old, d['cur'])
    tgt = d['target']
    if d['verdict'] == 'MOVE':
        tp = find(tgt, 'Work'); t = load(tp); assert not t.get('merged_into'), tgt
        ttitle = t.get('title')
    else:
        ttitle = new_works[tgt][0]['title']
    pre = hashlib.sha256(open(bp, 'rb').read()).hexdigest()
    ledger.append([d['book'], old, tgt, d['verdict'], ttitle, d['reason'], pre])
    print(d['verdict'], d['book'], old, '->', tgt, ttitle, '|', d['reason'][:60])
    if not APPLY:
        continue
    b['work_id'] = tgt
    b['ai_note'] = (b.get('ai_note') or '') + '\n\n2026-10-25 去重 4c 复核：由 %s 改挂 %s《%s》（%s）。依據：%s' % (
        old, tgt, ttitle, '新建 Work' if d['verdict'] == 'NEW' else '既有 Work', d['reason'])
    bump(b); dump(bp, b); touched.append(bp)

if APPLY:
    for wid, (w, ds) in new_works.items():
        p = mintid.path_for(wid, re.sub(r'[\\/:*?"<>|\s]', '', w['title']))
        os.makedirs(os.path.dirname(p), exist_ok=True); dump(p, w)
        for o in sorted({x['cur'] for x in ds}):
            judged.append([wid, o, 'C', '4c：國圖本著者與現挂 Work 不同，另立新 Work（%s）' % ds[0]['reason'][:80]])
        # 新 Work 入 index
        srel = f"index/works/{BD.shard_of(wid):x}.json"
        sh = json.load(open(srel, encoding='utf-8')); sh[wid] = BD.index_entry(w, 'Work', p)
        BD.write_index(ROOT, {srel: sh})
    with open(os.path.join(D, 'ledger.tsv'), 'w', encoding='utf-8') as f:
        f.write('book\told_work\tnew_work\tverdict\tnew_title\treason\tpre_sha256\n')
        for r in ledger: f.write('\t'.join(r) + '\n')
    json.dump({k: v[0] for k, v in new_works.items()}, open(os.path.join(D, 'new_works.json'), 'w'), ensure_ascii=False, indent=1)
    jp = '.claude/qa/dedup-judged/4c.tsv'
    os.makedirs(os.path.dirname(jp), exist_ok=True)
    head = not os.path.exists(jp)
    with open(jp, 'a', encoding='utf-8') as f:
        if head: f.write('# 4c 国图 Book 挂接复核：新建 Work 与原挂同题 Work 判为分立（C）\n')
        for r in judged: f.write('\t'.join(r) + '\n')
print('改挂', sum(1 for d in dec if d['verdict'] == 'MOVE'), '新建 Work', len(new_works), '涉及 Book', len(dec))
