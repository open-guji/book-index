import importlib.util, json, pathlib

_spec = importlib.util.spec_from_file_location(
    'build_id_table', pathlib.Path(__file__).resolve().parents[1] / 'scripts' / 'build-id-table.py')
bit = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bit)


def _put(root, typ, rid, **doc):
    d = root / typ / rid[-1] / rid[-2] / rid[-3]
    d.mkdir(parents=True, exist_ok=True)
    (d / f'{rid}-名.json').write_text(json.dumps({'id': rid, **doc}, ensure_ascii=False), encoding='utf-8')


def _run(root):
    ids, edges, prom = bit.scan(root)
    return bit.fold(ids, edges, prom)


def test_single_hop_and_object_form(tmp_path):
    _put(tmp_path, 'Work', 'aaa111', merged_into='bbb222')
    _put(tmp_path, 'Work', 'ccc333', merged_into={'id': 'bbb222'})
    _put(tmp_path, 'Work', 'bbb222')
    out, an = _run(tmp_path)
    assert out == {'aaa111': ('bbb222', 1), 'ccc333': ('bbb222', 1)}
    assert not any(an.values())


def test_multi_hop_collapses(tmp_path):
    _put(tmp_path, 'Entity', 'aaa111', merged_into='bbb222')
    _put(tmp_path, 'Entity', 'bbb222', merged_into='ccc333')
    _put(tmp_path, 'Entity', 'ccc333')
    out, an = _run(tmp_path)
    assert out['aaa111'] == ('ccc333', 2) and out['bbb222'] == ('ccc333', 1)
    assert not any(an.values())


def test_cycle_and_self_excluded(tmp_path):
    _put(tmp_path, 'Work', 'aaa111', merged_into='bbb222')
    _put(tmp_path, 'Work', 'bbb222', merged_into='aaa111')
    _put(tmp_path, 'Work', 'ddd444', merged_into='ddd444')
    out, an = _run(tmp_path)
    assert out == {}
    assert len(an['cycle']) == 2 and len(an['self']) == 1


def test_dangling_cross_type_and_promoted_end(tmp_path):
    _put(tmp_path, 'Work', 'aaa111', merged_into='zzz999')      # 目标不存在
    _put(tmp_path, 'Work', 'bbb222', merged_into='ccc333')      # 跨类型
    _put(tmp_path, 'Book', 'ccc333')
    _put(tmp_path, 'Work', 'ddd444', merged_into='eee555')      # 终点已升格
    _put(tmp_path, 'Work', 'eee555', promoted_to='fff666')
    out, an = _run(tmp_path)
    assert out == {}
    assert [x['id'] for x in an['dangling']] == ['aaa111']
    assert [x['id'] for x in an['cross_type']] == ['bbb222']
    assert [x['id'] for x in an['ends_at_promoted']] == ['ddd444']


def test_output_reproducible_and_format(tmp_path):
    _put(tmp_path, 'Work', 'aaa111', merged_into='bbb222')
    _put(tmp_path, 'Work', 'bbb222')
    for name in ('o1', 'o2'):
        assert bit.main([str(tmp_path), '--out-dir', str(tmp_path / name)]) == 0
    for fn in ('redirects.json', 'redirects.csv', 'anomalies.json'):
        assert (tmp_path / 'o1' / fn).read_bytes() == (tmp_path / 'o2' / fn).read_bytes()
    assert json.loads((tmp_path / 'o1' / 'redirects.json').read_text()) == {
        'version': 1, 'redirects': {'aaa111': 'bbb222'}}
