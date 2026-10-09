#!/usr/bin/env python3
"""按 schema/json/ 的 JSON Schema（2020-12）校验 book-index／book-index-draft 的记录。

只用 Python 标准库：自带一个够用的 2020-12 子集校验器（type、enum、const、required、
properties、patternProperties、additionalProperties、items、prefixItems、minItems、
maxItems、minLength、pattern、minimum、maximum、$ref、$defs、allOf、anyOf、oneOf、
not、if／then／else）。另认两个本库扩展关键字：

  x-legacy: true           旧字段或旧写法（暂留）：实例落在这个子 schema 上时报 WARN，不报 ERROR
  x-legacy-values: [...]   enum 之外、但属已知旧写法的值：出现时报 WARN

用法：
  python3 schema/check_schema.py                       # 校验本仓全部记录（正式库口径）
  python3 schema/check_schema.py --root ../book-index-draft --draft
  git diff --name-only origin/main... | python3 schema/check_schema.py --paths -
  python3 schema/check_schema.py --json report.json    # 另写机器可读报告（供吻合度报告）
  python3 schema/check_schema.py --build _build        # 校验 build 产物（entry/ 与 index/，见 derived.md）

退出码：有 ERROR 为 1，否则 0。格式说明见 schema/README.md。
"""
import argparse
import collections
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
JSON_DIR = os.path.join(HERE, "json")
TYPES = ("Work", "Book", "Collection", "Entity")
SCHEMA_OF = {"work": "work.schema.json", "book": "book.schema.json",
             "collection": "collection.schema.json", "entity": "entity.schema.json"}
SKIP_DIRS = {"collated_edition", "fragments"}


# ---------------------------------------------------------------- 校验器

class Validator:
    def __init__(self, json_dir):
        self.json_dir = json_dir
        self.docs = {}

    def doc(self, name):
        if name not in self.docs:
            with open(os.path.join(self.json_dir, name), encoding="utf-8") as f:
                self.docs[name] = json.load(f)
        return self.docs[name]

    def resolve(self, ref, base):
        """`a.schema.json#/$defs/X` 或 `#/$defs/X`；返回 (schema, 所在文件)。"""
        fname, _, frag = ref.partition("#")
        fname = fname or base
        node = self.doc(fname)
        for part in [p for p in frag.split("/") if p]:
            node = node[part.replace("~1", "/").replace("~0", "~")]
        return node, fname

    def validate(self, inst, schema, base, path, out):
        """out: list of (level, code, path, message)。返回是否通过（WARN 不算失败）。"""
        if schema is True or schema == {}:
            return True
        if schema is False:
            out.append(("ERROR", "false", path, "不允许出现"))
            return False
        ok = True
        if schema.get("x-legacy"):
            out.append(("WARN", "legacy", path, "旧字段或旧写法（暂留，见 legacy.md）"))
        if "$ref" in schema:
            sub, fbase = self.resolve(schema["$ref"], base)
            ok &= self.validate(inst, sub, fbase, path, out)
        t = schema.get("type")
        if t is not None and not type_ok(inst, t):
            out.append(("ERROR", "type", path, f"类型应为 {t}，实为 {jtype(inst)}"))
            return False
        if "const" in schema and inst != schema["const"]:
            out.append(("ERROR", "const", path, f"应为 {schema['const']!r}，实为 {short(inst)}"))
            ok = False
        if "enum" in schema and inst not in schema["enum"]:
            if inst in schema.get("x-legacy-values", []):
                out.append(("WARN", "legacy-value", path, f"旧写法 {short(inst)}"))
            else:
                out.append(("ERROR", "enum", path, f"值 {short(inst)} 不在枚举内"))
                ok = False
        if isinstance(inst, str):
            if "minLength" in schema and len(inst) < schema["minLength"]:
                out.append(("ERROR", "minLength", path, "不得为空"))
                ok = False
            if "pattern" in schema and not re.search(schema["pattern"], inst):
                out.append(("ERROR", "pattern", path, f"{short(inst)} 不合格式 {schema['pattern']}"))
                ok = False
        if isinstance(inst, (int, float)) and not isinstance(inst, bool):
            if "minimum" in schema and inst < schema["minimum"]:
                out.append(("ERROR", "minimum", path, f"{inst} 小于 {schema['minimum']}"))
                ok = False
            if "maximum" in schema and inst > schema["maximum"]:
                out.append(("ERROR", "maximum", path, f"{inst} 大于 {schema['maximum']}"))
                ok = False
        if isinstance(inst, list):
            if "minItems" in schema and len(inst) < schema["minItems"]:
                out.append(("ERROR", "minItems", path, f"至少 {schema['minItems']} 项"))
                ok = False
            if "maxItems" in schema and len(inst) > schema["maxItems"]:
                out.append(("ERROR", "maxItems", path, f"至多 {schema['maxItems']} 项"))
                ok = False
            pre = schema.get("prefixItems", [])
            for i, x in enumerate(inst):
                if i < len(pre):
                    ok &= self.validate(x, pre[i], base, f"{path}[{i}]", out)
                elif "items" in schema:
                    ok &= self.validate(x, schema["items"], base, f"{path}[]", out)
        if isinstance(inst, dict):
            for k in schema.get("required", []):
                if k not in inst:
                    out.append(("ERROR", "required", f"{path}.{k}" if path else k, "必填而缺"))
                    ok = False
            props = schema.get("properties", {})
            pats = schema.get("patternProperties", {})
            addl = schema.get("additionalProperties", True)
            for k, v in inst.items():
                kp = f"{path}.{k}" if path else k
                matched = False
                if k in props:
                    matched = True
                    ok &= self.validate(v, props[k], base, kp, out)
                for pat, ps in pats.items():
                    if re.search(pat, k):
                        matched = True
                        ok &= self.validate(v, ps, base, kp, out)
                if not matched:
                    if addl is False:
                        out.append(("ERROR", "unknown-field", kp, "格式文档里没有这个键"))
                        ok = False
                    elif isinstance(addl, dict):
                        ok &= self.validate(v, addl, base, kp, out)
        for sub in schema.get("allOf", []):
            ok &= self.validate(inst, sub, base, path, out)
        if "anyOf" in schema:
            ok &= self.first_match(inst, schema["anyOf"], base, path, out, "anyOf", any_ok=True)
        if "oneOf" in schema:
            ok &= self.first_match(inst, schema["oneOf"], base, path, out, "oneOf", any_ok=False)
        if "not" in schema:
            if self.validate(inst, schema["not"], base, path, []):
                out.append(("ERROR", "not", path, schema.get("x-not-message", "不允许的形状")))
                ok = False
        if "if" in schema:
            branch = "then" if self.validate(inst, schema["if"], base, path, []) else "else"
            if branch in schema:
                ok &= self.validate(inst, schema[branch], base, path, out)
        return bool(ok)

    def first_match(self, inst, subs, base, path, out, kw, any_ok):
        results = []
        for sub in subs:
            o = []
            results.append((self.validate(inst, sub, base, path, o), o))
        passing = [o for good, o in results if good]
        if passing and (any_ok or len(passing) == 1):
            out.extend(passing[0])   # 带出该分支里的 WARN
            return True
        if not passing:
            # 报最接近的分支（错最少者），免得一条形状错报出所有分支
            best = min((o for _, o in results), key=lambda o: sum(1 for x in o if x[0] == "ERROR"))
            out.extend(best)
            out.append(("ERROR", kw, path, "不合任何一种允许的形状"))
            return False
        out.append(("ERROR", kw, path, "同时合几种形状（oneOf 要求恰合一种）"))
        return False


def jtype(v):
    if v is None:
        return "null"
    if isinstance(v, bool):
        return "boolean"
    if isinstance(v, int):
        return "integer"
    if isinstance(v, float):
        return "number"
    if isinstance(v, str):
        return "string"
    if isinstance(v, list):
        return "array"
    return "object"


def type_ok(v, t):
    if isinstance(t, list):
        return any(type_ok(v, x) for x in t)
    j = jtype(v)
    return j == t or (t == "number" and j == "integer")


def short(v):
    s = json.dumps(v, ensure_ascii=False)
    return s if len(s) <= 40 else s[:37] + "…"


# ---------------------------------------------------------------- 遍历记录

def iter_records(root, paths=None):
    if paths is not None:
        for p in paths:
            ap = p if os.path.isabs(p) else os.path.join(root, p)
            rel = os.path.relpath(ap, root).replace(os.sep, "/")
            if is_record_path(rel) and os.path.exists(ap):
                yield rel, ap
        return
    for t in TYPES:
        top = os.path.join(root, t)
        if not os.path.isdir(top):
            continue
        for dp, dns, fns in os.walk(top):
            dns[:] = sorted(d for d in dns if d not in SKIP_DIRS)
            for fn in sorted(fns):
                ap = os.path.join(dp, fn)
                rel = os.path.relpath(ap, root).replace(os.sep, "/")
                if is_record_path(rel):
                    yield rel, ap


def is_record_path(rel):
    parts = rel.split("/")
    return len(parts) == 5 and parts[0] in TYPES and parts[-1].endswith(".json")


def iter_aux(root):
    """分类目录与 promotions 分片：(种类, 相对路径, 内容, schema 引用)。"""
    def load(ap):
        try:
            with open(ap, encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError) as e:
            return {"__parse_error__": str(e)}
    cdir = os.path.join(root, "classification")
    sp = os.path.join(cdir, "schemes.json")
    if os.path.exists(sp):
        schemes = load(sp)
        yield "schemes", "classification/schemes.json", schemes, "classification.schema.json#/$defs/schemes"
        for sc in schemes if isinstance(schemes, list) else []:
            sid = sc.get("id") if isinstance(sc, dict) else None
            if not sid:
                continue
            tp = os.path.join(cdir, sc.get("tree") or f"{sid}/tree.json")
            if os.path.exists(tp):
                yield "tree", os.path.relpath(tp, root), load(tp), "classification.schema.json#/$defs/tree"
            mdir = os.path.join(cdir, sid, "members")
            for fn in sorted(os.listdir(mdir)) if os.path.isdir(mdir) else []:
                if fn.endswith(".json"):
                    ap = os.path.join(mdir, fn)
                    yield "members", os.path.relpath(ap, root), load(ap), "classification.schema.json#/$defs/members"
    pdir = os.path.join(root, "promotions")
    for fn in sorted(os.listdir(pdir)) if os.path.isdir(pdir) else []:
        if fn.endswith(".json"):
            ap = os.path.join(pdir, fn)
            yield "promotions", os.path.relpath(ap, root), load(ap), "promotions.schema.json"


# ---------------------------------------------------------------- 构建产物（--build）

ENTRY_SCHEMA = "derived-entry.schema.json"
INDEX_SCHEMA = "index.schema.json"


def iter_build(out_dir):
    """--build：(种类, 相对路径, 绝对路径)。entry/*.json 逐档；index/**/*.json 逐档（档内逐条校验）。"""
    edir = os.path.join(out_dir, "entry")
    for fn in sorted(os.listdir(edir)) if os.path.isdir(edir) else []:
        if fn.endswith(".json"):
            yield "entry", f"entry/{fn}", os.path.join(edir, fn)
    idir = os.path.join(out_dir, "index")
    for dp, dns, fns in os.walk(idir):
        dns.sort()
        for fn in sorted(fns):
            if fn.endswith(".json"):
                ap = os.path.join(dp, fn)
                yield "index", os.path.relpath(ap, out_dir).replace(os.sep, "/"), ap


def emit_report(tally, examples, recs, a, label):
    """--build 的汇总输出，格式同记录校验。"""
    errors = sum(n for (lv, *_), n in tally.items() if lv == "ERROR")
    warns = sum(n for (lv, *_), n in tally.items() if lv == "WARN")
    print(f"{label}：{dict(recs)}")
    print(f"ERROR {errors}　WARN {warns}")
    for key, n in sorted(tally.items(), key=lambda kv: (kv[0][0] != "ERROR", -kv[1])):
        level, code, path, kind = key
        if level == "WARN" and a.quiet_warn:
            continue
        print(f"{level:5} {n:>8}  {kind:10} {code:20} {path}")
        for ex in examples[key]:
            print(f"{'':16}例：{ex}")
    if a.json:
        rep = {"records": dict(recs), "errors": errors, "warns": warns,
               "items": [{"level": k[0], "code": k[1], "path": k[2], "type": k[3], "count": n,
                          "examples": examples[k]} for k, n in tally.items()]}
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return 1 if errors else 0


def main_build(a):
    """校验 build 产物：entry/ 用 derived-entry.schema.json，index/ 每条用 index.schema.json 的 Entry。"""
    v = Validator(JSON_DIR)
    tally = collections.Counter()
    examples = collections.defaultdict(list)
    recs = collections.Counter()
    idx_entry, _ = v.resolve("#/$defs/Entry", INDEX_SCHEMA)

    def add(out, kind, where):
        seen = set()
        for level, code, path, msg in out:
            key = (level, code, re.sub(r"\[\d+\]", "[]", path), kind)
            tally[key] += 1
            if key not in seen and len(examples[key]) < a.examples:
                examples[key].append(f"{where}  {path}: {msg}")
            seen.add(key)

    for fam, rel, ap in iter_build(a.build):
        try:
            with open(ap, encoding="utf-8") as f:
                data = json.load(f)
        except (OSError, ValueError) as e:
            add([("ERROR", "parse", "", str(e))], f"{fam}:?", rel)
            continue
        if fam == "entry":
            kind = f"entry:{data.get('type')}" if isinstance(data, dict) else "entry:?"
            recs[kind] += 1
            out = []
            v.validate(data, v.doc(ENTRY_SCHEMA), ENTRY_SCHEMA, "", out)
            if isinstance(data, dict) and rel != f"entry/{data.get('id')}.json":
                out.append(("ERROR", "id-mismatch", "id", "文件名与 id 不符"))
            add(out, kind, rel)
            continue
        if not isinstance(data, dict):
            add([("ERROR", "type", "", "index 分片应为对象")], "index:?", rel)
            continue
        for k, e in data.items():
            kind = f"index:{e.get('type')}" if isinstance(e, dict) else "index:?"
            recs[kind] += 1
            out = []
            if not re.fullmatch(r"[0-9a-z]{1,13}", k):
                out.append(("ERROR", "key", "", f"键 {k!r} 不是 id"))
            v.validate(e, idx_entry, INDEX_SCHEMA, "", out)
            if isinstance(e, dict) and e.get("id") != k:
                out.append(("ERROR", "id-mismatch", "id", "条目 id 与键不符"))
            add(out, kind, f"{rel}#{k}")
    return emit_report(tally, examples, recs, a, "产物")


# ---------------------------------------------------------------- 主程序

def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--root", default=os.path.dirname(HERE), help="仓根（默认本仓）")
    ap.add_argument("--draft", action="store_true", help="草稿库口径：revision 可省")
    ap.add_argument("--paths", help="只查这些文件；'-' 从标准输入读（每行一个相对路径）")
    ap.add_argument("--json", help="另写机器可读报告到此路径")
    ap.add_argument("--examples", type=int, default=3, help="每类问题列几个例子")
    ap.add_argument("--quiet-warn", action="store_true", help="不打印 WARN 明细")
    ap.add_argument("--build", metavar="DIR",
                    help="改为校验 build 产物（build_derived.py 的 --out 目录）：entry/ 与 index/")
    a = ap.parse_args()
    if a.build:
        return main_build(a)

    paths = None
    if a.paths:
        src = sys.stdin if a.paths == "-" else open(a.paths, encoding="utf-8")
        paths = [ln.strip() for ln in src if ln.strip()]

    v = Validator(JSON_DIR)
    tally = collections.Counter()           # (level, code, 归一路径, 类型) -> 次数
    examples = collections.defaultdict(list)
    recs = collections.Counter()
    bad_files = 0
    for rel, abspath in iter_records(a.root, paths):
        try:
            with open(abspath, encoding="utf-8") as f:
                rec = json.load(f)
        except (OSError, ValueError) as e:
            tally[("ERROR", "parse", "", "?")] += 1
            examples[("ERROR", "parse", "", "?")].append(f"{rel}: {e}")
            bad_files += 1
            continue
        if not isinstance(rec, dict) or rec.get("type") not in SCHEMA_OF:
            tally[("ERROR", "not-a-record", "", "?")] += 1
            examples[("ERROR", "not-a-record", "", "?")].append(rel)
            continue
        kind = rec["type"]
        recs[kind] += 1
        out = []
        v.validate(rec, v.doc(SCHEMA_OF[kind]), SCHEMA_OF[kind], "", out)
        if not a.draft:
            for k in ("revision", "revised_at"):
                if k not in rec:
                    out.append(("ERROR", "required-production", k, "正式库必填而缺"))
        seen = set()
        for level, code, path, msg in out:
            key = (level, code, re.sub(r"\[\d+\]", "[]", path), kind)
            tally[key] += 1
            if key not in seen and len(examples[key]) < a.examples:
                examples[key].append(f"{rel}  {path}: {msg}")
            seen.add(key)

    if paths is None:   # 全库跑时，顺带校验分类目录与 promotions 分片
        for kind, rel, data, schema_ref in iter_aux(a.root):
            recs[kind] += 1
            sub, fbase = v.resolve(schema_ref, None)
            out = []
            v.validate(data, sub, fbase, "", out)
            if kind == "members" and isinstance(data, dict):
                rows = data.get("members") or []
                ids = [r[0] for r in rows if isinstance(r, list) and r]
                if ids != sorted(ids):
                    out.append(("ERROR", "order", "members", "成员行未按 work_id 排序"))
                if data.get("node") != os.path.basename(rel)[:-5]:
                    out.append(("ERROR", "node-name", "node", "node 与文件名不符"))
            if kind == "promotions" and isinstance(data, dict):
                key = os.path.basename(rel)[:-5]
                bad = [d for d in (data.get("promotions") or {}) if d[-2:] != key]
                if bad:
                    out.append(("ERROR", "shard-key", "promotions", f"{len(bad)} 项草稿 id 末 2 位与分片名不符"))
            for level, code, path, msg in out:
                k = (level, code, re.sub(r"\[\d+\]", "[]", path), kind)
                tally[k] += 1
                if len(examples[k]) < a.examples:
                    examples[k].append(f"{rel}  {path}: {msg}")

    errors = sum(n for (lv, *_), n in tally.items() if lv == "ERROR")
    warns = sum(n for (lv, *_), n in tally.items() if lv == "WARN")
    print(f"记录：{dict(recs)}")
    print(f"ERROR {errors}　WARN {warns}")
    for key, n in sorted(tally.items(), key=lambda kv: (kv[0][0] != "ERROR", -kv[1])):
        level, code, path, kind = key
        if level == "WARN" and a.quiet_warn:
            continue
        print(f"{level:5} {n:>8}  {kind:10} {code:20} {path}")
        for ex in examples[key]:
            print(f"{'':16}例：{ex}")
    if a.json:
        rep = {"records": dict(recs), "errors": errors, "warns": warns,
               "items": [{"level": k[0], "code": k[1], "path": k[2], "type": k[3], "count": n,
                          "examples": examples[k]} for k, n in tally.items()]}
        with open(a.json, "w", encoding="utf-8") as f:
            json.dump(rep, f, ensure_ascii=False, indent=2)
            f.write("\n")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
