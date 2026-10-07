"""专名子类型校验（overview#464 F6-5）：每个检查码至少一正一反的最小样例。
实现在 .claude/qa/entity_subtypes.py，check_v2.py／verify.py 共用。"""
import copy
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / ".claude/qa"))
import entity_subtypes as es  # noqa: E402
import check_v2  # noqa: E402

CANON = {"趙宋", "北宋", "南宋", "唐", "東周", "戰國", "先秦", "春秋", "春秋吳", "春秋齊"}


def dyn(i, name, start=None, end=None, **kw):
    r = {"id": i, "type": "entity", "subtype": "dynasty", "primary_name": name}
    if start is not None:
        r["dates"] = {"start": start, "end": end, "basis": "x"}
    r.update(kw)
    return r


def reign(i, name, did, start, end, **kw):
    r = {"id": i, "type": "entity", "subtype": "reign", "primary_name": name, "dynasty_id": did,
         "ruler": {"name": "某"}, "dates": {"start": start, "end": end, "basis": "x"}}
    r.update(kw)
    return r


def office(i, **kw):
    r = {"id": i, "type": "entity", "subtype": "office", "primary_name": "知縣", "office_level": "concept"}
    r.update(kw)
    return r


def conc(i, dids, **kw):
    return office(i, office_level="concrete", dynasty_ids=dids, function="掌一縣", basis="職官志", **kw)


def place(i, **kw):
    r = {"id": i, "type": "entity", "subtype": "place", "primary_name": "紹興",
         "history": [{"start": 1131, "end": 1276, "dynasty_ids": ["s"], "name": "紹興府", "level": "府"}]}
    r.update(kw)
    return r


def people(i):
    return {"id": i, "type": "entity", "subtype": "people", "primary_name": "蘇軾"}


def reg_of(*recs):
    reg = es.Registry()
    for r in recs:
        reg.add(r, "Entity/%s.json" % r["id"])
    return reg


BASE = [dyn("s", "趙宋", 960, 1279), dyn("n", "北宋", 960, 1127, parent_id="s", period="song"),
        dyn("t", "唐", 618, 907, period="sui-tang"), people("p1")]


def codes(rec, *extra, level=None):
    reg = reg_of(*BASE, *extra, rec)
    return sorted((c, lv) for c, lv, _, _ in es.check_record(rec, reg) if level is None or lv == level)


def has(rec, code, level=es.ERROR, *extra):
    return (code, level) in codes(rec, *extra)


def gcodes(*recs, canon=CANON):
    reg = reg_of(*recs)
    return sorted((c, lv) for _, c, lv, _, _ in es.check_global(reg, canon))


# ---- 正向：干净样例全过
def test_clean_samples():
    assert codes(BASE[1]) == []
    assert codes(reign("r1", "建和", "n", 960, 970)) == []
    c = office("o1")
    assert codes(c) == []
    assert codes(conc("o2", ["s"], parent_id="o1"), c) == []
    assert codes(place("pl1"), ) == [] or codes(place("pl1")) == [("P04", "ERROR")]  # 'dynasty_ids': ['s'] 存在
    assert codes(people("p2")) == []  # 非新子类型不受影响


# ---- E1
def test_e1():
    assert has(dyn("d", "唐", 618, 907, external_ids={"cbdb_dy": 6}), "E1")
    assert has(dyn("d", "唐", 618, 907, external_ids={"wikidata_id": "Q1", "chgis_id": "x"}), "E1")
    assert has(dyn("d", "唐", 618, 907, translation="x"), "E1")
    assert has(office("o", c_office_trans="x"), "E1")
    assert has(dyn("d", "唐", 618, 907, coords=[1, 2]), "E1")
    assert not has(dyn("d", "唐", 618, 907, external_ids={"wikidata_id": "Q123"}), "E1")
    assert has(dyn("d", "唐", 618, 907, external_ids={"wikidata_id": "bad"}), "E1")
    assert not has(dyn("d", "唐", 618, 907), "E1")


# ---- D1
def test_d1():
    assert gcodes(dyn("a", "唐", 618, 907)) == []
    assert ("D1", "ERROR") in gcodes(dyn("a", "不在枚舉", 1, 2))
    assert ("D1", "ERROR") in gcodes(dyn("a", "唐", 618, 907), dyn("b", "唐", 618, 907))


# ---- D2
def test_d2():
    assert not has(dyn("x", "南宋", 1127, 1279, parent_id="s"), "D2")
    assert has(dyn("x", "南宋", 1127, 1279, parent_id="nope"), "D2")
    assert has(dyn("x", "南宋", 1127, 1279, parent_id="p1"), "D2")  # 非 dynasty
    a = dyn("a", "春秋", -770, -476, parent_id="b")
    b = dyn("b", "戰國", -475, -221, parent_id="a")
    assert has(a, "D2", es.ERROR, b)  # 成環
    chain = [dyn("c1", "先秦", -2070, -221), dyn("c2", "東周", -770, -256, parent_id="c1"),
             dyn("c3", "春秋", -770, -476, parent_id="c2")]
    ok = dyn("c4", "春秋吳", -770, -476, parent_id="c3")
    assert not has(ok, "D2", es.ERROR, *chain)            # 3 跳，允許
    deep = dyn("c5", "春秋齊", -700, -500, parent_id="c4")
    assert has(deep, "D2", es.ERROR, *chain, ok)           # 4 跳，超深
    # 區間：越上級 → WARN 不是 ERROR
    assert has(dyn("w", "戰國", -475, -221, parent_id="c2"), "D2", es.WARN, *chain)
    assert not has(dyn("w", "戰國", -475, -221, parent_id="c2"), "D2", es.ERROR, *chain)
    assert not has(dyn("w", "戰國", -475, -257, parent_id="c2"), "D2", es.WARN, *chain)
    assert not has(dyn("w", "戰國", -770, -257, parent_id="c2"), "D2", es.WARN, *chain)  # 容差內


# ---- D3
def test_d3():
    assert not has(dyn("x", "唐", 618, 907), "D3")
    assert has(dyn("x", "唐", 907, 618), "D3")                   # start>end
    assert has(dyn("x", "唐", 0, 5), "D3")                       # 無 0 年
    assert has(dyn("x", "唐", "618", 907), "D3")                 # 非整數
    bad = dyn("x", "唐", 618, 907)
    bad["dates"]["birth"] = 1
    assert has(bad, "D3")                                         # 鍵不放行
    assert has(office("o", dates={"start": 1}), "D3")             # office 不用 dates
    assert has(place("pl", dates={"start": 1}), "D3")
    assert has(dyn("x", "唐", 618, 907, period="nope"), "D3")
    assert has(dyn("x", "唐", period="sui-tang"), "D3", es.WARN)  # 有 period 缺 start：WARN
    assert not has(dyn("x", "日本"), "D3", es.WARN)               # 域外可缺
    assert not has(dyn("x", "中華民國", 1912, None, period="modern"), "D3")  # end=None 允許


# ---- R1
def test_r1():
    r = reign("r", "建和", "n", 960, 970)
    assert not has(r, "R1")
    assert has(reign("r", "建和", None, 960, 970), "R1")                        # 缺 dynasty_id
    assert has(reign("r", "建和", None, 960, 970, ai_note="政權無條目"), "R1", es.WARN)
    assert has(reign("r", "建和", "nope", 960, 970), "R1")
    assert has(reign("r", "建和", "n", 960, 970, ruler={"name": ""}), "R1")
    assert not has(reign("r", "建和", "n", 960, 970, ruler={"name": "某", "entity_id": "p1"}), "R1")
    assert has(reign("r", "建和", "n", 960, 970, ruler={"name": "某", "entity_id": "n"}), "R1")  # 非 people
    nostart = reign("r", "建和", "n", 960, 970)
    nostart["dates"].pop("start")
    assert has(nostart, "R1")
    # 越朝代：WARN 非 ERROR；容差 5 年
    assert has(reign("r", "天命", "n", 940, 970), "R1", es.WARN)
    assert not has(reign("r", "天命", "n", 940, 970), "R1", es.ERROR)
    assert not has(reign("r", "天命", "n", 956, 970), "R1", es.WARN)
    assert has(reign("r", "天命", "n", 1100, 1140), "R1", es.WARN)
    # 全庫：三元組唯一、同朝同名重疊
    assert gcodes(reign("a", "建和", "n", 960, 962), reign("b", "建和", "n", 960, 965)) .count(("R1", "ERROR")) == 2
    assert ("R1", "ERROR") in gcodes(reign("a", "建和", "n", 960, 970), reign("b", "建和", "n", 965, 975))
    assert ("R1", "ERROR") not in gcodes(reign("a", "建和", "n", 960, 962), reign("b", "建和", "n", 963, 975))
    assert ("R1", "ERROR") not in gcodes(reign("a", "建和", "n", 960, 970), reign("b", "建和", "t", 965, 975))


# ---- A1
def test_a1():
    amb = {"name": "宋", "type": "簡稱", "ambiguous": True}
    assert not has(dyn("x", "南宋", 1127, 1279, alt_names=[amb]), "A1")
    assert has(dyn("x", "南宋", 1127, 1279, alt_names=[{"name": "宋", "type": "簡稱", "ambiguous": "yes"}]), "A1")
    assert has(dyn("x", "南宋", 1127, 1279, alt_names=[{"type": "簡稱"}]), "A1")
    # 全庫：ambiguous 僅 1 條聲稱 → WARN；2 條 → 無
    one = dyn("a", "南宋", 1127, 1279, alt_names=[amb])
    two = dyn("b", "北宋", 960, 1127, alt_names=[amb])
    assert ("A1", "WARN") in gcodes(one)
    assert ("A1", "WARN") not in gcodes(one, two)
    # 以 primary_name 作聲稱（後漢）
    assert ("A1", "WARN") not in gcodes(dyn("a", "唐", alt_names=[{"name": "北宋", "type": "別稱", "ambiguous": True}]),
                                       dyn("b", "北宋", 960, 1127))
    # 無 ambiguous 之 dynasty 別名全局唯一
    u1 = dyn("a", "唐", alt_names=[{"name": "李唐", "type": "別稱"}])
    u2 = dyn("b", "北宋", alt_names=[{"name": "李唐", "type": "別稱"}])
    assert ("A1", "ERROR") in gcodes(u1, u2)
    assert ("A1", "ERROR") not in gcodes(u1, dyn("b", "北宋"))


# ---- O01–O05, O09–O12
def test_office_codes():
    assert has(office("o", office_level="x"), "O01")
    assert not has(office("o"), "O01")
    c = office("o1")
    assert not has(conc("o2", ["s"], parent_id="o1"), "O02", es.ERROR, c)
    assert has(conc("o2", [], parent_id="o1"), "O02", es.ERROR, c)
    assert has(conc("o2", ["nope"], parent_id="o1"), "O02", es.ERROR, c)
    miss = conc("o2", ["s"], parent_id="o1")
    miss.pop("function")
    assert has(miss, "O02", es.ERROR, c)
    assert has(office("o", dynasty_ids=["s"]), "O02")            # 概念條禁字段
    assert has(office("o", rank={"text": "七品", "basis": "x"}), "O02")
    assert has(conc("o2", ["s"], parent_id="o1", office_class="亂寫"), "O03", es.ERROR, c)
    assert not has(conc("o2", ["s"], parent_id="o1", office_class="差遣"), "O03", es.ERROR, c)
    assert has(conc("o2", ["s"], parent_id="nope"), "O04")
    assert has(conc("o2", ["s"], parent_id="s"), "O04")           # 指向非 office
    assert has(office("o", parent_id="o1"), "O04", es.ERROR, c)    # 概念不得有 parent_id
    # O05
    base = conc("b1", ["s"], parent_id="o1")
    cmp_ = conc("c1", ["s"], parent_id="o1", base_office_id="b1", qualifier={"kind": "institution", "name": "資政殿"})
    assert not has(cmp_, "O05", es.ERROR, c, base)
    assert has(conc("c1", ["s"], parent_id="o1", base_office_id="b1"), "O05", es.ERROR, c, base)         # 缺 qualifier
    assert has(conc("c1", ["n"], parent_id="o1", base_office_id="c1",
                    qualifier={"kind": "mode", "name": "x"}), "O05", es.ERROR, c)                          # 自指
    assert has(conc("c1", ["n"], parent_id="o1", base_office_id="nope",
                    qualifier={"kind": "mode", "name": "x"}), "O05", es.ERROR, c)
    assert has(conc("c1", ["n"], parent_id="o1", base_office_id="b1",
                    qualifier={"kind": "亂", "name": "x"}), "O05", es.ERROR, c, base)                      # kind
    assert has(conc("c1", ["t"], parent_id="o1", base_office_id="b1",
                    qualifier={"kind": "mode", "name": "x"}), "O05", es.ERROR, c, base)                    # 朝不相交
    b2 = conc("b2", ["s"], base_office_id="c2", qualifier={"kind": "mode", "name": "x"})
    c2 = conc("c2", ["s"], base_office_id="b2", qualifier={"kind": "mode", "name": "x"})
    assert has(b2, "O05", es.ERROR, c2)                                                                      # 成環
    tocon = conc("c1", ["s"], parent_id="o1", base_office_id="o1", qualifier={"kind": "mode", "name": "x"})
    assert has(tocon, "O05", es.WARN, c)                                                                     # 指概念：WARN
    assert not has(dict(tocon, ai_note="暫指概念"), "O05", es.WARN, c)
    # O09
    assert has(conc("o2", ["s"], parent_id="o1", start=1100, end=1000), "O09", es.ERROR, c)
    assert has(conc("o2", ["s"], parent_id="o1", start="1100"), "O09", es.ERROR, c)
    assert not has(conc("o2", ["s"], parent_id="o1", start=960, end=1127), "O09", es.ERROR, c)
    # O10
    assert has(conc("o2", ["s"], parent_id="o1", alt_names=[{"name": "令", "type": "簡稱"}]), "O10", es.WARN, c)
    assert not has(conc("o2", ["s"], parent_id="o1", alt_names=[{"name": "縣太爺", "type": "簡稱"}]), "O10", es.WARN, c)
    # O11
    assert ("O11", "WARN") in gcodes(c, conc("o2", ["s"], parent_id="o1"), conc("o3", ["s"], parent_id="o1"))
    assert ("O11", "WARN") not in gcodes(c, conc("o2", ["s"], parent_id="o1"), conc("o3", ["t"], parent_id="o1"))
    # O12
    assert has(office("o", alt_names=[{"name": "令", "type": "亂寫"}]), "O12")
    assert not has(office("o", alt_names=[{"name": "令", "type": "異寫"}]), "O12")


# ---- P01–P09
def test_place_codes():
    pr = dyn("s", "趙宋", 960, 1279)
    assert not has(place("pl"), "P01")
    assert has(place("pl", history=[]), "P01")
    assert has(place("pl", primary_name=""), "P01")
    bad = place("pl")
    bad["history"][0]["level"] = "亂"
    assert has(bad, "P01")
    # P02
    h = lambda s, e, **k: dict({"start": s, "end": e, "dynasty_ids": ["s"], "name": "甲", "level": "縣"}, **k)
    assert not has(place("pl", history=[h(589, 621), h(1131, 1276)]), "P02")   # 空檔允許
    assert has(place("pl", history=[h(1200, 1100)]), "P02")
    assert has(place("pl", history=[h(1131, 1950)]), "P02")                      # end>1912
    assert has(place("pl", history=[h(1100, 1200), h(1150, 1250)]), "P02")       # 重疊
    # P03
    up = place("up", primary_name="兩浙路")
    assert not has(place("pl", history=[h(1131, 1276, parent_id="up")]), "P03", es.ERROR, up)
    assert has(place("pl", history=[h(1131, 1276, parent_id="nope")]), "P03")
    assert has(place("pl", history=[h(1131, 1276, parent_id="pl")]), "P03")      # 自引
    a = place("a", history=[h(1131, 1276, parent_id="b")])
    b = place("b", history=[h(1131, 1276, parent_id="a")])
    assert has(a, "P03", es.ERROR, b)                                             # 成環
    assert has(place("pl", history=[h(1131, 1276, parent_id="up", parent_text="兩浙路")]), "P03", es.WARN, up)
    # P04
    assert has(place("pl", history=[h(1131, 1276, dynasty_ids=["nope"])]), "P04")
    # P06
    ok = {"text": "浙江省紹興市", "adcode": "330602", "relation": "治所今在"}
    assert not has(place("pl", modern=ok), "P06")
    assert has(place("pl", modern=dict(ok, adcode="33")), "P06")
    assert has(place("pl", modern=dict(ok, relation="亂")), "P06")
    # P07
    assert not has(place("pl", predecessors=[{"id": "up", "kind": "析出"}]), "P07", es.ERROR, up)
    assert has(place("pl", predecessors=[{"id": "nope", "kind": "析出"}]), "P07")
    assert has(place("pl", predecessors=[{"id": "up", "kind": "亂"}]), "P07", es.ERROR, up)
    # P08
    assert has(place("pl", coords=[1, 2]), "P08")
    assert not has(place("pl"), "P08")
    # P09
    h2 = lambda: [h(1131, 1276, parent_id="up")]
    codes_ = gcodes(pr, up, place("a", history=h2()), place("b", history=h2()))
    assert ("P09", "WARN") in codes_ and ("P09", "INFO") in codes_
    codes_ = gcodes(pr, up, place("a", history=h2()), place("b", primary_name="乙", history=h2()))
    assert ("P09", "WARN") not in codes_ and ("P09", "INFO") not in codes_
    only = gcodes(place("a"), place("b"))
    assert ("P09", "INFO") in only and ("P09", "WARN") not in only      # 同名異地：僅 INFO


# ---- V01（派生／反向欄位）
def test_v01():
    assert has(dyn("x", "唐", 618, 907, children=["a"]), "V01")
    assert has(reign("r", "建和", "n", 960, 970, index_in_reign=1), "V01")
    assert has(dyn("x", "唐", 618, 907, _has_text=True), "V01")     # 新子類型不享豁免
    assert not has(dyn("x", "唐", 618, 907), "V01")
    # check_v2 自身之 `_` 起首 V01 仍報
    assert [c for c, _, _ in check_v2.check_record("Entity", dyn("x", "唐", 618, 907, _children=[]))] == ["V01"]


# ---- alt_names.type（含新增十項）
def test_alt_types_enum():
    for t in ("簡稱", "合稱", "避諱", "別稱", "雅稱", "全稱", "異寫", "舊稱", "異稱", "今名", "異體", "別名"):
        assert t in es.ALT_TYPES
    assert has(dyn("x", "唐", 618, 907, alt_names=[{"name": "李唐", "type": "亂寫"}]), "O12")


# ---- 與 check_v2／文件掃描整合
def _write(root, rel, obj):
    p = root / rel
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")


def test_check_v2_integration_levels_and_exit_code(tmp_path, capsys):
    canon_ok = dyn("1a", "唐", 618, 907, period="sui-tang")
    _write(tmp_path, "Entity/1/a/1a-唐.json", canon_ok)
    # 越朝代之年號：WARN，退出碼仍 0
    _write(tmp_path, "Entity/2/a/2a-x.json", reign("2a", "天命", "1a", 600, 620))
    assert check_v2.main(["--root", str(tmp_path), "--summary"]) == 0
    out = capsys.readouterr().out
    assert "WARN" in out and "R1" in out
    # 加一條 ERROR：外部 id
    _write(tmp_path, "Entity/3/a/3a-y.json", reign("3a", "天寶", "1a", 742, 756, external_ids={"cbdb_nianhao_id": 1}))
    assert check_v2.main(["--root", str(tmp_path), "--summary"]) == 1
    # 引用懸空：年號指向不存在朝代
    _write(tmp_path, "Entity/3/a/3a-y.json", reign("3a", "天寶", "nope", 742, 756))
    assert check_v2.main(["--root", str(tmp_path), "--summary", "--codes", "R1", "--errors-only"]) == 1


def test_check_v2_paths_mode_uses_full_registry(tmp_path):
    _write(tmp_path, "Entity/1/a/1a-唐.json", dyn("1a", "唐", 618, 907, period="sui-tang"))
    _write(tmp_path, "Entity/2/a/2a-x.json", reign("2a", "天寶", "1a", 742, 756))
    assert check_v2.main(["--root", str(tmp_path), "--summary", "--paths", "Entity/2/a/2a-x.json"]) == 0


def test_people_unaffected(tmp_path):
    _write(tmp_path, "Entity/1/a/1a-p.json", dict(people("1a"), dates={"birth": 1037, "death": 1101},
                                                  external_ids={"cbdb_id": 1}))
    assert check_v2.main(["--root", str(tmp_path), "--summary"]) == 0


# ---- 官署（collective_kind=官署，I01–I12；P3c 設計稿 §十二）
def inst(i, lvl, **kw):
    r = {"id": i, "type": "entity", "subtype": "collective", "collective_kind": "官署",
         "primary_name": "吏部", "institution_level": lvl}
    if lvl in ("concept", "group"):
        r["description"] = "x"
    else:
        r.update(dynasty_ids=["t"], function="掌銓選", basis="《新唐書·百官志》")
    r.update(kw)
    return r


IC = inst("ic", "concept")
IG = inst("ig", "group", primary_name="六部")


def test_inst_clean_and_legacy():
    assert codes(IC) == [] and codes(IG) == []
    assert codes(inst("i1", "concrete", parent_id="ic", group_ids=["ig"]), IC, IG) == []
    old = {"id": "c0", "type": "entity", "subtype": "collective", "primary_name": "郵傳部"}
    assert not es.applies(old) and codes(old) == []  # 舊 collective 不受約束
    assert codes(dict(old, collective_kind="書院學校")) == []
    assert has(dict(old, collective_kind="衙門"), "I01")


def test_i01_i02_i03():
    assert has(inst("x", "bad"), "I01")
    assert has(inst("x", "concept", dynasty_ids=["t"]), "I02")
    assert has(inst("x", "group", function="x"), "I02")
    assert has(inst("x", "group", group_ids=["ig"]), "I02", es.ERROR, IG)
    assert has(inst("x", "concept", description=None), "I02")
    c = inst("x", "concrete")
    del c["function"]
    assert has(c, "I02")
    assert has(inst("x", "concrete", basis="待核"), "I02")
    assert has(inst("x", "concrete", dynasty_ids=["nope"]), "I02")
    assert has(inst("x", "concept", parent_id="ic"), "I03", es.ERROR, IC)
    assert has(inst("x", "concrete", parent_id="ig"), "I03", es.ERROR, IG)
    assert not has(inst("x", "concrete", parent_id="ic"), "I03", es.ERROR, IC)


def test_i04_superiors():
    up = inst("up", "concrete", primary_name="尚書省")
    assert codes(inst("x", "concrete", superiors=[{"id": "up", "start": 700}]), up) == []
    assert has(inst("x", "concrete", superiors=[{"id": "x"}]), "I04")
    assert has(inst("x", "concrete", superiors=[{"id": "ic"}]), "I04", es.ERROR, IC)
    assert has(inst("x", "concrete", superiors=[{"id": "up", "start": 800, "end": 700}]), "I04", es.ERROR, up)
    sup_s = inst("up2", "concrete", dynasty_ids=["s"])
    assert has(inst("x", "concrete", superiors=[{"id": "up2"}]), "I04", es.WARN, sup_s)
    a = inst("a", "concrete", superiors=[{"id": "b"}])
    b = inst("b", "concrete", superiors=[{"id": "a"}])
    assert has(a, "I04", es.ERROR, b)


def test_i05_i06_i08_i09_i11():
    assert has(inst("x", "concrete", group_ids=["ic"]), "I05", es.ERROR, IC)
    c2 = inst("c2", "concept", group_ids=["ig"])
    assert has(inst("x", "concrete", parent_id="c2", group_ids=["ig"]), "I05", es.WARN, c2, IG)
    assert has(inst("x", "concrete", start=0), "I06")
    assert has(inst("x", "concrete", start=900, end=800), "I06")
    assert has(inst("x", "concrete", start=500), "I06", es.WARN)
    assert not has(inst("x", "concrete", start=618, end=907), "I06", es.WARN)
    assert has(inst("x", "concrete", external_ids={"cbdb_id": 1}), "I08")
    assert has(inst("x", "concrete", rank={"text": "正三品"}), "I08")
    assert has(inst("x", "concrete", location_id="pl"), "I09")
    assert has(inst("x", "concrete", succeeds=["y"]), "I09", es.WARN)
    assert has(inst("x", "concrete", members=["y"]), "I11")


def test_i07_i10_global():
    a = inst("a", "concrete", parent_id="ic")
    b = inst("b", "concrete", parent_id="ic", dynasty_ids=["t", "s"])
    g = gcodes(IC, a, b, *BASE)
    assert ("I07", "WARN") in g and ("I10", "WARN") in g
    assert ("I07", "WARN") not in gcodes(IC, a, inst("c", "concrete", parent_id="ic", dynasty_ids=["s"]), *BASE)


def test_i12_institution_ref():
    sub = inst("sub", "concrete", primary_name="吏部")
    o = lambda ref, **kw: conc("of", ["t"], institution_ref=ref, **kw)
    assert has(o("COL:六部"), "I12")            # O14 第二步：一律 ERROR
    assert has(o("COL:不在名單"), "I12")
    assert not has(o("sub"), "I12", es.ERROR, sub) and not has(o("sub"), "I12", es.WARN, sub)
    assert has(conc("of", ["s"], institution_ref="sub"), "I12", es.ERROR, sub)  # 朝代不相交
    assert has(o("ic"), "I12", es.WARN, IC)
    assert not has(o("ic", ai_note="暫指概念條，待補唐具體條"), "I12", es.WARN, IC)
    assert has(conc("of", ["t"], institution_ref="ig", primary_name="吏部尚書"), "I12", es.WARN, IG)
    assert has(o("p1"), "I12")                 # 非官署
    assert has(o("nowhere"), "I12", es.WARN)   # 不在本庫（指正式庫）
