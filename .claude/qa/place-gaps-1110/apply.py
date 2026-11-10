#!/usr/bin/env python3
"""殿本地名消歧库缺补建（A12，2026-11-10）：新建 唐·雍州、西晉·隨縣；补别名 昭武→邵武、合陽→郃陽。
依据见 PR 说明；写前拉最新 main。"""
import json, glob, sys, os
sys.path.insert(0, '.claude/qa')
import mintid

ROOT = '.'
def find(i):
    fs = glob.glob(f'{ROOT}/Entity/*/*/*/{i}-*.json')
    assert len(fs) == 1, (i, fs)
    return fs[0]
def load(i):
    f = find(i); return f, json.load(open(f, encoding='utf-8'))
def dump(f, d):
    json.dump(d, open(f, 'w', encoding='utf-8'), ensure_ascii=False, indent=2); open(f, 'a').write('\n')

AI = ("A12 殿本地名消歧库缺补建（GUJI-760），2026-11-10。依据《{src}》，起訖未逐條考訂者取該朝起訖或上級存續年份，待核。CBDB 未參與。")
new = []
def mk(name, dyns, concept, parent, start, end, level, note, src):
    i = mintid.mint('Entity', 'resA2', 1)[0]
    d = {"schema_version": 1, "id": i, "type": "entity", "subtype": "place", "place_level": "concrete",
         "primary_name": name, "dynasty_ids": dyns, "concept_id": concept,
         "history": [{"start": start, "end": end, "dynasty_ids": dyns, "name": name, "level": level, "parent_id": parent, "note": note}],
         "ai_note": AI.format(src=src), "revision": "1.0.0", "revised_at": "2026-11-10"}
    p = mintid.path_for(i, name)
    return i, p, d

TANG, WUZHOU, XIJIN = 'hixi1ubjgowi', 'hixi1ubjrxg7', 'hixi1ubkeeiu'
# 唐·雍州：新唐書卷三十七京兆府條「本雍州，開元元年為府」；上級關內道；跨朝條西安府 hixi4ugtrl6o（別名含雍州）
jobs = [
 mk('雍州', [TANG, WUZHOU], 'hixi4ugtrl6o', 'hixicabupv3l', 618, 713, '州',
    '《新唐書》卷三十七〈地理志一〉：「京兆府京兆郡，本雍州，開元元年為府。」（起年取唐之始，訖年為開元元年（713）升府；起年待核。）', '新唐書·地理志'),
 # 西晉·隨縣：晉書卷十五義陽郡條，上級義陽郡（西晉）hixicm9q21qx；跨朝條 hixicmgyp7ae（隨縣，concept）待核，不挂
 mk('隨縣', [XIJIN], None, 'hixicm9q21qx', 265, 316, '縣',
    '《晉書》卷十五〈地理志下〉：「義陽郡。太康中置。統縣十二，戶一萬九千。」所列縣有「隨」，注「故隨國」。（惠帝時又「分義陽立隨郡」，隨縣其後當屬隨郡；本條起訖取西晉起訖，待核。）', '晉書·地理志'),
]
for i, p, d in jobs:
    if glob.glob(f'Entity/*/*/*/hixil*-{d["primary_name"]}.json') and False: continue
    if d['concept_id'] is None: del d['concept_id']
    os.makedirs(os.path.dirname(p), exist_ok=True)
    dump(p, d); print('新建', i, d['primary_name'], p)

# 補別名
def add_alias(i, name, typ, note=None):
    f, d = load(i)
    if any(a['name'] == name for a in d.get('alt_names', [])):
        print('已有', i, name); return
    d.setdefault('alt_names', []).append({"name": name, "type": typ})
    dump(f, d); print('補別名', i, d['primary_name'], '+', name)
add_alias('hixi6kqhkxs4', '昭武', '舊稱')     # 邵武縣 跨朝條
add_alias('hixi5wauu68f', '昭武', '舊稱')     # 邵武府 跨朝條
add_alias('hixicl8ftlwb', '合陽', '異寫')     # 郃陽縣 跨朝條（已有郃陽）

# 補別名（朝代條，使按朝代查名可直接命中）
add_alias('hixicl88ydzf', '竟陵', '舊稱')     # 景陵縣（明）
add_alias('hixicl85is44', '竟陵', '舊稱')     # 景陵縣（宋）
add_alias('hixicl86ghq3', '瀛州', '舊稱')     # 河間路（元）
add_alias('hixictrqbx91', '廣陵', '舊稱')     # 揚州（南唐）
