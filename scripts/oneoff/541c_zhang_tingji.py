"""overview#541 强 8 对第 5 对：張廷濟 hixhd2h9bcy1。默认干跑，--apply 才写。

摘去错并入的 CBDB 80495（張汝霖，宣城人，1709–1769，著《張氏詩說》）及仅它带来的 10 个别名；
本人 CBDB 80448 自带別名「張汝霖」「張汝林」，故保留，《學詩毛鄭異同籤》（撰人張汝霖）对張廷濟的繫连也不动。
"""
import os, sys
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import v2common as v

APPLY = '--apply' in sys.argv
EID = 'hixhd2h9bcy1'
DROP = ['半岩樵子', '孟雲', '悟真道人', '柏園', '蕓墅', '藝墅', '西坂草堂', '雨亭', '雨齋', '雲澍']

recs, _, _ = v.load_repo(ROOT, keep_raw=True)
r = recs['Entity'][EID]; d = r.data
ex = d['external_ids']
assert ex['cbdb_id'] == 80448 and ex.get('cbdb_id_alt') == [80495], ex
assert set(DROP) <= {a['name'] for a in d['alt_names']}
del ex['cbdb_id_alt']
d['alt_names'] = [a for a in d['alt_names'] if a['name'] not in DROP]
d['ai_note'] = (d.get('ai_note') or '') + (
    '\n\n2026-10-11 #541 摘錯挂 cbdb_id_alt：摘去 [80495] 及僅其所帶之別名 ' + '、'.join(DROP) + '。'
    'CBDB 80495 張汝霖（宣城人，1709–1769，貢生，歷任香山、河源、陽春知縣，著《張氏詩說》一卷）與本條張廷濟（海鹽人，1768–1848，CBDB 80448）'
    '生卒、籍貫皆不同。本人 CBDB 80448 自帶別名「張汝霖」「張汝林」，故保留此二名；《學詩毛鄭異同籤》撰人「張汝霖」之繫連亦不動（無反證）。')
if APPLY:
    open(os.path.join(ROOT, r.path), 'w', encoding='utf-8').write(v.dump(d, r.fmt))
print('APPLY' if APPLY else 'DRY-RUN', r.path)
