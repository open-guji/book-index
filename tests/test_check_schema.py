"""schema/check_schema.py：自带 JSON Schema 子集校验器与各运行模式的最小样例（overview#496）。"""
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent.parent
SCRIPT = ROOT / "schema" / "check_schema.py"
sys.path.insert(0, str(ROOT / "schema"))
import check_schema  # noqa: E402


def errs(inst, schema):
    out = []
    check_schema.Validator(check_schema.JSON_DIR).validate(inst, schema, "common.schema.json", "", out)
    return [(code, path) for lv, code, path, _ in out if lv == "ERROR"]


def run(*args):
    p = subprocess.run([sys.executable, str(SCRIPT), *args], capture_output=True, text=True)
    return p.returncode, p.stdout + p.stderr


def write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


# ② minProperties／maxProperties
def test_min_max_properties():
    assert errs({}, {"type": "object", "minProperties": 1}) == [("minProperties", "")]
    assert errs({"a": 1}, {"type": "object", "minProperties": 1}) == []
    assert errs({"a": 1, "b": 2}, {"type": "object", "maxProperties": 1}) == [("maxProperties", "")]


# ③ const／enum 按 JSON 语义：布尔与数字不相等
def test_const_bool_int_distinct():
    assert errs(True, {"const": 1}) == [("const", "")]
    assert errs(1, {"const": True}) == [("const", "")]
    assert errs(1, {"const": 1}) == []
    assert errs(True, {"const": True}) == []
    assert errs(True, {"enum": [1, 2]}) == [("enum", "")]
    assert errs(0, {"enum": [False]}) == [("enum", "")]
    assert errs(1.0, {"const": 1}) == []


# ④ 记录 type 为列表／对象时报错而不崩
def test_record_type_malformed_no_crash(tmp_path):
    write(tmp_path / "Work/a/b/c/abc-x.json", {"id": "abc", "type": ["work"], "schema_version": 1, "title": "x"})
    write(tmp_path / "Work/a/b/d/abd-y.json", {"id": "abd", "type": {"t": "work"}, "schema_version": 1, "title": "y"})
    code, out = run("--root", str(tmp_path), "--draft")
    assert code == 1
    assert "Traceback" not in out
    assert "not-a-record" in out


# ④ schemes.json 里 id／tree 不是字符串时报错而不崩
def test_scheme_malformed_no_crash(tmp_path):
    write(tmp_path / "classification/schemes.json",
          [{"id": 123, "name": "x", "primary": True, "exclusive": True, "tree": []}])
    code, out = run("--root", str(tmp_path), "--draft")
    assert code == 1
    assert "Traceback" not in out
    assert "schemes" in out


# ⑤ 未登记的分类目录也查；已登记而缺 tree 报错
def test_classification_unregistered_and_missing_tree(tmp_path):
    write(tmp_path / "classification/schemes.json",
          [{"id": "zm", "name": "甲", "primary": True, "exclusive": True, "tree": "zm/tree.json"}])
    (tmp_path / "classification/zm/members").mkdir(parents=True)
    write(tmp_path / "classification/other/members/n1.json", {"node": "n1", "members": [["b", "x"], ["a", "x"]]})
    code, out = run("--root", str(tmp_path), "--draft")
    assert code == 1
    assert "missing-tree" in out
    assert "unregistered-scheme" in out
    assert "order" in out          # 未登记目录里的成员档照样逐项校验


# ① --build 另按记录类型校验源字段
def test_build_checks_record_schema(tmp_path):
    sample = ROOT / "build" / "contract-sample" / "entry"
    work = next(p for p in sorted(sample.glob("*.json"))
                if json.loads(p.read_text(encoding="utf-8")).get("type") == "work")
    (tmp_path / "entry").mkdir()
    shutil.copy(work, tmp_path / "entry" / work.name)
    code, out = run("--build", str(tmp_path))
    assert code == 0, out
    rec = json.loads(work.read_text(encoding="utf-8"))
    rec["title"] = 123                     # 源字段形状错
    write(tmp_path / "entry" / work.name, rec)
    code, out = run("--build", str(tmp_path))
    assert code == 1
    assert "title" in out


# x-legacy: "keep" 报 INFO（legacy-keep），不计入 WARN；x-legacy: true 仍报 WARN
def test_legacy_keep_is_info():
    v = check_schema.Validator(check_schema.JSON_DIR)
    out = []
    v.validate({"a": 1, "b": 2}, {"type": "object", "properties": {"a": {"x-legacy": "keep"}, "b": {"x-legacy": True}}},
               "common.schema.json", "", out)
    assert sorted((lv, code, path) for lv, code, path, _ in out) == [("INFO", "legacy-keep", "a"), ("WARN", "legacy", "b")]
    out = []
    v.validate({"text": "原文"}, {"$ref": "common.schema.json#/$defs/IndexEntry"}, "common.schema.json", "", out)
    assert ("INFO", "legacy-keep", "text") in [(lv, code, path) for lv, code, path, _ in out]
    assert not [x for x in out if x[0] == "WARN" and x[2] == "text"]


# S3-A8：语义 WARN
def test_semantic_warns():
    cs = _load() if "_load" in globals() else None
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("cs", os.path.join(os.path.dirname(__file__), "..", "schema", "check_schema.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    rec = {"period": "song", "dynasty": "宋", "resources": [{"group": "g"}], "indexed_by": [{"source": "x", "title_info": "t"}]}
    codes = sorted(c for _, c, _, _ in m.semantic_warns("work", rec))
    # 「缺依据」与著录条缺 title_info／summary 不再统计（第 13 组）
    assert codes == ["group-undefined", "single-member-group"]


def test_entity_stage4_legacy_forms_rejected():
    """S4 阶段 4（2026-11-03）：Entity 里已清零的旧写法不再合法：顶层 start／end／dates_basis、updated_at、
    官署的 dynasty／period 及 basis、null 占位、空 external_ids、缺 type 的别名。"""
    sample = ROOT / "Entity/j/n/s"
    files = sorted(sample.glob("hixi5dv8mjns-*.json"))
    if not files:   # 稀疏检出不含 Entity 时跳过
        import pytest
        pytest.skip("no Entity checkout")
    base = json.loads(files[0].read_text(encoding="utf-8"))   # 官署具体条，起讫在 dates
    schema = json.loads((check_schema.JSON_DIR / "entity.schema.json").read_text(encoding="utf-8")) \
        if hasattr(check_schema.JSON_DIR, "read_text") else json.load(open(check_schema.JSON_DIR + "/entity.schema.json", encoding="utf-8"))

    def bad(**kw):
        r = dict(base)
        r.update(kw)
        out = []
        check_schema.Validator(check_schema.JSON_DIR).validate(r, schema, "entity.schema.json", "", out)
        return [x for x in out if x[0] == "ERROR"]
    assert not bad()
    assert bad(start=1)                       # 顶层 start 已不是合法键
    assert bad(end=1)
    assert bad(dates_basis="x")
    assert bad(updated_at="2026-11-03T00:00:00+00:00")
    assert bad(dynasty="清")                  # 官署不写旧式朝代字符串
    assert bad(period_basis="x")
    assert bad(external_ids={})
    assert bad(alt_names=[{"name": "x"}])     # 别名缺 type
    assert bad(alt_names=["x"])               # 裸字符串别名


def test_book_index_summary_allowed():
    """第 13 组：Book 可写该版本自己的著录 summary，Work 缺 summary 也不报。"""
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("cs2", os.path.join(os.path.dirname(__file__), "..", "schema", "check_schema.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    ok = {"indexed_by": [{"source": "x", "title_info": "t"}]}
    assert m.semantic_warns("book", ok) == []
    assert m.semantic_warns("work", ok) == []
    assert m.semantic_warns("book", {"indexed_by": [{"source": "x", "title_info": "t", "summary": "s"}]}) == []


def test_entity_alt_type_legacy_values_closed():
    """2026-11-03：alt_names.type 的旧值清零后，枚举含 名／本名／小字／法號，其余旧写法（如 著錄形）不再合法。"""
    sch = json.load(open(check_schema.JSON_DIR + "/entity.schema.json", encoding="utf-8")) \
        if isinstance(check_schema.JSON_DIR, str) else json.loads((check_schema.JSON_DIR / "entity.schema.json").read_text(encoding="utf-8"))
    t = sch["$defs"]["AltName"]["properties"]["type"]
    assert {"名", "本名", "小字", "法號"} <= set(t["enum"])
    assert "x-legacy-values" not in t
    assert "著錄形" not in t["enum"]


def test_resource_warns():
    import importlib.util, os
    spec = importlib.util.spec_from_file_location("cs3", os.path.join(os.path.dirname(__file__), "..", "schema", "check_schema.py"))
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    rec = {"resource_groups": {"g": {"label": "x"}},
           "resources": [{"id": "nlc", "name": "n", "short_name": "國圖", "group": "g", "group_role": "origin"},
                         {"id": "nlc", "name": "n", "short_name": "別名"}]}
    codes = sorted(c for _, c, _, _ in m.semantic_warns("work", rec))
    assert codes == ["short-name-redundant", "single-member-group"]
