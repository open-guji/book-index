"""Data regressions for the 2026-10-21 duplicate audit (not identity heuristics)."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def record(family, rid, allow_purged=False):
    paths = list((ROOT / family / Path(*rid[-3:])).glob(rid + '-*.json'))
    if allow_purged and not paths:
        return None   # 墓碑已被定期清理（.claude/qa/purge-tombstones），旧 id 记在并条账 ledger 里
    assert len(paths) == 1, rid
    return json.loads(paths[0].read_text(encoding='utf-8'))


_LEDGER = None


def ledger_pairs():
    """并条账 {旧号: {留存号…}}：.claude/qa/purge-tombstones/ledger/*.tsv 前两列（history 的 keeper、purge 的 merged_into）。"""
    global _LEDGER
    if _LEDGER is None:
        _LEDGER = {}
        for f in (ROOT / '.claude/qa/purge-tombstones/ledger').glob('*.tsv'):
            lines = f.read_text(encoding='utf-8').splitlines()
            head = lines[0].split('\t')
            if 'keeper' not in head and 'merged_into' not in head:
                continue   # 如 draft-retarget-*.tsv：草稿库墓碑改指，不是正式库并条
            col = head.index('keeper') if 'keeper' in head else head.index('merged_into')
            for line in lines[1:]:
                row = line.split('\t')
                _LEDGER.setdefault(row[0], set()).add(row[col])
    return _LEDGER


def test_merge_ids_remain_resolvable_and_keep_history():
    ledger = json.loads((ROOT / '.claude/qa/reports/duplicate-audit-2026-10-21/merges.json').read_text())
    families = {'people': 'Entity', 'work': 'Work', 'book': 'Book'}
    for merge in ledger['merges']:
        family = families[merge['type']]
        keeper = record(family, merge['keeper'], allow_purged=True)
        if keeper is None:   # keeper 后来也被并、墓碑也清了：历史在后来的留存条里
            continue
        if keeper.get('merged_into'):
            continue   # keeper 后来被并，墓碑还没清
        for rid in merge['losers']:
            tomb = record(family, rid, allow_purged=True)
            if tomb is not None:   # 墓碑还在就仍须合规；已清理的不查
                assert tomb['merged_into'] == keeper['id']
                assert not any(key in tomb for key in ('authors', 'resources', 'indexed_by', 'contained_in'))
            else:                  # 墓碑清了：并条账里须记着旧号
                assert rid in ledger_pairs(), rid


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
    # 11-02 口径：查不到佐证就新建人物；现挂清代新建实体，不得挂到明代同名的两条
    assert zhang and all(a['dynasty'] == '清' and a.get('entity_id') not in ('hixhd2h9bnuk', 'hixhd2h9bcy1') for a in zhang)
    ent = record('Entity', zhang[0]['entity_id']) if zhang[0].get('entity_id') else None
    assert ent is None or ent.get('dynasty') == '清'
    assert work['period'] == 'qing'
    gone = record('Work', 'd59fy2deo4jk', allow_purged=True)
    assert gone is None or gone['merged_into'] == work['id']


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
    assert book['id'] in ledger_pairs()['988g481zb6']
    assert book['metadata']['npm_acckey']
    assert any('image' in resource.get('types', []) for resource in book['resources'])
    assert book['physical_description']['condition'] == '存卷一－五'
    assert book['base_edition']
