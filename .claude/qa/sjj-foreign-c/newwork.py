#!/usr/bin/env python3
"""十三經縱向補全·外國 1912 前（車道 a11-sjj-foreign-c）：補建老子／儀禮項下庫內無的日本（江戶／明治）及西人 1912 前著作 Work。
用法：newwork.py [--apply]。依據：CiNii Books 書誌（NCID 見各條）；口徑：用戶 2026-11-15「其他國家 1912 年以前都錄」。"""
import os, sys, json
here = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(here, "../../.."))
sys.path.insert(0, os.path.join(BI, ".claude/qa"))
import mintid
LAO = "d59ezkx8dt6o"; YILI = "d59ezak3445c"
EDO = "江戶時代"; MEIJI = "明治時代"
CI = "CiNii Books https://ci.nii.ac.jp/ncid/%s"
UP_E = "撰人為日本江戶時代人，與清並行；成書／刊行均在 1912 年前，無論何解皆不晚於 qing"
UP_M = "撰人為日本明治時代人（1868—1912），成書／首刊在 1912 年前，無論何解皆不晚於 qing"
# (經根, 題名, 原題, [(作者,role,朝代)], 作品朝代, relation, NCID, 書誌依據(含年), 備註)
R = [
 (LAO, "老子經講筵筆記", None, [("大町一水", "講述", EDO)], EDO, "contains_text_of", "BB26406908",
  "大町一水講述，二卷，享保 20（1735）寫本（大澤三喜）；別題《老子德經》《老子經筆記》", "寫本講筵筆記", UP_E),
 (LAO, "老子解題", None, [("東條一堂", "述", EDO)], EDO, "studies", "BA75962569",
  "東條一堂述，天保 12（1841）寫本；內容為《老子道德真經》卷一之題解", "寫本，書名據外題", UP_E),
 (LAO, "老子言言戰", "老子言言戦", [("鷲峯瑚山", "著", MEIJI)], MEIJI, "studies", "BA83716003",
  "鷲峯瑚山著，井上圓了校閱，明治 29（1896）3 月刊（京都，出雲寺文次郎）；副題「支那哲學」", "書名「戦」依庫內慣例作「戰」，原題見 original_title", UP_M),
 (LAO, "老子哲學", None, [("島津如泡", "著", MEIJI)], MEIJI, "studies", "BA37053165",
  "島津如泡著，嵩山房，明治 42（1909）刊", "", UP_M),
 (LAO, "和譯老子", None, [("田岡嶺雲", "譯註", MEIJI)], MEIJI, "contains_text_of", "BN14596163",
  "田岡嶺雲譯註，玄黃社，明治 43（1910）4 月刊；與《和譯莊子》合錄一書，別題《和譯老子全》", "合錄本中的《和譯莊子》屬莊子，本批不建", UP_M),
 (LAO, "評註ポケット老子", None, [("坂井松梁", "著", MEIJI)], MEIJI, "contains_text_of", "BD14340680",
  "坂井松梁著，德富蘇峰序，日進堂書店，明治 43（1910）5 月刊", "", UP_M),
 (LAO, "學生界の活老子", None, [("佐川環", "著", MEIJI)], MEIJI, "studies", "BN0958119X",
  "佐川環著，建文館，明治 44（1911）8 月刊，266 頁", "", UP_M),
 (LAO, "Lao-Tze's Tao-Teh-King", "Lao-Tze's Tao-Teh-King, Chinese and English = 老子道德經", [("Paul Carus", "譯註", "美國")], "美國", "contains_text_of", "BA37497511",
  "Paul Carus 英譯並注（含中文原文、音譯與導言），Open Court，1898 年刊；CiNii 別題「評註英譯老子道德經」", "西人英譯本；卡魯斯（1852—1919）生卒據通行傳記，未逐一覆核", "撰人為美國（德裔）學者，1898 年刊，在 1912 年前；不晚於 qing"),
 (YILI, "新定松氏儀禮圖", None, [("村松", "著", EDO)], EDO, "studies", "BB26879488",
  "村松著，野愼、木直、山偉、僧朗、施恭校，天明 8（1788）跋；另一著錄 BA79800252", "報告作「新定儀禮圖」，松安（村松貞吉），CiNii 責任者僅作「村松」，本名未覆核", UP_E),
 (YILI, "儀禮釋宮圖解", None, [("川合衡", "著", EDO)], EDO, "studies", "BD18326692",
  "川合衡著，佐藤興忠、森本祐昌同校，文化 12（1815）刊（鴨伊兵衞等）；另 BB29798804、BB17304962、BB13738472、BA82162620 同書", "與庫內《儀禮釋宮》（李如圭）題名相近而非同書", UP_E),
]
def main():
    apply = "--apply" in sys.argv
    ids = mintid.mint("Work", "a11-sjj-foreign-c", len(R)) if apply else ["-"] * len(R)
    for (root, t, ot, auth, dyn, rel, ncid, bib, memo, upb), i in zip(R, ids):
        jing = "老子" if root == LAO else "儀禮"
        note = ("2026-11-15 十三經縱向補全·外國 1912 前（%s）：據 %s 著錄——%s；成書／刊行在 1912 年前，依用戶口徑建條。" % (jing, CI % ncid, bib)
                + ("備註：%s。" % memo if memo else "") + "作者生平未逐一考證，責任者朝代取自書誌與刊年。")
        d = {"schema_version": 1, "id": i, "type": "work", "title": t,
             "authors": [{"name": n, "role": r, "dynasty": y} for n, r, y in auth], "dynasty": dyn}
        if ot: d["original_title"] = ot
        d["period_upper"] = "qing"; d["period_upper_basis"] = upb
        d["related_works"] = [{"id": root, "relation": rel}]
        d["ai_note"] = note; d["revision"] = "1.0.0"; d["revised_at"] = "2026-11-15"
        if not apply: print(t, auth[0][0], rel); continue
        p = "Work/%s/%s/%s/%s-%s.json" % (i[-3], i[-2], i[-1], i, t.replace("/", "／"))
        os.makedirs(os.path.join(BI, os.path.dirname(p)), exist_ok=True)
        open(os.path.join(BI, p), "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print(("新建 " if apply else "dry-run ") + str(len(R)))
main()
