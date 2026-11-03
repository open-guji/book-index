"""版本关系（06 稿）：derived_items／related_items 新旧两种写法读出同一组边。"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'build'))
import build_derived as BD  # noqa: E402


def test_derived_items_old_and_new_equal():
    old = {'lineage': {'derived_from': [
        {'ref': 'b1', 'ref_type': 'book', 'relation': '翻刻', 'confidence': 'probable'},
        {'ref': 'h_x', 'ref_type': 'hypothetical', 'relation': '過錄'}]}}
    new = {'base_edition': [
        {'role': '底本', 'relation': '翻刻', 'book_id': 'b1', 'confidence': 'probable', 'source': 's'},
        {'role': '底本', 'relation': '過錄', 'hypothetical_id': 'h_x', 'source': 's'}]}
    key = lambda x: (x['ref'], x['ref_type'], x['relation'], x['confidence'])  # noqa: E731
    assert sorted(map(key, BD.derived_items(old))) == sorted(map(key, BD.derived_items(new)))


def test_base_edition_without_relation_is_not_an_edge():
    b = {'base_edition': [{'role': '底本', 'name': '某本', 'book_id': 'b9', 'source': 's'}]}
    assert BD.derived_items(b) == []


def test_old_wins_when_both_present():
    b = {'lineage': {'derived_from': [{'ref': 'b1', 'ref_type': 'book', 'relation': '翻刻'}]},
         'base_edition': [{'role': '底本', 'relation': '刊刻', 'book_id': 'b1', 'source': 's'}]}
    assert [x['relation'] for x in BD.derived_items(b)] == ['翻刻']


def test_related_items():
    b = {'lineage': {'related_to': [{'book_id': 'b2', 'relation': '同版'}]},
         'related_books': ['b7', {'book_id': 'b3', 'relation': '兄弟本'}, {'book_id': 'b4'}]}
    assert [(x['ref'], x['relation']) for x in BD.related_items(b)] == [('b2', '同版'), ('b3', '兄弟本')]
