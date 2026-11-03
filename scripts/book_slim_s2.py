#!/usr/bin/env python3
"""Book 去空值与重复（schema 审查 S2 报告 §5.1 A／E／F，2026-11-03）。

只做三类机械清理，不改任何语义：
  A  provenance[]：call_number=="" / notes=="" / seals==[] 不写（institution、source 保留）
  E  edition=="" 不写；edition 与 edition_type 完全相同者也不写
  C  ai_note 中「…自動錄入；源記錄：<id>」行，且 <id> 恰為某 sources[].id 者刪該行（其余行照留；空了整體不寫）
  D  indexed_by[]（source=="中國古籍總目"）的 summary 不寫（title_info／source／source_bid 保留）
  U  顶层 updated_at 不写（S3-A6：不动 revision／revised_at，不 bump）
  S  值为 src_manual 的 source 键不写：location_history[]／current_location／juan_count／page_count／publication_info（S3-A7）
  M  current_location 并入 provenance 首项（institution＝name，description／起止年进 notes，source＝"current_location"），删 current_location
  T  顶层 section 复制进每个 contained_in[] 项后删顶层（无 contained_in 者保留顶层）
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
    # M
    cl = d.get('current_location')
    if isinstance(cl, dict) and isinstance(cl.get('name'), str) and cl['name']:
        notes = [x for x in (cl.get('description'), '、'.join(v for v in (cl.get('start_date'), cl.get('end_date')) if v) or None) if x]
        pv = d.get('provenance')
        if not isinstance(pv, list):
            pv = []
        hit = next((x for x in pv if isinstance(x, dict) and x.get('institution') == cl['name']), None)
        if hit is not None:
            pv.remove(hit)
            if notes and not hit.get('notes'):
                hit['notes'] = '；'.join(notes)
            pv.insert(0, hit); ch['M_merged_same'] += 1
        else:
            e = {'institution': cl['name']}
            if notes:
                e['notes'] = '；'.join(notes)
            e['source'] = 'current_location'
            pv.insert(0, e); ch['M_added'] += 1
        d['provenance'] = pv
        del d['current_location']
    elif isinstance(cl, dict) and not cl.get('name'):
        # 無機構名者（2 條）：說明併入 ai_note，不丟
        txt = '；'.join(x for x in (cl.get('description'),) if x)
        if txt:
            d['ai_note'] = (d['ai_note'] + '\n' if d.get('ai_note') else '') + '原 current_location 說明：' + txt
        del d['current_location']; ch['M_no_name'] += 1
    # T
    sec = d.get('section')
    ci = d.get('contained_in')
    if isinstance(sec, str) and sec and isinstance(ci, list) and ci and all(isinstance(x, dict) for x in ci):
        for x in ci:
            x.setdefault('section', sec)
        del d['section']; ch['T_section'] += 1
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
    # U
    if 'updated_at' in d:
        del d['updated_at']; ch['U_updated_at'] += 1
    # S
    for k in ('current_location', 'juan_count', 'page_count', 'publication_info'):
        o = d.get(k)
        if isinstance(o, dict) and o.get('source') == 'src_manual':
            del o['source']; ch['S_' + k] += 1
            if not o:
                del d[k]; ch['S_empty_' + k] += 1
    lh = d.get('location_history')
    if isinstance(lh, list):
        keep = []
        for it in lh:
            if isinstance(it, dict) and it.get('source') == 'src_manual':
                del it['source']; ch['S_location_history'] += 1
                if not it:
                    ch['S_empty_location_history_item'] += 1
                    continue
            keep.append(it)
        if keep != lh:
            if keep:
                d['location_history'] = keep
            else:
                del d['location_history']
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
