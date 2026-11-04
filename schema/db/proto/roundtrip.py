#!/usr/bin/env python3
"""D2 原型：JSON → 规范化表 → JSON，逐条比对，验证「还原门禁」。

  python3 schema/db/proto/roundtrip.py --dsn "host=/tmp/pgt port=5544 user=postgres dbname=gj" --type Collection [--limit N]

做法：拆表映射（MAPS）写明每个 JSON 键进哪一列或哪张明细表；类型对不上、或映射里没有的键，原样进该行的 extra。
extra 里另有几个记号：`_null`（显式写了 null 的键）、`_empty`（写了空容器 {} / [] 的键）、
拆进主表列的对象记 `{对象名: {"_present": 1, …}}`，还原时据此补回。
比对口径：解析后的对象相等（不比键序与缩进；键序由写出端按 schema 排）。
灌库在一个事务里，跑完回滚，不留数据；加 --keep 则比对全过才提交。
"""
import argparse, collections, glob, json, os, sys, time
import psycopg
from psycopg.types.json import Jsonb

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))


def K(table, m, fixed=None, owner='owner_id', mode='list', dictkey=None, sub=None, parent=None):
    """明细映射。mode：list＝数组每项一行（seq＝位置）；one＝单值一行；dict＝对象每个键一行（dictkey 存键）。
    sub：项里的数组再拆一层（如 provenance[].seal_marks），parent 是子表里记上层位置的列。"""
    return {'table': table, 'map': m, 'fixed': fixed or {}, 'owner': owner, 'mode': mode, 'dictkey': dictkey,
            'sub': sub or {}, 'parent': parent}


AUTH = {'name': 'name', 'role': 'role', 'entity_id': 'entity_id', 'dynasty': 'dynasty', 'dynasty_basis': 'dynasty_basis',
        'name_basis': 'name_basis', 'role_basis': 'role_basis', 'original_name': 'original_name', 'note': 'note', 'source': 'source'}
IDX = {'source': 'source', 'source_bid': 'source_bid', 'title_info': 'title_info', 'summary': 'summary', 'section': 'section',
       'section_basis': 'section_basis', 'author_info': 'author_info', 'juan_count': 'juan_count', 'juan': 'juan',
       'volume': 'volume', 'page': 'page', 'edition': 'edition', 'catalog_no': 'catalog_no', 'note': 'note',
       'in_note_of': 'in_note_of', 'attested_status': 'attested_status', 'attested_status_raw': 'attested_status_raw',
       'attested_status_note': 'attested_status_note', 'misattached': 'misattached', 'misattached_note': 'misattached_note'}
SRC = {'id': 'sid', 'name': 'name', 'type': 'type', 'details': 'details', 'position': 'position', 'version': 'version',
       'processor_version': 'processor_version'}
RES = {'id': 'rid', 'name': 'name', 'short_name': 'short_name', 'url': 'url', 'types': 'types', 'details': 'details',
       'group': 'grp', 'group_role': 'group_role', 'root_type': 'root_type', 'color_mode': 'color_mode',
       'expected_volumes': 'expected_volumes', 'note': 'note', 'source_label': 'source_label', 'volumes': 'volumes',
       'metadata': 'metadata'}
MEMBER = {'id': 'collection_id', 'volume_index': 'volume_index', 'group': 'grp', 'details': 'details', 'section': 'section',
          'sub_items': 'sub_items'}
# 墓碑的 merged_into＋merged_basis 合成一行 merged_into 表（doc() 先合、restore 再拆）
TOMB = {'into': 'direct_into', 'rule': 'rule', 'at': 'at', 'by': 'by', 'why': 'why'}


def common_kids(ot):
    return {
        'authors': K('authorship', AUTH),
        'indexed_by': K('index_entry', IDX, {'kind': 'I'}),
        'emendated_by': K('index_entry', IDX, {'kind': 'E'}),
        'sources': K('source_ref', SRC),
        'resources': K('resource', RES),
        'resource_groups': K('resource_group', {'label': 'label', 'description': 'description'}, mode='dict', dictkey='key'),
        'contained_in': K('member_of', MEMBER, {'member_type': ot}, owner='member_id'),
        'measures': K('measure', {'number': 'number', 'unit': 'unit', 'note': 'note'}),
        'todo': K('record_todo', {'what': 'what', 'by': 'by', 'date': 'date'}),
        'merged_into': K('merged_into', TOMB, {'record_type': ot, 'src': 'tombstone'}, owner='dead_id', mode='one'),
        'description.sources': K('description_source', {'@': 'source'}),
    }


COMMON_COLS = {'id': 'id', 'title': 'title', 'ai_note': 'ai_note', 'schema_version': 'schema_version', 'revision': 'revision',
               'revised_at': 'revised_at', 'measure_info': 'measure_info'}
JUAN = {'number': 'juan_number', 'unit': 'juan_unit', 'description': 'juan_description', 'source': 'juan_source'}

MAPS = {
    'Collection': {
        'table': 'collection', 'owner_type': 'C', 'fixed': {'type': 'collection'},
        'cols': dict(COMMON_COLS, subtype='subtype', edition='edition', work_id='work_id'),
        'flat': {
            'count': {'juan': 'count_juan', 'ce': 'count_ce', 'zhong': 'count_zhong', 'han': 'count_han', 'source': 'count_source'},
            'juan_count': JUAN,
            'publication_info': {'year': 'pub_year', 'year_iso': 'pub_year_iso', 'place': 'pub_place',
                                 'publisher': 'pub_publisher', 'details': 'pub_details'},
            'description': {'text': 'description_text'},
            'review': {'status': 'review_status'},
        },
        'jsonb': {'page_count': 'page_count', 'dating': 'dating', 'current_location': 'current_location'},
        'kids': dict(common_kids('C'), **{
            'contains': K('collection_content', {'type': 'type', 'title': 'title', 'scope': 'scope', 'note': 'note',
                                                 'position': 'position', 'work_id': 'work_id', 'book_id': 'book_id',
                                                 'collection_id': 'collection_id', 'related_work_id': 'related_work_id',
                                                 'own_work_id': 'own_work_id', 'categorization': 'categorization'}),
            'additional_titles': K('collection_title_alt', {'@': 'title'}),
            'related_collections': K('related_collection', {'@': 'dst'}, owner='src'),
        }),
    },
    'Work': {
        'table': 'work', 'owner_type': 'W', 'fixed': {'type': 'work'},
        'cols': dict(COMMON_COLS, subtype='subtype', original_title='original_title', title_basis='title_basis',
                     dynasty='dynasty', dynasty_basis='dynasty_basis', period='period', period_basis='period_basis',
                     period_upper='period_upper', period_upper_basis='period_upper_basis', loss_status='loss_status',
                     loss_status_basis='loss_status_basis', loss_status_note='loss_status_note', authenticity='authenticity',
                     authenticity_basis='authenticity_basis', preferred_book='preferred_book'),
        'flat': {'juan_count': JUAN, 'description': {'text': 'description_text'}, 'review': {'status': 'review_status'}},
        'jsonb': {'title_emendation': 'title_emendation', 'version_graph': 'version_graph', 'collection_scale': 'collection_scale',
                  'publication_info': 'publication_info', 'appendix': 'appendix'},
        'kids': dict(common_kids('W'), **{
            'additional_titles': K('work_title_alt', {'@': 'title'}),
            'additional_works': K('work_additional', {'book_title': 'book_title', 'n_juan': 'n_juan'}),
            'related_works': K('work_relation', {'id': 'dst', 'relation': 'relation', 'note': 'note'}, owner='src'),
        }),
    },
    'Book': {
        'table': 'book', 'owner_type': 'B', 'fixed': {'type': 'book'},
        'cols': dict(COMMON_COLS, work_id='work_id', edition='edition', edition_type='edition_type', zhsy_id='zhsy_id'),
        'flat': {
            'juan_count': JUAN,
            'publication_info': {'year': 'pub_year', 'year_iso': 'pub_year_iso', 'place': 'pub_place',
                                 'publisher': 'pub_publisher', 'details': 'pub_details', 'source': 'pub_source'},
            'dating': {'certainty': 'dating_certainty', 'source': 'dating_source', 'basis': 'dating_basis', 'era': 'dating_era',
                       'reign': 'dating_reign', 'year': 'dating_year', 'year_range': 'dating_year_range',
                       'based_on': 'dating_based_on', 'later_repair': 'dating_later_repair'},
            'physical_description': {'leaf_style': 'physical_leaf_style', 'binding': 'physical_binding',
                                     'dimensions': 'physical_dimensions', 'condition': 'physical_condition',
                                     'source': 'physical_source'},
            'description': {'text': 'description_text'},
            'review': {'status': 'review_status'},
            'lineage': {},
        },
        'flatrest': {'lineage': 'lineage'},
        'jsonb': {'volume_count': 'volume_count', 'page_count': 'page_count', 'metadata': 'metadata', 'appendix': 'appendix'},
        'kids': dict(common_kids('B'), **{
            'additional_titles': K('book_title_alt', {'@': 'title'}),
            'provenance': K('book_provenance', {'institution': 'institution', 'call_number': 'call_number', 'notes': 'notes',
                                                'source': 'source', 'seals': 'seals'},
                            sub={'seal_marks': K('book_seal_mark', {'seal_id': 'seal_id', 'position': 'position', 'note': 'note',
                                                                    'source': 'source'}, parent='prov_seq')}),
            'base_edition': K('book_base_edition', {'role': 'role', 'name': 'name', 'source': 'source', 'book_id': 'book_id',
                                                    'note': 'note'}),
            'attached_texts': K('book_attached_text', {'book_title': 'book_title'}),
            'location_history': K('book_location_history', {'location': 'location', 'name': 'name', 'item_id': 'item_id',
                                                            'url': 'url', 'note': 'note', 'description': 'description',
                                                            'source': 'source', 'acckey': 'acckey'}),
            'related_books': K('related_book', {'@': 'dst'}, owner='src'),
            'lineage.derived_from': K('book_relation', {'ref': 'dst', 'relation': 'relation', 'confidence': 'confidence',
                                                        'evidence': 'evidence'}, {'kind': 'derived_from'}, owner='src'),
            'lineage.related_to': K('book_relation', {'ref': 'dst', 'relation': 'relation', 'confidence': 'confidence',
                                                      'evidence': 'evidence'}, {'kind': 'related_to'}, owner='src'),
        }),
    },
    'Entity': {
        'table': 'entity', 'owner_type': 'E', 'fixed': {'type': 'entity'},
        'cols': {'id': 'id', 'subtype': 'subtype', 'primary_name': 'primary_name', 'dynasty': 'dynasty',
                 'dynasty_basis': 'dynasty_basis', 'period': 'period', 'period_basis': 'period_basis', 'name_basis': 'name_basis',
                 'ai_note': 'ai_note', 'schema_version': 'schema_version', 'revision': 'revision', 'revised_at': 'revised_at',
                 'retired': 'retired', 'retired_reason': 'retired_reason'},
        'flat': {'description': {'text': 'description_text'}, 'review': {'status': 'review_status'}},
        'jsonb': {},
        'side': {
            'people': ('person', {'title_or_office': 'title_or_office', 'native_place': 'native_place',
                                  'native_place_basis': 'native_place_basis', 'native_place_entity_id': 'native_place_entity_id'},
                       {'external_ids_meta': {'cbdb_match': 'cbdb_match', 'cbdb_source': 'cbdb_source'}}),
            'collective': ('collective', {'collective_kind': 'collective_kind', 'institution_level': 'institution_level',
                                          'function': 'function', 'function_basis': 'function_basis'}, {}),
            'publisher': ('publisher', {'publisher_kind': 'publisher_kind', 'status': 'status'}, {}),
            'office': ('office', {'office_level': 'office_level', 'office_class': 'office_class', 'function': 'function',
                                  'function_basis': 'function_basis', 'base_office_id': 'base_office_id'},
                       {'rank': {'text': 'rank_text', 'basis': 'rank_basis'},
                        'qualifier': {'kind': 'qualifier_kind', 'name': 'qualifier_name', 'note': 'qualifier_note',
                                      'target': 'qualifier_target'}}),
            'place': ('place', {'concept_id': 'concept_id', 'place_level': 'place_level'},
                      {'modern': {'text': 'modern_text', 'relation': 'modern_relation', 'adcode': 'modern_adcode',
                                  'note': 'modern_note'}}),
            'seal': ('seal', {'seal_text': 'seal_text', 'seal_kind': 'seal_kind', 'seal_style': 'seal_style',
                              'seal_form': 'seal_form', 'usage_scope': 'usage_scope'}, {}),
            'reign': ('reign', {}, {'ruler': {'name': 'ruler_name', 'entity_id': 'ruler_entity_id'}}),
            'dynasty': ('dynasty', {}, {}),
        },
        'kids': {
            'alt_names': K('entity_alt_name', {'name': 'name', 'type': 'type', 'ambiguous': 'ambiguous', 'note': 'note'}),
            'external_ids': K('entity_external_id', {'@': 'value'}, mode='dict', dictkey='key'),
            'dates': K('entity_dates', {'birth': 'birth', 'death': 'death', 'floruit': ('floruit_start', 'floruit_end'),
                                        'start': 'start_year', 'end': 'end_year', 'basis': 'basis'}, mode='one'),
            'history': K('place_history', {'name': 'name', 'level': 'level', 'start': 'start_year', 'end': 'end_year',
                                           'note': 'note', 'parent_id': 'parent_id'},
                         sub={'dynasty_ids': K('place_history_dynasty', {'@': 'dynasty_id'}, parent='hseq')}),
            'images': K('entity_image', {'file': 'file', 'credit': 'credit', 'license': 'license', 'source_url': 'source_url',
                                         'note': 'note'}),
            'locations': K('entity_location', {'name': 'name', 'place_id': 'place_id', 'note': 'note'}),
            'appears_in': K('entity_appears_in', {'ref_type': 'ref_type', 'id': 'ref_id', 'position': 'position', 'note': 'note'}),
            'dynasty_ids': K('entity_relation', {'@': 'dst'}, {'rel': 'in_dynasty', 'src_key': 'dynasty_ids'}, owner='src'),
            'dynasty_id': K('entity_relation', {'@': 'dst'}, {'rel': 'in_dynasty', 'src_key': 'dynasty_id'}, owner='src', mode='one'),
            'parent_id': K('entity_relation', {'@': 'dst'}, {'rel': 'parent', 'src_key': 'parent_id'}, owner='src', mode='one'),
            'institution_ref': K('entity_relation', {'@': 'dst'}, {'rel': 'institution', 'src_key': 'institution_ref'},
                                 owner='src', mode='one'),
            'institution_ids': K('entity_relation', {'@': 'dst'}, {'rel': 'institution', 'src_key': 'institution_ids'}, owner='src'),
            'predecessors': K('entity_relation', {'id': 'dst', 'kind': 'kind', 'year': 'year', 'note': 'note'},
                              {'rel': 'predecessor', 'src_key': 'predecessors'}, owner='src'),
            'superiors': K('entity_relation', {'id': 'dst', 'start': 'start_year', 'end': 'end_year', 'note': 'note'},
                           {'rel': 'superior', 'src_key': 'superiors'}, owner='src'),
            'owner_ids': K('entity_relation', {'@': 'dst'}, {'rel': 'owner', 'src_key': 'owner_ids'}, owner='src'),
            'owners': K('entity_relation', {'id': 'dst', 'role': 'role', 'note': 'note'}, {'rel': 'owner', 'src_key': 'owners'},
                        owner='src'),
            'group_ids': K('entity_relation', {'@': 'dst'}, {'rel': 'in_group', 'src_key': 'group_ids'}, owner='src'),
            'relations': K('entity_relation', {'entity_id': 'dst', 'type': 'kind', 'basis': 'note', 'sources': 'sources'},
                           {'rel': 'person', 'src_key': 'relations'}, owner='src'),
            'todo': K('record_todo', {'what': 'what', 'by': 'by', 'date': 'date'}),
            'merged_into': K('merged_into', TOMB, {'record_type': 'E', 'src': 'tombstone'}, owner='dead_id', mode='one'),
            'description.sources': K('description_source', {'@': 'source'}),
        },
    },
}


def coltypes(cur):
    cur.execute("SELECT table_name, column_name, data_type, udt_name FROM information_schema.columns WHERE table_schema='public'")
    t = {}
    for tab, col, dt, udt in cur.fetchall():
        t.setdefault(tab, {})[col] = udt if dt in ('USER-DEFINED', 'ARRAY') else dt
    cur.execute("SELECT t.typname, e.enumlabel FROM pg_enum e JOIN pg_type t ON t.oid=e.enumtypid")
    enums = collections.defaultdict(set)
    for ty, lab in cur.fetchall():
        enums[ty].add(lab)
    return t, enums


def fits(v, ty, enums):
    """值能否无损放进该类型的列。"""
    if v is None:
        return False
    if ty in ('text', 'character'):
        return isinstance(v, str)
    if ty == 'integer':
        return isinstance(v, int) and not isinstance(v, bool) and -2**31 <= v < 2**31
    if ty == 'boolean':
        return isinstance(v, bool)
    if ty == 'date':
        return isinstance(v, str) and len(v) == 10 and v[4] == '-' and v[7] == '-'
    if ty == 'jsonb':
        return True
    if ty == '_text':
        return isinstance(v, list) and bool(v) and all(isinstance(x, str) for x in v)
    if ty == '_int4':
        return isinstance(v, list) and len(v) == 2 and all(isinstance(x, int) and not isinstance(x, bool) for x in v)
    if ty in enums:
        return isinstance(v, str) and v in enums[ty]
    return False


def val(v, ty):
    return Jsonb(v) if ty == 'jsonb' else v


def shred(obj, keymap, types, enums, extra):
    """按 keymap 把对象拆成 {列: 值}；装不下的进 extra。keymap 里 '@' 表示「项本身整个进这一列」。"""
    row = {}
    if '@' in keymap:
        col = keymap['@']
        if fits(obj, types[col], enums):
            row[col] = val(obj, types[col])
        else:
            extra['@'] = obj
        return row
    if not isinstance(obj, dict):
        extra['@'] = obj
        return row
    for k, v in obj.items():
        col = keymap.get(k)
        if v is None:
            extra.setdefault('_null', []).append(k)
        elif isinstance(v, (dict, list)) and not v:
            extra.setdefault('_empty', []).append([k, v])
        elif isinstance(col, tuple):
            if isinstance(v, list) and len(v) == len(col) and all(x is not None and fits(x, types[c], enums) for x, c in zip(v, col)):
                row.update(zip(col, v))
            else:
                extra[k] = v
        elif col and fits(v, types[col], enums):
            row[col] = val(v, types[col])
        else:
            extra[k] = v
    return row


class Loader:
    def __init__(self, m, types, enums):
        self.m, self.types, self.enums = m, types, enums
        self.rows = collections.defaultdict(list)   # table -> [row dict]

    def add(self, table, row):
        self.rows[table].append(row)

    def doc(self, d):
        m, tab = self.m, self.m['table']
        if isinstance(d.get('merged_into'), str) and isinstance(d.get('merged_basis', {}), dict):
            d = dict(d)
            d['merged_into'] = dict({'into': d.pop('merged_into')}, **(d.pop('merged_basis', None) or {}))
        tcols = self.types[tab]
        extra, row, later = {}, {}, []
        side = m.get('side', {}).get(d.get('subtype'))
        srow = {}
        for k, v in d.items():
            if side and v is not None and k in side[1] and fits(v, self.types[side[0]][side[1][k]], self.enums):
                srow[side[1][k]] = v
                continue
            if side and k in side[2] and isinstance(v, dict) and v:
                sub = {'_present': 1}
                srow.update(shred(v, side[2][k], self.types[side[0]], self.enums, sub))
                extra[k] = sub
                continue
            if k in m['fixed']:
                if v != m['fixed'][k]:
                    extra[k] = v
            elif v is None:
                extra.setdefault('_null', []).append(k)
            elif k in m['cols'] and fits(v, tcols[m['cols'][k]], self.enums):
                row[m['cols'][k]] = v
            elif k in m['jsonb']:
                row[m['jsonb'][k]] = Jsonb(v)
            elif k in m['flat'] and isinstance(v, dict):
                sub = {'_present': 1}
                rest = {}
                for kk, vv in v.items():
                    key = '%s.%s' % (k, kk)
                    if key in m['kids'] and isinstance(vv, list) and vv:
                        later.append((key, vv))
                    else:
                        rest[kk] = vv
                row.update(shred(rest, m['flat'][k], tcols, self.enums, sub))
                rc = m.get('flatrest', {}).get(k)
                if rc:
                    spill = {kk: vv for kk, vv in sub.items() if kk not in ('_present', '_null', '_empty')}
                    if spill:
                        row[rc] = Jsonb(spill)
                        for kk in spill:
                            del sub[kk]
                extra[k] = sub
            elif k in m['kids'] and self.kid_ok(k, v):
                later.append((k, v))
            elif isinstance(v, (dict, list)) and not v:
                extra.setdefault('_empty', []).append([k, v])
            else:
                extra[k] = v
        row['repo'] = 'book-index'
        if extra:
            row['extra'] = Jsonb(extra)
        self.add(tab, row)
        if side:
            srow['id'] = d['id']
            self.add(side[0], srow)
        for k, v in later:
            self.kids(k, d['id'], v)

    def kid_ok(self, k, v):
        mode = self.m['kids'][k]['mode']
        return (mode == 'list' and isinstance(v, list) and v) or (mode == 'dict' and isinstance(v, dict) and v) \
            or (mode == 'one' and (isinstance(v, str) or (isinstance(v, dict) and v)))

    def kids(self, key, oid, v):
        s = self.m['kids'][key]
        tcols = self.types[s['table']]
        if s['mode'] == 'one':
            items = [(None, v)]
        elif s['mode'] == 'dict':
            items = list(v.items())
        else:
            items = list(enumerate(v))
        self.put(s, oid, items, tcols)

    def put(self, s, oid, items, tcols, parent=None):
        for pos, it in items:
            extra = {}
            subs = []
            if s['sub'] and isinstance(it, dict):
                for sk in s['sub']:
                    if isinstance(it.get(sk), list) and it[sk]:
                        subs.append((sk, it[sk]))
                it = {k: v for k, v in it.items() if k not in dict(subs)}
            row = shred(it, s['map'], tcols, self.enums, extra)
            row[s['owner']] = oid
            if parent is not None:
                row[s['parent']] = parent
            if 'owner_type' in tcols:
                row['owner_type'] = self.m['owner_type']
            if s['mode'] == 'list' and 'seq' in tcols:
                row['seq'] = pos
            if s['mode'] == 'dict':
                row[s['dictkey']] = pos
            if s['table'] == 'merged_into':
                row['live_id'] = it['into']   # 原型：链末解析留给正式装载
            row.update(s['fixed'])
            if extra:
                if 'extra' not in tcols:
                    raise SystemExit('%s 没有 extra 列，装不下：%s %s' % (s['table'], oid, extra))
                row['extra'] = Jsonb(extra)
            self.add(s['table'], row)
            for sk, sv in subs:
                ss = s['sub'][sk]
                self.put(ss, oid, list(enumerate(sv)), self.types[ss['table']], parent=pos)

    def flush(self, cur):
        order = [self.m['table']] + [t for t in self.rows if t != self.m['table']]
        for t in order:
            groups = collections.defaultdict(list)
            for r in self.rows[t]:
                groups[tuple(r)].append(r)
            for cols, rows in groups.items():
                with cur.copy('COPY %s (%s) FROM STDIN' % (t, ','.join(cols))) as cp:
                    for r in rows:
                        cp.write_row([r[c] for c in cols])


def unshred(row, keymap, extra):
    if '@' in extra:
        return extra['@']
    if '@' in keymap:
        return row[keymap['@']]
    o = {}
    for k, col in keymap.items():
        if isinstance(col, tuple):
            if all(row.get(c) is not None for c in col):
                o[k] = [row[c] for c in col]
        elif row.get(col) is not None:
            o[k] = row[col]
    for k in extra.get('_null', []):
        o[k] = None
    for k, v in extra.get('_empty', []):
        o[k] = v
    for k, v in extra.items():
        if k not in ('_null', '_empty', '_present'):
            o[k] = v
    return o


def fetch(cur, table, where=None, args=()):
    cur.execute('SELECT * FROM %s%s' % (table, ' WHERE ' + where if where else ''), args)
    names = [c.name for c in cur.description]
    return [dict(zip(names, r)) for r in cur.fetchall()]


def restore_all(cur, m):
    """整表读回，按 owner 分组还原成 {id: doc}。"""
    kids = {}
    for key, s in m['kids'].items():
        cond = ' AND '.join("%s='%s'" % (k, v) for k, v in s['fixed'].items() if k != 'src')
        if 'owner_type' in [c for c in coltypes_cache[s['table']]]:
            cond = (cond + ' AND ' if cond else '') + "owner_type='%s'" % m['owner_type']
        subs = {}
        for sk, ss in s['sub'].items():
            g = collections.defaultdict(list)
            for r in fetch(cur, ss['table']):
                g[(r[ss['owner']], r[ss['parent']])].append((r['seq'], unshred(r, ss['map'], r.get('extra') or {})))
            subs[sk] = g
        by = collections.defaultdict(list)
        for r in fetch(cur, s['table'], cond or None):
            pos = r.get('seq') if s['mode'] == 'list' else r.get(s['dictkey']) if s['mode'] == 'dict' else 0
            it = unshred(r, s['map'], r.get('extra') or {})
            for sk, g in subs.items():
                got = g.get((r[s['owner']], pos))
                if got and isinstance(it, dict):
                    it[sk] = [x for _, x in sorted(got, key=lambda y: y[0])]
            by[r[s['owner']]].append((pos, it))
        kids[key] = by
    sides = {}
    for st, (t, cm, fm) in m.get('side', {}).items():
        sides[st] = {r['id']: r for r in fetch(cur, t)}
    out = {}
    for row in fetch(cur, m['table']):
        extra = row.get('extra') or {}
        d = dict(m['fixed'])
        side = m.get('side', {}).get(row.get('subtype'))
        if side:
            sr = sides[row['subtype']].get(row['id'], {})
            for k, col in side[1].items():
                if sr.get(col) is not None:
                    d[k] = sr[col]
            for k, fm in side[2].items():
                if k in extra:
                    d[k] = unshred(sr, fm, extra.pop(k))
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
                rc = m.get('flatrest', {}).get(k)
                if rc and row.get(rc):
                    d[k].update(row[rc])
        for key, s in m['kids'].items():
            items = kids[key].get(row['id'])
            if not items:
                continue
            items.sort(key=lambda x: x[0])
            if s['mode'] == 'one':
                v = items[0][1]
            elif s['mode'] == 'dict':
                v = {p: it for p, it in items}
            else:
                v = [it for _, it in items]
            if '.' in key:
                a, b = key.split('.')
                d.setdefault(a, {})[b] = v
            else:
                d[key] = v
        if isinstance(d.get('merged_into'), dict):
            mb = d.pop('merged_into')
            d['merged_into'] = mb.pop('into')
            if mb:
                d['merged_basis'] = mb
        for k in extra.get('_null', []):
            d[k] = None
        for k, v in extra.get('_empty', []):
            d[k] = v
        for k, v in extra.items():
            if k not in ('_null', '_empty') and k not in m['flat']:
                d[k] = v
        out[row['id']] = d
    return out


coltypes_cache = {}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--dsn', required=True)
    ap.add_argument('--type', default='Collection')
    ap.add_argument('--limit', type=int)
    ap.add_argument('--keep', action='store_true', help='比对通过就提交，留下数据（供 checks.sql、外键 VALIDATE）')
    a = ap.parse_args()
    m = MAPS[a.type]
    t0 = time.time()
    paths = sorted(glob.glob(os.path.join(ROOT, a.type, '**', '*.json'), recursive=True))[:a.limit]
    docs = []
    for p in paths:
        with open(p, encoding='utf-8') as f:
            docs.append(json.load(f))
    print('读入 %d 条，%.0fs' % (len(docs), time.time() - t0), flush=True)
    with psycopg.connect(a.dsn) as conn, conn.cursor() as cur:
        types, enums = coltypes(cur)
        coltypes_cache.update(types)
        ld = Loader(m, types, enums)
        for d in docs:
            ld.doc(d)
        ld.flush(cur)
        print('灌库 %s，%.0fs' % ({t: len(r) for t, r in ld.rows.items()}, time.time() - t0), flush=True)
        back = restore_all(cur, m)
        bad = collections.Counter()
        shown = 0
        for d in docs:
            r = back.get(d['id'])
            if r != d:
                diff = sorted(k for k in set(d) | set(r or {}) if d.get(k) != (r or {}).get(k))
                for k in diff:
                    bad[k] += 1
                if shown < 5:
                    shown += 1
                    print('不一致', d['id'], {k: (d.get(k), (r or {}).get(k)) for k in diff[:2]}, file=sys.stderr)
        n_bad = sum(1 for d in docs if back.get(d['id']) != d)
        print('%s：%d 条，还原不一致 %d %s，%.0fs' % (a.type, len(docs), n_bad, dict(bad), time.time() - t0))
        cur.execute("SELECT k, count(*) FROM %s, jsonb_object_keys(extra) k GROUP BY 1 ORDER BY 2 DESC" % m['table'])
        print('主表 extra 键：', cur.fetchall())
        for t in ld.rows:
            if t != m['table'] and 'extra' in types[t]:
                cur.execute("SELECT k, count(*) FROM %s, jsonb_object_keys(extra) k GROUP BY 1 ORDER BY 2 DESC LIMIT 12" % t)
                r = cur.fetchall()
                if r:
                    print('  %s extra 键：' % t, r)
        if a.keep and not n_bad:
            conn.commit()
        else:
            conn.rollback()
    sys.exit(1 if n_bad else 0)


if __name__ == '__main__':
    main()
