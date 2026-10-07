"""schema-v2 單測用的小樣本倉（**樣本，非真數據**；在臨時目錄生成，不入庫）。

覆蓋：Work.books 舊反向、成對關係兩側都寫且 note 不同、只有反向形、related 只在大 id 側、
詞表外詞、Collection.books／contained_works（叢編側獨有）、Entity.works 帶 role 而 Work 缺、
sidecar（sub_items、wiki_title、parent_work_id）、承襲（lineage）。
"""
import json
import os

W1, W2, W3, W4, W5 = 'w0000000001', 'w0000000002', 'w0000000003', 'w0000000004', 'w0000000005'
B1, B2, B3 = 'b000000001', 'b000000002', 'b000000003'
C1 = 'c0000000001'
E1 = 'e0000000001'


def path(root, typ, rid, title='樣本'):
    return os.path.join(root, typ, rid[-1], rid[-2], rid[-3], f'{rid}-{title}.json')


def put(root, typ, d, indent=2):
    p = path(root, typ, d['id'])
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(json.dumps(d, ensure_ascii=False, indent=indent) + '\n')
    return p


def read(root, typ, rid):
    return json.load(open(path(root, typ, rid), encoding='utf-8'))


def make(root):
    put(root, 'Work', {
        'id': W1, 'type': 'work', 'title': '甲書', 'revision': '1.0.3', 'revised_at': '2026-01-01',
        'books': [B1, B2], '_edition_count': 2,
        'authors': [{'name': '張三', 'entity_id': E1}],                     # 缺 role，Entity 側有
        'related_works': [
            {'id': W2, 'relation': 'has_part', 'title': '乙書', 'note': '甲側說'},  # 兩側都寫、note 不同
            {'id': W3, 'relation': 'studied_by', 'title': '丙書'},               # 只有反向形
        ],
        'classification': {'l1': '經部', 'l2': '易類', 'basis': 'S', 'source': '樣本'},
    })
    put(root, 'Work', {
        'id': W2, 'type': 'work', 'title': '乙書', 'revision': '1.0.0',
        'related_works': [{'id': W1, 'relation': 'part_of', 'title': '甲書', 'note': '乙側說'}],
    })
    put(root, 'Work', {
        'id': W3, 'type': 'work', 'title': '丙書', 'revision': '1.0.0',
        'related_works': [{'id': W4, 'relation': 'commentary_on', 'title': '丁書'}],
    })
    put(root, 'Work', {
        'id': W4, 'type': 'work', 'title': '丁書', 'revision': '1.0.0',
        'related_works': [{'id': W1, 'relation': 'related', 'title': '甲書', 'note': '大 id 側的 note'}],
        'indexed_by': [{'source': '某志', 'source_bid': W5, 'section': '經部', 'summary': '丁書一卷'}],
    }, indent=1)                                                                 # 縮排 1：驗保格式
    put(root, 'Work', {'id': W5, 'type': 'work', 'title': '某志', 'revision': '1.0.0'})
    put(root, 'Book', {
        'id': B1, 'type': 'book', 'title': '甲書宋本', 'work_id': W1, 'revision': '1.0.0',
        'dating': {'year': 1200}, 'resources': [{'id': 'x', 'url': 'u', 'types': ['image']}],
        'contained_in': [{'id': C1, 'volume_index': 3}],
    })
    put(root, 'Book', {
        'id': B2, 'type': 'book', 'title': '甲書明本', 'work_id': W1, 'revision': '1.0.0',
        'dating': {'year': 1500}, 'lineage': {'derived_from': [{'ref': B1, 'ref_type': 'book', 'relation': '翻刻'}]},
    })
    put(root, 'Book', {'id': B3, 'type': 'book', 'title': '乙書刊本', 'work_id': W2, 'revision': '1.0.0'})
    put(root, 'Collection', {
        'id': C1, 'type': 'collection', 'title': '某叢書', 'revision': '1.0.0',
        'books': [B1, B3],                                                       # B3 只在叢編側
        'contained_works': [{'id': W2, 'title': '乙書', 'group': '甲編'}],          # 只在叢編側
        '_member_count': 1,
    })
    put(root, 'Entity', {
        'id': E1, 'type': 'entity', 'primary_name': '張三',
        'works': [{'work_id': W1, 'role': '撰'}, {'work_id': W2, 'role': '注', 'title': '乙書'}],
    })
    sc = os.path.join(os.path.dirname(path(root, 'Collection', C1)), C1, 'src', 'volume_book_mapping.json')
    os.makedirs(os.path.dirname(sc), exist_ok=True)
    with open(sc, 'w', encoding='utf-8') as f:
        json.dump({'collection_id': C1, 'books': [
            {'title': '甲書宋本', 'book_id': B1, 'work_id': W1, 'volumes': [3], 'section': '經部',
             'sub_items': ['附錄一', '考證'], 'wiki_title': '甲書 (宋本)', 'parent_work_id': W4},
            {'title': '乙書刊本', 'book_id': B3, 'work_id': W2, 'volumes': [4], 'section': '經部'},
        ]}, f, ensure_ascii=False, indent=2)
    return root
