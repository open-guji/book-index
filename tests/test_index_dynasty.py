"""index 的 dynasty（撰人朝代）取法：第一个有朝代的作者优先，顶层兜底（overview#496 §六-1）。
与 bim entry_extractor.build_index_entry、ui storage.ts 同；卡片 dyn（成书朝代，顶层优先）另是一回事。"""
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "build"))
from build_derived import index_entry, first_dynasty  # noqa: E402


def _dyn(d):
    return index_entry(d, "Work", "Work/x/1.json").get("dynasty")


def test_first_author_with_dynasty_not_only_first():
    d = {"id": "w1", "title": "X", "authors": [{"name": "甲", "dynasty": ""}, {"name": "乙", "dynasty": "清"}]}
    assert _dyn(d) == "清"


def test_author_dynasty_wins_over_top_level():
    d = {"id": "w1", "title": "X", "dynasty": "明", "authors": [{"name": "甲", "dynasty": "元末明初"}]}
    assert _dyn(d) == "元末明初"
    # 卡片取成书朝代，顶层优先——两字段有意不同
    assert first_dynasty(d) == "明"


def test_top_level_fallback_when_no_author_dynasty():
    assert _dyn({"id": "w1", "title": "X", "authors": [], "dynasty": "戰國"}) == "戰國"


def test_absent_when_neither():
    assert _dyn({"id": "w1", "title": "X", "authors": [{"name": "甲"}]}) is None
