"""Data regressions for the 2026-10-21 duplicate audit (not identity heuristics)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def record(family, rid):
    paths = list((ROOT / family / Path(*rid[-3:])).glob(rid + '-*.json'))
    assert len(paths) == 1, rid
    return json.loads(paths[0].read_text(encoding='utf-8'))


def test_merge_ids_remain_resolvable_and_keep_history():
    ledger = json.loads((ROOT / '.claude/qa/reports/duplicate-audit-2026-10-21/merges.json').read_text())
    families = {'people': 'Entity', 'work': 'Work', 'book': 'Book'}
    for merge in ledger['merges']:
        family = families[merge['type']]
        keeper = record(family, merge['keeper'])
        assert not keeper.get('merged_into')
        history = keeper.get('merged_in', []) if family != 'Book' else keeper.get('merged_from', [])
        history_ids = {entry['id'] if isinstance(entry, dict) else entry for entry in history}
        for rid in merge['losers']:
            tomb = record(family, rid)
            assert tomb['merged_into'] == keeper['id']
            assert rid in history_ids
            assert not any(key in tomb for key in ('authors', 'resources', 'indexed_by', 'contained_in'))


def test_commentary_and_original_authors_keep_their_distinct_roles():
    work = record('Work', 'd59f2j522ltu')
    assert any(a['name'] == '劉瑾' for a in work['authors'])
    assert any(a['name'] == '朱熹' and a['role'] == '集傳' for a in work['authors'])
    assert work['period'] == 'liao-jin-yuan'
    assert any('劉瑾通釋' in entry.get('author_info', '') for entry in work['indexed_by'])
    # Bibliographic responsibility overrides the imported blank author list.
    mengxi = record('Work', 'd59f2q7zj6yp')
    assert any(a['name'] == '沈括' for a in mengxi['authors'])
    assert mengxi['period'] == 'song'


def test_macau_author_does_not_acquire_the_unrelated_ming_person():
    work = record('Work', 'd59f2mdml0qo')
    zhang = [a for a in work['authors'] if a['name'] == '張汝霖']
    assert zhang and all(a['dynasty'] == '清' and not a.get('entity_id') for a in zhang)
    assert work['period'] == 'qing'
    assert record('Work', 'd59fy2deo4jk')['merged_into'] == work['id']


def test_same_viaf_does_not_merge_distinct_people():
    shen_yiguan = record('Entity', 'hixhd2h9bdu8')
    shen_li = record('Entity', 'hixhd2h9bf09')
    assert not shen_yiguan.get('merged_into') and not shen_li.get('merged_into')
    assert shen_yiguan['external_ids']['wikidata_id'] != shen_li['external_ids']['wikidata_id']


def test_same_rubbing_with_unresolved_work_model_is_preserved():
    books = [record('Book', rid) for rid in ('993avdq3up', '9954l761oh')]
    assert all(not b.get('merged_into') for b in books)
    assert books[0]['work_id'] != books[1]['work_id']


def test_nine_chapters_keeps_digitization_and_physical_description():
    book = record('Book', '988g4v5jid')
    assert '988g481zb6' in book['merged_from']
    assert book['metadata']['npm_acckey']
    assert any('image' in resource.get('types', []) for resource in book['resources'])
    assert book['physical_description']['condition'] == '存卷一－五'
    assert book['base_edition']
