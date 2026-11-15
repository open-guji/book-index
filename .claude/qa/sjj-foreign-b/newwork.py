#!/usr/bin/env python3
"""十三經縱向補全·外國 1912 前（孝經／孟子，日本 CiNii 候補）：補建庫內無的獨立著作 Work。
口徑（用戶 2026-11-15）：近現代學者著作、民國讀本不錄；他國 1912 年以前者錄；選本單卷不另立 Work。
依據 CiNii Books（cinii_fetch.txt 為建前逐條抓取之記錄：NCID｜題名｜責任者｜出版者｜年）。
用法：newwork.py [--apply]"""
import os, sys, json, glob, re
here = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(here, "../../.."))
sys.path.insert(0, os.path.join(BI, ".claude/qa")); import mintid
EDO, MEIJI = "江戶時代", "明治時代"
ROOT = {"孝": "d59f1iosq6tc", "孟": "d59ezajwvda8"}
JING = {"孝": "孝經", "孟": "孟子"}
CIN = {}
for l in open(os.path.join(here, "cinii_fetch.txt"), encoding="utf-8"):
    p = [x.strip() for x in l.split("|")]
    if len(p) >= 5 and re.match(r"B[A-Z0-9]+$", p[0]): CIN[p[0]] = p
def cb(n):
    p = CIN[n]; return "CiNii Books NCID %s https://ci.nii.ac.jp/ncid/%s：%s，%s，%s" % (n, n, p[2], p[3], p[4])
PB_E = "撰人為日本江戶時代人，與清並行；無論何解皆不晚於 qing"
PB_M = "據 CiNii 刊行年（%s），日本明治時代，與清並行；無論何解皆不晚於 qing；撰人生卒未逐一核"
# 經, 題名, [(責任者,role,entity_id)], 朝代, 關係, 卷數, NCID(主), 備註
R = [
 ("孝","孝經啓蒙",[("中江藤樹","撰",None)],EDO,"contains_text_of",None,"BN09565750","中江藤樹（1608—1648）撰；CiNii 所見為 1939 年目黒書店排印本（西晉一郎解）；同書別本《かながき孝経》（BA5648691X，縣社藤樹神社1942）不另立；庫內劉定之《孝經啓蒙》（d59fxra9w7pc）為異書"),
 ("孝","孝經頌義",[("岡本監輔","撰","hixi8us1n2vl")],MEIJI,"contains_text_of",None,"BA32345108","岡本監輔（1839—1904）"),
 ("孝","古文孝經精解",[("宗内静処","撰",None)],MEIJI,"contains_text_of",None,"BN14657825",""),
 ("孝","古文孝經講義",[("高橋省三","編",None)],MEIJI,"contains_text_of",None,"BB08799252","與松井方景《古文孝經講義》同題異撰"),
 ("孝","古文孝經講義",[("松井方景","述",None)],MEIJI,"contains_text_of",None,"BA62846973","與高橋省三《古文孝經講義》同題異撰"),
 ("孝","古文孝經解釋",[("松井方景","撰",None),("櫻井省吾","撰",None)],MEIJI,"contains_text_of",None,"BA32379154","小學校用"),
 ("孝","孝經義解",[("吉富亀次郎","撰",None)],MEIJI,"contains_text_of",None,"BN14655546",""),
 ("孝","孝經發揮",[("津阪孝綽","撰",None)],EDO,"contains_text_of",None,"BB25517914","津阪孝綽即津阪東陽（1757—1825）；CiNii 所見為 1897 年關西圖書刊本"),
 ("孝","孝經塾本",[("谷銕臣","編",None)],MEIJI,"contains_text_of",None,"BB15694334","CiNii 著錄「谷銕臣手録」"),
 ("孝","古文孝經詳解",[("田中參","述",None)],MEIJI,"contains_text_of",None,"BA32398217","田中亀太郎筆記"),
 ("孝","孝經纂註校本",[("田中正義","撰",None)],MEIJI,"contains_text_of",1,"BB2770960X","與庫內五十川左武郎《孝經纂註》（d59fxs6c7shs）題近而撰人不同"),
 ("孝","古今両用孝經箋註",[("龜山雲平","撰",None)],MEIJI,"contains_text_of",None,"BB25730580","寫本"),
 ("孝","古文孝經訓解",[("東條淡斎","述",None),("峯岸煥","輯",None)],MEIJI,"contains_text_of",None,"BB25713424",""),
 ("孝","諺解古文孝經",[("大槻誠之","撰",None),("大槻篤郎","撰",None)],MEIJI,"contains_text_of",None,"BB25563081","同書另有 BA83568121（大槻東陽、大槻篤郎編，大槻東陽1884）、BA32341752（永松作之助1884）著錄，大槻東陽即大槻誠之"),
 ("孝","今文孝經御註",[("橋村正璟","評註",None)],MEIJI,"contains_text_of",None,"BB12839838","CiNii 著錄「(日本)橋村正璟訓點評註」，註本為唐玄宗御註"),
 ("孝","孝經便蒙",[("竹田定直","撰",None)],EDO,"contains_text_of",None,"BA32398647","竹田定直（1661—1731），貝原益軒訂正；CiNii 所見為 1884 年嵩山房刊本"),
 ("孝","孝經講釋",[("熊澤遊軒","講",None),("大鹽中齊","參釋",None)],EDO,"contains_text_of",None,"BA32342314","大鹽中齋即大塩平八郎（1793—1837），可見成於江戶；CiNii 所見為 1884 年山中市兵衛刊本"),
 ("孝","明治新註古文孝經校本",[("關徳士順","集註",None)],MEIJI,"contains_text_of",None,"BB06483724",""),
 ("孝","孝經纂釋",[("土屋弘","撰",None)],MEIJI,"contains_text_of",None,"BA5058568X","土屋弘即土屋鳳洲"),
 ("孝","孝經淺説",[("椿時中","註釋",None)],MEIJI,"contains_text_of",None,"BA3237740X","新保正與評閱"),
 ("孝","古文孝經簡解",[("二宮哲昌","解",None)],MEIJI,"contains_text_of",None,"BA32348128",""),
 ("孝","畫入譯解古文孝經",[("大舘熙","訓解",None)],MEIJI,"contains_text_of",None,"BA6697912X","CiNii 題「画入譯觧古文孝經」"),
 ("孝","孝經蠡測",[("佐野煥","註釋",None)],MEIJI,"contains_text_of",None,"BA60015269",""),
 ("孝","古文孝經略解",[("渡井量臧","註釋",None)],MEIJI,"contains_text_of",None,"BA32335057","與細野栗齋《古文孝經畧解》同題異撰"),
 ("孝","譯語便蒙古文孝經字引",[("石川孝藏","編",None)],MEIJI,"studies",None,"BB25747608","古文孝經字引；同人另有《古文孝經讀本》（訓點本，BA83946502）按版本處理，不另立"),
 ("孝","古文孝經畧解",[("細野栗斎","撰",None)],MEIJI,"contains_text_of",None,"BA60016942","與渡井量臧《古文孝經略解》同題異撰"),
 ("孝","女學孝經",[("南摩綱紀","編",None),("片山訓熙","訓",None)],MEIJI,"contains_text_of",None,"BC01772255","川瀬益書《女學孝經》（BA71878358，遠藤平左衛門1873；BA48911907，田中治兵衛1890）為同書之書寫本，不另立"),
 ("孝","古文孝經定本",[("朝川善庵","撰",None)],EDO,"contains_text_of",None,"BB25730558","朝川善庵（1781—1849）；CiNii 所見為 1873 年松村九兵衛刊本"),
 ("孝","和言孝經",[("横尾謙","撰",None)],MEIJI,"contains_text_of",None,"BA32418369",""),
 ("孝","孝經講義",[("安藤道","集説",None)],MEIJI,"contains_text_of",1,"BB15705962","萬波栗訂、下野蘊閱；庫內另有永明諸王、潘任、鍾福球、車胤、張雲鸞等同題《孝經講義》，撰人皆異"),
 ("孝","繪本孝經",[("高井蘭山","撰",None)],EDO,"contains_text_of",2,"BN14402482","高井蘭山（1762—1839），葛飾北齋畫圖；元治元年（1864）須原屋新兵衛刊"),
 ("孝","倫理教科孝經採要",[("斎藤清之丞","編述",None)],MEIJI,"contains_text_of",None,"BA83436674","教科書"),
 ("孟","新譯孟子",[("濱野知三郎","註解",None)],MEIJI,"contains_text_of",None,"BN0810170X","附孟子索引"),
 ("孟","孟子と新教育",[("谷本富","講述",None)],MEIJI,"studies",None,"BA34758255",""),
 ("孟","孟子講話",[("駒北堂主人","撰",None)],MEIJI,"studies",None,"BC15845142","署名駒北堂主人"),
 ("孟","蘇批評朱註解孟子講義",[("坂本信次郎","講述",None)],MEIJI,"contains_text_of",None,"BA61378111","馬場讓校閱；與阪本信《蘇批朱註孟子講義》（1900）題近，是否同一人未核，暫分立"),
 ("孟","蘇批朱註孟子講義",[("阪本信","講述",None)],MEIJI,"contains_text_of",None,"BN03672758","與坂本信次郎《蘇批評朱註解孟子講義》（1909）題近，是否同一人未核，暫分立"),
 ("孟","孟子言行録",[("武安衛","撰",None)],MEIJI,"studies",None,"BN15933189","與有馬祐政《孟子言行録》同題異撰"),
 ("孟","孟子言行録",[("有馬祐政","編",None)],MEIJI,"studies",None,"BN1139138X","與武安衛《孟子言行録》同題異撰"),
 ("孟","孟子神髄",[("尾池義雄","撰",None)],MEIJI,"studies",None,"BA44965766",""),
 ("孟","標註孟子",[("深井鑑一郎","標註",None),("山田準","標註",None)],MEIJI,"contains_text_of",None,"BD01660204","書名「標註孟子：教科適用」；同書較早之刊本題《教科適用標註孟子》（BB17818835，誠之堂書店1897），不另立"),
 ("孟","新點孟子撮要",[("桑原俊郎","編",None)],MEIJI,"contains_text_of",None,"BB04085185",""),
 ("孟","孟子養氣章或問圖解",[("山田方谷","撰",None)],EDO,"studies",None,"BA67511870","CiNii 著錄 1902 年版署「山田球」（方谷名球），1875 年寫本（BA75823187）署「山田方谷」，方谷（1805—1877）；養氣章為《孟子》公孫丑上篇"),
 ("孟","孟子學説",[("松村正一","撰",None)],MEIJI,"studies",None,"BN12825339","杉浦重剛閱"),
 ("孟","孟子鈔",[("金港堂書籍編輯所","編",None)],MEIJI,"contains_text_of",None,"BA79681244","庫內無同題；同題另有國語漢文研究會編《孟子鈔》（明治書院，1912），出版月份未核，列入 SKIPPED"),
 ("孟","學校用孟子讀本",[("後藤巳男","標注訓點",None)],MEIJI,"contains_text_of",None,"BB14196706","CiNii 著錄「後藤巳男輔標注訓點」"),
 ("孟","孟子定本",[("安井衡","訂",None)],EDO,"contains_text_of",14,"BA46273741","安井衡即安井息軒（1799—1876）；CiNii 所見為 1885 年本"),
 ("孟","孟子欄外書",[("佐藤一齋","撰",None)],EDO,"contains_text_of",2,"BB15946812","佐藤一齋（1772—1859）；NDL Search 著錄「大学摘説・中庸欄外書・論語欄外書・孟子欄外書 佐藤一斎」https://ndlsearch.ndl.go.jp/ ；CiNii 所見為明治17年（1884）益田祐之寫本（署「一齋居士稿本」）"),
 ("孟","孟子字類大全",[("宮島純熈","編",None)],MEIJI,"studies",None,"BA32499451","頭書畧解；戶屋孝悌校閱"),
 ("孟","孟子摘説",[("吉村彰","撰",None)],MEIJI,"contains_text_of",None,"BN12821859",""),
 ("孟","孟子論文",[("竹添光鴻","撰",None)],MEIJI,"contains_text_of",7,"BN06354318","竹添光鴻即竹添進一郎；另有 BC05966424（奎文堂1882）同書；庫內牛運震、陳履中同題《孟子論文》為異書"),
]
def main():
    apply = "--apply" in sys.argv
    ex = {}
    for g in glob.glob(os.path.join(BI, "Work/*/*/*/*.json")):
        t = os.path.basename(g)[13:-5]
        ex.setdefault(t, []).append(g)
    todo = []
    for r in R:
        if r[6] not in CIN: raise SystemExit("缺 CiNii 記錄 " + r[6])
        hit = []
        for g in ex.get(r[1], []):
            d = json.load(open(g, encoding="utf-8"))
            if any(r[2][0][0][:2] in a.get("name", "") for a in d.get("authors", [])): hit.append(g)
        if not hit: todo.append(r)
    print("待建", len(todo), "跳過", len(R) - len(todo))
    if not apply:
        for r in todo: print(r[1], r[2][0][0]); 
        return
    ids = mintid.mint("Work", "a11-sjj-foreign-b", len(todo))
    out = []
    for r, i in zip(todo, ids):
        jing, t, au, dyn, rel, n, ncid, memo = r
        authors = []
        for (name, role, eid) in au:
            a = {"name": name, "role": role, "dynasty": dyn}
            if eid: a["entity_id"] = eid
            authors.append(a)
        d = {"schema_version": 1, "id": i, "type": "work", "title": t, "authors": authors, "dynasty": dyn}
        if n: d["measures"] = [{"unit": "卷", "number": n}]
        d["related_works"] = [{"id": ROOT[jing], "relation": rel}]
        year = CIN[ncid][4]
        note = "2026-11-15 十三經縱向補全·外國 1912 前（%s）：依據 %s。庫內按異體歸一題名＋責任者查無同書而新建（用戶口徑：他國 1912 年以前著作錄）；責任者與卷數取自依據，未逐一考證" % (JING[jing], cb(ncid))
        if memo: note += "；" + memo
        d["ai_note"] = note + "。"
        d["revision"] = "1.0.0"; d["revised_at"] = "2026-11-15"
        d["period_upper"] = "qing"
        d["period_upper_basis"] = PB_E if dyn == EDO else PB_M % year
        p = "Work/%s/%s/%s/%s-%s.json" % (i[-3], i[-2], i[-1], i, t)
        os.makedirs(os.path.join(BI, os.path.dirname(p)), exist_ok=True)
        open(os.path.join(BI, p), "w", encoding="utf-8").write(json.dumps(d, ensure_ascii=False, indent=2) + "\n")
        out.append((i, t, au[0][0], p))
    json.dump(out, open(os.path.join(here, "created.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    print("新建", len(todo))
main()
