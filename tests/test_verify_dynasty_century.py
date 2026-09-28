"""verify.py 新增報告項 dynasty_century_mismatch() 回归（overview#217，据 #214 check5）：
只报数不入 FAIL 的粗筛监控，覆盖尹淳／毛爽两例新发现，以及词表外朝代／无年份/常态皆不算。
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '.claude', 'qa'))

import verify


def test_no_dynasty_or_no_years_passes():
    assert verify.dynasty_century_mismatch({}) is False
    assert verify.dynasty_century_mismatch({'dynasty': '明'}) is False


def test_unknown_dynasty_not_in_table_passes():
    assert verify.dynasty_century_mismatch({'dynasty': '不知何朝', 'birth_year': 1}) is False


def test_within_margin_passes():
    # 明 1368-1644，±40 容差；1650 在容差内
    assert verify.dynasty_century_mismatch({'dynasty': '明', 'death_year': 1650}) is False


def test_yinchun_flagged():
    """尹淳：dynasty=明，但生卒 1680-1741 纯为清代纪年（体检新发现①）。"""
    d = {'dynasty': '明', 'birth_year': 1680, 'death_year': 1741}
    assert verify.dynasty_century_mismatch(d) is True


def test_maoshuang_flagged():
    """毛爽：dynasty=隋，但卒年 705（隋亡于618，体检新发现②）。"""
    d = {'dynasty': '隋', 'death_year': 705}
    assert verify.dynasty_century_mismatch(d) is True


def test_checks_dates_subobject_too():
    d = {'dynasty': '明', 'dates': {'birth': 1680, 'death': 1741}}
    assert verify.dynasty_century_mismatch(d) is True
