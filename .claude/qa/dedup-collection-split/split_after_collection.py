#!/usr/bin/env python3
"""【Collection 补建后续做】存疑 Book 按总目丛书实例拆开并挂 Collection。
基于 split_hidden.py：不限 E／F／G 道、不要求 contained_in 为空；每个拆分部分直接 contained_in＝其丛书头对应的 Collection（同题同版本项的几个头都挂），原有挂靠中不在目标内的（如故宫善本舊籍、文淵閣）留给馆藏机构匹配的部分，匹配不到留给保留原 id 的部分。
只有 1 组（归一化后）的 Book 不拆，只追加 contained_in。
用法：--only 文件（每行一个 Book id）；不写 index/（已删）。

原文档：拆开隐性错并：E／F／G 道 Book 的源记录分属 ≥2 个总目丛书实例，却不挂（或只挂 1 个）Collection，按丛书实例拆开。

口径（用户 2026-10-28 定，见 ai-team 去重方案 00 文件第七节）：
- 一个 Book＝一个版本；不同丛书实例＝不同实体书＝不同版本；同一丛书同一版次的多条著录合为一个 Book。
- 分册（总目丛书实例带 set_name／volume_name，如「第三函」「昴集」）绝不作为拆分依据：丛书名与版本项相同则并回同一组。
- 复核「同名丛书不同版次是否其实同一版本」：丛书实例头记录的版本项（刊刻者＋年代）完全相同才并（key=丛书名+版本项），
  否则按 series_id 各成一组。
- 暂不挂 Collection；本批只拆 contained_in 为空的 Book（已挂 ≥2 的归拆回-二，挂 1 个的存疑）。
- 版本信息写进 ai_note（丛书名、丛书版本项、series_id），edition 置空，与拆回-二一致。

用法：split_hidden.py --parsed <parsed 目录> [--limit-new N] [--skip-new N] --out <批目录> [--apply]
乾跑默认；--apply 才写正式库与 index。
"""
import argparse, collections, copy, glob, hashlib, json, os, pathlib, re, sys, time

ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / '.claude/qa'))
import mintid  # noqa: E402

MACHINE = 2034
TODAY = time.strftime('%Y-%m-%d')
LANE = re.compile(r'^([EFG]) 道')
NORMT = re.compile(r'（[^）]*）|[一二三四五六七八九十百千零〇]+種.*$|[一二三四五六七八九十百千零〇]+卷.*$')
def normt(t):
    return NORMT.sub('', t or '')
DROP = ('edition_type', 'publication_info', 'dating')


def die(m):
    sys.exit('错误：' + m)


def jdump(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def sha(p):
    return hashlib.sha256(pathlib.Path(p).read_bytes()).hexdigest()


def clean(label):
    return ';'.join(x for x in (label or '').split(';') if x and '磧砂' not in x and '延聖院' not in x)


def item(src):
    return (src or '').rsplit('item/', 1)[-1].rsplit('/', 1)[-1]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--parsed', required=True)
    ap.add_argument('--only')
    ap.add_argument('--limit-new', type=int, help='本批新建 Book 数上限（整本为单位）')
    ap.add_argument('--skip', help='已拆过的原 Book id 文件（每行一个），跳过')
    ap.add_argument('--out', default=str(pathlib.Path(__file__).parent / 'plan'))
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    only = set(open(a.only).read().split()) if a.only else None
    skip = set(open(a.skip).read().split()) if a.skip else set()

    books, paths = {}, {}
    for r, _d, fs in os.walk(ROOT / 'Book'):
        for fn in fs:
            if not fn.endswith('.json'):
                continue
            p = pathlib.Path(r) / fn
            d = json.loads(p.read_text(encoding='utf-8'))
            paths[d['id']] = p
            if 'merged_into' in d:
                continue
            if only is None or d['id'] in only:
                books[d['id']] = d
    need = {s.get('id') for b in books.values() for s in b.get('sources') or []}
    rec = {}
    for f in sorted(glob.glob(os.path.join(a.parsed, '*.json'))):
        for r in json.load(open(f, encoding='utf-8')):
            if r['source_record_id'] in need:
                rec[r['source_record_id']] = r
    sids = {(r.get('series') or {}).get('series_id') for r in rec.values()} - {None, ''}
    head = {}
    exist, cdesc = {}, {}
    for f in glob.glob(str(ROOT / 'Collection/**/*.json'), recursive=True):
        dd = json.load(open(f, encoding='utf-8'))
        cdesc[dd['id']] = (dd.get('title'), dd.get('edition'))
        for s_ in dd.get('sources') or []:
            if isinstance(s_, dict) and s_.get('id'):
                exist[s_['id']] = dd['id']
    for f in sorted(glob.glob(os.path.join(a.parsed, '*.json'))):
        for r in json.load(open(f, encoding='utf-8')):
            if r['source_record_id'] in sids:
                head[r['source_record_id']] = r
    print(f'载入：正式 Book {len(paths)}、范围 Book {len(books)}、源记录 {len(rec)}、丛书实例头记录 {len(head)}/{len(sids)}')
    if not books or not rec or not head:
        die('载入条数为 0')


    def key(sid, se):
        h = head.get(sid); e = h['edition'] if h else {}
        spec = bool(e.get('label')) and (e.get('publisher') or re.search(r'[年間间]', e.get('time_text') or ''))
        t = normt(se.get('series_title') or ((h or {}).get('title') or {}).get('name'))  # batch-19 起：源记录无 series_title 时用丛书头记录名
        vol = bool(se.get('volume_name') or se.get('set_name'))
        if t and (spec or vol):
            return ('E' if spec else 'V', t, e.get('label', ''))
        return ('S', sid)

    plan, hold, stat = [], [], collections.Counter()
    for bid in sorted(books):
        b = books[bid]
        if bid in skip or (only is not None and bid not in only):
            continue
        m_ = LANE.match(b.get('ai_note') or ''); lane = m_.group(1) if m_ else '-'

        def H(why):
            hold.append({'book': bid, 'lane': lane, 'why': why, 'title': b.get('title')}); stat['存疑：' + why] += 1
        srcs = [s.get('id') for s in b.get('sources') or []]
        if any(s not in rec for s in srcs):
            H('源记录不在总目解析数据'); continue
        sid_of = {s: (rec[s].get('series') or {}).get('series_id') or '' for s in srcs}
        real = {x for x in sid_of.values() if x}
        if not real:
            H('无丛书源记录'); continue
        if re.search(r'[终終]判', b.get('ai_note') or ''):
            H('有人工终判（如 hold80）'); continue
        if any(x not in head for x in real):
            H('丛书实例头记录缺失'); continue
        groups = collections.OrderedDict(); virt = []; bad = None
        for s in srcs:
            sid = sid_of[s]
            if not sid:
                if rec[s]['holdings']:
                    bad = '无丛书源记录带馆藏（疑单行本混入）'; break
                virt.append(s); continue
            groups.setdefault(key(sid, rec[s]['series']), []).append(s)
        if bad:
            H(bad); continue
        cols_of = lambda ss: sorted({exist[sid_of[s]] for s in ss if sid_of[s] in exist})
        if any(sid not in exist for sid in real):
            H('丛书头尚无 Collection'); continue
        if len(groups) < 2:
            ss = next(iter(groups.values()))
            cur = [x['id'] for x in b.get('contained_in') or []]
            new = cols_of(ss)
            if set(cur) == set(new):
                stat['单版本且已挂对，不动'] += 1; continue
            extra = [c for c in cur if c not in new]
            if extra:
                H('单版本但已挂的 Collection 与总目丛书头不符'); continue
            plan.append({'book': bid, 'lane': lane, 'attach_only': True, 'path': str(paths[bid].relative_to(ROOT)), 'sha256': sha(paths[bid]),
                         'virtual_removed': [], 'parts': [{'keep': True, 'id': bid, 'path': str(paths[bid].relative_to(ROOT)), 'series': [], 'sources': ss, 'cols': cur + new, 'record': None}]})
            stat['单版本补挂'] += 1
            continue
        owner = {}
        for k, ss in groups.items():
            for s in ss:
                for h in rec[s]['holdings']:
                    owner.setdefault(item(h.get('item_uri')), set()).add(k)
        pv = collections.defaultdict(list); amb = False
        for p in b.get('provenance') or []:
            o = owner.get(item(p.get('source')))
            if not o or len(o) != 1:
                curci = {x['id'] for x in b.get('contained_in') or []}
                anchor = next((k for k, ss in groups.items() if set(cols_of(ss)) & curci), None)
                if anchor is not None and (not o or anchor in o):
                    pv[anchor].append(p); continue
                amb = True; break
            pv[next(iter(o))].append(p)
        if amb:
            H('provenance 分不干净'); continue
        srcmap = {s['id']: s for s in b.get('sources') or []}
        ks = list(groups)
        keepk = max(ks, key=lambda k: (len(pv[k]), -ks.index(k)))
        old_ed = b.get('edition') or ''
        dropped = {k: b[k] for k in DROP if k in b}
        parts = []
        for k in ks:
            ss = groups[k]; nb = copy.deepcopy(b)
            for d in DROP:
                nb.pop(d, None)
            nb['edition'] = ''
            nb['sources'] = [srcmap[s] for s in ss]
            nb['provenance'] = pv[k]
            if not nb['provenance']:
                nb.pop('provenance')
            names = collections.Counter(rec[s]['title'].get('name') for s in ss if rec[s]['title'].get('name'))
            if virt and names:
                nb['title'] = names.most_common(1)[0][0]
            sidlist = list(dict.fromkeys(sid_of[s] for s in ss))
            h0 = head[sidlist[0]]; e0 = h0['edition']
            stitle = rec[ss[0]]['series'].get('series_title') or ''
            for ib in nb.get('indexed_by') or []:
                if ib.get('summary') and ib['summary'].count('｜') >= 3:
                    f = ib['summary'].split('｜')
                    f[2] = e0.get('label') or ''
                    f[3] = '、'.join(dict.fromkeys(p.get('institution') for p in pv[k] if p.get('institution')))
                    ib['summary'] = '｜'.join(f)
            labels = list(dict.fromkeys(clean(rec[s]['edition']['label']) for s in ss if clean(rec[s]['edition']['label'])))
            note = (f'拆分（{TODAY}，隐性错并拆分）：E／F／G 道聚簇把同一子目在不同叢書實例（不同實體版本）的總目記錄並成一條'
                    f'（原 {bid}，涉 {len(real)} 個叢書實例、拆為 {len(ks)} 條），按源記錄所屬叢書實例（總目 series_id）拆開；'
                    f'本條屬叢書{"「" + stitle + "」" if stitle else ""}實例 {"、".join(sidlist)}，'
                    f'叢書版本項：{e0.get("label") or "（無）"}。按丛书头挂入对应 Collection。')
            if k == keepk:
                note += '原 id 保留於本條。'
                if virt:
                    note += f'總目「××本」子目著錄（無叢書、無館藏）{"、".join(virt)} 不屬任何實例，已自 sources 移出。'
            if old_ed or dropped:
                note += f'原 edition「{old_ed}」' + (f'及 {",".join(dropped)}' if dropped else '') + ' 取自聚簇代表記錄，已去，版本見上。'
            if labels:
                note += f'總目子目版本標注：{"；".join(labels)}。'
            nb['ai_note'] = (b.get('ai_note') or '') + '\n' + note
            if k == keepk:
                rv = (b.get('revision') or '1.0.0').split('.')
                nb['revision'] = f'{int(rv[0]) + 1}.0.0'
            else:
                nb['revision'] = '1.0.0'
                nb.pop('merged_from', None)
            nb['revised_at'] = TODAY
            nb['contained_in'] = [{'id': c} for c in cols_of(ss)]
            parts.append({'keep': k == keepk, 'series': sidlist, 'sources': ss, 'record': nb})
        extras = [x['id'] for x in b.get('contained_in') or [] if x['id'] not in {c for p in parts for c in (y['id'] for y in p['record']['contained_in'])}]
        for c in extras:
            tt = ' '.join(str(v) for v in cdesc.get(c, []) if v)
            tgt = [p for p in parts if any(pp.get('institution') and (pp['institution'] in tt or tt.split(' ')[0] in pp['institution']) for pp in p['record'].get('provenance') or [])] or [p for p in parts if p['keep']]
            for p in tgt:
                if c not in [y['id'] for y in p['record']['contained_in']]:
                    p['record']['contained_in'].append({'id': c})
        got = [s for p in parts for s in p['sources']]
        assert sorted(got + virt) == sorted(srcs), bid
        assert sum(len(p['record'].get('provenance') or []) for p in parts) == len(b.get('provenance') or []), bid
        if a.limit_new and stat['新建 Book'] + len(parts) - 1 > a.limit_new:
            stat['超批上限，留下批'] += 1
            continue
        plan.append({'book': bid, 'lane': lane, 'path': str(paths[bid].relative_to(ROOT)), 'sha256': sha(paths[bid]),
                     'virtual_removed': virt, 'parts': parts})
        stat['拆的原 Book'] += 1; stat['新建 Book'] += len(parts) - 1

    used = set(paths); ts = int(time.time()); seq = 0
    for it in plan:
        for p in it['parts']:
            if p['keep']:
                p['id'] = it['book']; p['path'] = it['path']; continue
            while True:
                if seq > 255:
                    ts += 1; seq = 0
                raw = ((ts & ((1 << 40) - 1)) << 19) | (MACHINE << 8) | seq
                seq += 1
                i = mintid.b36(raw)
                if mintid.dec(i) == raw and i not in used:
                    break
            used.add(i)
            r = p['record']; r['id'] = i
            p['record'] = {k: r[k] for k in ['schema_version', 'id'] + [k for k in r if k not in ('schema_version', 'id')]}
            p['id'] = i
            p['path'] = mintid.path_for(i, re.sub(r'[\s/\\［］\[\]（）()〔〕【】<>:"|?*、，。·]', '', p['record'].get('title') or '')
                                      or pathlib.Path(it['path']).name.split('-', 1)[1][:-5], 'Book')
    out = pathlib.Path(a.out); out.mkdir(parents=True, exist_ok=True)
    (out / 'plan.json').write_text(json.dumps({'stat': stat, 'hold': hold, 'plan': plan}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    (out / 'splits.json').write_text(json.dumps({'stat': stat, 'splits': [
        {'book': it['book'], 'virtual_removed': it['virtual_removed'],
         'parts': [{'id': p['id'], 'keep': p['keep'], 'series': p['series'], 'sources': p['sources'], 'path': p['path']} for p in it['parts']]}
        for it in plan]}, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    with open(out / '存疑.tsv', 'w', encoding='utf-8') as f:
        f.write('book\tlane\twhy\ttitle\n')
        for h in hold:
            f.write(f"{h['book']}\t{h['lane']}\t{h['why']}\t{h['title']}\n")
    print(dict(stat))
    if not a.apply:
        return
    for it in plan:
        if sha(ROOT / it['path']) != it['sha256']:
            die('原档已变：' + it['path'])
        if it.get('attach_only'):
            fp = ROOT / it['path']; b = json.loads(fp.read_text(encoding='utf-8'))
            have = {x['id'] for x in b.get('contained_in') or []}
            b['contained_in'] = (b.get('contained_in') or []) + [{'id': c} for c in dict.fromkeys(it['parts'][0]['cols']) if c not in have]
            rv = (b.get('revision') or '1.0.0').split('.'); b['revision'] = f'{int(rv[0]) + 1}.0.0'; b['revised_at'] = TODAY
            fp.write_text(jdump(b), encoding='utf-8'); continue
        for p in it['parts']:
            fp = ROOT / p['path']
            if not p['keep']:
                if fp.exists():
                    die('新档已存在：' + p['path'])
                fp.parent.mkdir(parents=True, exist_ok=True)
            fp.write_text(jdump(p['record']), encoding='utf-8')
    print('已写：原 Book', len(plan), '新 Book', sum(len(it['parts']) - 1 for it in plan if not it.get('attach_only')))


if __name__ == '__main__':
    main()
