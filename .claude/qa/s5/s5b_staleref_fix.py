#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S5b 道（overview#198）：stale_ref 清账，逐条按 issue 判准处置。

三项：
1. Work.related_works[].title 漂移 77 处——全部属"冗余名跟着目标现名过时"，机械同步。
2. Collection.contained_works[].title 漂移 47 处——按目录总管裁定（issue#198 首条评论）：
   只在现名后加括注撰人消歧者算正常、不同步；括注以外部分对不上者才是漂移、同步；
   目标本身之 title 字段自带缺陷（非本卡写域，不可碰）者列清单、不动。
   47 处逐条人工核过，分三档，见下方 CONTAINED_VERDICTS。
3. Book.provenance[].institution 简体字 3 处——全库仅两种机构名简繁两写，显式表转换
   （不用 opencc，坑 15）。

跑法：
  python3 .claude/qa/s5/s5b_staleref_fix.py            # 干跑
  python3 .claude/qa/s5/s5b_staleref_fix.py --apply     # 落盘
"""
import glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
QA_DIR = os.path.join(ROOT, '.claude', 'qa')
KI_DIR = os.path.join(QA_DIR, 'known-issues')

sys.path.insert(0, QA_DIR)
import jio  # noqa: E402

NOTE_DATE = '2026-09-28'

# ---- Collection.contained_works 47 处人工裁决（collection_id, member_id) -> verdict ----
# verdict: 'sync'（同步为现名）／'normal'（括注撰人消歧，正常不动）／'list'（目标自身缺陷，列清单不动）
CONTAINED_VERDICTS = {
    ('8rlcsy6ubh1d', 'd59f2mpesiyp'): 'sync',   # 金雲翹傳（雙奇夢）——括注非撰人，是别名
    ('8rlcsybg2hhf', 'd59f27x5axhe'): 'sync',   # 春秋釋例杜預撰——无括注，同一般 related_works 漂移
    ('8rlcsybg2hhh', 'd59f23o7ygw2'): 'sync',   # 漢書藝文志 -> 漢書·藝文志，标点
    ('8rlcsybg2hhh', 'd59f2o2lary9'): 'normal', # 補後漢書藝文志（顧懷三）
    ('8rlcsybg2hhh', 'd59f2o2lm0ht'): 'normal', # 補後漢書藝文志（侯康）
    ('8rlcsybg2hhh', 'd59f2mp1232a'): 'normal', # 補三國藝文志（侯康）
    ('8rlcsybg2hhh', 'd59f2mp2xibm'): 'normal', # 補晉書藝文志（丁國鈞）
    ('8rlcsybg2hhh', 'd59f2o2m8hky'): 'normal', # 補晉書藝文志（文廷式）
    ('8rlcsybg2hhh', 'd59f5ilweo6h'): 'normal', # 補晉書藝文志（秦榮光）
    ('8rlcsybg2hhh', 'd59f2o2lx91d'): 'normal', # 補晉書藝文志（黄逢元）
    ('8rlcsybg2hhh', 'd59f2o2muyo2'): 'normal', # 補宋書藝文志（王仁俊）
    ('8rlcsybg2hhh', 'd59f2ofz9b0h'): 'normal', # 補宋書藝文志（聶崇岐）
    ('8rlcsybg2hhh', 'd59f28nmafwh'): 'sync',   # 隋書經籍志 -> 隋書·經籍志，标点
    ('8rlcsybg2hhh', 'd59f2ntopu68'): 'normal', # 隋書經籍志考證（章宗源）
    ('8rlcsybg2hhh', 'd59f2mp0flz6'): 'normal', # 隋書經籍志考證（姚振宗）
    ('8rlcsybg2hhh', 'd59f2gcburcx'): 'sync',   # 舊唐書經籍志 -> 舊唐書·經籍志
    ('8rlcsybg2hhh', 'd59f2hl0cmio'): 'sync',   # 新唐書藝文志 -> 新唐書·藝文志
    ('8rlcsybg2hhh', 'd59f2msyrtoh'): 'normal', # 補五代史藝文志（顧懷三）
    ('8rlcsybg2hhh', 'd59f2mp1dblv'): 'normal', # 補五代史藝文志（宋祖駿）
    ('8rlcsybg2hhh', 'd59f2gdp696q'): 'sync',   # 宋史藝文志 -> 宋史·藝文志
    ('8rlcsybg2hhh', 'd59f2o2mjq4i'): 'normal', # 補遼史經籍志（厲鶚）
    ('8rlcsybg2hhh', 'd59f2o2kzjer'): 'normal', # 補遼史經籍志（楊復吉）
    ('8rlcsybg2hhh', 'd59f2mp2m9s0'): 'normal', # 明史藝文志（萬斯同）——括注外恰等现名
    ('8rlcsybg2hhh', 'd59f2mox0000'): 'sync',   # 明史藝文志（張廷玉）——现名实为「明史·藝文志」，括注外对不上
    ('8rlcsybg2hhh', 'd59f2mp0flz4'): 'sync',   # 清史稿藝文志 -> 清史稿·藝文志
    ('8rlcsybg2hhn', 'd59f24mpohs0'): 'sync',   # 孟子注疏 -> 孟子注疏解經
    ('8rlcsybg2hhn', 'd59f2hqvd1qa'): 'sync',   # 論語注疏 -> 論語注疏解經
    ('8rlcsybg2hhn', 'd59f28nosc91'): 'sync',   # 春秋穀梁傳注疏 -> 春秋穀梁注疏
    ('8rlcsybg2hho', 'd59f2ni9mewz'): 'normal', # 重刻西漢通俗演義（甄偉）
    ('8rlcsybg2hho', 'd59f2ngxv403'): 'normal', # 重刻京本增評東漢十二帝通俗演義（謝詔）
    ('8rlcsybg2hhp', 'd59f2ni9mewz'): 'normal', # 重刻西漢通俗演義（甄偉）——同一 member 两处挂载
    ('8rlcsybg2hhp', 'd59f2mp3v7y8'): 'normal', # 東漢演義評（清遠道人重編）
    ('8rlcsybg2hhq', 'd59f2nei5fcx'): 'sync',   # 新鐫全像孫龐鬥志演義（前七國志）——括注是别名非撰人
    ('8rlcsybg2hhq', 'd59f2mp3jzep'): 'normal', # 後七國志樂田演義（徐震）
    ('8rlcsybg2hhr', 'd59f2mp9hhq9'): 'sync',   # 十二峰 -> 十二峯，异体字
    ('8rlcsybg2hhs', 'd59f2mpehaf6'): 'normal', # 玉嬌梨（天花藏主人）
    ('8rlcsybg2hht', 'd59f2nhaz2f6'): 'sync',   # 新刊八仙出處東遊記（吳元泰）——括注外对不上，实为异名同书
    ('8rlcsybg2hht', 'd59f2nh1x729'): 'normal', # 南遊華光傳（余象斗）
    ('8rlcsybg2hht', 'd59f2nigsveo'): 'normal', # 北遊記玄帝出身傳（余象斗）
    ('8rlcsybg2hhv', 'd59f2nig6ebn'): 'sync',   # 龍圖公案（包公案）——括注是别名非撰人
    ('8rlcsybg2hhv', 'd59f2md5eyv4'): 'normal', # 鹿洲公案（藍鼎元）
    ('8rlcsybg2hhw', 'd59f2ngcy7er'): 'list',   # 水滸後傳（陳忱）-> 現名「水滸後傳陳忱」本身缺分隔，非本卡写域可碰
    ('8rlcsybg2hhx', 'd59f28m9wnpg'): 'normal', # 遊仙窟（唐張鷟）
    ('8rlcsybg2hhx', 'd59f2mp9hhq8'): 'normal', # 照世杯（酌元亭主人）
    ('8rlcsybg2hhy', 'd59f2nhf15oi'): 'normal', # 古今小說（馮夢龍）
    ('8rld0ts2thj4', 'd59fazdcd98g'): 'sync',   # 八千卷樓書目 -> 八千卷樓書目二十卷
    ('8rld0ts2thj4', 'd59f2msw9xc1'): 'sync',   # 述古堂藏書目 -> 錢遵王述古堂藏書目錄
}

INSTITUTION_MAP = {
    '中国国家图书馆': '中國國家圖書館',
    '北京大学图书馆': '北京大學圖書館',
}


def find_work_file(wid):
    hits = glob.glob(os.path.join(ROOT, 'Work', '*', '*', '*', f'{wid}-*.json'))
    return hits[0] if hits else None


def find_book_file(bid):
    hits = glob.glob(os.path.join(ROOT, 'Book', '*', '*', '*', f'{bid}-*.json'))
    return hits[0] if hits else None


def fix_related_works(apply):
    d = json.load(open(os.path.join(KI_DIR, 's5-20260928-related_works标题漂移.json'), encoding='utf-8'))
    examples = d['examples']
    by_work = {}
    for e in examples:
        by_work.setdefault(e['work_id'], []).append(e)
    n = 0
    for wid, items in by_work.items():
        rel = os.path.relpath(find_work_file(wid) or '', ROOT)
        if not rel or not os.path.exists(os.path.join(ROOT, rel)):
            print(f'  !! Work 檔缺：{wid}'); continue
        dd, fmt = jio.load(rel)
        touched = []
        for e in items:
            found = False
            for r in (dd.get('related_works') or []):
                if r.get('id') == e['related_id']:
                    if r.get('title') != e['actual_title']:
                        if apply:
                            r['title'] = e['actual_title']
                        touched.append((e['related_id'], e['recorded_title'], e['actual_title']))
                    found = True
                    break
            if not found:
                print(f'  !! {wid} 找不到 related_works.id={e["related_id"]}')
        if touched:
            n += len(touched)
            if apply:
                jio.addnote(dd, f'{NOTE_DATE} qa-sweep/S5b：related_works[].title 同步为目标现名（overview#198），'
                                 + '；'.join(f'{rid}「{old}」→「{new}」' for rid, old, new in touched) + '。')
                jio.save(rel, dd, fmt)
            else:
                for rid, old, new in touched:
                    print(f'  [related_works] {wid}.{rid}: {old!r} -> {new!r}')
    print(f'related_works[].title 同步：{n} 处')
    return n


def fix_contained_works(apply):
    d = json.load(open(os.path.join(KI_DIR, 's5-20260928-Collection成员名标题漂移.json'), encoding='utf-8'))
    examples = d['examples']
    by_coll = {}
    for e in examples:
        key = (e['collection_id'], e['member_id'])
        if key not in CONTAINED_VERDICTS:
            raise SystemExit(f'未裁决之项：{key} {e}')
        by_coll.setdefault(e['collection_id'], []).append(e)
    IC = json.load(open(os.path.join(ROOT, 'index', 'collections.json'), encoding='utf-8'))
    n_sync, n_normal, n_list = 0, 0, 0
    listed = []
    for cid, items in by_coll.items():
        path = IC.get(cid, {}).get('path')
        if not path or not os.path.exists(os.path.join(ROOT, path) if not os.path.isabs(path) else path):
            p2 = path if os.path.isabs(path) else os.path.join(ROOT, path)
            print(f'  !! Collection 檔缺：{cid} {path}'); continue
        rel = os.path.relpath(os.path.join(ROOT, path) if not os.path.isabs(path) else path, ROOT)
        dd, fmt = jio.load(rel)
        touched = []
        for e in items:
            verdict = CONTAINED_VERDICTS[(cid, e['member_id'])]
            if verdict == 'normal':
                n_normal += 1
                continue
            if verdict == 'list':
                n_list += 1
                listed.append(e)
                continue
            found = False
            for cw in (dd.get('contained_works') or []):
                if not isinstance(cw, dict):
                    continue
                x = cw.get('id') or cw.get('work_id')
                if x == e['member_id']:
                    if cw.get('title') != e['actual_title']:
                        if apply:
                            cw['title'] = e['actual_title']
                        touched.append((e['member_id'], e['recorded_title'], e['actual_title']))
                    found = True
                    break
            if not found:
                print(f'  !! {cid} 找不到 contained_works.id={e["member_id"]}')
        if touched:
            n_sync += len(touched)
            if apply:
                jio.addnote(dd, f'{NOTE_DATE} qa-sweep/S5b：contained_works[].title 同步为目标现名（overview#198，'
                                 '括注撰人消歧之展示题按目录总管裁定不动），'
                                 + '；'.join(f'{mid}「{old}」→「{new}」' for mid, old, new in touched) + '。')
                jio.save(rel, dd, fmt)
            else:
                for mid, old, new in touched:
                    print(f'  [contained_works] {cid}.{mid}: {old!r} -> {new!r}')
    print(f'contained_works[].title 同步：{n_sync} 处，括注消歧正常不动：{n_normal} 处，'
          f'目标自身缺陷列清单不动：{n_list} 处')
    if listed:
        os.makedirs(KI_DIR, exist_ok=True)
        outp = os.path.join(KI_DIR, 's5b-20260928-contained_works目标自身缺陷不同步清单.json')
        with open(outp, 'w', encoding='utf-8') as f:
            json.dump({
                'lane': 'S5b', 'date': NOTE_DATE,
                'kind': 'Collection.contained_works[].title 漂移之目标自身缺陷型（不同步）',
                'note': '该项 recorded_title 已是「现名+括注撰人」之规范展示题，而目标记录自身的 title '
                         '字段反而是撰人名与题名未加分隔地粘连（如「水滸後傳陳忱」）——目标 title 字段本身'
                         '疑有历史遗留缺陷，但 Work.title／Collection.title 不在本卡写域，不可碰。'
                         '同步只会把粘连写法带进 contained_works，是倒退，故不动，留待目录总管另裁是否修 Work.title。',
                'examples': listed,
            }, f, ensure_ascii=False, indent=1)
            f.write('\n')
        print(f'  wrote {outp}')
    return n_sync, n_normal, n_list


def fix_institutions(apply):
    d = json.load(open(os.path.join(KI_DIR, 's5-20260928-provenance机构名简繁不一.json'), encoding='utf-8'))
    examples = d['examples']
    n = 0
    for e in examples:
        bid = e['book_id']
        new_name = INSTITUTION_MAP.get(e['institution'])
        if not new_name:
            print(f'  !! 未收之简体机构名：{e["institution"]}（{bid}）'); continue
        rel = os.path.relpath(find_book_file(bid) or '', ROOT)
        if not rel or not os.path.exists(os.path.join(ROOT, rel)):
            print(f'  !! Book 檔缺：{bid}'); continue
        dd, fmt = jio.load(rel)
        touched = False
        for item in (dd.get('provenance') or []):
            if isinstance(item, dict) and item.get('institution') == e['institution']:
                if apply:
                    item['institution'] = new_name
                touched = True
        if touched:
            n += 1
            if apply:
                jio.addnote(dd, f'{NOTE_DATE} qa-sweep/S5b：provenance[].institution 简体字归一为全库繁体惯例'
                                 f'（overview#198）：「{e["institution"]}」→「{new_name}」（显式表，非 opencc 自动转，坑15）。')
                jio.save(rel, dd, fmt)
            else:
                print(f'  [provenance] {bid}: {e["institution"]!r} -> {new_name!r}')
    print(f'provenance[].institution 简繁归一：{n} 处')
    return n


def main():
    apply = '--apply' in sys.argv
    print('=== related_works ===')
    n1 = fix_related_works(apply)
    print('=== contained_works ===')
    n2, n2b, n2c = fix_contained_works(apply)
    print('=== provenance ===')
    n3 = fix_institutions(apply)
    print()
    print(f'合计同步：{n1 + n2 + n3}　括注消歧不动：{n2b}　目标自身缺陷不动：{n2c}')
    print('APPLIED' if apply else 'DRY RUN（加 --apply 落盘）')


if __name__ == '__main__':
    main()
