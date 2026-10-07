"""F6-3（overview#459）：舊 qa 讀取方改讀新格式的最小樣例（**樣本，非真數據**）。"""
import json, os, sys, pathlib, subprocess

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / '.claude/qa'))
import scan, reindex, verify  # noqa: E402


def test_scan_derives_entity_works_and_books_in_memory():
    works = {'w1': {'id': 'w1', 'title': '甲', 'period': 'song', 'loss_status': 'lost',
                    'authors': [{'name': '某', 'role': '撰', 'dynasty': '北宋', 'entity_id': 'e1'}]}}
    IW = {'w1': {'id': 'w1', 'title': '甲', 'period': 'song', 'loss_status': 'lost',
                 'author': '某', 'role': '撰', 'dynasty': '北宋'}}
    IB = {'b1': {'id': 'b1', 'work_id': 'w1'}}
    IE = {'e1': {'id': 'e1', 'primary_name': '某', 'period': 'song'}}
    ents = {'e1': {'id': 'e1', 'primary_name': '某'}}           # 新格式：無 works
    R = scan.run_checks(works, IW, IB, IE, {}, ents)
    assert ents['e1']['works'] == [{'work_id': 'w1', 'role': '撰'}]   # 記憶體視圖
    assert not R['K']                                                 # 無「互不回指」假報
    assert [r['books'] for r in R['E']] == [1]                        # 版本數由 Book.work_id 反查
    assert not R['M']                                                 # dynasty 口徑同 build


def test_reindex_main_delegates_to_build(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(subprocess, 'call', lambda cmd: calls.append(cmd) or 0)
    monkeypatch.setattr(sys, 'argv', ['reindex.py'])
    assert reindex.main() == 0
    monkeypatch.setattr(sys, 'argv', ['reindex.py', '--run'])
    assert reindex.main() == 0
    assert calls[0][-1] == '--check-only' and calls[1][-1] == '--write-index'
    assert calls[0][1].endswith(os.path.join('build', 'build_derived.py'))
    assert '已廢' in capsys.readouterr().err


def test_verify_classific_vocab_tolerates_missing_file(tmp_path, monkeypatch):
    monkeypatch.setattr(verify, 'ROOT', str(tmp_path))
    assert verify.load_classific_vocab() == (set(), set(), set(), set())
