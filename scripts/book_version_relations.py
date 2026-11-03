#!/usr/bin/env python3
"""第6组步3：Book 版本关系并入 base_edition / related_books。
  lineage.derived_from + dating.based_on → base_edition
  lineage.related_to + 旧 related_books(字符串) → related_books(对象)；related_to 里「用其書葉配補」→ base_edition 配補
  lineage.category → edition_type（能对上词表且 edition_type 空）或 ai_note
可重复运行；--apply 才写盘；--rollback tsv 写出被动文件的原值（path/key/json）。
冲突不覆盖，原值写入 ai_note，不丢信息。
"""
import argparse, collections, glob, json, os, sys

ETYPES = {'刻本', '抄本', '稿本', '活字本', '石印本', '油印本', '曬印本', '鉛印本', '影印本', '套印本', '拓本', '印刷本', '其他'}
BE_ORDER = ['role', 'relation', 'name', 'book_id', 'work_id', 'hypothetical_id', 'confidence', 'evidence', 'note', 'source']
ARTIFACT_ERAS = {'元', '三國'}  # 「光緒元年」「楊春元」被误切出的朝代


def note(d, line):
    d['ai_note'] = (d['ai_note'] + '\n' if d.get('ai_note') else '') + line


def j(x):
    return json.dumps(x, ensure_ascii=False)


def order(it):
    out = {k: it[k] for k in BE_ORDER if k in it}
    out.update({k: v for k, v in it.items() if k not in out})
    return out


def role_of(rel):
    return rel if rel in ('配補', '參校') else '底本'


def find(be, key, val):
    for it in be:
        if it.get(key) == val:
            return it
    return None


def merge_field(d, it, k, v, ch, tag):
    if v in (None, ''):
        return
    if k not in it:
        it[k] = v
    elif it[k] != v:
        note(d, f'原 {tag}.{k}：{v}（与 base_edition 同一来源项已有值「{it[k]}」不同，未覆盖）')
        ch['conflict'] += 1


def migrate(d, ch, rb):
    ln = d.get('lineage') if isinstance(d.get('lineage'), dict) else None
    dt = d.get('dating') if isinstance(d.get('dating'), dict) else None
    touched = False
    def save(key, val):
        rb.append((key, val))
    be = d.get('base_edition')
    be = be if isinstance(be, list) else None
    have_be = bool(be)
    be_new = [dict(x) for x in (be or [])]
    be_before = be

    # ---- derived_from
    if ln is not None and 'derived_from' in ln:
        df = ln['derived_from']
        save('lineage.derived_from', df)
        for x in df or []:
            ref, rt, rel = x.get('ref'), x.get('ref_type'), x.get('relation')
            key = 'hypothetical_id' if rt == 'hypothetical' else 'book_id'
            it = find(be_new, key, ref)
            if it is None:
                it = {'role': role_of(rel), 'source': 'lineage.derived_from', key: ref}
                be_new.append(it); ch['df_new_item'] += 1
            else:
                ch['df_merged_item'] += 1
                if rel in ('配補', '參校') and it.get('role') != rel:
                    note(d, f'原 lineage.derived_from 关系「{rel}」与 base_edition 角色「{it.get("role")}」不一致（{ref}），未改角色')
                    ch['conflict'] += 1
            merge_field(d, it, 'relation', rel, ch, 'lineage.derived_from')
            merge_field(d, it, 'confidence', x.get('confidence'), ch, 'lineage.derived_from')
            merge_field(d, it, 'evidence', x.get('evidence'), ch, 'lineage.derived_from')
        del ln['derived_from']; touched = True; ch['df_deleted'] += 1

    # ---- dating.based_on
    if dt is not None and 'based_on' in dt:
        bo = dt['based_on']
        save('dating.based_on', bo)
        era, reign, year, rel = bo.get('era') or '', bo.get('reign') or '', bo.get('year'), bo.get('relation') or ''
        extra = set(bo) - {'era', 'reign', 'year', 'relation'}
        arte = era in ARTIFACT_ERAS and not reign
        if not be_new:
            if arte:
                name = '底本未詳'
                note(d, f'原 dating.based_on：{j(bo)}（朝代欄「{era}」疑为「元年」等误切，未采入底本名）')
                ch['synth_artifact'] += 1
            else:
                name = era + reign + (f'{year}年' if year else '') + '本'
                ch['synth'] += 1
            it = {'role': '底本', 'name': name, 'source': 'dating.based_on'}
            if rel:
                it['relation'] = rel
            be_new.append(it)
        else:
            cand = [x for x in be_new if x.get('role') == '底本']
            if len(cand) == 1:
                it = cand[0]
                if rel:
                    if 'relation' not in it:
                        it['relation'] = rel; ch['bo_relation_set'] += 1
                    elif it['relation'] != rel:
                        note(d, f'原 dating.based_on：{j(bo)}（与 base_edition 底本项已有 relation「{it["relation"]}」不同，未覆盖）')
                        ch['conflict'] += 1
                names = ' '.join(x.get('name', '') for x in be_new)
                if era and not arte and era not in names:
                    note(d, f'原 dating.based_on：{j(bo)}（朝代未见于底本名）'); ch['bo_era_missing'] += 1
            else:
                note(d, f'原 dating.based_on：{j(bo)}（base_edition 底本项数≠1，未合并）'); ch['conflict'] += 1
            if extra:
                note(d, f'原 dating.based_on 额外字段：{j({k: bo[k] for k in extra})}')
        del dt['based_on']; touched = True; ch['bo_deleted'] += 1

    # ---- related_to / related_books
    rbooks = d.get('related_books')
    rt = ln.get('related_to') if ln is not None and 'related_to' in ln else None
    if ln is not None and 'related_to' in ln:
        save('lineage.related_to', rt)
    if 'related_books' in d:
        save('related_books', rbooks)
    if rt is not None or (isinstance(rbooks, list) and any(isinstance(x, str) for x in rbooks)) or rbooks == []:
        objs = []
        for x in rbooks or []:
            objs.append({'book_id': x} if isinstance(x, str) else dict(x))
        for x in rt or []:
            if 'ref' in x:  # 用其書葉配補…
                it = find(be_new, 'book_id', x['ref'])
                if it is None:
                    it = {'role': '配補', 'source': 'lineage.related_to', 'book_id': x['ref']}
                    be_new.append(it)
                merge_field(d, it, 'relation', x.get('relation'), ch, 'lineage.related_to')
                ch['rt_to_be'] += 1
                continue
            o = find(objs, 'book_id', x['book_id'])
            if o is None:
                o = {'book_id': x['book_id']}; objs.append(o); ch['rt_to_rb'] += 1
            else:
                ch['rt_merged_rb'] += 1
            for k in ('relation', 'confidence', 'evidence'):
                merge_field(d, o, k, x.get(k), ch, 'lineage.related_to')
            for k in set(x) - {'book_id', 'relation', 'confidence', 'evidence'}:
                note(d, f'原 lineage.related_to.{k}：{j(x[k])}')
        objs = [order_rb(o) for o in objs]
        if objs:
            d['related_books'] = objs
        else:
            d.pop('related_books', None); ch['rb_empty_dropped'] += 1
        if rt is not None:
            del ln['related_to']
        touched = True

    # ---- category
    if ln is not None and 'category' in ln:
        cat = ln['category']
        save('lineage.category', cat); save('edition_type', d.get('edition_type'))
        et = d.get('edition_type')
        if et == cat:
            ch['cat_same'] += 1
        elif cat in ETYPES and not et:
            d['edition_type'] = cat; ch['cat_to_edition_type'] += 1
        else:
            note(d, f'原 lineage.category：{cat}'); ch['cat_to_note'] += 1
        del ln['category']; touched = True

    if be_new != (be_before or []):
        d['base_edition'] = [order(x) for x in be_new]
        ch['be_changed'] += 1
    elif be_new and be_before is not None:
        d['base_edition'] = [order(x) for x in be_new]
    if ln is not None and not ln:
        del d['lineage']; ch['lineage_emptied'] += 1
    return touched


def order_rb(o):
    out = {k: o[k] for k in ('book_id', 'relation', 'confidence', 'evidence') if k in o}
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--root', default='.')
    ap.add_argument('--apply', action='store_true')
    ap.add_argument('--rollback')
    a = ap.parse_args()
    ch = collections.Counter(); rows = []
    for f in sorted(glob.glob(os.path.join(a.root, 'Book/*/*/*/*.json'))):
        raw = open(f, encoding='utf-8').read()
        d = json.loads(raw)
        ln = d.get('lineage') if isinstance(d.get('lineage'), dict) else {}
        dt = d.get('dating') if isinstance(d.get('dating'), dict) else {}
        if not (ln.keys() & {'derived_from', 'related_to', 'category'} or 'based_on' in dt or
                (isinstance(d.get('related_books'), list) and (not d['related_books'] or any(isinstance(x, str) for x in d['related_books'])))):
            continue
        before = {k: d.get(k) for k in ('base_edition', 'ai_note')}
        rb = []
        migrate(d, ch, rb)
        rel = os.path.relpath(f, a.root)
        for k, v in rb:
            rows.append((rel, k, v))
        rows.append((rel, 'base_edition', before['base_edition']))
        rows.append((rel, 'ai_note', before['ai_note']))
        ch['files'] += 1
        if a.apply:
            open(f, 'w', encoding='utf-8').write(json.dumps(d, indent=2, ensure_ascii=False) + '\n')
    if a.rollback:
        with open(a.rollback, 'w', encoding='utf-8') as fh:
            for p, k, v in rows:
                fh.write(f'{p}\t{k}\t{j(v)}\n')
    for k, v in sorted(ch.items()):
        print(k, v)


if __name__ == '__main__':
    main()
