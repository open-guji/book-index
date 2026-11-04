"""第12组 S2-T：_titles_split 按 type 拆出异名与附刻。"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'build'))
import build_derived as BD  # noqa: E402


def test_split_by_type():
    d = {'additional_titles': ['甲', {'book_title': '丙', 'type': '附刻'}, {'book_title': '丁', 'type': '附刻'}]}
    assert BD._titles_split(d) == (['甲'], ['丙', '丁'])


def test_empty_and_garbage():
    assert BD._titles_split({}) == ([], [])
    assert BD._titles_split({'additional_titles': [{'book_title': ''}, 3, {'type': '附刻'}]}) == ([], [])
