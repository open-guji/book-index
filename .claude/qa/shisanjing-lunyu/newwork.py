#!/usr/bin/env python3
"""十三经纵向补全·论语：据嚴靈峯《無求備齋論語集成》書目補建库内无的独立著作 Work。用法：newwork.py [--apply]
依据与比对见 ai-team domain/目录与资源/设计/2026-11-十三经纵向补全/论语.md。"""
import os, sys, json, glob, importlib.util
here = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(here, "../../.."))
sys.path.insert(0, os.path.join(BI, ".claude/qa")); import mintid
ROOT = "d59f1iopaku8"   # 論語 原典
EDO = "江戶時代"
# (題名, 責任者, role, 朝代, entity_id, 關係, 卷數, 備註)
R = [
 ("論語傳授考略","嚴靈峯","撰","民國",None,"studies","一卷",""),
 ("論語點睛補助","釋智旭","撰","明","hixhd2h9bntx","contains_text_of","二卷","江謙補注"),
 ("論語疏證","楊樹達","撰","民國","hixhd2h9brle","studies","二十卷",""),
 ("論語新證","于省吾","撰","民國",None,"studies","一卷",""),
 ("論語古訓正文","太宰純","撰",EDO,"hixicdy3hjxx","contains_text_of","二卷",""),
 ("論語繹解","皆川淇園","撰",EDO,None,"contains_text_of","十卷","著錄作「皆川原」，據書名擬為皆川淇園，待核"),
 ("論語語由","龜井魯","撰",EDO,None,"contains_text_of","二十卷",""),
 ("論語徵批","岡白駒","撰",EDO,None,"studies","一卷",""),
 ("論語逢源","中井積德","撰",EDO,None,"contains_text_of","二十卷",""),
 ("論語集解考異","吉田漢官","撰",EDO,None,"studies","十卷",""),
 ("論語考文","豬飼彥博","撰",EDO,None,"studies","一卷",""),
 ("論語說抄","豬飼彥博","撰",EDO,None,"contains_text_of","一卷",""),
 ("論語欄外書","佐藤坦","撰",EDO,None,"studies","二卷",""),
 ("論語知言","東條弘","撰",EDO,None,"contains_text_of","十卷",""),
 ("論語剳記","岡田欽","撰","日本",None,"studies","一卷","著錄作日本岡田欽，朝代未明"),
 ("論語序說私考","伊藤馨","撰","日本",None,"studies","一卷","朝代未明"),
 ("論語義疏校刊記","武內義雄","撰","民國",None,"studies","一卷","日本學者，現代人"),
 ("論語古義","伊藤維楨","撰",EDO,None,"contains_text_of","十卷","與惠棟《論語古義》（d59fy2dezd34）同題異書"),
 ("論語古訓","太宰純","撰",EDO,"hixicdy3hjxx","contains_text_of","十卷","與陳鱣《論語古訓》（d59f2na7blkx）同題異書"),
 ("論語新註","豐島幹","撰",EDO,None,"contains_text_of","二卷","與盧懋《論語新註》同題異書"),
 ("論語駁異","海保鶴皐","撰",EDO,None,"studies","一卷","與王衡《論語駁異》（d59f2nd1eb5v）同題異書"),
 ("讀論語","廣瀨建","撰",EDO,None,"contains_text_of","一卷","與曹珖、方鑄《讀論語》同題異書"),
]
CN = {"一":1,"二":2,"三":3,"十":10}
def num(s):
    s=s.rstrip("卷")
    if s.startswith("二十"): return 20+(CN.get(s[2:],0))
    if s.startswith("十"): return 10+CN.get(s[1:],0)
    return CN[s]
def main():
    apply = "--apply" in sys.argv
    ex = {}
    for g in glob.glob(os.path.join(BI,"Work/*/*/*/*.json")):
        d=json.load(open(g,encoding="utf-8")); ex.setdefault(d["title"],[]).append([a.get("name","") for a in d.get("authors",[])])
    todo=[r for r in R if not any(r[1][:2] in "".join(n) for n in ex.get(r[0],[]))]
    print("待建",len(todo),"跳過",len(R)-len(todo))
    if not apply:
        for r in todo: print(r[0],r[1])
        return
    ids = mintid.mint("Work","a11-shisanjing",len(todo))
    for r,i in zip(todo,ids):
        t,name,role,dyn,eid,rel,juan,memo = r
        a={"name":name,"role":role,"dynasty":dyn}
        if eid: a["entity_id"]=eid
        d={"schema_version":1,"id":i,"type":"work","title":t,"authors":[a],"dynasty":dyn,
           "measures":[{"unit":"卷","number":num(juan)}],"measure_info":juan,
           "related_works":[{"id":ROOT,"relation":rel}],
           "ai_note":"2026-11-15 十三經縱向補全（論語）：據嚴靈峯《無求備齋論語集成》書目（儒家網轉載 https://www.rujiazg.com/article/2514）著錄，庫內無同題同撰人 Work 而新建。卷數取自該目，未覆核；責任者未逐一考證"+("；"+memo if memo else "")+"。",
           "revision":"1.0.0","revised_at":"2026-11-15"}
        if dyn==EDO:
            d["period_upper"]="qing"; d["period_upper_basis"]="撰人為日本江戶時代人，與清並行；歧而未決，無論何解皆不晚於 qing"
        elif dyn=="民國":
            d["period"]="modern"; d["period_basis"]="據 authors[0].dynasty「民國」"
        elif dyn=="明":
            d["period"]="ming"; d["period_basis"]="據 authors[0].dynasty「明」"
        p="Work/%s/%s/%s/%s-%s.json"%(i[-3],i[-2],i[-1],i,t)
        os.makedirs(os.path.join(BI,os.path.dirname(p)),exist_ok=True)
        open(os.path.join(BI,p),"w",encoding="utf-8").write(json.dumps(d,ensure_ascii=False,indent=2)+"\n")
    print("新建",len(todo))
main()
