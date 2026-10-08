"""build：專名派生欄與匹配鍵表（F6-5b，build/names.py）。以最小樣例逐項驗。"""
import json
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'build'))
sys.path.insert(0, str(ROOT / 'tests'))
import build_derived as BD  # noqa: E402
import v2sample as S  # noqa: E402

DY_SONG, DY_NS, DY_MING, DY_LIANG = 'e00000dy01', 'e00000dy02', 'e00000dy03', 'e00000dy04'
R_A, R_B, R_C = 'e00000rg01', 'e00000rg02', 'e00000rg03'
EMPEROR = 'e00000pp01'
P_SONG, P_AMBIG, P_DRAFTDY = 'e00000pp02', 'e00000pp03', 'e00000pp04'
OF_C, OF_K, OF_X = 'e00000of01', 'e00000of02', 'e00000of03'
IN_C, IN_K, IN_SUB, IN_G = 'e00000in01', 'e00000in02', 'e00000in03', 'e00000in04'
PL_UP, PL_DN = 'e00000pl01', 'e00000pl02'
W = 'w00000wk01'


def ent(i, sub, name, **kw):
    return dict({'id': i, 'type': 'entity', 'schema_version': 1, 'subtype': sub, 'primary_name': name}, **kw)


def make(root):
    E = [
        ent(DY_SONG, 'dynasty', '趙宋', dates={'start': 960, 'end': 1279},
            alt_names=[{'name': '宋', 'type': '簡稱', 'ambiguous': True}]),
        ent(DY_NS, 'dynasty', '北宋', parent_id=DY_SONG, dates={'start': 960, 'end': 1127}),
        ent(DY_LIANG, 'dynasty', '南朝宋', dates={'start': 420, 'end': 479},
            alt_names=[{'name': '宋', 'type': '簡稱', 'ambiguous': True}, {'name': '劉宋全稱', 'type': '全稱'}]),
        ent(R_A, 'reign', '建隆', dynasty_id=DY_NS, ruler={'name': '趙匡胤', 'entity_id': EMPEROR},
            dates={'start': 960, 'end': 963}),
        ent(R_B, 'reign', '乾德', dynasty_id=DY_NS, ruler={'name': '趙匡胤', 'entity_id': EMPEROR},
            dates={'start': 963, 'end': 968}),
        ent(R_C, 'reign', '建隆', dynasty_id=DY_LIANG, ruler={'name': '某'}, dates={'start': 450, 'end': 451}),
        ent(EMPEROR, 'people', '趙匡胤', dynasty='北宋'),
        ent(P_SONG, 'people', '甲', dynasty='北宋'),
        ent(P_AMBIG, 'people', '乙', dynasty='宋'),
        ent(OF_C, 'office', '尚書', office_level='concept'),
        ent(OF_K, 'office', '尚書', office_level='concrete', parent_id=OF_C, dynasty_ids=[DY_NS],
            institution_ref=IN_K, alt_names=[{'name': '尙書', 'type': '異體'}]),
        ent(OF_X, 'office', '吏部尚書', office_level='concrete', base_office_id=OF_K, dynasty_ids=[DY_NS]),
        ent(IN_C, 'collective', '吏部', collective_kind='官署', institution_level='concept'),
        ent(IN_K, 'collective', '吏部', collective_kind='官署', institution_level='concrete', parent_id=IN_C,
            dynasty_ids=[DY_NS], superiors=[{'id': IN_SUB}], group_ids=[IN_G]),
        ent(IN_SUB, 'collective', '尚書省', collective_kind='官署', institution_level='concrete', dynasty_ids=[DY_NS]),
        ent(IN_G, 'collective', '六部', collective_kind='官署', institution_level='group'),
        ent(PL_UP, 'place', '甲州', history=[{'start': 600, 'end': 900, 'name': '甲州', 'dynasty_ids': [DY_NS]}]),
        ent(PL_DN, 'place', '乙縣', history=[{'start': 620, 'end': 700, 'name': '乙縣', 'parent_id': PL_UP},
                                             {'start': 701, 'end': 950, 'name': '乙縣'}]),
    ]
    for d in E:
        S.put(root, 'Entity', d)
    S.put(root, 'Work', {'id': W, 'type': 'work', 'schema_version': 1, 'title': '某書',
                         'authors': [{'name': '甲', 'role': '撰', 'dynasty': '北宋', 'entity_id': P_SONG}]})
    return root


def build(root, **kw):
    kw.setdefault('quiet', True)
    return BD.run(root, check_only=True, **kw)


def test_dynasty_reign_fields(tmp_path):
    r, P = build(make(str(tmp_path / 'repo')))
    assert r['fatal'] == [] and r['contract'] == 2
    ns = P[f'entry/{DY_NS}.json']
    assert ns['_ancestors'] == [{'id': DY_SONG, 'name': '趙宋', 'start': 960, 'end': 1279}]
    assert [x['id'] for x in ns['_reigns']] == [R_A, R_B]
    assert ns['_reigns'][0] == {'id': R_A, 'name': '建隆', 'start': 960, 'end': 963, 'ruler': '趙匡胤', 'dynasty': '北宋'}
    assert [x['id'] for x in P[f'entry/{DY_SONG}.json']['_children']] == [DY_NS]
    a, b = P[f'entry/{R_A}.json'], P[f'entry/{R_B}.json']
    assert a['_dynasty']['id'] == DY_NS and a['_ruler'] == {'id': EMPEROR, 'name': '趙匡胤', 'dyn': '北宋'}
    assert (a['_index_in_reign'], b['_index_in_reign']) == (1, 2)
    assert [x['id'] for x in a['_same_name']] == [R_C] and '_same_name' not in b
    assert '_ruler' not in P[f'entry/{R_C}.json']           # 無 entity_id 不出 _ruler


def test_dynasty_ref_unique_ambiguous_and_work(tmp_path):
    _, P = build(make(str(tmp_path / 'repo')))
    assert P[f'entry/{P_SONG}.json']['_dynasty_id'] == DY_NS
    amb = P[f'entry/{P_AMBIG}.json']
    assert amb['_dynasty_candidates'] == sorted([DY_SONG, DY_LIANG]) and '_dynasty_id' not in amb
    assert P[f'entry/{W}.json']['_dynasty_id'] == DY_NS


def test_office_institution_place(tmp_path):
    _, P = build(make(str(tmp_path / 'repo')))
    assert [x['id'] for x in P[f'entry/{OF_C}.json']['_children']] == [OF_K]
    assert P[f'entry/{OF_K}.json']['_compounds'] == [{'id': OF_X, 'name': '吏部尚書', 'level': 'concrete',
                                                       'dynasties': ['北宋']}]
    assert [x['id'] for x in P[f'entry/{IN_C}.json']['_children']] == [IN_K]
    assert [x['id'] for x in P[f'entry/{IN_SUB}.json']['_subordinates']] == [IN_K]
    assert [x['id'] for x in P[f'entry/{IN_G}.json']['_members']] == [IN_K]
    assert [x['id'] for x in P[f'entry/{IN_K}.json']['_offices']] == [OF_K]
    up = P[f'entry/{PL_UP}.json']
    assert up['_children'] == [{'id': PL_DN, 'name': '乙縣', 'start': 620, 'end': 950}]
    assert up['_span'] == {'start': 600, 'end': 900}


def test_keys_files(tmp_path):
    _, P = build(make(str(tmp_path / 'repo')))
    dk = P['dynasty_reign_keys.json']
    assert dk['count'] == {'keys': len(dk['keys']), 'dynasty': 3, 'reign': 3}
    song = dk['keys']['宋']
    assert [c['id'] for c in song] == [DY_LIANG, DY_SONG] and all(c['ambiguous'] for c in song)   # 按起年
    assert '劉宋全稱' not in dk['keys']                       # 全稱不參與匹配
    jl = dk['keys']['建隆']
    assert [c['id'] for c in jl] == [R_C, R_A] and jl[1]['dynasty'] == '北宋' and jl[1]['ruler'] == '趙匡胤'
    ok = P['office_keys.json']
    assert ok['count']['office'] == 3 and ok['count']['官署'] == 4
    sh = ok['keys']['尚書']                                    # 「尙書」歸一後併到同鍵，同條不重複
    assert [(c['id'], c['via']) for c in sh] == [(OF_C, 'primary_name'), (OF_K, 'primary_name')]
    assert [(c['id'], c['via']) for c in ok['keys']['尙書']] == [(OF_K, '異體')]
    lb = ok['keys']['吏部']
    assert [(c['subtype'], c['level']) for c in lb] == [('官署', 'concept'), ('官署', 'concrete')]


def test_promoted_draft_resolves_to_official(tmp_path):
    """草稿條已升格者：不進反查、不進鍵表；草稿裡指向它的 id 一律換成正式 id。"""
    prod = make(str(tmp_path / 'prod'))
    draft = str(tmp_path / 'draft')
    old = 'd00000dy09'
    S.put(draft, 'Entity', ent(old, 'dynasty', '北宋', dates={'start': 960, 'end': 1127}))      # 已升格為 DY_NS
    S.put(draft, 'Entity', ent('d00000rg09', 'reign', '開寶', dynasty_id=old, ruler={'name': '趙匡胤'},
                               dates={'start': 968, 'end': 976}))
    with open(os.path.join(prod, 'promotions.json'), 'w', encoding='utf-8') as f:
        json.dump({'promotions': {old: {'production_id': DY_NS}}}, f)
    _, P = build(draft, ref_roots=[prod])
    rg = P['entry/d00000rg09.json']
    assert rg['_dynasty']['id'] == DY_NS and rg['_index_in_reign'] == 3      # 建隆、乾德之後
    assert all(c['id'] != old for c in P['dynasty_reign_keys.json']['keys']['北宋'])
    assert '_reigns' not in P[f'entry/{old}.json']


def test_place_keys_sources_and_default(tmp_path):
    root = str(tmp_path / 'repo')
    pl = [
        ent('e00000px01', 'place', '撫州府', history=[{'start': 1368, 'end': 1912, 'name': '撫州府', 'level': '府'}]),
        ent('e00000px02', 'place', '臨川縣', history=[{'start': 589, 'end': 1912, 'name': '臨川縣', 'level': '縣',
                                                   'parent_id': 'e00000px01'}]),
        ent('e00000px03', 'place', '臨川府', history=[{'start': 1000, 'end': 1100, 'name': '臨川府', 'level': '府'}]),
        ent('e00000px04', 'place', '紹興府', history=[{'start': 618, 'end': 1131, 'name': '越州', 'level': '州'},
                                                   {'start': 1131, 'end': 1912, 'name': '紹興府', 'level': '府'}]),
        ent('e00000px05', 'place', '淸江縣', history=[{'start': 1000, 'end': 1912, 'name': '淸江縣', 'level': '縣'}]),
        ent('e00000px06', 'place', '建寧縣', history=[{'start': 900, 'end': 1912, 'name': '建寧縣', 'level': '縣'}]),
        ent('e00000px07', 'place', '建寧州', history=[{'start': 900, 'end': 1912, 'name': '建寧州', 'level': '州'}]),
    ]
    for d in pl:
        S.put(root, 'Entity', d)
    _, P = build(root)
    k = P['place_keys.json']['keys']
    yz = k['越州']
    assert yz[0]['via'] == '沿革' and yz[0]['segments'][0]['name_then'] == '越州'
    lc = k['臨川']                               # 去通名：縣、府兩條同鍵
    assert all(c['via'] == '去通名' for c in lc)
    assert '清江縣' in k and k['清江縣'][0]['id'] == 'e00000px05'      # 淸→清 歸一
    # default ②：臨川縣之上級鏈不含臨川府 → 不標
    assert not any(c.get('default') for c in lc)
    # default ①：鍵「臨川縣」只有一條，不標；鍵「撫州」只一條，不標
    assert not any(c.get('default') for c in k['撫州'])
    # default ③：建寧縣、建寧州無上下級 → 「建寧」不標
    assert not any(c.get('default') for c in k['建寧'])
    assert P['place_keys.json']['count']['place'] == 7


def test_mark_default_rules():
    import names
    anc = {'x': {'y'}}
    a = [{'id': 'x', 'via': '去通名', 'level': '縣'}, {'id': 'y', 'via': '去通名', 'level': '府'}]
    names.mark_default(a, anc)
    assert a[0].get('default') and not a[1].get('default')        # ② 其餘皆其上級
    b = [{'id': 'x', 'via': 'primary_name', 'level': '府'}, {'id': 'y', 'via': '沿革', 'level': '縣'}]
    names.mark_default(b, {})
    assert b[0].get('default') and not b[1].get('default')        # ① 規範名命中優先
    c = [{'id': 'x', 'via': '去通名', 'level': '縣'}, {'id': 'z', 'via': '去通名', 'level': '縣'}]
    names.mark_default(c, {})
    assert not any(x.get('default') for x in c)                   # 最低一級兩條 → 不標
