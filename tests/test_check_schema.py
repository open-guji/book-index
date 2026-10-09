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
