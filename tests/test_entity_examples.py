"""schema/entity/*.md 〈真实示例〉小节与「按类型找示例」入口表里的路径必须真实存在。

示例行形如 | 名 `id` | [Entity/…json](相对路径) | [index/entities/N.json](相对路径) | 说明 |：
源档存在且 subtype 与所在文档一致，id 出现在所指 index 分片里；入口表的链接必须能解析到文件。
"""
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ENTITY_DIR = os.path.join(ROOT, "schema", "entity")
SUBTYPES = ["people", "collective", "dynasty", "reign", "office", "place", "seal", "publisher"]
LINK = re.compile(r"\]\(([^)#]+)(?:#[^)]*)?\)")
ROW = re.compile(r"^\| [^|]*`([0-9a-z]+)` \| \[([^\]]+)\]\(([^)]+)\) \| \[([^\]]+)\]\(([^)]+)\) \|")


def _read(path):
    with open(path, encoding="utf-8") as f:
        return f.read()


def _section(text):
    m = re.search(r"^## 真实示例\n(.*?)(?=^#|\Z)", text, flags=re.S | re.M)
    return m.group(1) if m else None


def test_each_subtype_doc_has_verified_examples():
    for sub in SUBTYPES:
        path = os.path.join(ENTITY_DIR, sub + ".md")
        sec = _section(_read(path))
        assert sec is not None, "%s.md 缺〈真实示例〉小节" % sub
        rows = [ROW.match(line) for line in sec.splitlines() if line.startswith("| ") and "`" in line]
        rows = [r for r in rows if r]
        assert len(rows) >= 2, "%s.md 示例少于 2 条" % sub
        for m in rows:
            eid, epath, elink, ipath, ilink = m.groups()
            assert epath.startswith("Entity/"), epath
            full = os.path.normpath(os.path.join(ENTITY_DIR, elink))
            assert full == os.path.join(ROOT, epath), (sub, elink)
            assert os.path.isfile(full), "示例源档不存在：%s" % epath
            ent = json.loads(_read(full))
            assert ent["id"] == eid, (epath, eid)
            assert ent["subtype"] == sub, "%s 的 subtype 是 %s，不是 %s" % (epath, ent["subtype"], sub)
            ifull = os.path.normpath(os.path.join(ENTITY_DIR, ilink))
            assert ifull == os.path.join(ROOT, ipath), (sub, ilink)
            assert os.path.isfile(ifull), "示例 index 分片不存在：%s" % ipath
            assert eid in json.loads(_read(ifull)), "%s 不在 %s 里" % (eid, ipath)


def test_entry_tables_resolve():
    files = [
        os.path.join(ROOT, "schema", "entity.md"),
        os.path.join(ROOT, "schema", "README.md"),
        os.path.join(ENTITY_DIR, "_common.md"),
    ]
    for path in files:
        text = _read(path)
        m = re.search(r"^#+ 按类型找 ?(?:Entity )?示例\n(.*?)(?=^#|^---|\Z)", text, flags=re.S | re.M)
        assert m, "%s 缺「按类型找示例」入口表" % path
        links = LINK.findall(m.group(1))
        assert len(links) >= 2 * len(SUBTYPES), path
        for link in links:
            target = os.path.normpath(os.path.join(os.path.dirname(path), link))
            assert os.path.isfile(target), "%s 里的链接不存在：%s" % (path, link)
