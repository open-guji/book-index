#!/usr/bin/env python3
"""以記錄檔為真，回寫索引（協調者與各道合流撞衝突時用）。

**【已廢，2026-10-07 schema-v2 起】`index/` 由 `build/build_derived.py` 生成**（SCHEMA〈十四〉；
其欄位規則逐字承本檔與 bim `entry_extractor.py`）。本檔命令行已改為轉呼：
  python3 .claude/qa/reindex.py            → build_derived.py --check-only（只校驗，報告含 index 漂移）
  python3 .claude/qa/reindex.py --run      → build_derived.py --write-index（重生並寫回 index/）
`--membership` 之「檔不坐在其 id 所定分片路徑上」檢查（misplaced）仍在本檔、照跑。
下列函式（expect_*、shard、fix_membership…）留作參考與舊測試，不再是索引的生成者。

  python3 .claude/qa/reindex.py            # 乾跑，只列
  python3 .claude/qa/reindex.py --run
  python3 .claude/qa/reindex.py --run --membership   # 併補「增鍵／刪鍵／修 path」

三類不合（前二類 --run 即治，第三類須加 --membership，因其增刪鍵而非只改欄）：
  1. 欄漂移——索引之欄與記錄不符
  2. path 過時而檔尚在——檔名經整理（去標點空白）而索引未同步（坑 41(a)）
  3. 成員不合——有檔而索引無鍵（新入庫漏建索引）、索引有鍵而無檔（併條刪檔未清索引，坑 41(b)）
**記錄是真**：故「有檔無鍵」補建，「有鍵無檔」刪去。刪鍵前請先自行確認該記錄確係併入他條
（法見坑 41：自刪除提交之父取回原檔，以其著錄撞全庫活條），本函式只作機械對齊。
索引 works 分片之欄與記錄之對應：
  period/loss_status/title/subtype ← 同名頂層欄
  author ← authors[0].name   role ← authors[0].role
  dynasty ← 頂層 dynasty，無則 authors[0].dynasty（空字串視同無）
索引 entities 分片：primary_name/dynasty/birth_year/death_year/period ← 同名頂層欄
索引 collections（單一檔 `index/collections.json`，不比照 works/entities/books 分 16 片）：
  title/subtype 恆有，逐字面值；work_id/edition/additional_titles/measure_info ← 同名頂層欄；
  author/dynasty/role ← authors[0]；era ← dating.era；sort_year ← dating.year，
  無則 dating.year_range[0]；holder ← current_location.name；juan_count ← juan_count.number
  （0 略去，慣例同 books）；has_image/has_text ← resources 任一 types 含 image／text
  （字段口徑照 book_index_manager/entry_extractor.py，逆推自既有 84 條索引核對：0 誤差）。
  type 索引恆大寫 'Collection'，record 自身 type 欄是小寫 'collection'。
"""
import json, os, sys, glob, re
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__))); import jio
# 協調者裁（09-26，回 pit-jio與reindex的ROOT不同源）：ROOT 收為單一來源，
# 一律經 jio.ROOT 取用（每處用 jio.ROOT 直查，不在本檔另存副本——存副本則
# patch jio.ROOT 救不了這裡，坑同名）。jio.py 不動。
SH = '0123456789abcdef'
def shard(i):
    """索引分片之鍵：id 逐字 h=h*31+ord(c) 後取模 16。與 book-index-draft/scripts/b1/merge.py
    之 shard() 同源；已以全庫 30,740 個 entity 鍵驗過，無一不合。"""
    h = 0
    for c in i: h = ((h * 31) + ord(c)) & 0xFFFFFFFF
    return SH[h % 16]
def nz(v): return None if v in ('', None) else v
def expect_work(d):
    au = d.get('authors') or []; a0 = au[0] if au else {}
    return {'period': nz(d.get('period')), 'loss_status': nz(d.get('loss_status')), 'title': d.get('title'),
            'subtype': nz(d.get('subtype')), 'author': nz(a0.get('name')), 'role': nz(a0.get('role')),
            'dynasty': nz(d.get('dynasty')) if nz(d.get('dynasty')) is not None else nz(a0.get('dynasty'))}
def expect_ent(d):
    return {k: nz(d.get(k)) for k in ('primary_name', 'dynasty', 'birth_year', 'death_year', 'period')}
def expect_book(d):
    """併自先秦道 `附-reindex_books.py`，並按 SCHEMA.md「索引檔」一節訂正 sort_year：
    id/title/edition/work_id 恆有，其餘欄值為空即不寫。
    author/role/dynasty←authors[0]，era←dating.era，
    sort_year←dating.year，無則 dating.year_range[0]（附檔原只取 dating.year，
    而庫中年代多記於 year_range，逢之即誤把 sort_year 清空——見任務書 ask）。
    holder←current_location，juan_count←juan_count.number，
    has_image←resources 任一 types 含 image。"""
    au = (d.get('authors') or [{}])[0]; dt = d.get('dating') or {}
    cl = d.get('current_location') or {}; jc = d.get('juan_count') or {}
    img = any('image' in (r.get('types') or ([r['type']] if r.get('type') else []))
              for r in (d.get('resources') or []))
    yr = dt.get('year')
    if yr is None:
        yr_range = dt.get('year_range')
        if isinstance(yr_range, (list, tuple)) and yr_range:
            yr = yr_range[0]
    # title/work_id 全庫恆非空（結構性必填），逐字面值；edition 偶為空串，
    # 既有索引逢空即不寫該鍵（48/1310 抽驗），故與其餘選填欄一併 nz() 過濾。
    out = {'title': d.get('title'), 'work_id': d.get('work_id')}
    for k, v in (('edition', d.get('edition')), ('author', au.get('name')), ('era', dt.get('era')),
                 ('sort_year', yr), ('holder', cl.get('name')),
                 ('dynasty', au.get('dynasty')), ('role', au.get('role'))):
        out[k] = nz(v)
    # juan_count.number==0（「選印冊數待考」一類）既有 280 條索引樣本無一寫 0，
    # 顯係上游以真值判斷而非 is not None；從眾略去 0，免與既有慣例不一致。
    out['juan_count'] = jc.get('number') or None
    out['has_image'] = True if img else None
    return out
def expect_collection(d):
    """字段口徑逆推自既有 `index/collections.json` 84 條核對（0 誤差，見任務書）：
    title/subtype 全庫恆非空，逐字面值；work_id（僅部分 collection 有）與 edition/
    additional_titles/measure_info 一併走 nz() 過濾。author/dynasty/role←authors[0]，
    era←dating.era，sort_year 邏輯同 expect_book。holder←current_location.name。
    juan_count/has_image 邏輯同 expect_book；has_text 同 has_image，改認 'text'。"""
    au = (d.get('authors') or [{}])[0]; dt = d.get('dating') or {}
    cl = d.get('current_location') or {}; jc = d.get('juan_count') or {}
    def types_of(r): return r.get('types') or ([r['type']] if r.get('type') else [])
    img = any('image' in types_of(r) for r in (d.get('resources') or []))
    txt = any('text' in types_of(r) for r in (d.get('resources') or []))
    yr = dt.get('year')
    if yr is None:
        yr_range = dt.get('year_range')
        if isinstance(yr_range, (list, tuple)) and yr_range:
            yr = yr_range[0]
    out = {'title': d.get('title'), 'subtype': d.get('subtype')}
    for k, v in (('work_id', d.get('work_id')), ('edition', d.get('edition')), ('author', au.get('name')),
                 ('era', dt.get('era')), ('sort_year', yr), ('holder', cl.get('name')),
                 ('dynasty', au.get('dynasty')), ('role', au.get('role')),
                 ('additional_titles', d.get('additional_titles')), ('measure_info', d.get('measure_info'))):
        out[k] = nz(v)
    out['juan_count'] = jc.get('number') or None
    out['has_image'] = True if img else None
    out['has_text'] = True if txt else None
    return out
REC_RE = re.compile(r'^[0-9a-z]{10,13}-')
# 各族 (索引名, 記錄子目錄, 欄位函式, 是否 16 分片)；collections 是單一檔，非分片目錄。
FAMS = (('works', 'Work', expect_work, True), ('entities', 'Entity', expect_ent, True),
        ('books', 'Book', expect_book, True), ('collections', 'Collection', expect_collection, False))
def index_files(fam, sharded):
    """回傳某族現有之索引檔（分片族為目錄下 *.json 排序表；單一檔族為 [該檔]，
    即便該檔尚不存在——呼叫端自 jio.load 處自然報錯，不在此吞掉）。"""
    if sharded: return sorted(glob.glob(os.path.join(jio.ROOT, 'index', fam, '*.json')))
    return [os.path.join(jio.ROOT, 'index', f'{fam}.json')]
def scan_files():
    """一次建全庫 id→路徑表（勿逐 id glob，九萬條會慢到不可用）。
    **用遞迴 glob 而非固定四層**：檔名一改，人手誤置深淺一層者有之
    （2026-09-06 `d59f6eq7hnnl`《紫霞洞琴譜》正題改檔名時落在 `Work/n/l/` 而非
    `Work/n/n/l/`），固定層數之 glob 掃不到，membership 遂補不了鍵，全庫閘因之而紅（坑 50）。"""
    byid = {}
    for sub in ('Work', 'Entity', 'Book', 'Collection'):
        for f in glob.glob(os.path.join(jio.ROOT, sub, '**', '*.json'), recursive=True):
            b = os.path.basename(f)
            if not REC_RE.match(b): continue          # collated_edition 之屬不是記錄檔
            byid[b.split('-', 1)[0]] = os.path.relpath(f, jio.ROOT)
    return byid

def misplaced():
    """記錄檔是否坐在其 id 末三字所定之分片路徑上。回傳 [(現路徑, 應在)]。"""
    out = []
    for sub in ('Work', 'Entity', 'Book', 'Collection'):
        for f in glob.glob(os.path.join(jio.ROOT, sub, '**', '*.json'), recursive=True):
            b = os.path.basename(f)
            if not REC_RE.match(b): continue
            wid = b.split('-', 1)[0]
            want = os.path.join(sub, *list(wid[-3:]))
            got = os.path.dirname(os.path.relpath(f, jio.ROOT))
            if got != want: out.append((os.path.relpath(f, jio.ROOT), want))
    return out

def fix_membership(run):
    """對齊索引之成員與 path（坑 41）。回傳 (補建, 刪鍵, 修path) 三數。"""
    byid = scan_files(); add = drop = repath = 0
    for fam, sub, exp, sharded in FAMS:
        seen = set()
        shards = index_files(fam, sharded)
        for f in shards:
            if not os.path.exists(f): continue        # 單一檔族、庫中尚未建檔（今無此況，留守）
            rel = os.path.relpath(f, jio.ROOT); idx, fmt = jio.load(rel); ch = False
            for k in list(idx):
                real = byid.get(k)
                if real is None:
                    print(f'[{fam}] 刪鍵（索引有而無檔）{k} {idx[k].get("title") or idx[k].get("primary_name")}')
                    del idx[k]; drop += 1; ch = True; continue
                seen.add(k)
                if idx[k].get('path') != real:
                    print(f'[{fam}] 修 path {k}: {idx[k].get("path")} -> {real}')
                    idx[k]['path'] = real; repath += 1; ch = True
            if ch and run: jio.save(rel, idx, fmt)
        # 有檔而索引無鍵者：分片族按 id 末字歸片補建，單一檔族直接併入該檔
        missing = [k for k, p in byid.items() if p.startswith(sub + os.sep) and k not in seen]
        if not missing: continue
        # Book／Collection 索引之 type 恆大寫（附-reindex_books.py 舊例併沿用於 collection），
        # record 自身 type 欄是小寫，不可直取。
        def mktype(d): return sub if sub in ('Book', 'Collection') else d.get('type', fam[:-1])
        if sharded:
            byshard = {}
            for k in missing: byshard.setdefault(shard(k), []).append(k)
            for sh, ks in byshard.items():
                rel = os.path.join('index', fam, f'{sh}.json')
                if not os.path.exists(os.path.join(jio.ROOT, rel)):
                    print(f'[{fam}] 無分片 {rel}，{len(ks)} 鍵未補', file=sys.stderr); continue
                idx, fmt = jio.load(rel)
                for k in ks:
                    d = json.load(open(os.path.join(jio.ROOT, byid[k])))
                    ie = {'id': k, 'type': mktype(d), 'path': byid[k]}
                    ie.update({a: b for a, b in exp(d).items() if b is not None})
                    idx[k] = ie; add += 1
                    print(f'[{fam}] 補鍵（有檔而索引無）{k} {ie.get("title") or ie.get("primary_name")}')
                if run: jio.save(rel, idx, fmt)
        else:
            rel = os.path.join('index', f'{fam}.json')
            idx, fmt = jio.load(rel)
            for k in missing:
                d = json.load(open(os.path.join(jio.ROOT, byid[k])))
                ie = {'id': k, 'type': mktype(d), 'path': byid[k]}
                ie.update({a: b for a, b in exp(d).items() if b is not None})
                idx[k] = ie; add += 1
                print(f'[{fam}] 補鍵（有檔而索引無）{k} {ie.get("title") or ie.get("primary_name")}')
            if run: jio.save(rel, idx, fmt)
    return add, drop, repath

def main():
    """schema-v2：轉呼 build_derived.py（見文首）。舊的逐欄回寫見 legacy_main()。"""
    import subprocess
    root = jio.ROOT
    cmd = [sys.executable, os.path.join(root, 'build', 'build_derived.py'), '--root', root]
    cmd += ['--write-index'] if '--run' in sys.argv else ['--check-only']
    print('reindex.py 已廢：index/ 由 build 生成。轉呼：' + ' '.join(cmd), file=sys.stderr)
    if '--membership' in sys.argv:
        mp = misplaced()
        if mp:
            print(f'有 {len(mp)} 檔不坐在其 id 所定之分片路徑上（坑 50，須人手移動）：')
            for f, want in mp[:10]: print(f'  {f}  →應在 {want}/')
    return subprocess.call(cmd)


def legacy_main():
    run = '--run' in sys.argv; n = 0
    if '--membership' in sys.argv:
        a, d_, r = fix_membership(run)
        print(('已' if run else '待') + f'補鍵 {a}、刪鍵 {d_}、修 path {r}')
        mp = misplaced()
        if mp:
            print(f'另有 {len(mp)} 檔不坐在其 id 所定之分片路徑上（坑 50，須人手移動）：')
            for f, want in mp[:10]: print(f'  {f}  →應在 {want}/')
    for fam, _sub, exp, sharded in FAMS:
        for f in index_files(fam, sharded):
            if not os.path.exists(f): continue
            rel = os.path.relpath(f, jio.ROOT); idx, fmt = jio.load(rel); ch = False
            for k, ie in idx.items():
                p = os.path.join(jio.ROOT, ie['path'])
                if not os.path.exists(p): continue
                want = exp(json.load(open(p)))
                for fld, v in want.items():
                    if nz(ie.get(fld)) != v:
                        n += 1; print(f'[{fam}] {k} {fld}: {ie.get(fld)!r} -> {v!r}')
                        if v is None: ie.pop(fld, None)
                        else: ie[fld] = v
                        ch = True
            if ch and run: jio.save(rel, idx, fmt)
    print(('回寫' if run else '待回寫'), n)
if __name__ == '__main__': sys.exit(main())
