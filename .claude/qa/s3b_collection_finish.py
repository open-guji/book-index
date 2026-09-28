#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S3b 道：Collection 小补（issue open-guji-core/overview#171）。

一次性脚本，做三件事：
1. 订正《二十五史藝文經籍志考補萃編》（8rlcsybg2hhh）total_volumes：description 明记
   「全套27卷31冊」，既有 total_volumes=27 实为字段填反（27 是卷数），S3（overview#140）
   已在 count.juan/count.ce 填对但因超出该卡授权范围未订正 total_volumes 本身；本卡订正。
2. 回补 S3 拿不准未写 count 的 17 条里、本次逐条复核后能定的 13 条（其余 4 条本次仍拿不准，
   保持不写，理由见 UNRESOLVED）。
3. 给全库 84 条 Collection 补 `_member_type`（派生：由 books／contained_works 是否非空机械
   推出，见 SCHEMA.md、.claude/qa/verify.py:derive_member_type）。

跑法：
  python3 .claude/qa/s3b_collection_finish.py            # 干跑，只列将做的改动
  python3 .claude/qa/s3b_collection_finish.py --apply    # 落盘（幂等：再跑一遍应无改动）
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import verify

# ---- 1. total_volumes 订正 ----
TOTAL_VOLUMES_FIX = {
    '8rlcsybg2hhh': 31,
}

# S3（overview#140）填 count.source 时，total_volumes 订正尚未授权，原文说「未改动既有
# total_volumes...另行提请协调者复核」；本卡（overview#171）已订正，该句转陈述句，随
# total_volumes 一并更新，避免留下自相矛盾的旧记录。
COUNT_SOURCE_AMEND = {
    '8rlcsybg2hhh': (
        '未改动既有 total_volumes（超出本卡授权范围，另行在 issue 中提请协调者复核是否订正 total_volumes）',
        '既有 total_volumes 已由本卡（overview#171）订正为 31（原 27 系卷冊互填反，见上）',
    ),
}

def nz(n): return None if n is None else int(n)

# ---- 2. count 回补：id -> (juan, ce, zhong, han, source) ----
COUNT_FILL = {
 '8rlb6yi1ecqo': (79309, None, 3461, None,
   'contains[] 之「main_corpus／正書」項 scope 明記「3461 部、79309 卷」（不含聖諭、進表、'
   '凡例、門目、《總目》、《簡明目錄》、《考證》、分架圖等前置及附屬部分，這些另計於 contains，'
   '非平列成員）；description 僅記 1917 年清點缺 23 卷之事，非應收總數，未採；冊／函數本條未見'
   '明文，暫缺'),
 '8rlcsybg2hib': (None, None, 14, None,
   'description「整理得古書十餘種」為量小相對不確定之約數，S3 未採；本次改核 books 成員清單：'
   '14 條互不相同之獨立 Book 記錄（詩經、周易、蒼頡篇、萬物、年表、大事記、春秋事語、儒家者言、'
   '作務員程、行氣、相狗經、刑德、日書、算術書），機械計數 zhong=14'),
 '8rlcsybg2hi8': (None, None, 18, None,
   'description「凡十六篇（分書為十八組）」16／18 兩說並存，S3 未定；本次改核 books 成員清單：'
   '18 條獨立 Book 記錄（《老子》甲乙丙分記三種、《語叢》一至四分記四種等），與「十八組」一致，'
   '本庫收書種數之口徑以此 18 條為準，zhong=18'),
 '8rlcsybg2hii': (None, None, 2, None,
   'description 未見收書種數明文；books 成員清單列 2 條（長台關一號楚墓竹書、長台關一號楚墓'
   '遣策），機械計數 zhong=2'),
 '8rlcsybg2hif': (None, None, 12, None,
   'description 未見收書種數明文；books 成員清單列 12 條獨立 Book（詩經、論語、孝經、春秋、'
   '儀禮、禮記、易經、知道、悼亡賦、五色食勝、海昏侯墓醫書、六博棋譜），機械計數 zhong=12'),
 '8rlcsybg2hie': (None, None, 6, None,
   'description 未見收書種數明文；books 成員清單列 6 條獨立 Book（詩經、曹沫之陳、仲尼曰、'
   '善而、哀誦、申徒狄見周公），機械計數 zhong=6'),
 '8rlcsybg2hia': (None, None, 14, None,
   'description 未見收書種數明文；books 成員清單列 14 條獨立 Book（孫子兵法、孫臏兵法、尉繚子、'
   '晏子、六韜、吳問、四變、黃帝伐赤帝、地形二、見吳王、守法守令十三篇、論政論兵之類、陰陽時令'
   '占候之類、元光元年曆譜），機械計數 zhong=14'),
 '8rlcsybg2hig': (None, None, 3, None,
   'description「《詩經·國風》、體裁近《論語》之《孔子曰》，及一種疑為樂譜之新見簡冊」與 books '
   '成員清單（詩經、孔子曰、王家嘴楚簡樂譜）3 條互證，zhong=3'),
 '8rld46zzcyrk': (None, None, 580, None,
   'description「凡八十卷、目錄一卷，共得五百八十餘種（《續修四庫全書》影印本著錄作七百三十九'
   '卷）」——卷數兩說並存（81 卷 vs 739 卷）仍拿不準，juan／ce／han 留空；惟「五百八十餘種」為'
   '獨立於卷數爭議之單一數字，屬量級較大之約數（比照 S3 對「約」「餘」類大數之採納慣例，如'
   '「二千餘種」「七百餘種」），據此填 zhong=580（約數，見 description 原文）'),
 '8rlct5hvmjuo': (None, None, 13, None,
   'Collection 自身 description「《孟子》入石經自蜀石經始，開十三經之數」；其存世拓本之一（Book '
   '9898t4083k）description 明列現存 4 經（左傳、穀梁傳、周禮、公羊傳）與缺佚 9 經（孝經、論語、'
   '爾雅、周易、毛詩、尚書、儀禮、禮記、孟子），4+9=13，與「十三經之數」互證，確定蜀石經原刻經目'
   '總數 zhong=13'),
 '8rlct5ib8f0g': (None, None, 7, None,
   'description 未記所刻經目及總數；books 成員清單列 7 條（周易、尚書、詩經、左傳、論語、孟子、'
   '中庸），機械計數 zhong=7'),
 '8rlct5i3qpz4': (None, None, 4, None,
   'description 未記所刻經目及總數；books 成員清單列 4 條（周易、尚書、禮記、孝經），機械計數 '
   'zhong=4'),
 '8rlct5h87r40': (None, None, 2, None,
   'description「所刻為《尚書》《春秋》，《左傳》未竟」——左傳未竟不計入已完成刻經數；books 成員'
   '清單列 2 條（尚書、春秋），與已完成部分一致，zhong=2'),
}

# 本次仍拿不准、保持不写 count 的 4 条（S3 原 17 条余下部分）——原因见此，供复核者核对，非落盘数据
UNRESOLVED = {
 '8rlcsybg2hih': '主題性總集容器（出土簡帛），本身無卷冊種函規模，各子集分別記於各自 Collection；'
   '「凡十二批」為子集清單，無結構化 related_collections／members 可據，不可與其下屬各 Collection '
   '各自的 count 相加或另立一個總數（會與各子集重複計算），保持不寫',
 '8rlcsybg2hi0': '清華大學藏戰國竹簡：books 現有 70 條，然 description 明記「整理報告...至 2025 年'
   '已刊十五輯」，係持續整理出版中、尚未出全，現有 70 條為現存下限而非應收總數，保持不寫',
 '8rld46zzcyrq': '館藏泛稱容器 Collection（國家圖書館〔臺灣〕善本舊籍），供館藏古籍之 Book 掛 '
   'contained_in 用，本身無收錄規模概念（開放容器，非有限定總數之叢編），保持不寫',
 '8rld46zzcyrr': '館藏泛稱容器 Collection（天津市圖書館），同上，保持不寫',
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

    missing = (set(TOTAL_VOLUMES_FIX) | set(COUNT_FILL) | set(UNRESOLVED)) - set(files)
    if missing:
        print('!! 決策表裡的 id 不在 Collection 目錄中：', missing)
        sys.exit(1)

    n_tv = n_count = n_mt = n_amend = 0
    mt_dist = {}

    for cid, new_tv in TOTAL_VOLUMES_FIX.items():
        f = files[cid]
        d = json.load(open(f, encoding='utf-8'))
        old = d.get('total_volumes')
        old_src, new_src = COUNT_SOURCE_AMEND.get(cid, (None, None))
        changed = False
        if old != new_tv:
            d['total_volumes'] = new_tv
            n_tv += 1
            changed = True
            if not apply:
                print(f'  [total_volumes] {cid} {old} -> {new_tv}')
        cur_src = (d.get('count') or {}).get('source') or ''
        if old_src and old_src in cur_src:
            d['count']['source'] = cur_src.replace(old_src, new_src)
            n_amend += 1
            changed = True
            if not apply:
                print(f'  [count.source 改述] {cid}')
        if changed and apply:
            with open(f, 'w', encoding='utf-8') as out:
                json.dump(d, out, ensure_ascii=False, indent=2)
                out.write('\n')

    for cid, (juan, ce, zhong, han, source) in COUNT_FILL.items():
        f = files[cid]
        d = json.load(open(f, encoding='utf-8'))
        target = {'juan': nz(juan), 'ce': nz(ce), 'zhong': nz(zhong), 'han': nz(han), 'source': source}
        existing = d.get('count')
        if existing == target:
            continue  # 已回補過，幂等跳過
        if existing is not None:
            print(f'!! {cid} 已有 count 且與本表不同，跳過落盤（本表只回補 S3 拿不准之 17 條中'
                  f'已定案者，不應與既有 count 衝突）：現有 {existing}　本表 {target}')
            sys.exit(1)
        d['count'] = target
        n_count += 1
        if not apply:
            print(f'  [count] {cid} <- {d["count"]}')
        if apply:
            with open(f, 'w', encoding='utf-8') as out:
                json.dump(d, out, ensure_ascii=False, indent=2)
                out.write('\n')

    # ---- 3. _member_type：全庫 84 條機械推導 ----
    for cid, f in sorted(files.items()):
        d = json.load(open(f, encoding='utf-8'))
        mt = verify.derive_member_type(d)
        mt_dist[mt] = mt_dist.get(mt, 0) + 1
        if d.get('_member_type') == mt:
            continue
        if mt is None:
            if '_member_type' in d:
                del d['_member_type']
                n_mt += 1
                if apply:
                    with open(f, 'w', encoding='utf-8') as out:
                        json.dump(d, out, ensure_ascii=False, indent=2)
                        out.write('\n')
            continue
        d['_member_type'] = mt
        n_mt += 1
        if not apply:
            print(f'  [_member_type] {cid} <- {mt}')
        if apply:
            with open(f, 'w', encoding='utf-8') as out:
                json.dump(d, out, ensure_ascii=False, indent=2)
                out.write('\n')

    print(f'total_volumes 訂正 {n_tv}　count.source 改述 {n_amend}　count 回補 {n_count}　'
          f'_member_type 寫入/更新 {n_mt}　共 {len(files)} 條 Collection')
    print('_member_type 分布（含 None＝無可推之依據，不寫）：', mt_dist)
    print('APPLIED' if apply else 'DRY RUN（加 --apply 落盤）')


if __name__ == '__main__':
    main()
