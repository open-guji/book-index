"""去重普查：小样本上各类计数与草稿库指向墓碑。"""
import importlib.util, json, pathlib, sys

HERE = pathlib.Path(__file__).parent.parent
spec = importlib.util.spec_from_file_location('dedup_census', HERE / 'scripts/dedup-census.py')
census = importlib.util.module_from_spec(spec)
spec.loader.exec_module(census)


def put(root, typ, d):
    i = d['id']
    p = root / typ / i[-3] / i[-2] / i[-1] / f'{i}-x.json'
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def fixture(tmp):
    root, draft = tmp / 'prod', tmp / 'draft'
    au = lambda n, e=None: [{'name': n, **({'entity_id': e} if e else {})}]
    for d in [
        {'id': 'w001', 'title': '甲集（二卷）', 'authors': au('張三', 'e001')},
        {'id': 'w002', 'title': '甲集', 'authors': au('張三')},                          # 同首位（名同）
        {'id': 'w003', 'title': '乙集', 'authors': au('李四')},
        {'id': 'w004', 'title': '乙集', 'authors': []},                                  # 一侧有一侧无
        {'id': 'w005', 'title': '丙集', 'authors': au('佚名')},
        {'id': 'w006', 'title': '丙集', 'authors': []},                                  # 全无
        {'id': 'w007', 'title': '丁集', 'authors': au('王五'),
         'related_works': [{'id': 'w008', 'relation': 'related', 'note': '同題異書'}]},
        {'id': 'w008', 'title': '丁集', 'authors': au('趙六'),
         'related_works': [{'id': 'w009', 'relation': 'related', 'note': '待並條複核'}]},  # 不同、已判
        {'id': 'w009', 'title': '戊', 'authors': au('孫七')},
        {'id': 'w00a', 'title': '戊', 'merged_into': 'w00b'},
        {'id': 'w00b', 'title': '戊', 'merged_into': 'w009'},                            # 墓碑链
    ]:
        put(root, 'Work', d)
    put(root, 'Work', {'id': 'w00c', 'title': '己', 'merged_in': [{'id': 'w00d'}]})
    put(root, 'Work', {'id': 'w00d', 'title': '己', 'merged_into': 'w00c'})
    for d in [
        {'id': 'b001', 'work_id': 'w001', 'edition': '清刻本'},
        {'id': 'b002', 'work_id': 'w001', 'edition': '清刻本'},
        {'id': 'b003', 'work_id': 'w00d', 'edition': '明刻本'},                           # 引用墓碑
    ]:
        put(root, 'Book', d)
    put(root, 'Entity', {'id': 'e001', 'subtype': 'people', 'primary_name': '張三'})
    put(root, 'Entity', {'id': 'e002', 'subtype': 'people', 'primary_name': '張三'})
    (root / 'classification/zongmu/members').mkdir(parents=True)
    (root / 'classification/zongmu/tree.json').write_text(json.dumps({'nodes': [
        {'id': 'zm0001', 'label': '經部', 'parent': None}, {'id': 'zm0002', 'label': '易類', 'parent': 'zm0001'}]}))
    (root / 'classification/zongmu/members/zm0002.json').write_text(json.dumps(
        {'node': 'zm0002', 'members': [['w001', 'x'], ['w00d', 'x']]}))
    (root / 'promotions').mkdir()
    (root / 'promotions/00.json').write_text(json.dumps(
        {'promotions': {'dr1': {'production_id': 'w00d'}, 'dr2': {'production_id': 'w003'}}}))
    put(draft, 'Book', {'id': 'db01', 'work_id': 'w00a'})
    put(draft, 'Work', {'id': 'w00a', 'title': '戊'})                                    # 键 id 不算
    return root, draft


def test_census(tmp_path):
    root, draft = fixture(tmp_path)
    rep, detail = census.census(str(root), str(draft), [])
    w = rep['W 同题组']
    assert (w['组'], w['同首位组'], w['一侧有一侧无组'], w['全无组'], w['不同组']) == (4, 1, 1, 1, 1)
    assert w['已判组'] == 1 and w['經部·同首位组'] == 1
    assert rep['T 墓碑'] == {'墓碑链（应改指链末）': 1}
    assert rep['H keeper 未记并入历史（多为立规前旧并，看数不拦）'] == {'Work': 1}
    assert rep['L 引用墓碑'] == {'Book.work_id': 1, '分类成员→墓碑': 1, 'promotions→墓碑': 1}
    assert rep['B 同 Work 重复 Book']['同 Work 同版本名组'] == 1
    assert rep['E 人物重名']['同名组'] == 1
    assert rep['R related 待並條']['待並條链接'] == 1
    assert rep['D 草稿库指向正式墓碑'] == {'载入文件': 2, 'work_id': 1}
    assert census.main(['--root', str(root), '--strict']) == 1


def test_empty_root_fails(tmp_path):
    try:
        census.census(str(tmp_path))
    except SystemExit as e:
        assert '为 0' in str(e)
    else:
        raise AssertionError('空库应报错')
