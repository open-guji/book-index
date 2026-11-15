#!/usr/bin/env python3
"""十三經縱向補全·其餘諸經（周易／尚書／毛詩／儀禮／禮記／左傳／穀梁／孝經）：補建庫內無的獨立著作 Work。
用法：newwork.py [--apply]
依據與比對見 ai-team domain/目錄與資源/設計/2026-11-十三經縱向補全/ 各經報告；
建前逐條到依據頁核實（經義考原頁／CiNii／NDL），核不實者不建，見同目錄 SKIPPED.tsv。"""
import os, sys, json, glob
here = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(here, "../../.."))
sys.path.insert(0, os.path.join(BI, ".claude/qa")); import mintid
EDO = "江戶時代"
JYK = "經義考（四庫全書本）卷%s，https://zh.wikisource.org/wiki/經義考_(四庫全書本)/卷%s"
ROOT = {"易": "d59ezakdey2o", "書": "d59ezajmkjcw", "詩": "d59ezak9zc3k", "儀禮": "d59ezak3445c",
        "禮記": "d59f1iofm800", "左傳": "d59ezak6jq4g", "穀梁": "d59ezajtfrb4", "孝經": "d59f1iosq6tc"}
CIN = "CiNii Books 檢索題名「%s」所見 https://ci.nii.ac.jp/books/search?title=%s"
# 每項：經, 題名, [(責任者,role,entity_id)], 朝代, 關係, 卷數(整數|None), 卷數文字, 依據, 備註, 時代依據
R = [
 ("易","學易宗孔",[("劉應元","撰",None)],"明","studies",2,"二卷",JYK%("62","062")+"，著錄「二卷，存」，並引按語稱作者為楚人，與顧憲成（卒1612）論易",
  "經義考所載之劉應元（字筠喬）；庫內另有清人劉應元《南鴻草》（Entity hixicm3cmne9，朝代清），不同人，故未掛 entity_id","據經義考按語，作者與顧憲成同時，定為明人"),
 ("易","周易通解",[("沈束","撰","hixhd2h9bruk")],"明","contains_text_of",None,"",JYK%("55","055")+"，著錄「沈氏束《周易通解》《易圖》，俱未見」（經義考以雙空格並列兩書）",
  "經義考注：沈束字宗約，會稽人，嘉靖甲辰進士；與庫內他家同題《周易通解》（楊以迥、徐㭿、朱星、卞斌）異書","據 authors[0].dynasty「明」"),
 ("易","易圖",[("沈束","撰","hixhd2h9bruk")],"明","studies",None,"",JYK%("55","055")+"，與《周易通解》並列著錄，俱未見",
  "題名泛，與庫內端木國瑚《易圖》異書；與沈束《周易通解》同條著錄","據 authors[0].dynasty「明」"),
 ("易","繫辭纂義",[("鄒浩","撰","hixhd2h9bfcl")],"北宋","studies",2,"二卷",JYK%("69","069")+"，著錄「宋志二卷，未見」，並引鄒浩自序",
  "庫內鄒浩另有《易解》（d59f2hej6cqp），題名不同，未判同書","據 authors[0].dynasty「北宋」"),
 ("易","易韻補遺",[("董守諭","撰",None)],"明","studies",None,"",JYK%("63","063")+"，與《讀易鈔》《卦變考畧》並列於董守諭條，引陸元輔「著有讀易一抄二抄卦變考畧易韻補遺等編藏於家」，未見",
  "庫內董守諭已有《讀易一鈔》《卦變考略》《易餘》等，無此書；庫內 Entity 董守諭（hixhd2h9bmeb）朝代作清，與經義考所載天啟甲子舉人不符，故未掛 entity_id","經義考載其為天啟甲子（1624）舉人，據以定明"),
 ("書","書傳通",[("陳煥","撰",None)],"趙宋","contains_text_of",None,"",JYK%("84","084")+"，著錄「陳氏煥《書傳通》，未見」，引王圻「煥豐城人」",
  "朝代據經義考排次（前後皆宋元人）推定，庫內同名陳煥另有《詩傳微》《禮記釋》（南宋），未確證為同一人，故未掛 entity_id","經義考卷84排次在宋元人之間；王圻（明）已著錄，故不晚於明；朝代為推定"),
 ("詩","詩經鐸",[("申佳胤","撰","hixhd2h9bfnh")],"明","studies",None,"",JYK%("117","117")+"，著錄「申氏佳胤《詩經鐸》《詩鏡》，俱未見」",
  "體裁未詳，關係暫以 studies 系之；陸元輔注：字孔嘉，永年人，崇禎辛未進士，甲申死寇難","據 authors[0].dynasty「明」"),
 ("詩","詩鏡",[("申佳胤","撰","hixhd2h9bfnh")],"明","studies",None,"",JYK%("117","117")+"，與《詩經鐸》並列，俱未見",
  "與庫內陸時雍《詩鏡》（d59fssnz3itc，選詩）同題異書","據 authors[0].dynasty「明」"),
 ("儀禮","鄉飲酒禮會通",[("許孚遠","撰","hixhd2h9bfvl")],"明","studies",None,"",JYK%("135","135")+"，著錄「許氏孚逺《鄉飲酒禮會通》，未見」",
  "庫內許孚遠名下無此書","據 authors[0].dynasty「明」"),
 ("禮記","投壺新式",[("何宗姚","撰",None)],None,"studies",1,"一卷",JYK%("147","147")+"，著錄「何氏宗姚《投壺新式》一卷，未見（一齋書目有）」",
  "投壺為《禮記》篇名，故系於禮記；經義考注稱《一齋書目》著錄，作者朝代未詳，僅得上限","catalog_bound：經義考注載《一齋書目》（明人書目）著錄，故不晚於明"),
 ("左傳","左氏本末",[("劉伯証","撰",None)],"趙宋","studies",None,"",JYK%("189","189")+"，著錄「劉氏伯証《左氏本末》《三傳制度辨》，俱佚」，引徽州府志「伯証字正甫，歙縣人」",
  "與庫內曹元博《左氏本末》（d59f2gdt8c8y，元）同題異撰人；朝代據經義考排次（前後皆宋人）推定","經義考卷189排次在宋人（趙彥秬、趙崇度）之間；朝代為推定"),
 ("左傳","三傳制度辨",[("劉伯証","撰",None)],"趙宋","studies",None,"",JYK%("189","189")+"，與《左氏本末》並列，俱佚",
  "春秋三傳通論，系於左傳；朝代據經義考排次推定","經義考卷189排次在宋人之間；朝代為推定"),
 ("左傳","春秋左傳雕題略",[("中井積德","撰",None)],EDO,"contains_text_of",6,"六卷",CIN%("春秋左傳雕題略","%E6%98%A5%E7%A7%8B%E5%B7%A6%E5%82%B3%E9%9B%95%E9%A1%8C%E7%95%A5")+"：六卷，中井積德（履軒）著，萬延元年（1860）刊",
  "中井積德即中井履軒；庫內《論語逢源》同作「中井積德」","撰人為日本江戶時代人，與清並行；無論何解皆不晚於 qing"),
 ("左傳","左傳逢原",[("中井積德","撰",None)],EDO,"contains_text_of",12,"十二卷",CIN%("左傳逢原","%E5%B7%A6%E5%82%B3%E9%80%A2%E5%8E%9F")+"：十二卷，[中井履軒撰]，水哉館學自筆稿本",
  "中井積德即中井履軒；另見《域外漢籍珍本文庫》收錄","撰人為日本江戶時代人，與清並行；無論何解皆不晚於 qing"),
 ("左傳","春秋左傳考義",[("龜井魯","撰",None)],EDO,"contains_text_of",4,"四卷",
  "NDL Search 見岡村繁〈龜井南冥「春秋左傳考義」の現存寫本について〉https://ndlsearch.ndl.go.jp/books/R000000004-I1761363；"+CIN%("左傳考義","%E5%B7%A6%E5%82%B3%E8%80%83%E7%BE%A9")+"：江戶後期寫本四卷",
  "龜井魯即龜井南冥；庫內《論語語由》同作「龜井魯」；寫本，撰人據岡村繁論文","撰人為日本江戶時代人，與清並行；無論何解皆不晚於 qing"),
 ("左傳","左傳纘考",[("龜井昭陽","撰",None)],EDO,"contains_text_of",30,"三十卷",CIN%("左傳纘考","%E5%B7%A6%E5%82%B3%E7%BA%98%E8%80%83")+"：三十卷，[龜井昭陽撰]，文政11年（1828）寫本",
  "龜井昭陽為龜井南冥之子","撰人為日本江戶時代人，與清並行；無論何解皆不晚於 qing"),
 ("左傳","左傳標識",[("東條一堂","撰",None)],EDO,"studies",None,"",CIN%("左傳標識","%E5%B7%A6%E5%82%B3%E6%A8%99%E8%AD%98")+"：東條一堂著，寫本；《東條一堂著作集》1963 收",
  "東條一堂即東條弘，庫內《論語知言》作「東條弘」","撰人為日本江戶時代人，與清並行；無論何解皆不晚於 qing"),
 ("左傳","左傳輯釋",[("安井衡","撰",None)],EDO,"contains_text_of",None,"",CIN%("左傳輯釋","%E5%B7%A6%E5%82%B3%E8%BC%AF%E9%87%8B")+"：安井衡撰，明治17年（1884）刊（內藤傳右衞門），臺北廣文書局1978/1979影印",
  "安井衡即安井息軒（1799—1876），幕末至明治初人；成書於明治初，朝代以其主要活動時期記江戶時代","撰人為日本江戶時代人，與清並行；無論何解皆不晚於 qing"),
 ("穀梁","春秋穀梁傳條指",[("江慎中","撰",None)],"清","studies",None,"",
  "段熙仲《公羊》研究要籍舉隅所列「《春秋毂梁傳條指》江慎中 庚戌《國粹學報》」https://www.rujiazg.com/article/31914，庚戌為宣統二年（1910）",
  "載《國粹學報》，是否單行未詳；晚清人","據 authors[0].dynasty「清」（庚戌1910刊於《國粹學報》）"),
 ("穀梁","穀梁真偽攷",[("張西堂","撰",None)],"民國","studies",None,"",
  "CiNii Books NCID BA42857230 https://ci.nii.ac.jp/ncid/BA42857230：張西堂著，和記印書館，1931.8（別題《穀梁眞僞考》）","","據 authors[0].dynasty「民國」"),
 ("孝經","古文孝經序贊",[("洪興祖","撰","hixhd2h9bf9g")],"趙宋","studies",1,"一卷",JYK%("225","225")+"，著錄「洪氏興祖《古文孝經序贊》一卷，未見（一齋書目有）」",
  "庫內洪興祖名下無此書","據 authors[0].dynasty「趙宋」"),
 ("孝經","孝經新讀本",[("唐文治","撰","hixi5fxknyuy")],"民國","contains_text_of",None,"","吳平等主編《孝經文獻集成》（廣陵書社2011）第26冊目錄，CiNii https://ci.nii.ac.jp/ncid/BB09012484",
  "","據 authors[0].dynasty「民國」"),
 ("孝經","孝經要義",[("陳柱","撰",None)],"民國","studies",None,"","《孝經文獻集成》第27冊目錄，CiNii https://ci.nii.ac.jp/ncid/BB09012484；"+CIN%("孝經要義","%E5%AD%9D%E7%B6%93%E8%A6%81%E7%BE%A9")+"：商務印書館1936，國學小叢書",
  "CiNii 著者欄作「陳注」，當為陳柱之誤錄；庫內兩條陳柱 Entity 朝代作清，不合，故未掛 entity_id","據 authors[0].dynasty「民國」"),
 ("孝經","孝經通考",[("蔡汝堃","撰",None)],"民國","studies",None,"","《孝經文獻集成》第29冊目錄，CiNii https://ci.nii.ac.jp/ncid/BB09012484；"+CIN%("孝經通考","%E5%AD%9D%E7%B6%93%E9%80%9A%E8%80%83")+"：商務印書館1937，國學小叢書","","據 authors[0].dynasty「民國」"),
 ("孝經","孔子文昌孝經合刻",[("李鳳彩","輯",None),("周福山","輯",None)],"清","contains_text_of",None,"","《孝經文獻集成》第16冊目錄，CiNii https://ci.nii.ac.jp/ncid/BB09012484；"+CIN%("孔子文昌孝經合刻","%E5%AD%94%E5%AD%90%E6%96%87%E6%98%8C%E5%AD%9D%E7%B6%93%E5%90%88%E5%88%BB")+"：(清)李鳳彩[輯]，乾隆51年（1786）跋",
  "孝經與《文昌孝經》合刻之編本；庫內李鳳彩 Entity（雍正《藏紀概》作者）是否同人未定，故未掛 entity_id","據 CiNii 著錄「(清)李鳳彩」，乾隆51年跋"),
 ("孝經","古文孝經私記",[("朝川鼎","撰",None)],EDO,"contains_text_of",2,"二卷",CIN%("古文孝經私記","%E5%8F%A4%E6%96%87%E5%AD%9D%E7%B6%93%E7%A7%81%E8%A8%98")+"：二巻，朝川鼎著，文化8年（1811）刊；《孝經文獻集成》第30冊亦收",
  "朝川鼎即朝川善庵（1781—1849）","撰人為日本江戶時代人，與清並行；無論何解皆不晚於 qing"),
 ("孝經","孝經參釋",[("川崎魯齋","撰",None)],EDO,"contains_text_of",None,"","CiNii Books NCID BA65611626 https://ci.nii.ac.jp/ncid/BA65611626：川崎魯齊著，一貫堂萬屋忠藏，慶應4年（1868）；《孝經文獻集成》第30冊作「山崎履」，以CiNii為準",
  "CiNii 著者標目作「川崎, 也魯齋」","撰人為日本江戶時代人，與清並行；無論何解皆不晚於 qing"),
 ("孝經","孝經大義詳解",[("蘆川桂洲","撰",None)],EDO,"contains_text_of",4,"四卷首一卷",CIN%("孝經大義詳解","%E5%AD%9D%E7%B6%93%E5%A4%A7%E7%BE%A9%E8%A9%B3%E8%A7%A3")+"：四巻首一巻，蘆川桂洲著，元祿元年（1688）；NDL Search 同；《孝經文獻集成》第29—30冊作「桂洲」",
  "《孝經文獻集成》僅署「桂洲」，據 CiNii／NDL 補全為蘆川桂洲；與庫內董鼎、王守仁《孝經大義》異書","撰人為日本江戶時代人，與清並行；無論何解皆不晚於 qing"),
]
CJK = {"經義考": ""}
def main():
    apply = "--apply" in sys.argv
    import pickle
    sys.path.insert(0, here)
    ex = {}
    for g in glob.glob(os.path.join(BI, "Work/*/*/*/*.json")):
        d = json.load(open(g, encoding="utf-8"))
        ex.setdefault(d["title"], []).append([a.get("name", "") for a in d.get("authors", [])])
    todo = [r for r in R if not any(r[2][0][0][:2] in "".join(n) for n in ex.get(r[1], []))]
    if "--limit" in sys.argv: todo = todo[:int(sys.argv[sys.argv.index("--limit") + 1])]
    print("待建", len(todo), "跳過", len(R) - len(todo))
    if not apply:
        for r in todo: print(r[1], r[2][0][0])
        return
    ids = mintid.mint("Work", "a11-sjj-misc", len(todo))
    for r, i in zip(todo, ids):
        jing, t, au, dyn, rel, n, juan, basis, memo, pbasis = r
        authors = []
        for (name, role, eid) in au:
            a = {"name": name, "role": role}
            if dyn: a["dynasty"] = dyn
            if eid: a["entity_id"] = eid
            authors.append(a)
        d = {"schema_version": 1, "id": i, "type": "work", "title": t, "authors": authors}
        if dyn: d["dynasty"] = dyn
        if n: d["measures"] = [{"unit": "卷", "number": n}]
        if juan: d["measure_info"] = juan
        d["related_works"] = [{"id": ROOT[jing], "relation": rel}]
        note = "2026-11-15 十三經縱向補全（%s）：依據 %s。庫內按異體歸一題名＋責任者查無同書而新建；責任者與卷數取自依據，未逐一考證" % (
            {"易":"周易","書":"尚書","詩":"毛詩","儀禮":"儀禮","禮記":"禮記","左傳":"左傳","穀梁":"穀梁傳","孝經":"孝經"}[jing], basis)
        if jing == "詩": note += "；毛詩原典根條庫內以《詩經》（d59ezak9zc3k）為準，故 related_works 系於該條"
        if memo: note += "；" + memo
        d["ai_note"] = note + "。"
        d["revision"] = "1.0.0"; d["revised_at"] = "2026-11-15"
        if dyn == EDO:
            d["period_upper"] = "qing"; d["period_upper_basis"] = pbasis
        elif dyn is None:
            d["period_upper"] = "ming"; d["period_upper_basis"] = pbasis
        else:
            d["period"] = {"明": "ming", "北宋": "song", "趙宋": "song", "清": "qing", "民國": "modern"}[dyn]
            d["period_basis"] = pbasis
            if "推定" in pbasis or "定為" in pbasis or "據經義考" in pbasis:
                d["dynasty_basis"] = "manual：" + pbasis
        p = "Work/%s/%s/%s/%s-%s.json" % (i[-3], i[-2], i[-1], i, t)
        os.makedirs(os.path.join(BI, os.path.dirname(p)), exist_ok=True)
        open(os.path.join(BI, p), "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
    print("新建", len(todo))
main()
