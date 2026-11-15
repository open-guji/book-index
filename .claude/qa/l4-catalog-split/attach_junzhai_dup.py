#!/usr/bin/env python3
"""郡齋 N 档里「与同撰人已有 Work 题名相近」者：人工逐条对照后确认同书的，挂 indexed_by（不新建）。用法：attach_junzhai_dup.py [--apply]"""
import os, sys, json, importlib.util
here = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("sp", os.path.join(here, "split.py")); sp = importlib.util.module_from_spec(spec); spec.loader.exec_module(sp)
# 题名片段（原书条首）→ 库内 Work id；2026-11-15 逐条读提要与现有 Work 对照后定
M = """周易流演 d59f28j814hx|鉤隱圖 d59f2htvzmrk|易意蘊 d59f2q7zuf40|程氏《易》 d59f2hsnnxmo|易集傳 d59f2hqvoa9u|明道中庸解 d59f2hehxekl|楊中立中庸解 d59f2hgowg03
嘉祐謚法 d59f2hkjht6q|太常禮書 d59f2hq89hj7|皇祐樂記 d59f2hq9to8w|郊廟禮文 d59f2hj81qm8|黎氏春秋經解 d59f2he5r5dt|穎濱春秋集傳 d59f2hg9x1xe|橫渠春秋說 d59f2hdsby0z|春秋經社 d59f2hkc045e
王介甫孝經解 d59f2he891qb|範淳夫古文孝經說 d59f2hhsutj5|何晏註論語 d59fxwgdtv5t|皇侃論語疏 d59f284r21vn|韓李論語筆解 d59f28mjw934|王介甫論語解 d59f2hkj6kn5|東坡論語解 d59f2hllkrgj|范氏論語說 d59f2hjtl43k|呂與叔論語解 d59f2hgyw1du|汪氏論語直解 d59f2hli55hd
智永千字文 d59f286vj6ys|於祿字書 d59f28jxml1i|古文四聲 d59fyjschxq8|陸氏埤雅 d59f2hqn8vls|通鑒舉要歷 d59f2hih7bwi|唐高宗實錄 d59f28krwlqd|大宗實錄 d59f2hkf4hky|徽廟實錄 d59f2hixfo5f|開元傳信記 d59fybb7pp8h|建炎日曆 d59f2hfqkc8x|唐末汎聞錄 d59f2q8d9mv5
呂夏卿兵志 d59f2hiuxrsw|碧雲𩤣 d59fxu4faz29|皇祐蠻記 d59f2hh3vu2o|石晉陷蕃記 d59f2gcc5zwi|劉氏史通 d59f28jau9du|東漢刊誤 d59fyutxphqa|中臺志 d59f28kg1l36|翰林續志 d59f2hjq5i4h|新御史 d59f2ofwregw|將作營造法式 d59f2hth08oy
封禪記 d59f2hiqvoqo|祀汾陰記 d59f2hhijzlu|《疑獄》 d59f2gcq7och|明皇幸蜀記 d59f28jyvj7p|吳氏西齊書目 d59f28lfxvk3|田氏書目 d59f2og9k4xt|《刪孟》 d59f2hkysfsx|徐庸註太玄經解 d59f2hea4gzo|成玄英莊子疏 d59f28nkq96s
馭臣鑒古 d59f2hjd1jb6|呂惠卿建安茶記 d59f2hh7bg1s|《資暇》 d59f28jj9o1s|秘閣雅談 d59f2hkrx7ur|幕府燕閒錄 d59f2q0cj474|《詩眼》 d59fybc4hm9t|集聖曆 d59f2hg58hs2|武侯十六策 d59f27s99340|郭元振安邊策 d59f28jsmscg|侍女小名錄 d59fybachyww|溫公投壺新格 d59f2hi6whz6
王叔和脈經 d59f27x4zoxs|巢氏病源候論 d59f28lycvlu|運氣論奧 d59f2htji51d|補註神農本草 d59f2hlgw7b4|本草廣義 d59f2hux4vep|養生必用方 d59f2pzc0d1c|群仙會真記 d59f28j9lb7o|道引養生圖 d59f286m62o1|日月元樞樞論 d59gdzjop0ju|玉英集 d59fyj9t4lq8
宋之問考功集 d59f28kcaqkj|獨孤及毗陵集 d59f28jjkwle|陸贄奏議 d59fyt6wm0ht|武元衡臨淮集 d59f28jggj5x|李絳論諫集 d59f2pu3s9hd|李觀文編 d59f28jp76dh|白居易長慶集 d59f28lx3xfp|皇甫湜文 d59f28jiyfib|李紳追昔遊 d59f28kkq58i|施肩吾西山集 d59f28l778cm
李賀集四卷 d59f2q6jejup|李德裕會昌一品集 d59f28kaqjuw|劉綺莊歌詩 d59f2q1z7qbk|薛逢歌詩 d59f28k4hszm|趙嘏渭南詩 d59fsev1aqdf|李郢端公詩 d59f28jokpab|溫庭筠金荃集 d59fxu8xb1fl|唐彥謙鹿門詩 d59fsfwaa800|杜荀鶴唐風集 d59f28lwsow1
王元之小畜集 d59f2hm8d341|陳文惠愚丘集 d59f2q4jlz40|民士編 d59f2pwc08ow|田公金巖集 d59f2q2x8lq9|梅聖俞宛陵集 d59f2hqkfqpu|文與可丹淵集 d59f2hqyhf5s|呂汲公文錄 d59f2hhgokci
張浮休畫墁集 d59f2hrkyi9t|張文潛柯山集 d59f2hpreo76|秦少遊淮海集 d59f2hupbxtu|陳無己後山集 d59f2hrjpk3l|陳參政簡齋集 d59f2hu3639c|陳亞之集 d59f2qa2re2o|黃虞部詩 d59f2q3pbytc|邵堯夫擊壤集 d59fsifsot1h|瑤池新集 d59f2qa4mt4w|續金針詩格 d59fyay3qw3l
蘇頲許公集 d59f28l8g6ip|嚴從中黃子集 d59f28l50kjk|吳筠宗元先生集 d59f28nlnyti|李端司馬集 d59f28jn0ikg"""
PAIRS = [x.rsplit(" ", 1) for x in M.replace("\n", "|").split("|")]
def main():
    apply = "--apply" in sys.argv
    idx, by = sp.load_idx(); ents = sp.parse_junzhai(); sbid = "d59f2hpm3myp"
    done = 0; miss = []
    for frag, wid in PAIRS:
        es = [e for e in ents if frag in e["head"] and sp.match(e, idx, by, "song")[0] == "N"]
        if len(es) != 1 or wid not in idx: miss.append((frag, len(es), wid in idx)); continue
        e = es[0]; p = os.path.join(sp.BI, idx[wid]["path"])
        raw = open(p, encoding="utf-8").read(); d = json.loads(raw); lines = raw.split("\n")
        ind = len(lines[1]) - len(lines[1].lstrip(" ")) if len(lines) > 2 and lines[0] == "{" else 2
        ib = d.setdefault("indexed_by", [])
        if any(x.get("source_bid") == sbid and x.get("title_info") == e["head"] for x in ib): continue
        ent = {"source": "郡齋讀書志", "source_bid": sbid, "title_info": e["head"]}
        if e["summary"]: ent["summary"] = e["summary"]
        if e["juan"]: ent["juan_count"] = e["juan"]
        if e["sec"]: ent["section"] = e["sec"]
        print(e["head"][:30], "->", wid, idx[wid]["t"], idx[wid]["a"][:2])
        if apply:
            ib.append(ent)
            with open(p, "w", encoding="utf-8") as f:
                json.dump(d, f, ensure_ascii=False, indent=ind)
                if raw.endswith("\n"): f.write("\n")
        done += 1
    print("挂接", done, "未对上", miss)
main()
