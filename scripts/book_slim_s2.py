#!/usr/bin/env python3
"""Book 去空值与重复（schema 审查 S2 报告 §5.1 A／E／F，2026-11-03）。

只做三类机械清理，不改任何语义：
  A  provenance[]：call_number=="" / notes=="" / seals==[] 不写（institution、source 保留）
  E  edition=="" 不写；edition 与 edition_type 完全相同者不写 edition（信息在 edition_type）
  C  ai_note 中「…自動錄入；源記錄：<id>」行，且 <id> 恰為某 sources[].id 者刪該行（其余行照留；空了整體不寫）
  D  indexed_by[]（source=="中國古籍總目"）的 summary 不寫（title_info／source／source_bid 保留）
  F  metadata.npm_item_id 与某 provenance[].call_number 相同者删去该键（metadata 空了整体不写）
幂等。默认只统计；--apply 才写。写盘格式与 bim 一致（indent=2、ensure_ascii=False）。
用法：python3 scripts/book_slim_s2.py [--root .] [--apply]
"""
import argparse, glob, json, os, re, collections

SIG = re.compile(r'^.*自動錄入；源記錄：([0-9a-z]{16})$')


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
    # C
    ai = d.get('ai_note')
    if isinstance(ai, str) and '自動錄入；源記錄：' in ai:
        ids = {x.get('id') for x in d.get('sources') or [] if isinstance(x, dict)}
        keep = []
        for ln in ai.split('\n'):
            m = SIG.match(ln)
            if m and m.group(1) in ids:
                ch['C_signature'] += 1
            else:
                keep.append(ln)
        if ch['C_signature']:
            new = '\n'.join(keep).strip('\n')
            if new:
                d['ai_note'] = new
            else:
                del d['ai_note']; ch['C_ai_note_empty'] += 1
    # D
    for e in d.get('indexed_by') or []:
        if isinstance(e, dict) and e.get('source') == '中國古籍總目' and 'summary' in e:
            del e['summary']; ch['D_summary'] += 1
    return ch


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--limit', type=int, default=0, help='只处理前 N 个有变化的文件（小样本）')
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
        if a.limit and files > a.limit:
            break
        if a.apply:
            nl = '\n' if raw.endswith('\n') else ''
            open(p, 'w', encoding='utf-8', newline='\n').write(json.dumps(d, ensure_ascii=False, indent=2) + nl)
    print(('已写 ' if a.apply else '将改 ') + f'{files} 个文件', dict(tot))


if __name__ == '__main__':
    main()
