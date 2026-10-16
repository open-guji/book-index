"""黄金样例对拍：build_derived.index_entry 对官方样例（overview#606 B6）。

`tests/golden/entries.json` 是官方副本；bim（Python＋ui）、web `derived.mjs` 各拷一份并写来源 sha，
四处提取逻辑读同一批向量。本测试管 build_derived 一侧；改坏任一侧，对应测试立刻红。
"""
import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / 'build'))
import build_derived as BD  # noqa: E402

CASES = json.loads((ROOT / 'tests' / 'golden' / 'entries.json').read_text(encoding='utf-8'))


# 已知口径差异（对拍首跑暴露，overview#606）：strict xfail，读法删掉那一步合并时会变红，逼着把名字从这里删。
KNOWN_RED_UNTIL = {}  # 2026-10-16 清零（GUJI-13 / Eric）：_res_flags 旧单值分支与源档 has_collated 透传均已删


def _params():
    return [pytest.param(c, id=c['name'],
                         marks=[pytest.mark.xfail(strict=True, reason=KNOWN_RED_UNTIL[c['name']])]
                         if c['name'] in KNOWN_RED_UNTIL else [])
            for c in CASES]


@pytest.mark.parametrize('case', _params())
def test_index_entry_matches_golden(case):
    expect = case['expect_index_entry']
    # promoted_to 在 build_derived 里取自 promotions.json（源记录不带），测试里用墓碑的 _promoted_to 代入
    got = BD.index_entry(case['record'], case['type'], expect['path'],
                         promoted_to=case['record'].get('_promoted_to'))
    assert got == expect


def test_golden_shape():
    assert any(c['negative'] for c in CASES) and any(not c['negative'] for c in CASES)
    assert len({c['name'] for c in CASES}) == len(CASES)
    assert KNOWN_RED_UNTIL.keys() <= {c['name'] for c in CASES}
