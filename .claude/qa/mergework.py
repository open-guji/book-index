#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""併條，並把善後七件一次辦完。

**所以立此**：坑 41 說善後三件、坑 61 補第四、坑 64 第五，「每次以為數全了就又冒出一處」。
逐次手辦必有遺漏，故把善後寫成一支，由 `backrefs.py` 那張「誰指著我」之表驅動。

    python3 .claude/qa/mergework.py --keeper <id> --drop <id>[,<id>...] \
        --rule <判準> --why <所以然> [--apply]

**不加 `--apply` 即為乾跑**：只印逐欄之 diff 與將要動的每一處，不寫任何檔。
坑 67 之戒——「做去重之前，先把兩個重複項並排逐欄 diff 一遍」——故乾跑是預設，
且 diff 印的是**整節所有欄位**，不是我挑的那幾欄。

善後七件：
  1 著錄併入 keeper（indexed_by，**整節為鍵**去重，不取子集——坑 67）
  2 index/works 刪被併者之項（jio.drop_index）
  3 Entity.works 反邊改指 keeper（並保證 keeper 之 authors 帶該 entity_id，否則 verify 報單向邊）
  4 他條之 Work.related_works 改指（id／work_id 二形；跨 Work／Collection 二 id 空間——坑 61）
  5 Collection.contained_works 改指（verify.py 不驗此處，斷了無人知）
  6 Work.books 併入 keeper
  7 keeper 之 `merged_in` **填欄位**，不只寫散文（坑 64：141 個被併 id 只 61 個填了）
"""
import json, os, sys, glob, argparse, datetime, collections

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import jio, backrefs


def wpath(wid):
    for p in glob.glob(os.path.join(ROOT, 'Work/*/*/*/%s-*.json' % wid)):
        return p
    return None


def rel(p):
    return os.path.relpath(p, ROOT)


def diff_fields(keeper, drops):
    """逐欄並排。坑 67：印所有欄位之並集，不挑。"""
    keys = set(keeper)
    for d in drops:
        keys |= set(d)
    out = []
    for k in sorted(keys):
        vals = [keeper.get(k)] + [d.get(k) for d in drops]
        same = all(json.dumps(v, ensure_ascii=False, sort_keys=True) ==
                   json.dumps(vals[0], ensure_ascii=False, sort_keys=True) for v in vals)
        mark = '  ' if same else '**'
        out.append('%s %-18s %s' % (mark, k, ' | '.join(
            json.dumps(v, ensure_ascii=False)[:150] for v in vals)))
    return '\n'.join(out)


def node_key(n):
    """整節為鍵——所有欄位，不取子集（坑 67：我的鍵取三欄而記錄有八欄，
    沒取的五欄裡恰好有一欄承載全部區別——續修四庫之 volume 冊次）。"""
    return json.dumps(n, ensure_ascii=False, sort_keys=True)


def main():
    ap = argparse.ArgumentParser(description='併條並辦善後七件')
    ap.add_argument('--keeper', required=True)
    ap.add_argument('--drop', required=True, help='逗號分隔')
    ap.add_argument('--rule', required=True, help='判準——第一等公民，無 rule 則日後無從整批翻案')
    ap.add_argument('--why', required=True)
    ap.add_argument('--by', default='lane-B')
    ap.add_argument('--round', type=int, default=0)
    ap.add_argument('--drop-entity-ref', default='', help=
        '逗號分隔之 entity id：其指向被併條之 works 項**撤去**而非改指 keeper。'
        '用於「該 entity 之繫本身就是這批入庫誤加的」——改指會把誤繫轉嫁給 keeper，'
        '且 keeper 之 authors 不含它，必生單向邊。撤去即回到入庫前之狀。')
    ap.add_argument('--apply', action='store_true', help='真寫；不加即乾跑')
    a = ap.parse_args()

    drops = [x for x in a.drop.split(',') if x]
    kp = wpath(a.keeper)
    if not kp:
        raise SystemExit('keeper 檔不存在：%s' % a.keeper)
    keeper, kfmt = jio.load(rel(kp))
    dps = []
    for d in drops:
        p = wpath(d)
        if not p:
            raise SystemExit('被併者檔不存在：%s（先查坑 64：曾建而後刪 vs 從未建出）' % d)
        dd, dfmt = jio.load(rel(p))
        dps.append((d, p, dd, dfmt))

    print('== 逐欄 diff（keeper | %s）==' % ' | '.join(drops))
    print(diff_fields(keeper, [x[2] for x in dps]))

    back = backrefs.scan()
    plan = collections.defaultdict(list)

    # 1 著錄
    have = {node_key(n) for n in (keeper.get('indexed_by') or [])}
    add_nodes = []
    for d, p, dd, _ in dps:
        for n in (dd.get('indexed_by') or []):
            if node_key(n) not in have:
                have.add(node_key(n)); add_nodes.append((d, n))
            else:
                plan['著錄·整節全同故不重複移'].append((d, n.get('source')))
    for d, n in add_nodes:
        plan['著錄移入 keeper'].append((d, n.get('source'), n.get('title_info')))

    # 6 books
    kb = list(keeper.get('books') or [])
    for d, p, dd, _ in dps:
        for b in (dd.get('books') or []):
            if b not in kb:
                kb.append(b); plan['Work.books 併入'].append((d, b))

    # 3/4/5 反邊
    ent_fix, rw_fix, cw_fix = [], [], []
    for d, p, dd, _ in dps:
        for where, src, det in back.get(d, []):
            if where == 'Entity.works':
                ent_fix.append((src, d))
            elif where == 'Work.related_works':
                rw_fix.append((src, d)); plan['Work.related_works 改指'].append((src, d))
            elif where == 'Collection.contained_works':
                cw_fix.append((src, d)); plan['Collection.contained_works 改指'].append((src, d))
            elif where in ('index/works',):
                plan['index/works 刪項'].append((d,))
            elif where == 'Work.merged_in':
                plan['**他條之 merged_in 指著被併者——須人看**'].append((src, d))

    # keeper 之 authors 須帶那些 entity_id，否則 verify 報單向邊
    drop_eref = {x for x in a.drop_entity_ref.split(',') if x}
    ent_fix = [(e, d) for e, d in ent_fix if e not in drop_eref]
    for e, d in ent_fix:
        plan['Entity.works 改指'].append((e, d))
    kent = {x.get('entity_id') for x in (keeper.get('authors') or []) if x.get('entity_id')}
    need_ent = {e for e, _ in ent_fix if e not in kent}
    for e in sorted(drop_eref):
        plan['Entity.works 撤項（不改指）'].append((e,))
    for e in sorted(need_ent):
        plan['**keeper authors 缺此 entity_id（單向邊）——須人看**'].append((e,))

    # description 之陳述併後可能失實（「本書惟某志著錄，別無他證」）——併入新源即翻該句
    dtxt = ((keeper.get('description') or {}).get('text') or '') if isinstance(keeper.get('description'), dict) else ''
    if any(w in dtxt for w in ('別無他證', '一志著錄', '惟《')):
        plan['**keeper description 有「別無他證／惟某志著錄」之語，併入新源後即失實——須人改**'].append((a.keeper,))

    print('\n== 將動之處 ==')
    if not plan:
        print('   （無）')
    for k in sorted(plan):
        print('  %s  ×%d' % (k, len(plan[k])))
        for it in plan[k][:12]:
            print('      %s' % (it,))

    if not a.apply:
        print('\n[乾跑] 未寫任何檔。覆核無誤後加 --apply。')
        return

    if need_ent:
        raise SystemExit('拒絕：keeper 之 authors 不含 %s，逕併必生單向邊。'
                         '先在 keeper 補 entity_id，或先併 entity。' % sorted(need_ent))

    now = datetime.datetime.utcnow().replace(microsecond=0).isoformat() + 'Z'
    # 1 著錄
    keeper.setdefault('indexed_by', []).extend([n for _, n in add_nodes])
    # 6 books
    if kb:
        keeper['books'] = kb
    # additional_titles：保住被併者之題（異體字之異，正是查重失效之由——坑 47）
    at = list(keeper.get('additional_titles') or [])
    for d, p, dd, _ in dps:
        t = dd.get('title')
        if t and t != keeper.get('title') and t not in at:
            at.append(t)
    if at:
        keeper['additional_titles'] = at
    # 7 merged_in（欄位，非散文）
    mi = list(keeper.get('merged_in') or [])
    for d, p, dd, _ in dps:
        mi.append({'id': d, 'title': dd.get('title'), 'at': now,
                   'by': a.by, 'rule': a.rule, 'why': a.why})
    keeper['merged_in'] = mi
    jio.addnote(keeper, '%s %s 併條（rule=%s）：併 %s 入本條。%s' % (
        now[:10], a.by, a.rule, '、'.join('%s《%s》' % (d, dd.get('title')) for d, _, dd, _ in dps), a.why))
    jio.save(rel(kp), keeper, kfmt)

    # 3b 撤項：該繫本身是誤加，撤之即回入庫前之狀
    for e in sorted(drop_eref):
        for p in glob.glob(os.path.join(ROOT, 'Entity/*/*/*/%s-*.json' % e)):
            ed, efmt = jio.load(rel(p))
            gone = [w for w in (ed.get('works') or []) if w.get('work_id') in drops]
            ed['works'] = [w for w in (ed.get('works') or []) if w.get('work_id') not in drops]
            jio.addnote(ed, '%s %s 併條善後：所繫 %s 已併入 %s，而本 entity 之繫係該批入庫誤加，'
                            '今撤其項而不改指（改指即把誤繫轉嫁 keeper）。撤去 %d 項。'
                        % (now[:10], a.by, '、'.join(w.get('work_id') for w in gone), a.keeper, len(gone)))
            jio.save(rel(p), ed, efmt)

    # 3 Entity.works
    for e, d in ent_fix:
        for p in glob.glob(os.path.join(ROOT, 'Entity/*/*/*/%s-*.json' % e)):
            ed, efmt = jio.load(rel(p))
            ws, seen, out = ed.get('works') or [], set(), []
            for w in ws:
                wid = a.keeper if w.get('work_id') == d else w.get('work_id')
                w = dict(w, work_id=wid)
                if wid in seen:
                    continue
                seen.add(wid); out.append(w)
            ed['works'] = out
            jio.addnote(ed, '%s %s 併條善後：所繫 %s 已併入 %s，反邊改指。' % (now[:10], a.by, d, a.keeper))
            jio.save(rel(p), ed, efmt)
    # 4 Work.related_works
    for src, d in rw_fix:
        p = wpath(src)
        sd, sfmt = jio.load(rel(p))
        seen, out = set(), []
        for r in (sd.get('related_works') or []):
            k = 'id' if 'id' in r else 'work_id'
            if r.get(k) == d:
                r = dict(r, **{k: a.keeper})
            sig = (r.get(k), r.get('relation'))
            if sig in seen:
                continue
            seen.add(sig); out.append(r)
        sd['related_works'] = out
        jio.addnote(sd, '%s %s 併條善後：所關聯之 %s 已併入 %s，改指。' % (now[:10], a.by, d, a.keeper))
        jio.save(rel(p), sd, sfmt)
    # 5 Collection.contained_works
    for src, d in cw_fix:
        for p in glob.glob(os.path.join(ROOT, 'Collection/*/*/*/%s-*.json' % src)):
            cd, cfmt = jio.load(rel(p))
            seen, out = set(), []
            for c in (cd.get('contained_works') or []):
                k = 'id' if 'id' in c else 'work_id'
                if c.get(k) == d:
                    c = dict(c, **{k: a.keeper})
                if c.get(k) in seen:
                    continue
                seen.add(c.get(k)); out.append(c)
            cd['contained_works'] = out
            jio.addnote(cd, '%s %s 併條善後：子目 %s 已併入 %s，改指。' % (now[:10], a.by, d, a.keeper))
            jio.save(rel(p), cd, cfmt)
    # 2 索引項＋刪檔
    for d, p, dd, _ in dps:
        jio.drop_index('works', d)
        os.remove(p)
    print('\n已併：%s <- %s' % (a.keeper, ','.join(drops)))
    print('善後：著錄 %d 節、Entity 反邊 %d、related_works %d、contained_works %d、索引項 %d、刪檔 %d'
          % (len(add_nodes), len(ent_fix), len(rw_fix), len(cw_fix), len(dps), len(dps)))


if __name__ == '__main__':
    main()
