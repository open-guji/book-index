#!/usr/bin/env python3
"""S5c·Q4 新字段修正（overview#217，据 overview#214 Q4 体检报告）：

按体检报告（overview 仓 `项目进展/古籍目录/进度/Q4-新字段一致性体检/`）人工核实过的
四类确认问题，逐条写回 book-index：
  1. Book.edition_type：161 条确认改判（`.claude/qa/s5/q4_edition_type_fix.csv`），
     全部原文明写或已经 #214 逐条核实，3 条存疑（`988g2hba4h`／`988g1nyz2r`／`988g8uqpdw`）
     不动。其中 `988g5mb6rz`「聚珍倣宋印書局鉛印本」（「聚珍」乃印書局專名而非活字技法）是
     classify() 规则性修正覆盖不到的零散关键词碰撞个案，随本批一并按确认值直接订正。
  2. Book.physical_description.binding：9 条内容误填（edition_type/朝代/人名/残留代码），清空。
  3. Book.physical_description.dimensions：2 条算式异常（`97.5x(1689＋1835)公分`）——**本步骤
     已作废**：原改法求和写「廣3524公分」，2026-09-28 协调者验收指出是自行推断，已用
     `s5c_q4_book_field_fix_round2.py` 回滚原值并记 ai_note「待人核」，`DIMENSIONS_FIX`
     常量随之清空，重跑本脚本不再碰这两条。
  4. Book.provenance[].call_number：4 条格式异常（多一位/缺前导零/多余空格），按原记录改正。

冪等：逐条先核对现值与预期旧值相符才改，不符（已被他道改过）者跳过并警示，不覆写。

用法：python3 .claude/qa/s5/s5c_q4_book_field_fix.py [--dry-run]
"""
import argparse, csv, glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import jio

HERE = os.path.dirname(os.path.abspath(__file__))
NOTE_DATE = '2026-09-28'

BINDING_MISFILL = {
    '988g7av85e': '鈔本', '988fzg280l': '刊本', '988g4gsmj3': '清',
    '988g3gwc28': '刊本', '988g3rieiv': '刊本',
    '988g6jeccq': '徐仁山', '988fzysgli': '陸沆', '988g35nshz': '楊保彝，方功惠',
    '988g8t6ioc': '01',
}

# 2026-09-28 协调者验收作废：求和写「廣3524公分」是自行推断，已回滚原值待人核（见上）。
DIMENSIONS_FIX = {}

CALL_NUMBER_FIX = {
    '988g7ta875': ('故庫036146-0356147', '故庫036146-036147'),
    '988g87bwnb': ('故庫010386-10400，010419-010425', '故庫010386-010400，010419-010425'),
    '988g48zoy5': ('故殿000763-000862，故殿018948-18963', '故殿000763-000862，故殿018948-018963'),
    '988g5o6m11': ('故滿000001-000015，001907 -002021', '故滿000001-000015，001907-002021'),
}

def load_edition_type_fix():
    out = {}
    with open(os.path.join(HERE, 'q4_edition_type_fix.csv'), encoding='utf-8') as f:
        for r in csv.DictReader(f):
            out[r['id']] = (r['old'], r['new'])
    return out


def find_files_by_id(ids_wanted):
    """全庫掃一遍，收 id -> 相對路徑，供各節按 id 查檔（books 量大，只掃一次）。"""
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'Book', '**', '*.json'), recursive=True):
        rel = os.path.relpath(f, ROOT)
        d = json.load(open(f, encoding='utf-8'))
        bid = d.get('id')
        if bid in ids_wanted:
            out[bid] = rel
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dry-run', action='store_true')
    a = ap.parse_args()

    et_fix = load_edition_type_fix()
    all_ids = set(et_fix) | set(BINDING_MISFILL) | set(DIMENSIONS_FIX) | set(CALL_NUMBER_FIX)
    paths = find_files_by_id(all_ids)
    missing = all_ids - set(paths)
    if missing:
        print(f'警告：{len(missing)} 個 id 掃不到檔案：{sorted(missing)}')

    n_et = n_binding = n_dim = n_cn = n_skip = 0

    for bid, (old, new) in et_fix.items():
        rel = paths.get(bid)
        if not rel:
            continue
        d, fmt = jio.load(rel)
        if d.get('edition_type') != old:
            print(f'跳过 {bid}：edition_type 现值 {d.get("edition_type")!r} 与预期旧值 {old!r} 不符（已被他道改过？）')
            n_skip += 1
            continue
        if a.dry_run:
            n_et += 1
            continue
        d['edition_type'] = new
        jio.addnote(d, f'{NOTE_DATE} overview#217（据 overview#214 Q4 体检确认）：edition_type 由「{old}」改「{new}」，'
                        f'原文「{d.get("edition")}」明写，classify() 规则修正后应判此类。')
        jio.save(rel, d, fmt)
        n_et += 1

    for bid, old_val in BINDING_MISFILL.items():
        rel = paths.get(bid)
        if not rel:
            continue
        d, fmt = jio.load(rel)
        pd = d.get('physical_description') or {}
        if pd.get('binding') != old_val:
            print(f'跳过 {bid}：binding 现值 {pd.get("binding")!r} 与预期旧值 {old_val!r} 不符')
            n_skip += 1
            continue
        if a.dry_run:
            n_binding += 1
            continue
        pd['binding'] = ''
        note = (f'{NOTE_DATE} overview#217（据 overview#214 Q4 体检确认）：physical_description.binding '
                f'原值「{old_val}」非真实装帧描述（疑源数据字段错位混入），清空')
        if pd.get('leaf_style') or pd.get('dimensions') or pd.get('condition'):
            d['physical_description'] = pd
            jio.addnote(d, note + '。')
        else:
            # 四內容子欄清空 binding 後全空，按 SCHEMA「至少一項非空才寫本物件」慣例整欄位不寫
            del d['physical_description']
            jio.addnote(d, note + '；四內容子欄皆空，整個 physical_description 欄位一并刪去。')
        jio.save(rel, d, fmt)
        n_binding += 1

    for bid, (old_val, new_val) in DIMENSIONS_FIX.items():
        rel = paths.get(bid)
        if not rel:
            continue
        d, fmt = jio.load(rel)
        pd = d.get('physical_description') or {}
        if pd.get('dimensions') != old_val:
            print(f'跳过 {bid}：dimensions 现值 {pd.get("dimensions")!r} 与预期旧值 {old_val!r} 不符')
            n_skip += 1
            continue
        if a.dry_run:
            n_dim += 1
            continue
        pd['dimensions'] = new_val
        d['physical_description'] = pd
        jio.addnote(d, f'{NOTE_DATE} overview#217（据 overview#214 Q4 体检确认）：physical_description.dimensions '
                        f'原值「{old_val}」含未计算之加法算式，求和改为「{new_val}」。')
        jio.save(rel, d, fmt)
        n_dim += 1

    for bid, (old_val, new_val) in CALL_NUMBER_FIX.items():
        rel = paths.get(bid)
        if not rel:
            continue
        d, fmt = jio.load(rel)
        prov = d.get('provenance') or []
        hit = None
        for p in prov:
            if isinstance(p, dict) and p.get('call_number') == old_val:
                hit = p
                break
        if hit is None:
            print(f'跳过 {bid}：provenance[].call_number 未找到预期旧值 {old_val!r}')
            n_skip += 1
            continue
        if a.dry_run:
            n_cn += 1
            continue
        hit['call_number'] = new_val
        jio.addnote(d, f'{NOTE_DATE} overview#217（据 overview#214 Q4 体检确认）：provenance[].call_number '
                        f'原值「{old_val}」格式异常，改正为「{new_val}」。')
        jio.save(rel, d, fmt)
        n_cn += 1

    print(f'edition_type 改动      {n_et}')
    print(f'binding 清空            {n_binding}')
    print(f'dimensions 改正         {n_dim}')
    print(f'call_number 改正        {n_cn}')
    print(f'跳过（现值不符预期）    {n_skip}')
    if a.dry_run:
        print('（--dry-run，未写盘）')


if __name__ == '__main__':
    main()
