#!/usr/bin/env python3
"""Book 去空值与重复（schema 审查 S2 报告 §5.1 A／E／F，2026-11-03）。

只做三类机械清理，不改任何语义：
  A  provenance[]：call_number=="" / notes=="" / seals==[] 不写（institution、source 保留）
  E  edition=="" 不写；edition 与 edition_type 完全相同者不写 edition（信息在 edition_type）
  F  metadata.npm_item_id 与某 provenance[].call_number 相同者删去该键（metadata 空了整体不写）
幂等。默认只统计；--apply 才写。写盘格式与 bim 一致（indent=2、ensure_ascii=False）。
用法：python3 scripts/book_slim_s2.py [--root .] [--apply]
"""
import argparse, glob, json, os, collections


def slim(d):
    ch = collections.Counter()
    pv = d.get('provenance')
    if isinstance(pv, list):
        for x in pv:
            if not isinstance(x, dict):
                continue
            if x.get('call_number') == '':
                del x['call_number']; ch['A_call_number'] += 1
            if x.get('notes') == '':
                del x['notes']; ch['A_notes'] += 1
            if x.get('seals') == []:
                del x['seals']; ch['A_seals'] += 1
    ed = d.get('edition')
    if ed == '':
        del d['edition']; ch['E_empty_edition'] += 1
    elif isinstance(ed, str) and ed == d.get('edition_type'):
        del d['edition']; ch['E_edition_eq_type'] += 1
    md = d.get('metadata')
    if isinstance(md, dict) and isinstance(md.get('npm_item_id'), str):
        cns = {x.get('call_number') for x in (pv or []) if isinstance(x, dict)}
        if md['npm_item_id'] in cns:
            del md['npm_item_id']; ch['F_npm_item_id'] += 1
            if not md:
                del d['metadata']; ch['F_metadata_empty'] += 1
    return ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--apply', action='store_true')
    a = ap.parse_args()
    tot = collections.Counter(); files = 0
    for p in glob.iglob(os.path.join(a.root, 'Book', '*', '*', '*', '*.json')):
        raw = open(p, encoding='utf-8').read()
        d = json.loads(raw)
        if d.get('merged_into'):
            continue
        ch = slim(d)
        if not ch:
            continue
        files += 1; tot.update(ch)
        if a.apply:
            nl = '\n' if raw.endswith('\n') else ''
            open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(d, ensure_ascii=False, indent=2) + nl)
    print(('已写 ' if a.apply else '将改 ') + f'{files} 个文件', dict(tot))


if __name__ == '__main__':
    main()
