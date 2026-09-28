"""S2b classify() 回归（overview#217，据 #214 体检确认之 pipeline bug；overview#233 追加）：

覆盖两处规则性修正：
  1. 「寫刻本／寫刊本」曾因裸「寫」判准先於「刻本」命中而誤判抄本，今須判刻本。
  2. 「朱墨鈔本／朱墨寫本」（雙色手抄，非刷印技法）曾因裸「朱墨」判准誤判套印本，今須判抄本，
     真正的套印本仍須含「套印／三色套／五色套」字樣方判。
  3.（overview#233）「排印」技法兩可，須靠紀年助判：光緒／宣統以後、或紀年不詳但明寫「民國」者，
     歸鉛印本；光緒之前紀年、或無朝代紀年線索之裸「排印」，不判（留空待人核）。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '.claude', 'qa', 's2'))

from backfill_edition_type import classify


def test_xiekeben_classifies_as_kigravure():
    assert classify('清康熙三十二年林佶寫刻本') == '刻本'


def test_xiekanben_classifies_as_kigravure():
    assert classify('明寫刊本') == '刻本'


def test_bare_xie_still_classifies_as_manuscript():
    assert classify('明萬曆間某氏寫本') == '抄本'


def test_zhumo_chaoben_classifies_as_manuscript_not_taoyin():
    assert classify('清同治間內府朱墨寫本') == '抄本'
    assert classify('明朱墨鈔本') == '抄本'


def test_explicit_taoyin_still_classifies_as_taoyin():
    assert classify('清乾隆間顏氏萬卷樓刊朱墨套印本') == '套印本'
    assert classify('三色套印本') == '套印本'


def test_juzhen_still_classifies_as_movable_type():
    assert classify('武英殿聚珍版') == '活字本'


def test_paiyin_with_qing_late_or_republic_era_classifies_as_lead_print():
    assert classify('民國二十三年排印本') == '鉛印本'
    assert classify('清宣統庚戌(二年)排印本') == '鉛印本'
    assert classify('民國排印本') == '鉛印本'
    assert classify('清光緒三十四年農工商部印刷科排印本') == '鉛印本'


def test_paiyin_without_era_marker_stays_undetermined():
    assert classify('排印本') is None
    assert classify('清排印本') is None


def test_qianyin_and_qianzi_still_unconditional():
    assert classify('鉛印本') == '鉛印本'
    assert classify('鉛字排印本') == '鉛印本'
