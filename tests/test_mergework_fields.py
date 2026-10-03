"""Regression: mergework.py 补搬迁被并条独有字段（D1 #3）。

坑：原七件善后只管 indexed_by/books/反边/merged_in，被并条独有的
contained_in/period/resources 等其余字段随刪档一并静默丢失。
只测纯函数 plan_scalar_merge（无磁盘 I/O）——mergework.py 另外还引入
jio.py/backrefs.py 各自独立的 ROOT（同 D1 #2 的坑，见另一份 pit 单），
沙盒跑 --apply 端到端要三处 ROOT 都 patch 才安全，这里不需要动真文件，
故只验纯函数，绕开这颗雷。
"""
import sys, pathlib

sys.path.insert(0, str(pathlib.Path(__file__).parent.parent / ".claude/qa"))
import mergework


def test_moves_field_keeper_lacks():
    keeper = {"id": "K", "title": "keeper本"}
    dps = [("D1", "/x", {"id": "D1", "title": "drop本", "period": "song"}, None)]
    moved, conflicts, new_values = mergework.plan_scalar_merge(keeper, dps)
    assert new_values.get("period") == "song"
    assert ("D1", "period", "song") in moved
    assert conflicts == []


def test_conflicting_field_not_moved_but_reported():
    keeper = {"id": "K", "title": "keeper本", "period": "yuan"}
    dps = [("D1", "/x", {"id": "D1", "title": "drop本", "period": "song"}, None)]
    moved, conflicts, new_values = mergework.plan_scalar_merge(keeper, dps)
    assert "period" not in new_values, "冲突字段不许搬"
    assert conflicts == [("D1", "period", "yuan", "song")]
    assert moved == []


def test_same_value_neither_moved_nor_conflict():
    keeper = {"id": "K", "period": "song"}
    dps = [("D1", "/x", {"id": "D1", "period": "song"}, None)]
    moved, conflicts, new_values = mergework.plan_scalar_merge(keeper, dps)
    assert moved == [] and conflicts == [] and new_values == {}


def test_list_fields_union_dedup():
    keeper = {"id": "K", "contained_in": ["C1"]}
    dps = [("D1", "/x", {"id": "D1", "contained_in": ["C1", "C2"]}, None)]
    moved, conflicts, new_values = mergework.plan_scalar_merge(keeper, dps)
    assert new_values["contained_in"] == ["C1", "C2"]
    assert conflicts == []


def test_skip_fields_never_auto_merged():
    keeper = {"id": "K", "authors": [{"name": "甲"}], "description": {"text": "旧"}}
    dps = [("D1", "/x", {
        "id": "D1", "authors": [{"name": "乙"}], "description": {"text": "新"},
        "related_works": [{"id": "X", "relation": "注"}],
    }, None)]
    moved, conflicts, new_values = mergework.plan_scalar_merge(keeper, dps)
    assert new_values == {}, "authors/description/related_works 不由本函式自動搬"


def test_idempotent_second_pass_on_merged_keeper_is_noop():
    """幂等：把第一次算出的 new_values 真的写回 keeper 后，同一批 drop 再算一次，
    须 moved/conflicts 均为空（无论是重跑还是崩溃后重试，结果都稳定）。"""
    keeper = {"id": "K", "title": "keeper本"}
    drop_record = {"id": "D1", "title": "drop本", "period": "song",
                    "contained_in": ["C1", "C2"]}
    dps = [("D1", "/x", drop_record, None)]

    moved1, conflicts1, new_values1 = mergework.plan_scalar_merge(keeper, dps)
    assert moved1 and not conflicts1
    for k, v in new_values1.items():
        keeper[k] = v

    moved2, conflicts2, new_values2 = mergework.plan_scalar_merge(keeper, dps)
    assert moved2 == [] and conflicts2 == [] and new_values2 == {}, \
        "keeper 已含该值后重跑，须是稳定不动点"


if __name__ == "__main__":
    test_moves_field_keeper_lacks()
    test_conflicting_field_not_moved_but_reported()
    test_same_value_neither_moved_nor_conflict()
    test_list_fields_union_dedup()
    test_skip_fields_never_auto_merged()
    test_idempotent_second_pass_on_merged_keeper_is_noop()
    print("PASS")
