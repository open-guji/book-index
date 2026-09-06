#!/usr/bin/env python3
"""全庫品質掃描電池（qa-sweep）。

用法：
  python3 .claude/qa/scan.py                      # 全庫，按 period 分組計數
  python3 .claude/qa/scan.py --period song        # 只報 song 之條（宇宙仍是全庫）
  python3 .claude/qa/scan.py --period none        # period 缺值者
  python3 .claude/qa/scan.py --period ming --show F --limit 50   # 印某一項之明細
  python3 .claude/qa/scan.py --period ming --out /tmp/ming.json  # 明細全數落檔

各項檢查（字母即報表之鍵）：
  A basis_stale      period_basis 句首稱「據 authors[i].dynasty「X」」而實錄非 X／無此鍵
  B dangling         related_works / books / authors.entity_id / contained_in / source_bid 指向不存在之 ID
  C entity_period    撰人 entity 之 period 與 work 之 period 不同（附役，注疏類自行判）
  D upper_conflict   period_upper 早於 period
  E lost_but_text    loss_status=lost 而有 Book／_has_text／_has_image
  F name_mismatch    撰人名不在所繫 entity 之 primary_name／alt_names（容「X等」「X氏」）
  G title_catalog    題名夾雜卷數／撰人／殘語（「二卷」「(存卷上)」「 題」…）
  H author_odd       撰人名可疑：單字、含數字／標點／「等」「撰」「注」
  I dup_title        同題且撰人集合相同（或俱無撰人）之組
  J desc_gap         著錄 ≥4 源而 description 全缺
  K entity_oneway    work→entity 無回指；entity.works 懸空；entity→work 無回指（人指書而書之 authors 不指人）
  L lone_outlier     一 entity 名下諸 work 之 period，n−1 同而恰一異（磁鐵／誤繫徵候）
  M index_drift      索引 period/loss_status/title/subtype/author/dynasty/role 與記錄檔不符（dynasty 取頂層，無則 authors[0]）
  N source_no_bid    indexed_by 有 source 而無 source_bid（來源為 Collection 者豁免：其本無 work-space 之 bid）
  O dyn_transitional 撰人 entity 之 dynasty 作「元末明初」類跨代標籤而生卒與之相斥（L5 循環論據之遺）

判準與踩坑見 PROTOCOL.md、PITFALLS.md。本檔只掃不改。
"""
import argparse, collections, glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
ORD = ['pre-qin','qin-han','three-kingdoms','jin','nanbeichao','sui-tang','five-dynasties',
       'song','liao-jin-yuan','ming','qing','modern']

def _load_idx(fam):
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'index', fam, '*.json')):
        out.update(json.load(open(f)))
    return out

def load_universe():
    IW, IB, IE = _load_idx('works'), _load_idx('books'), _load_idx('entities')
    IC = json.load(open(os.path.join(ROOT, 'index', 'collections.json')))
    return IW, IB, IE, IC

def read(path):
    return json.load(open(os.path.join(ROOT, path)))

def period_key(p):
    return 'none' if p is None else p

# ---------------------------------------------------------------- checks
BASIS_RE = re.compile(r'^據 authors\[(\d+)\]\.dynasty[「『"]([^」』"]+)[」』"]')
TITLE_RE = re.compile(r'[一二三四五六七八九十百]+卷|\d+卷|\(存|（存|原目|[，,：:]| 題$|卷首$| 著$')
ODD_RE = re.compile(r'[0-9〇一二三四五六七八九十百千]|卷|篇|撰$|注$|等$|、|，|。|\?|？|\[|\]|（|）|\(|\)')
LATE_ROLE = {'注','疏','箋','訓詁','音','音義','集解','集注','校','校注','輯','輯佚','輯錄','補','補注','釋','正義','章句','解','箋注','纂','編','刊','訂','評','批','校刊','校訂','增補','續'}

def run_checks(works, IW, IB, IE, IC, ents):
    """works: dict id->record (全庫)。回傳 {check: [row,...]}。row 皆含 id,title,period。"""
    ALL = set(IW) | set(IB) | set(IE) | set(IC)
    COLL_TITLES = {v.get('title') for v in IC.values()}
    R = collections.defaultdict(list)
    def row(w, **kw):
        d = {'id': w['id'], 'title': w.get('title'), 'period': period_key(w.get('period'))}
        d.update(kw); return d

    # 反向表：entity -> works 實繫（自 work 側）
    w2e = collections.defaultdict(set)
    for w in works.values():
        for a in (w.get('authors') or []):
            if a.get('entity_id'): w2e[a['entity_id']].add(w['id'])

    for w in works.values():
        a_list = w.get('authors') or []
        # A
        m = BASIS_RE.match((w.get('period_basis') or '').strip())
        if m:
            i, claim = int(m.group(1)), m.group(2)
            real = a_list[i].get('dynasty') if i < len(a_list) else '<無此撰人>'
            if real != claim:
                R['A'].append(row(w, claim=claim, real=real, author=(a_list[i].get('name') if i < len(a_list) else None)))
        # B
        for r in (w.get('related_works') or []):
            if r.get('id') and r['id'] not in ALL: R['B'].append(row(w, field='related_works', ref=r['id'], ref_title=r.get('title')))
        for b in (w.get('books') or []):
            if b not in ALL: R['B'].append(row(w, field='books', ref=b))
        for a in a_list:
            if a.get('entity_id') and a['entity_id'] not in IE: R['B'].append(row(w, field='authors.entity_id', ref=a['entity_id'], author=a.get('name')))
        for k in ('contained_in', 'additional_works'):
            for r in (w.get(k) or []):
                rid = r.get('id') if isinstance(r, dict) else r
                if rid and rid not in ALL: R['B'].append(row(w, field=k, ref=rid))
        for ib in (w.get('indexed_by') or []) + (w.get('emendated_by') or []):
            if ib.get('source_bid') and ib['source_bid'] not in ALL: R['B'].append(row(w, field='source_bid', ref=ib['source_bid'], source=ib.get('source')))
            if ib.get('source') and not ib.get('source_bid') and ib.get('source') not in COLL_TITLES: R['N'].append(row(w, source=ib.get('source')))
        # C / F / K(oneway)
        for a in a_list:
            eid = a.get('entity_id')
            if not eid or eid not in IE: continue
            e = ents.get(eid)
            ie = IE[eid]
            ep = ie.get('period')
            if ep and w.get('period') and ep != w['period']:
                R['C'].append(row(w, author=a.get('name'), role=a.get('role'), entity=eid, entity_name=ie.get('primary_name'),
                                  entity_dynasty=ie.get('dynasty'), entity_period=ep,
                                  annot=(a.get('role') in LATE_ROLE)))
            nm = a.get('name') or ''
            if e is not None:
                names = {e.get('primary_name')} | {x.get('name') for x in (e.get('alt_names') or []) if isinstance(x, dict)}
                ok = nm in names or (nm.endswith('等') and nm[:-1] in names) or (nm.endswith('氏') and any((n or '').startswith(nm[:-1]) for n in names))
                if not ok:
                    R['F'].append(row(w, author=nm, entity=eid, entity_name=e.get('primary_name'),
                                      alt=[x.get('name') for x in (e.get('alt_names') or []) if isinstance(x, dict)], entity_dynasty=e.get('dynasty')))
                if not any(x.get('work_id') == w['id'] for x in (e.get('works') or [])):
                    R['K'].append(row(w, kind='work->entity 無回指', author=nm, entity=eid, entity_name=e.get('primary_name')))
        # D
        pu, p = w.get('period_upper'), w.get('period')
        if pu in ORD and p in ORD and ORD.index(pu) < ORD.index(p):
            R['D'].append(row(w, period_upper=pu))
        # E
        if w.get('loss_status') == 'lost' and (w.get('books') or w.get('_has_text') or w.get('_has_image')):
            R['E'].append(row(w, books=len(w.get('books') or []), has_text=bool(w.get('_has_text')), has_image=bool(w.get('_has_image'))))
        # G
        if TITLE_RE.search(w.get('title') or ''): R['G'].append(row(w))
        # H
        for a in a_list:
            nm = a.get('name') or ''
            if nm and (len(nm) == 1 or ODD_RE.search(nm)):
                R['H'].append(row(w, author=nm, dynasty=a.get('dynasty'), entity=a.get('entity_id'), note=(a.get('note') or '')[:60]))
        # J
        d = w.get('description'); dt = (d.get('text') if isinstance(d, dict) else d) or ''
        if not dt and len(w.get('indexed_by') or []) >= 4:
            R['J'].append(row(w, sources=len(w['indexed_by'])))
        # M
        ie = IW.get(w['id']) or {}
        nz = lambda v: None if v in ('', None) else v
        a0 = a_list[0] if a_list else {}
        want = {f: nz(w.get(f)) for f in ('period', 'loss_status', 'title', 'subtype')}
        want.update({'author': nz(a0.get('name')), 'role': nz(a0.get('role')),
                     'dynasty': nz(w.get('dynasty')) if nz(w.get('dynasty')) is not None else nz(a0.get('dynasty'))})
        for f, b_ in want.items():
            a_ = nz(ie.get(f))
            if a_ != b_: R['M'].append(row(w, field=f, index=a_, record=b_))

    # I 同題同撰人
    groups = collections.defaultdict(list)
    for w in works.values():
        au = tuple(sorted((a.get('name') or '') for a in (w.get('authors') or [])))
        groups[(w.get('title'), au)].append(w)
    for (t, au), ws in groups.items():
        if len(ws) > 1:
            for w in ws:
                R['I'].append(row(w, group_title=t, authors=list(au), group_ids=[x['id'] for x in ws],
                                  sources=[i.get('source') for i in (w.get('indexed_by') or [])]))

    # K(entity side) / L / O
    for eid, e in ents.items():
        per = collections.Counter()
        for x in (e.get('works') or []):
            wid = x.get('work_id')
            if wid not in IW:
                R['K'].append({'id': wid, 'title': None, 'period': 'none', 'kind': 'entity.works 懸空',
                               'entity': eid, 'entity_name': e.get('primary_name')})
                continue
            if wid in works and eid not in w2e.get(eid, set()) and not any(a.get('entity_id') == eid for a in (works[wid].get('authors') or [])):
                R['K'].append(row(works[wid], kind='entity->work 無回指（人指書而書不指人）', entity=eid, entity_name=e.get('primary_name'),
                                  work_authors=[a.get('name') for a in (works[wid].get('authors') or [])]))
            per[period_key(IW[wid].get('period'))] += 1
        dy = e.get('dynasty') or ''
        if ('末' in dy and '初' in dy) or dy in ('宋元', '元明', '明清', '金元'):
            by, dyr = e.get('birth_year'), e.get('death_year')
            # 跨代標籤所跨之後一代起年：元末明初→1368；宋末元初→1279；明末清初→1644；金元→1234
            start = {'明': 1368, '元': 1279, '清': 1644}.get(dy[dy.index('初')-1] if '初' in dy else dy[-1], None)
            bogus = bool(start and ((by and by >= start + 2) or (dyr and dyr >= start + 82)))
            if bogus:
                for x in (e.get('works') or []):
                    wid = x.get('work_id')
                    if wid in works:
                        R['O'].append(row(works[wid], entity=eid, entity_name=e.get('primary_name'), entity_dynasty=dy,
                                          birth=by, death=dyr, basis=(e.get('dynasty_basis') or '')[:80]))
        dated = {k: v for k, v in per.items() if k != 'none'}
        if len(dated) >= 2:
            top, n = max(dated.items(), key=lambda kv: kv[1])
            rest = sum(v for k, v in dated.items() if k != top)
            if rest == 1 and n >= 2:
                odd = [k for k in dated if k != top][0]
                odd_w = [x['work_id'] for x in e['works'] if x.get('work_id') in IW and period_key(IW[x['work_id']].get('period')) == odd]
                for wid in odd_w:
                    wrec = works.get(wid)
                    R['L'].append({'id': wid, 'title': IW[wid].get('title'), 'period': odd, 'entity': eid,
                                   'entity_name': e.get('primary_name'), 'entity_dynasty': e.get('dynasty'),
                                   'majority_period': top, 'majority_n': n,
                                   'role': next((a.get('role') for a in ((wrec or {}).get('authors') or []) if a.get('entity_id') == eid), None)})
    return R

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--period', help='逗號分隔；none 表缺值', default=None)
    ap.add_argument('--show', help='印某一檢查之明細，如 F', default=None)
    ap.add_argument('--limit', type=int, default=40)
    ap.add_argument('--out', help='明細落檔（JSON）', default=None)
    ap.add_argument('--summary-out', help='計數落檔（JSON）', default=None)
    a = ap.parse_args()
    want = set(a.period.split(',')) if a.period else None

    IW, IB, IE, IC = load_universe()
    works = {}
    for wid, ie in IW.items():
        try: works[wid] = read(ie['path'])
        except Exception as ex: print('讀檔失敗', wid, ex, file=sys.stderr)
    ents = {}
    for eid, ie in IE.items():
        try: ents[eid] = read(ie['path'])
        except Exception as ex: print('讀檔失敗', eid, ex, file=sys.stderr)
    print(f'宇宙：works {len(works)} books {len(IB)} entities {len(ents)} collections {len(IC)}', file=sys.stderr)

    R = run_checks(works, IW, IB, IE, IC, ents)
    if want:
        R = {k: [r for r in v if r.get('period') in want] for k, v in R.items()}

    # 計數表：check × period
    table = collections.defaultdict(lambda: collections.Counter())
    for k, rows in R.items():
        for r in rows: table[k][r.get('period')] += 1
    periods = [p for p in ORD + ['none'] if (not want or p in want)]
    print('check ' + ' '.join(f'{p[:6]:>6}' for p in periods) + '   total')
    for k in sorted(table):
        print(f'{k:5s} ' + ' '.join(f'{table[k].get(p,0):6d}' for p in periods) + f'   {sum(table[k].values()):6d}')
    if a.show:
        rows = R.get(a.show, [])
        print(f'\n== {a.show}: {len(rows)} ==')
        for r in rows[:a.limit]: print(json.dumps(r, ensure_ascii=False))
    if a.out:
        json.dump(R, open(a.out, 'w'), ensure_ascii=False, indent=1)
        print('明細已寫', a.out, file=sys.stderr)
    if a.summary_out:
        json.dump({'periods': {p: sum(1 for w in works.values() if period_key(w.get('period')) == p) for p in ORD + ['none']},
                   'checks': {k: dict(v) for k, v in table.items()}},
                  open(a.summary_out, 'w'), ensure_ascii=False, indent=1)

if __name__ == '__main__':
    main()
