#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""十三經縱向補全·Book 層第三輪（車道 a11-sjj-book；日本／朝鮮／越南）。
用法：build3.py <data模塊名> [--apply]
批1（data3_b1）＝日本國指定文化財（國寶／重文）經書寫本與宋刊本：據文化遺產オンライン＋國指定文化財DB 詳情頁逐條建 Book。"""
import argparse, importlib, json, os, re, sys
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa')); sys.path.insert(0, HERE)
import mintid
ap = argparse.ArgumentParser(); ap.add_argument('mod'); ap.add_argument('--apply', action='store_true'); A = ap.parse_args()
D = importlib.import_module(A.mod)
TODAY = '2026-11-15'; LANE = 'a11-sjj-book'
KD = json.load(open(os.path.join(HERE, 'kd_cache.json'), encoding='utf-8'))
def jd(d): return json.dumps(d, ensure_ascii=False, indent=2) + '\n'
def jp_date(s):
    m = re.match(r'(\d{4})\.(\d{2})\.(\d{2})', s or '')
    return '%d年%d月%d日' % (int(m.group(1)), int(m.group(2)), int(m.group(3))) if m else ''
newwork = {}
def work_id(key, ids_iter):
    if key.startswith('NEW:'):
        if key not in newwork: newwork[key] = next(ids_iter)
        return newwork[key]
    return key
items = D.ITEMS
need_w = len({it[2] for it in items if D.W[it[2]].startswith('NEW:')})
if A.apply:
    book_ids = mintid.mint('Book', LANE, len(items)); work_ids = iter(mintid.mint('Work', LANE, need_w) if need_w else [])
else:
    book_ids = ['dryb%06d' % i for i in range(len(items))]; work_ids = iter(['dryw%06d' % i for i in range(need_w)])
files = {}; rows = []
for it, bid in zip(items, book_ids):
    b, title, wk, ed, et, dt, inst, desc = it
    k = KD[b]; wid = work_id(D.W[wk], work_ids)
    dating = {'era': dt['era']}
    if 'reign' in dt: dating['reign'] = dt['reign']
    if 'year' in dt: dating['year'] = dt['year']
    if 'text' in dt: dating['text'] = dt['text']
    dating.update({'certainty': 'attested', 'source': 'catalog', 'basis': dt['basis']})
    kind = k.get('国宝・重文区分') or ''
    if kind == '国宝': kind, dstr = '國寶', jp_date(k.get('国宝指定年月日'))
    else: kind, dstr = '重要文化財', jp_date(k.get('重文指定年月日'))
    note = '%s，%s指定（指定番號%s）' % (kind, dstr, k.get('指定番号（登録番号）'))
    if k.get('員数'): note += '；員數%s' % k['員数'].replace('冊', '冊').replace('帖', '帖')
    if k.get('所有者名') and k['所有者名'] not in inst: note += '；所有者%s' % k['所有者名']
    if k.get('所在地'): note += '；所在地%s' % k['所在地']
    if k.get('ト書'): note += '；ト書『%s』' % k['ト書']
    prov = {'institution': inst, 'notes': note, 'source': '國指定文化財DB %s；文化遺產オンライン %s' % (k['kid'], b)}
    d = {'schema_version': 1, 'type': 'book', 'title': title, 'work_id': wid, 'edition': ed, 'edition_type': et, 'dating': dating}
    m = re.match(r'(\d+)', (k.get('員数') or ''))
    if m:
        unit = re.sub(r'^\d+', '', k['員数']); d['measures'] = [{'number': int(m.group(1)), 'unit': unit}]
    d['provenance'] = [prov]
    srcs = [('kunishitei-' + k['kid'].replace('/', '-'), '國指定文化財等データベース', 'https://kunishitei.bunka.go.jp/heritage/detail/' + k['kid']),
            (b, '文化遺産オンライン', 'https://online.bunka.go.jp/heritages/detail/' + b)]
    d['description'] = {'text': desc, 'sources': ['%s %s' % (n, u) for _, n, u in srcs]}
    d['sources'] = [{'id': i, 'name': n, 'type': 'url', 'details': u} for i, n, u in srcs]
    d['ai_note'] = '十三經縱向補全·Book 層第三輪（2026-11-15，日本國寶／重文批）：據國指定文化財DB與文化遺產オンライン詳情頁核定（指定番號、員數、時代、年代、ト書、所有者均錄自該頁），未核原書。'
    d['id'] = bid; d['revision'] = '1.0.0'; d['revised_at'] = TODAY
    safe = re.sub(r'[\\/:*?"<>|（）() ,，;；「」《》、·]', '', ed)[:24]
    files['Book/%s/%s/%s/%s-%s%s.json' % (bid[-3], bid[-2], bid[-1], bid, title, safe)] = d
    rows.append((b, bid, title, ed))
for key, wid in newwork.items():
    t = key[4:]
    wd = {'schema_version': 1, 'id': wid, 'type': 'work', 'title': t, 'authors': [{'name': '佚名', 'role': '撰'}],
          'related_works': [{'id': 'd59f1iofm800', 'relation': 'contains_text_of'}],
          'period_upper': 'sui-tang', 'period_upper_basis': 'catalog_bound：早稻田大學藏唐寫本殘卷（國寶，國指定文化財DB 201/660），故成書不晚於唐',
          'description': {'text': '《禮記》子本疏義，今存唐寫本卷第五十九殘卷，早稻田大學藏，國寶。撰人未詳。', 'sources': ['國指定文化財等データベース https://kunishitei.bunka.go.jp/heritage/detail/201/660', '文化遺產オンライン https://online.bunka.go.jp/heritages/detail/159585']},
          'ai_note': '2026-11-15 十三經縱向補全·Book 層第三輪：因庫內無此書而補建 Work（庫內按異體歸一題名查無同題；經名「子本」指以經注為母本、疏義為子本的義疏體，撰人與卷數未見權威著錄，故署佚名、不寫卷數）。', 'revision': '1.0.0', 'revised_at': TODAY}
    files['Work/%s/%s/%s/%s-%s.json' % (wid[-3], wid[-2], wid[-1], wid, t)] = wd
print('Book', len(items), 'Work', len(newwork))
for p in files: print(p)
if not A.apply: sys.exit(0)
for pth, d in files.items():
    os.makedirs(os.path.join(BI, os.path.dirname(pth)), exist_ok=True)
    open(os.path.join(BI, pth), 'w', encoding='utf-8').write(jd(d))
json.dump({'rows': rows, 'files': list(files)}, open(os.path.join(HERE, 'result3_' + A.mod.split('_')[-1] + '.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('已寫')
