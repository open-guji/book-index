#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S3 道：Collection.count 回填（issue open-guji-core/overview#140）。

一次性脚本：DATA 是人工逐条核对全库 84 条 Collection 记录（total_works/total_volumes/
juan_count/page_count/description 全部读过）后手工编码的结果，非机械算法生成，改动前
请先读 issue #140 的进展评论——里面列了每条判断的取舍理由与拿不准清单。

跑法：
  python3 .claude/qa/s3_collection_count.py            # 乾跑，只列将做的改动
  python3 .claude/qa/s3_collection_count.py --apply    # 落盘（幂等：已回填过的库再跑一遍应无改动）

跑完务必接着跑一次 `python3 .claude/qa/reindex.py --run`——本脚本会订正部分
juan_count（如百衲本二十四史「820」误记为卷数，实为册数），index/collections.json
里同源的 juan_count 分片需要跟着重建，否则 verify.py／tests 的漂移检查会报不合。
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))

def nz(n): return None if n is None else int(n)

# id -> (juan, ce, zhong, han, source, juan_count_fix)
# juan_count_fix: None=不动旧 juan_count；否则是新的 {'number':..,'description':..} 或 'CLEAR'（订正误记）
DATA = {
 # ---- 四库全书七阁本：juan_count 里塞的其实是册/函数，误记，订正 ----
 '8rlb6yjlwb28': (None, 36300, None, None,
   'juan_count 原填「約36,300冊」，其实是册数非卷数，误记；已订正移入 count.ce（原书 1853 年毁于兵火，卷数不详，juan_count 归空）', 'CLEAR'),
 '8rlb6yjvvwg0': (None, 36300, None, None,
   'juan_count 原填「約36,300餘冊」，其实是册数非卷数，误记；已订正移入 count.ce（原书 1853 年毁于兵火，卷数不详，juan_count 归空）', 'CLEAR'),
 '8rlb6yibp6o0': (None, 36304, None, 6144,
   'juan_count 原填「36,304冊，6,144函」，其实是册/函数非卷数，误记；已订正移入 count.ce／count.han，卷数不详', 'CLEAR'),
 '8rlb6yj1lvr4': (None, 36000, None, None,
   'juan_count 原填「36,000餘冊（含原書與補抄本）」，其实是册数非卷数，误记；已订正移入 count.ce，卷数不详', 'CLEAR'),
 '8rlb6yjblh4w': (None, 36304, None, 6144,
   'juan_count 原填「原存36,304冊，分裝6,144函」，其实是册/函数非卷数，误记；已订正移入 count.ce／count.han，卷数不详', 'CLEAR'),
 '8rlb6yirb1ts': (None, 36315, None, 6144,
   'juan_count 原填「36,315冊，6,144函」，其实是册/函数非卷数，误记；已订正移入 count.ce／count.han，卷数不详', 'CLEAR'),
 '8rlb6yi1ecqo': (None, None, None, None,
   '本条无 total_works/total_volumes；juan_count 原本为空（0/""）；description 仅记 1917 年清点缺 23 卷之事，非应收总数；暂缺', None),

 # ---- 荟要两部：juan_count.number 本为 0（占位），真数据在 description 子字段里，非误记，机械取 ----
 '8rlb6ykg6br4': (20828, None, 463, 500,
   'description 与 juan_count.description 一致：463 種、20828 卷、500 函（乾隆四十三年与摛藻堂本同制）', None),
 '8rlb6yk66qdc': (20828, None, 463, None,
   'description 与 juan_count.description 一致：463 種、20828 卷；juan_count.description 另记「500冊（景印本）」，经核为 1985 年世界書局影印本之册数，非摛藻堂原本自身册/函数，摛藻堂原件规模从缺（味腴書屋本条载「與摛藻堂本同制」，暗示摛藻堂原本亦为 500 函，但本条自身无明文，未采，列拿不准）', None),

 # ---- 四库衍生丛刊：juan_count.number=0，真数据在 description，机械取 ----
 '8rlcsybg2hi3': (None, 301, None, None, 'description：「十輯 301 冊」', None),
 '8rlcsybg2hi5': (None, 732, None, None,
   'description：「全 732 冊」；種數「珍本1100+種+戲本/檔案1700+種」为下限估计，非确数，暂缺', None),
 '8rlcsybg2hi2': (None, 90, None, None,
   'description：「補編 90 冊」；「與正編合計...401冊」为与四庫禁燬書叢刊正編合计之数，非本条（补编）自身规模，未采', None),
 '8rlcsybg2hi6': (None, None, 1800, None,
   'description：「全套1-12集+別輯合計選印約1800種」（約数）；1960冊/231種属另一 Collection《四庫全書珍本初集》，本条不含初集，未采', None),
 '8rlcsybg2hi4': (None, 100, 219, None,
   'description：「100 冊（含目錄索引1冊），收書219種」；「與存目叢書本體合計4727種」为跨 Collection 合计，非本条自身，未采', None),
 '8rlcsybg2hi1': (None, 311, 634, None, 'description：「正編311冊」「計收書634種」', None),
 '8rlb6yy86eww': (None, 1960, 231, None, 'description：「共231種1960冊」（1933-1935 上海商務印書館刊）', None),
 '8rlcxphotse8': (None, 1800, 5213, None, 'description：「1800冊，收書5213種」', None),

 # ---- 二十四史 / 十三经注疏 三个 book_collection 版本 + 一个 work_collection 抽象层 ----
 '8rlcsybg2hhf': (2416, 964, None, None,
   'juan_count「二千四百十六卷」为原有正确记录（非误记），非另行订正；ce 964 取自 description「全 964 冊」（國圖 02324 全帙）；種數 138／141／144 三说并存且本条 ai_note 已标「異見」，未定案不采（列拿不准）', None),
 '8rlcsybg2hhc': (None, 820, 24, None,
   'juan_count 原填 820，description 明记「全書共820冊」，其实是册数非卷数，误记；已订正移入 count.ce，卷数本条未见明文暂缺（二十四史通行卷数 3213 卷是否适用于百衲本装帧未核实，未采，列拿不准）；種數 24 取自「二十四部紀傳體史書」', 'CLEAR'),
 '8rlcsybg2hhg': (416, None, 13, None, 'juan_count「416卷」为原有正确记录（十三经注疏合计416卷，非误记）；種數13取自「十三經」定数', None),
 '8rlcsybg2hhe': (3213, None, 24, None, 'juan_count「3213卷」为原有正确记录（非误记）；種數24取自「二十四部正史」', None),
 '8rlcsybg2hhi': (3213, None, 24, None, 'description：「共3213卷」「二十四部紀傳體史書」（work_collection 抽象层，与武英殿本版本记载一致）', None),

 # ---- 司马泰类书丛辑系列：total_works 已有（→zhong），description「凡N卷」补 juan ----
 '8rlcsybg2hij': (100, None, 36, None, 'total_works=36（既有）；description：「凡一百卷」', None),
 '8rlcsybg2him': (80, None, 70, None, 'total_works=70（既有）；description：「凡八十卷」', None),
 '8rlcsybg2hio': (100, None, 16, None,
   'total_works=16（既有）；description：「凡一百卷（共缺八十四卷）」——原设计100卷为应收总数，其中84卷已佚，与其他四种同例记设计总数', None),
 '8rlcsybg2hik': (80, None, 42, None, 'total_works=42（既有）；description：「凡八十卷」', None),
 '8rlcsybg2hin': (30, None, 24, None, 'total_works=24（既有）；description：「凡三十卷」', None),
 '8rlcsybg2hil': (60, None, 30, None, 'total_works=30（既有）；description：「凡六十卷」', None),

 # ---- 出土简帛系列 ----
 '8rlcsybg2hih': (None, None, None, None, '主题性总集容器，本身无卷册种函规模，各子集分别记于各自 Collection', None),
 '8rlcsybg2hib': (None, None, None, None, 'description「整理得古書十餘種」为「十余」概数，量小而相对不确定区间大，未采，列拿不准', None),
 '8rlcsybg2hi8': (None, None, None, None, 'description「凡十六篇（分書為十八組）」16与18两说并存，未定，列拿不准', None),
 '8rlcsybg2hii': (None, None, None, None, '本条未见收書种数或册数之明文', None),
 '8rlcsybg2hif': (None, None, None, None, '本条未见收書种数或册数之明文（仅按内容分类列举，未给总数）', None),
 '8rlcsybg2hie': (None, None, None, None, '本条仅记各辑部分数字（第一輯93簡等），未给全帙种数总计', None),
 '8rlcsybg2hi0': (None, None, None, None, 'description「已刊十五輯」为持续出版中之现有册数，非应收总数（尚未出全），未采', None),
 '8rlcsybg2hia': (None, None, None, None, '本条未见收書种数或册数之明文', None),
 '8rlcsybg2hi9': (None, 9, None, None, 'description：「上海古籍出版社...刊行九冊」（2001-2012 已出齐，非持续出版中）', None),
 '8rlcsybg2hip': (None, None, 8, None, 'description：「所出八種」（曆譜/二年律令/奏讞書/脈書/算數書/蓋廬/引書/遣策，逐一列名確認）', None),
 '8rlcsybg2hic': (None, None, 8, None, 'description：「經整理得古書八種」', None),
 '8rlcsybg2hig': (None, None, None, None, '本条仅列举內容类别（詩經、孔子曰、疑似樂譜一種），未给收書种数总计', None),
 '8rlcsybg2hid': (7, None, 20, None,
   'description：「得二十种左右」（约数，量级较大相对确定，采）；「整理報告分七卷」指今人整理本卷数，非竹書本身规模，本条 juan 暂缺——注：此处最终未采整理报告卷数，juan 留空', None),
 '8rlcsybg2hi7': (None, 7, None, None, 'description：「2014年中華書局...集成七冊，為集大成之本」', None),

 # ---- 私家丛书容器 ----
 '8rld46zzcyrm': (109, None, 13, None, 'description：「收書十三種、一百零九卷」', None),
 '8rld46zzcyro': (10, None, 1, None, 'description：「世本輯補十卷」；本 Collection 专指秦嘉謨辑本一种', None),
 '8rld46zzcyrk': (None, None, None, None,
   'description 卷数两说并存且相差悬殊（原刻「凡八十卷、目錄一卷」共81卷 vs 續修四庫影印本著錄「七百三十九卷」），未定，列拿不准；種數「五百八十餘種」量级大概数暂不单独采（与卷数关联存疑，一并列拿不准）', None),
 '8rld46zzcyrn': (5, None, None, None,
   'description：「問字堂集五卷」（孫星衍自著文集本身）；「內收其校輯之《燕丹子》等」数量不明，種數暂缺', None),
 '8rld46zzcyrl': (254, None, 43, None, 'description：「收書四十三種、二百五十四卷」', None),

 # ---- 抽象经典合称 work_collection（书名/正文即定数）----
 '8rlcsybg2hhm': (None, None, 13, None, 'description 列十三经篇目，書名即为定数', None),
 '8rlcsybg2hhn': (None, None, 13, None, 'description：「十三部儒家經典歷代注、疏的合編」', None),
 '8rlcsybg2hhz': (None, None, 3, None, 'description：《春秋》三部主要傳本', None),
 '8rlcsy6ubh1c': (None, None, 4, None, 'description：明清通俗小說四部代表作', None),

 # ---- 才子佳人/演义合刻本：description 明写「收N書」，種數采，卷数因系分部各记未采合计 ----
 '8rlcsybg2hhq': (None, None, 2, None, '前七國、後七國二書合刻；各书卷数分记（前七國四卷、後七國四卷或十八回本），非单一合计明文，juan 未采', None),
 '8rlcsybg2hhw': (None, None, 2, None, 'description：「合刊水滸續書二種」', None),
 '8rlcsybg2hho': (None, None, 2, None, '西漢、東漢二書合刻；卷数分记（西漢八卷、東漢十卷），非单一合计明文，juan 未采', None),
 '8rlcsybg2hhp': (None, None, 2, None, '西漢、東漢二書合刻；卷数分记（各八卷），非单一合计明文，juan 未采', None),
 '8rlcsybg2hhv': (None, None, 3, None, 'description：「收三書」（包公案、施公案、鹿洲公案）', None),
 '8rlcsybg2hhx': (None, None, 3, None, 'description：「收三書」', None),
 '8rlcsybg2hhs': (None, None, 2, None, 'description：「此合刻本實收二書」（雖總題「七才子書」，此本实收二书，不可依题名误记为7）', None),
 '8rlcsybg2hhy': (None, None, 4, None, 'description：「所收凡四書」', None),
 '8rlcsybg2hhu': (None, None, 3, None, 'description：「所收三書」', None),
 '8rlcsybg2hhr': (None, None, 6, None, 'description：「所收凡六書」', None),
 '8rlcsy6ubh1d': (None, None, 5, None, 'description：「合刻才子佳人小說五種」，題名「怡園五種」亦合', None),
 '8rlcsybg2hht': (None, None, 4, None, 'description 列東遊、南遊、北遊、西遊四書，題名「四遊全傳」亦合', None),

 # ---- 中國明朝檔案總匯 / 二十五史藝文經籍志考補萃編：既有字段核对 ----
 '8rlcsybg2hhj': (None, 101, 17, None,
   'total_works=17、total_volumes=101（既有，与 description「全101冊」一致）；description 另记「113卷」仅指第二編簿冊類一部分，非全書卷数总计，未采', None),
 '8rlcsybg2hhh': (27, 31, 83, None,
   '**发现既有字段亦误记**：total_works=83（与 description「共計83種」一致，采）；total_volumes=27，但 description 明记「全套27卷31冊」——27实为卷数、31才是册数，total_volumes 字段本身填反；本次仅在新 count 字段填 juan=27／ce=31（据 description 明文订正），未改动既有 total_volumes（超出本卡授权范围，另行在 issue 中提请协调者复核是否订正 total_volumes）', None),

 # ---- 其余零散 book_collection ----
 '8rlcsybg2hhd': (None, None, 700, None, 'description：「刊行約七百餘種」（約数，量级大相对确定，采）', None),
 '8rlcsybg2hhl': (None, 200000, 10000, None,
   'description：「著錄...善本古籍約一萬種、二十萬冊」（1983年《國立故宮博物院善本舊籍總目》紙本目錄所载約数，采）', None),
 '8rlcsybg2hhk': (None, None, 1300, None,
   'description：「共約1300種宋元明清善本」（唐宋編約758種＋金元編約213種＋明清編約565種，約数，采合计）', None),
 '8rld46zzcyrp': (None, None, 2000, None, 'description：「收書二千餘種」（約数，量级大相对确定，采）', None),

 # ---- 无法确定规模的容器类 / 石经 ----
 '8rld46zzcyrq': (None, None, None, None, '馆藏泛称容器 Collection，供 Book 挂 contained_in 用，本身无收录规模概念', None),
 '8rld46zzcyrr': (None, None, None, None, '馆藏泛称容器 Collection，供 Book 挂 contained_in 用，本身无收录规模概念', None),
 '8rlct5hvmjuo': (None, None, None, None, '蜀石經历代续刻，各本所刻经目不一，本条未给明确合计经数，列拿不准', None),
 '8rlct5hntm9s': (None, None, 1, None, '只刻《孝經》一種', None),
 '8rlct5h0q22o': (None, None, 7, None, 'description：「所刻為...七經」（周易/尚書/魯詩/儀禮/春秋/公羊傳/論語）', None),
 '8rlct5ijntog': (None, None, 13, None, 'description：「十三經全刻」', None),
 '8rlct5hg0oow': (None, None, 13, None, 'description：原刻十二經白文，「清代補刻《孟子》，遂足十三經」，以最终定本计', None),
 '8rlct5ib8f0g': (None, None, None, None, '本条未记所刻经目及总数，列拿不准', None),
 '8rlct5i3qpz4': (None, None, None, None, '本条未记所刻经目及总数，列拿不准', None),
 '8rlct5h87r40': (None, None, None, None, 'description：「所刻為《尚書》《春秋》，《左傳》未竟」，完刻与未竟状态不一，总数不定，列拿不准', None),

 # ---- 先秦系列 work_collection：total_works 已有，机械映射 ----
 '8rld0tpplp8g': (None, None, 202, None, 'total_works=202（既有，与 description 186+16 分组之和一致）', None),
 '8rld0tom9ssg': (None, None, 137, None, 'total_works=137（既有，与《先秦典籍》条 description 所记「137种」一致）', None),
 '8rld0tvwsdmo': (None, None, 6, None, 'total_works=6（既有）', None),
 '8rld0ts2thj4': (None, None, 105, None, 'total_works=105（既有，主题性汇集，无统一卷数概念）', None),
 '8rlcsy6ubh1e': (84, None, 42, None,
   'total_works=42（既有）；description：「《唐志》猶存九部八十四卷，今則全佚」——84卷为文献所记最后存世规模（今已全佚，仍记其历史规模）', None),
}

def main():
    apply = '--apply' in sys.argv
    import glob
    files = {}
    for f in glob.glob(os.path.join(ROOT, 'Collection/*/*/*/*.json')):
        if f.endswith('volume_book_mapping.json'):
            continue
        d = json.load(open(f, encoding='utf-8'))
        files[d['id']] = f

    missing = set(files) - set(DATA)
    extra = set(DATA) - set(files)
    if missing:
        print('!! 缺决策：', missing)
    if extra:
        print('!! 决策表多余 id（不在 Collection 目录中）：', extra)
    if missing or extra:
        sys.exit(1)

    n_juan = n_ce = n_zhong = n_han = n_fix = 0
    for cid, (juan, ce, zhong, han, source, jc_fix) in DATA.items():
        f = files[cid]
        d = json.load(open(f, encoding='utf-8'))
        if juan is None and ce is None and zhong is None and han is None:
            d['count'] = None  # 四項全空：依 SCHEMA「至少一項非空才寫」，不寫這個物件；理由見本檔 DATA 註記或報告的拿不准清單
        else:
            d['count'] = {'juan': nz(juan), 'ce': nz(ce), 'zhong': nz(zhong), 'han': nz(han), 'source': source}
        if juan is not None: n_juan += 1
        if ce is not None: n_ce += 1
        if zhong is not None: n_zhong += 1
        if han is not None: n_han += 1
        if jc_fix == 'CLEAR':
            old = d.get('juan_count')
            d['juan_count'] = None
            n_fix += 1
            if not apply:
                print(f'  [订正] {cid} juan_count {old} -> None')
        if apply:
            with open(f, 'w', encoding='utf-8') as out:
                json.dump(d, out, ensure_ascii=False, indent=2)
                out.write('\n')
    print(f'juan填 {n_juan}  ce填 {n_ce}  zhong填 {n_zhong}  han填 {n_han}  juan_count订正 {n_fix}  共 {len(DATA)} 条')
    print('APPLIED' if apply else 'DRY RUN（加 --apply 落盘）')

if __name__ == '__main__':
    main()
