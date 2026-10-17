"""seal_backfill.plan 的形色判定与幂等（GUJI-542 P4）：最小假数据，不依赖实库。"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".claude", "qa"))
import seal_backfill as sb  # noqa: E402

ENTS = {
    "S1": {"subtype": "seal", "seal_text": "八徵耄念之寶", "seal_form": "方", "seal_style": "朱文"},
    "S2": {"subtype": "seal", "seal_text": "無形印", "seal_style": ""},
    "S3": {"subtype": "seal", "seal_text": "八徵耄念之寶", "merged_into": "S1"},
}


def book(seals, marks=None):
    pv = {"institution": "X", "seals": seals}
    if marks:
        pv["seal_marks"] = marks
    return [("B1", {"provenance": [pv]})]


def run(seals, marks=None, ids=("S1", "S2")):
    return sb.plan(book(seals, marks), ENTS, set(ids))


def test_ok_variant_unchecked():
    todo, odd, have, unk = run(["「八徵耄念之寶」大朱方", "「八徵耄念之寶」朱長", "「八徵耄念之寶」", "「無形印」朱方"])
    assert [t[3] for t in todo] == ["「八徵耄念之寶」大朱方"]
    assert [o[3] for o in odd] == ["「八徵耄念之寶」朱長"]
    assert unk == 2


def test_color_mismatch_is_odd():
    _t, odd, _h, _u = run(["「八徵耄念之寶」白方"])
    assert len(odd) == 1


def test_idempotent_and_multi_skipped():
    todo, _o, have, _u = run(["「八徵耄念之寶」朱方"], marks=[{"seal_id": "S1"}])
    assert todo == [] and have == 1
    todo, *_ = run(["「八徵耄念之寶」朱方。「無形印」朱方"])
    assert todo == []


def test_only_requested_seal_and_tombstone_ignored():
    todo, *_ = run(["「八徵耄念之寶」朱方"], ids=("S2",))
    assert todo == []


def test_canonical_form_not_substring():
    ents = {"R": {"subtype": "seal", "seal_text": "乙", "seal_form": "橢圓", "seal_style": "朱文"},
            "Q": {"subtype": "seal", "seal_text": "丙", "seal_form": "方", "seal_style": "朱文"}}
    bk = [("B", {"provenance": [{"seals": ["「乙」朱橢", "「乙」朱圓", "「乙」朱方", "「丙」朱長", "「丙」朱方"]}]})]
    todo, odd, _h, _u = sb.plan(bk, ents, {"R", "Q"})
    assert [t[3] for t in todo] == ["「乙」朱橢", "「丙」朱方"]
    assert [o[3] for o in odd] == ["「乙」朱圓", "「乙」朱方", "「丙」朱長"]
