#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""S5 道：stale_ref 校验推广（overview#189）之命中清单落盘。

只读、只生成 known-issues 报表，**不改任何既有字段的值**——本卡写域明文排除此事。
三项校验定义见 .claude/qa/verify.py：

  1. Work.related_works[].title  漂移（对现行既有校验之「补issue」：SCHEMA.md 早已宣称
     此项「在校验中报漂移，基线0」，然全库实无此校验落地——本卡先把它做实，再报现有命中）。
  2. Collection.contained_works[].title  漂移（同一校验推广到 Collection 成员名，S1-S4
     新增/現有均涵盖，因该字段并非本轮新增，故列入「盘点后发现的既有缺口」一并推广）。
  3. Book.provenance[].institution  含简体字（S2b 新增字段，字段本身无 id 可漂移，改查
     与全库繁体惯例不一之处）。

跑法：
  python3 .claude/qa/s5/staleref_report.py
"""
import glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..'))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import verify

OUT_DIR = os.path.join(ROOT, '.claude', 'qa', 'known-issues')


def dump(name, obj):
    p = os.path.join(OUT_DIR, name)
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=1)
        f.write('\n')
    print(f'  wrote {p}')


def main():
    IW = verify.idx('works')
    IC = json.load(open(os.path.join(ROOT, 'index', 'collections.json')))
    ALL_TITLED = set(IW) | set(IC)

    stale_related = []
    checked_related = 0
    for f in glob.glob(os.path.join(ROOT, 'Work/*/*/*/*.json')):
        d = json.load(open(f, encoding='utf-8'))
        wid = d.get('id')
        for r in (d.get('related_works') or []):
            rid, rt = r.get('id'), r.get('title')
            if not rid or rt is None:
                continue
            checked_related += 1
            actual = verify.title_of(rid, IW, IC)
            if actual is not None and actual != rt:
                stale_related.append({'work_id': wid, 'related_id': rid,
                                       'recorded_title': rt, 'actual_title': actual,
                                       'relation': r.get('relation')})

    stale_contained = []
    checked_contained = 0
    for cid, ie in IC.items():
        p = ie.get('path')
        if not p or not os.path.exists(p):
            continue
        d = json.load(open(p, encoding='utf-8'))
        for cw in (d.get('contained_works') or []):
            if not isinstance(cw, dict):
                continue
            rid, rt = (cw.get('id') or cw.get('work_id')), cw.get('title')
            if not rid or rt is None:
                continue
            checked_contained += 1
            actual = verify.title_of(rid, IW, IC)
            if actual is not None and actual != rt:
                stale_contained.append({'collection_id': cid, 'member_id': rid,
                                         'recorded_title': rt, 'actual_title': actual})

    bad_inst = []
    for f in glob.glob(os.path.join(ROOT, 'Book/*/*/*/*.json')):
        d = json.load(open(f, encoding='utf-8'))
        for item in (d.get('provenance') or []):
            inst = item.get('institution') if isinstance(item, dict) else None
            if inst and verify.institution_simplified(inst):
                bad_inst.append({'book_id': d.get('id'), 'institution': inst})

    os.makedirs(OUT_DIR, exist_ok=True)
    dump('s5-20260928-related_works标题漂移.json', {
        'lane': 'S5', 'date': '2026-09-28', 'kind': 'stale_ref 推广（现行既有欄位内容漂移，不改值，只报）',
        'title': 'Work.related_works[].title 与目标记录现行 title 不一致',
        'checked': checked_related, 'hit': len(stale_related),
        'note': 'SCHEMA.md 原称此项「在校验中报漂移，基线0」，但全库并无此校验落地——'
                '本卡在 verify.py 补上该检查（related_works_title 相关代码），本清单即其首次全量命中结果。'
                '本卡「不改任何已有字段的值」，故只报不修，留待另开道处理。',
        'examples': stale_related,
    })
    dump('s5-20260928-Collection成员名标题漂移.json', {
        'lane': 'S5', 'date': '2026-09-28', 'kind': 'stale_ref 推广（现行既有欄位内容漂移，不改值，只报）',
        'title': 'Collection.contained_works[].title 与目标 Work/Collection 现行 title 不一致',
        'checked': checked_contained, 'hit': len(stale_contained),
        'note': '与 related_works[].title 同一漂移校验推广到 Collection 成员名（issue #189 §一 举例）。'
                '多见于书目丛编（如《二十五史藝文經籍志考補萃編》）以括注撰人消歧的展示题，'
                '与 Work.title 本身不同——是否改判为「合法消歧展示」而非漂移，留待目录总管定夺。',
        'examples': stale_contained,
    })
    dump('s5-20260928-provenance机构名简繁不一.json', {
        'lane': 'S5', 'date': '2026-09-28', 'kind': 'stale_ref 推广（现行既有欄位内容不一致，不改值，只报）',
        'title': 'Book.provenance[].institution 含简体字，与全库繁体惯例不一',
        'hit': len(bad_inst),
        'note': '全库 provenance[].institution 现有 8 种写法，其中「中国国家图书馆」（简）／'
                '「中國國家圖書館」（繁）、「北京大学图书馆」（简）／「北京大學圖書館」（繁）'
                '各为同一机构的简繁两写。本卡「不改任何已有字段的值」，故只报，未做归一。',
        'examples': bad_inst,
    })
    print(f'related_works[].title 漂移：checked={checked_related} hit={len(stale_related)}')
    print(f'Collection.contained_works[].title 漂移：checked={checked_contained} hit={len(stale_contained)}')
    print(f'provenance[].institution 简体字：hit={len(bad_inst)}')


if __name__ == '__main__':
    main()
