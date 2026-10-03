"""Regression: curation/meta-home.json（元数据首页策展，overview#324／#322）。
所有 id 必须存在；lineage_picks 必须是确有谱系的 Work（version_graph 启用且有分组）。"""
import glob
import json
import pathlib

ROOT = pathlib.Path(__file__).parent.parent
HOME = json.loads((ROOT / "curation" / "meta-home.json").read_text(encoding="utf-8"))


def _work(wid):
    hits = glob.glob(str(ROOT / "Work" / "*" / "*" / "*" / f"{wid}-*.json"))
    assert len(hits) == 1, f"Work {wid} 不存在"
    return json.loads(pathlib.Path(hits[0]).read_text(encoding="utf-8"))


def test_schema():
    assert HOME["schema"] == "meta-home/1"


def test_collection_ids_exist():
    cols = json.loads((ROOT / "index" / "collections.json").read_text(encoding="utf-8"))
    ids = [i for g in HOME["collection_groups"] for i in g["items"]]
    assert ids and len(ids) == len(set(ids))
    assert [i for i in ids if i not in cols] == []


def test_bibliographer_ids_exist():
    ents = {}
    for f in glob.glob(str(ROOT / "index" / "entities" / "*.json")):
        ents.update(json.loads(pathlib.Path(f).read_text(encoding="utf-8")))
    ids = HOME["bibliographers"]
    assert ids and len(ids) == len(set(ids))
    assert [i for i in ids if i not in ents] == []


def test_lineage_picks_have_lineage():
    ids = HOME["lineage_picks"]
    assert ids and len(ids) == len(set(ids))
    for wid in ids:
        vg = _work(wid).get("version_graph") or {}
        assert vg.get("enabled") and vg.get("groups"), f"{wid} 无谱系"
