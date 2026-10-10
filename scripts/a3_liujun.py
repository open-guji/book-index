"""A3：劉俊 hixhd2h9bib6 生卒矛盾。保 CBDB 198612（天順元年進士，生1425）；
死1408 屬 CBDB 66803（劉儁，江陵人，永樂六年卒），是並條串入，移除。"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'build'))
import v2common as v

root = os.path.join(os.path.dirname(__file__), '..')
recs, _, _ = v.load_repo(root, keep_raw=True)
r = recs['Entity']['hixhd2h9bib6']
d = r.data
assert d.get('birth_year') == 1425 and d.get('death_year') == 1408 and 'dates' not in d
new = {}
for k, val in d.items():
    if k == 'death_year':
        continue
    new[k] = val
    if k == 'dynasty':
        new['dates'] = {'birth': 1425, 'basis': 'CBDB 198612（劉俊，新鄉人，天順元年進士）YearBirth 1425；原 death_year 1408 屬 CBDB 66803（劉儁，江陵人，永樂六年卒），並條串入，已移除'}
new['ai_note'] += ('\n\n2026-10-10 生卒矛盾覈修：原 birth_year 1425／death_year 1408 卒早於生。查 CBDB：'
    '198612 劉俊（新鄉人，天順元年進士，生1425，無卒年）；66803 劉儁（江陵人，永樂六年卒1408，無生年）——二人。'
    '本條《白鹿洞書院志》撰人籍新鄉，取 198612 之生年，補 dates.birth=1425，移除屬 66803 之 death_year 1408。'
    '又：alt_names 中劉儁、劉雋、子士、子奇、愍節、節愍及 cbdb_id_alt 66803 實屬劉儁（66803），待拆分，未動。')
r.data.clear(); r.data.update(new)
open(os.path.join(root, r.path), 'w', encoding='utf-8').write(v.dump(r.data, r.fmt))
