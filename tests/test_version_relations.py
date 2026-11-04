"""版本关系（06 稿）：derived_items／related_items 只读 base_edition／related_books。"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'build'))
import build_derived as BD  # noqa: E402


def test_derived_items_from_base_edition():
    b = {'base_edition': [
        {'role': '底本', 'relation': '翻刻', 'book_id': 'b1', 'confidence': 'probable', 'source': 's'},
        {'role': '底本', 'relation': '過錄', 'hypothetical_id': 'h_x', 'source': 's'}]}
    assert [(x['ref'], x['ref_type'], x['relation'], x['confidence']) for x in BD.derived_items(b)] == [
        ('b1', 'book', '翻刻', 'probable'), ('h_x', 'hypothetical', '過錄', None)]


def test_base_edition_without_relation_is_not_an_edge():
    b = {'base_edition': [{'role': '底本', 'name': '某本', 'book_id': 'b9', 'source': 's'}]}
    assert BD.derived_items(b) == []


def test_old_lineage_keys_are_ignored():
    b = {'lineage': {'derived_from': [{'ref': 'b1', 'ref_type': 'book', 'relation': '翻刻'}],
                     'related_to': [{'book_id': 'b2', 'relation': '同版'}]}}
    assert BD.derived_items(b) == [] and BD.related_items(b) == []


def test_related_items():
    b = {'related_books': [{'book_id': 'b3', 'relation': '兄弟本'}, {'book_id': 'b4'}]}
    assert [(x['ref'], x['relation']) for x in BD.related_items(b)] == [('b3', '兄弟本')]
