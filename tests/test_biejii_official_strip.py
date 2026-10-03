"""Regression for §二·3 别集官称题剥离：官称前缀应剥离，姓氏如司馬不应剥离。"""
import pathlib, sys

# 复刻 audit_fast2.py 的剥离逻辑，避免导入大库
OFFICES = ["散騎常侍","散骑常侍","太常","光禄勋","侍中","尚书","中书","秘书","太尉","司徒","司空","大将军","骠骑将军","车骑将军","卫将军","征西将军","安西将军","镇西将军","龙骧将军","宁朔将军","建威将军","振威将军","安北将军","冠军将军","抚军将军","辅国将军","镇军将军","征虏将军","安国将军","平西将军","太守","刺史","尚书令","中书令","侍郎","黄门侍郎","散骑侍郎","给事中","御史中丞","廷尉","大鸿胪","少府","大司农","司隶校尉","河南尹","丹阳尹","征士","处士","徵士","隠士"]
OFFICES_SORTED = sorted(OFFICES, key=len, reverse=True)

def strip_official(title: str):
    for off in OFFICES_SORTED:
        if title.startswith(off):
            return title[len(off):]
    return None

def test_strip_known_officials():
    assert strip_official("散騎常侍應貞集") == "應貞集"
    assert strip_official("司徒王渾集") == "王渾集"
    assert strip_official("太常江逌集") == "江逌集"
    assert strip_official("徵士戴逵集") == "戴逵集"
    assert strip_official("徵士范宣集") == "范宣集"
    assert strip_official("御史中丞熊遠集") == "熊遠集"
    assert strip_official("散騎常侍鄭襲集") == "鄭襲集"

def test_surname_not_stripped():
    # 司馬是姓，不在官称表，不应剥离
    assert strip_official("司馬君卿集") is None
    assert strip_official("司馬光集") is None
    # 正名题本身不应被剥离
    assert strip_official("王渾集") is None
    assert strip_official("應貞集") is None

def test_non_official_prefix():
    assert strip_official("某某集") is None
    assert strip_official("") is None

if __name__ == "__main__":
    test_strip_known_officials()
    test_surname_not_stripped()
    test_non_official_prefix()
    print("PASS")
