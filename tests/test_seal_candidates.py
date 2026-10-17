"""qa/seal_candidates.py：旧 seals 字串 → 印文／色／形解析、规范化、匹配状态（GUJI-542 P3）。"""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / '.claude' / 'qa'))
import seal_candidates as SC  # noqa: E402

SEALS = {'s1': (SC.norm('乾隆御覽之寶'), ''), 's2': (SC.norm('金澤文庫'), '長方'),
         's3': (SC.norm('同文'), ''), 's4': (SC.norm('同文'), '')}


def test_parse_quoted_and_bare():
    assert SC.parse('「乾隆御覽之寶」朱橢') == ([('乾隆御覽之寶', '朱', '橢')], None)
    assert SC.parse('國立北平圖書館收藏朱方') == ([('國立北平圖書館收藏', '朱', '方')], None)
    assert SC.parse('「八徵耄念之寶」大朱方') == ([('八徵耄念之寶', '大朱', '方')], None)
    assert SC.parse('「 天祿繼鑑」白方')[0] == [('天祿繼鑑', '白', '方')]
    assert SC.parse('朱方「雨農藏書」')[0] == [('雨農藏書', '朱', '方')]
    assert SC.parse('「江安傅增湘沅叔珍藏」')[0] == [('江安傅增湘沅叔珍藏', '', '')]


def test_parse_multi_and_location_prefix():
    items, why = SC.parse('「星吾海外訪得祕笈」朱方。每冊首頁：「勝鹿文庫」朱長')
    assert why is None and items == [('星吾海外訪得祕笈', '朱', '方'), ('勝鹿文庫', '朱', '長')]


def test_parse_failures_not_guessed():
    assert SC.parse('「學部圖書之印」滿漢文大朱方') == ([], '滿漢合璧')
    assert SC.parse('「宗密」圖案印') == ([], '圖案／肖形印')
    assert SC.parse('「雲伯」朱白相間方記')[1] == '朱白相間'
    assert SC.parse('「居嶙之印」？白方')[1] == '带「？」存疑'
    assert SC.parse('「國子監崇文閣官書')[1] == '引号不成对'


def test_norm_small_variant_table():
    assert SC.norm('星吾海外訪得祕笈') == SC.norm('星吾海外訪得秘笈')
    assert SC.norm('天祿繼鑑') == SC.norm('天祿繼鑒')
    assert SC.norm('  金 澤文庫') == '金澤文庫'


def test_match_states():
    assert SC.match('乾隆御覽之寶', '橢', SEALS) == ('命中', ['s1'], '條上無形，形未核')
    assert SC.match('金澤文庫', '長方', SEALS)[0] == '命中'
    assert SC.match('金澤文庫', '圓', SEALS)[0] == '歧義'          # 形冲突不自选
    assert SC.match('同文', '方', SEALS)[0] == '歧義'              # 同文多条不自选
    assert SC.match('不存在', '方', SEALS) == ('無條', [], '')


def test_run_rows_conserved_and_frequency():
    books = [('b1', {'provenance': [{'institution': 'X', 'seals': ['「乾隆御覽之寶」朱橢', '「甲」朱方。「乙」白方', '「學部圖書之印」滿漢文大朱方']}]}),
             ('b2', {'provenance': [{'institution': 'Y', 'seals': ['「甲」朱方', '甲朱圓']}, {'seals': []}]})]
    ents = {'s1': {'subtype': 'seal', 'seal_text': '乾隆御覽之寶'}, 's9': {'subtype': 'seal', 'seal_text': '甲', 'merged_into': 's1'}}
    rows, freq, st = SC.run(books, ents)
    assert len(rows) == 5                                           # 行数＝字串数
    assert [r[5] for r in rows] == ['命中', '多印', '解析失敗', '無條', '無條']
    top = {r[0]: r for r in freq}
    assert top['甲'][1] == 3 and top['甲'][2] == 2 and '朱方×2' in top['甲'][3] and top['甲'][6] == ''   # 墓碑条不算已有
    assert top['乾隆御覽之寶'][6] == 's1'
    assert st['fails']['滿漢合璧'] == 1
