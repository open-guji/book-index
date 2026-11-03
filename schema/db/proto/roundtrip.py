#!/usr/bin/env python3
"""D2 原型：JSON → 规范化表 → JSON，逐条比对，验证「还原门禁」。

  python3 schema/db/proto/roundtrip.py --dsn "host=/tmp/pgt port=5544 user=postgres dbname=gj" --type Collection

做法：拆表映射（MAPS）写明每个 JSON 键进哪一列或哪张明细表；类型对不上、或映射里没有的键，原样进该行的 extra。
extra 里另有两个记号：`_null`（显式写了 null 的键）、`_empty`（写了空容器 {} / [] 的键），还原时据此补回。
比对口径：解析后的对象相等（不比键序与缩进；键序由写出端按 schema 排）。
"""
import argparse, glob, json, os, sys
import psycopg
from psycopg.types.json import Jsonb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 拆表映射。flat：对象拆进主表列；kids：数组进明细表（每项一行，seq=位置）；jsonb：整块进 jsonb 列。
MAPS = {
    'Collection': {
        'table': 'collection', 'owner_type': 'C', 'fixed': {'type': 'collection'},
        'cols': {'id': 'id', 'subtype': 'subtype', 'title': 'title', 'edition': 'edition', 'work_id': 'work_id',
                 'measure_info': 'measure_info', 'ai_note': 'ai_note', 'schema_version': 'schema_version',
                 'revision': 'revision', 'revised_at': 'revised_at', 'updated_at': 'updated_at'},
        'flat': {
            'count': {'juan': 'count_juan', 'ce': 'count_ce', 'zhong': 'count_zhong', 'han': 'count_han', 'source': 'count_source'},
            'juan_count': {'number': 'juan_number', 'unit': 'juan_unit', 'description': 'juan_description', 'source': 'juan_source'},
            'publication_info': {'year': 'pub_year', 'year_iso': 'pub_year_iso', 'place': 'pub_place',
                                 'publisher': 'pub_publisher', 'details': 'pub_details'},
            'description': {'text': 'description_text'},
            'review': {'status': 'review_status'},
        },
        'jsonb': {'page_count': 'page_count', 'dating': 'dating', 'current_location': 'current_location'},
        'kids': {
            'authors': ('authorship', {'name': 'name', 'role': 'role', 'entity_id': 'entity_id', 'dynasty': 'dynasty',
                                       'dynasty_basis': 'dynasty_basis', 'name_basis': 'name_basis', 'role_basis': 'role_basis',
                                       'original_name': 'original_name', 'note': 'note', 'source': 'source'}),
            'indexed_by': ('index_entry', {'source': 'source', 'source_bid': 'source_bid', 'title_info': 'title_info',
                                           'summary': 'summary', 'section': 'section', 'note': 'note'}, {'kind': 'I'}),
            'sources': ('source_ref', {'id': 'sid', 'name': 'name', 'type': 'type', 'details': 'details',
                                       'position': 'position', 'version': 'version', 'processor_version': 'processor_version'}),
            'resources': ('resource', {'id': 'rid', 'name': 'name', 'short_name': 'short_name', 'url': 'url', 'types': 'types',
                                       'details': 'details', 'group': 'grp', 'group_role': 'group_role',
                                       'expected_volumes': 'expected_volumes', 'volumes': 'volumes', 'metadata': 'metadata'}),
            'contains': ('collection_content', {'type': 'type', 'title': 'title', 'scope': 'scope', 'note': 'note',
                                                'position': 'position', 'work_id': 'work_id', 'book_id': 'book_id',
                                                'collection_id': 'collection_id', 'related_work_id': 'related_work_id',
                                                'own_work_id': 'own_work_id', 'categorization': 'categorization'}),
            'contained_in': ('member_of', {'id': 'collection_id', 'volume_index': 'volume_index', 'group': 'grp',
                                           'details': 'details', 'section': 'section', 'sub_items': 'sub_items'},
                             {'member_type': 'C'}, 'member_id'),
            'measures': ('measure', {'number': 'number', 'unit': 'unit', 'note': 'note'}),
            'additional_titles': ('collection_title_alt', {'@': 'title'}),
            'related_collections': ('related_collection', {'@': 'dst'}, {}, 'src'),
            'merged_from': ('merge_event', {'@': 'other_id'}, {'kind': 'merged_from'}),
            'description.sources': ('description_source', {'@': 'source'}),
        },
    },
}


def coltypes(cur):
    cur.execute("SELECT table_name, column_name, data_type, udt_name FROM information_schema.columns WHERE table_schema='public'")
    t = {}
    for tab, col, dt, udt in cur.fetchall():
        t.setdefault(tab, {})[col] = udt if dt in ('USER-DEFINED', 'ARRAY') else dt
    return t


def fits(v, ty):
    """值能否无损放进该类型的列。"""
    if v is None:
        return False
    if ty in ('text', 'character'):
        return isinstance(v, str)
    if ty == 'integer':
        return isinstance(v, int) and not isinstance(v, bool)
    if ty == 'boolean':
        return isinstance(v, bool)
    if ty == 'date':
        return isinstance(v, str) and len(v) == 10 and v[4] == '-' and v[7] == '-'
    if ty == 'jsonb':
        return True
    if ty == '_text':
        return isinstance(v, list) and all(isinstance(x, str) for x in v)
    return isinstance(v, str)   # 枚举：值不在词表里时 INSERT 会报错，原型里先当文本


def shred(obj, keymap, types, extra):
    """按 keymap 把对象拆成 {列: 值}；装不下的进 extra。keymap 里 '@' 表示「项本身是标量」。"""
    row = {}
    if '@' in keymap and types[keymap['@']] == 'jsonb':
        row[keymap['@']] = Jsonb(obj)
        return row
    if not isinstance(obj, dict):
        col = keymap.get('@')
        if col and fits(obj, types[col]):
            row[col] = Jsonb(obj) if types[col] == 'jsonb' else obj
        else:
            extra['@'] = obj
        return row
    for k, v in obj.items():
        col = keymap.get(k)
        if v is None:
            extra.setdefault('_null', []).append(k)
        elif v in ({}, []):
            extra.setdefault('_empty', []).append([k, v])
        elif col and fits(v, types[col]):
            row[col] = Jsonb(v) if types[col] == 'jsonb' else v
        else:
            extra[k] = v
    return row


def load(cur, m, types, docs):
    tab, ot = m['table'], m['owner_type']
    for d in docs:
        extra, row, later = {}, {}, []
        for k, v in d.items():
            if k in m['fixed']:
                if v != m['fixed'][k]:
                    extra[k] = v
            elif v is None:
                extra.setdefault('_null', []).append(k)
            elif k in m['cols'] and fits(v, types[tab][m['cols'][k]]):
                row[m['cols'][k]] = v
            elif k in m['jsonb']:
                row[m['jsonb'][k]] = Jsonb(v)
            elif k in m['flat'] and isinstance(v, dict):
                sub = {}
                kids_here = {kk: vv for kk, vv in v.items() if '%s.%s' % (k, kk) in m['kids']}
                rest = {kk: vv for kk, vv in v.items() if kk not in kids_here}
                row.update(shred(rest, m['flat'][k], types[tab], sub))
                sub['_present'] = 1
                for kk, vv in kids_here.items():
                    if isinstance(vv, list) and vv:
                        later.append(('%s.%s' % (k, kk), vv))
                    else:
                        sub[kk] = vv
                extra[k] = sub
            elif k in m['kids'] and isinstance(v, list) and v:
                later.append((k, v))
            else:
                extra[k] = v
        row['repo'] = 'book-index'
        if extra:
            row['extra'] = Jsonb(extra)
        cols = list(row)
        cur.execute('INSERT INTO %s (%s) VALUES (%s)' % (tab, ','.join(cols), ','.join(['%s'] * len(cols))), [row[c] for c in cols])
        for k, v in later:
            put_kids(cur, m, types, k, d['id'], v)


def put_kids(cur, m, types, key, oid, items):
    spec = m['kids'][key]
    tab, keymap = spec[0], spec[1]
    fixed = spec[2] if len(spec) > 2 else {}
    owner_col = spec[3] if len(spec) > 3 else 'owner_id'
    tcols = types[tab]
    for i, it in enumerate(items):
        extra = {}
        row = shred(it, keymap, tcols, extra)
        row[owner_col] = oid
        if 'owner_type' in tcols:
            row['owner_type'] = m['owner_type']
        if 'seq' in tcols:
            row['seq'] = i
        row.update(fixed)
        if extra:
            if 'extra' not in tcols:
                raise SystemExit('%s 没有 extra 列，装不下：%s %s' % (tab, oid, extra))
            row['extra'] = Jsonb(extra)
        cols = list(row)
        cur.execute('INSERT INTO %s (%s) VALUES (%s)' % (tab, ','.join(cols), ','.join(['%s'] * len(cols))), [row[c] for c in cols])


def unshred(row, keymap, extra):
    if '@' in extra:
        return extra['@']
    if '@' in keymap:
        return row[keymap['@']]
    o = {}
    for k, col in keymap.items():
        if row.get(col) is not None:
            o[k] = row[col]
    for k in extra.get('_null', []):
        o[k] = None
    for k, v in extra.get('_empty', []):
        o[k] = v
    for k, v in extra.items():
        if k not in ('_null', '_empty', '_present'):
            o[k] = v
    return o


def restore(cur, m, oid):
    tab = m['table']
    cur.execute('SELECT * FROM %s WHERE id=%%s' % tab, [oid])
    names = [c.name for c in cur.description]
    row = dict(zip(names, cur.fetchone()))
    extra = row.get('extra') or {}
    d = dict(m['fixed'])
    for k, col in m['cols'].items():
        if row.get(col) is not None:
            v = row[col]
            d[k] = v.isoformat() if hasattr(v, 'isoformat') else v
    for k, col in m['jsonb'].items():
        if row.get(col) is not None:
            d[k] = row[col]
    for k, sub in m['flat'].items():
        if k in extra:
            d[k] = unshred(row, sub, extra[k])
    for key in m['kids']:
        items = get_kids(cur, m, key, oid)
        if not items:
            continue
        if '.' in key:
            a, b = key.split('.')
            d.setdefault(a, {})[b] = items
        else:
            d[key] = items
    for k in extra.get('_null', []):
        d[k] = None
    for k, v in extra.get('_empty', []):
        d[k] = v
    for k, v in extra.items():
        if k not in ('_null', '_empty') and k not in m['flat']:
            d[k] = v
    return d


def get_kids(cur, m, key, oid):
    spec = m['kids'][key]
    tab, keymap = spec[0], spec[1]
    fixed = spec[2] if len(spec) > 2 else {}
    owner_col = spec[3] if len(spec) > 3 else 'owner_id'
    where = ['%s=%%s' % owner_col] + ['%s=%%s' % k for k in fixed]
    cur.execute('SELECT * FROM %s WHERE %s ORDER BY seq' % (tab, ' AND '.join(where)), [oid] + list(fixed.values()))
    names = [c.name for c in cur.description]
    out = []
    for r in cur.fetchall():
        row = dict(zip(names, r))
        out.append(unshred(row, keymap, row.get('extra') or {}))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dsn', required=True)
    ap.add_argument('--type', default='Collection')
    a = ap.parse_args()
    m = MAPS[a.type]
    docs = []
    for p in sorted(glob.glob(os.path.join(ROOT, a.type, '**', '*.json'), recursive=True)):
        with open(p, encoding='utf-8') as f:
            docs.append(json.load(f))
    with psycopg.connect(a.dsn) as conn, conn.cursor() as cur:
        types = coltypes(cur)
        load(cur, m, types, docs)
        bad, used_extra = 0, 0
        for d in docs:
            r = restore(cur, m, d['id'])
            if r != d:
                bad += 1
                if bad <= 5:
                    diff = sorted(k for k in set(d) | set(r) if d.get(k) != r.get(k))
                    print('不一致', d['id'], diff, file=sys.stderr)
        cur.execute('SELECT count(*) FROM %s WHERE extra IS NOT NULL' % m['table'])
        used_extra = cur.fetchone()[0]
        print('%s：%d 条，还原不一致 %d；主表用到 extra 的 %d 条' % (a.type, len(docs), bad, used_extra))
        cur.execute("SELECT k, sk, count(*) FROM %s, jsonb_each(extra) e(k, v), jsonb_object_keys(CASE WHEN jsonb_typeof(v)='object' THEN v ELSE '{}' END) sk GROUP BY 1,2 ORDER BY 3 DESC" % m['table'])
        print('extra 子键：', cur.fetchall())
        conn.rollback()
    sys.exit(1 if bad else 0)


if __name__ == '__main__':
    main()
