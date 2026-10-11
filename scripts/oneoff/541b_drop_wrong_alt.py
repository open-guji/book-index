"""overview#541 强 8 对（摘 id 部分）。默认干跑，--apply 才写。

只摘错挂的 external_ids.cbdb_id_alt（及其带入的别名），不拆 Entity：
吳山 69276、脫脫 117121、李遵 173997、王炎 1925（+別名 公明／季思）、楊鼐 57309、莊昶 67611、李顒 77299。
另：Book 98y70ku6m8《施註蘇詩》摘去誤繫的「托克托」撰人。
"""
import os, sys, copy
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'build'))
import v2common as v

APPLY = '--apply' in sys.argv
D = '2026-10-11 #541 摘錯挂 cbdb_id_alt：'

# eid: (本人 cbdb_id, 被摘 alt, 理由, 另摘別名)
PLAN = {
    'hixhd2h9bi5c': (69268, 69276, 'CBDB 69276 吳山（吳江人，1470–1542，諡忠襄）是另一人；本條 CBDB 69268 吳山（高安人，1501–1577，諡文端）與《四庫總目》所載《河治通考》撰人「吳山，高安人，嘉靖乙未進士，官至禮部尚書，諡文端」吻合。', []),
    'hixhd2h9bh83': (28192, 117121, 'CBDB 117121 脫脫（1264–1307）卒於元世祖／成宗間，而本條 CBDB 28192 脫脫（1314–1355，元順帝朝右丞相）方是《宋史》《金史》《遼史》總裁；117121 無著作命中。', []),
    'hixhd2h9bhic': (187428, 173997, 'CBDB 173997 李遵（贊皇人，卒 501）早於本條唐代著作（《三茅君內傳》等）二百餘年；本條 CBDB 187428 李遵（長安人，卒 757）與之相符。', []),
    'hixhd2h9bff0': (16692, 1925, 'CBDB 1925 王炎（廬陵人，1115–1178，樞密使，父王綯）非本條王炎（婺源人，1138–1218，父王橐，CBDB 16692 著作命中《雙溪集》等）；別名 公明、季思 僅 1925 有，一併卸除。', ['公明', '季思']),
    'hixhd2h9bgkr': (199908, 57309, 'CBDB 57309 楊鼐（仁和／臨清，1620–1699）與本條楊鼐（豐城人，生 1437，CBDB 199908）生年相差 183 年、籍貫與父系皆不同。', []),
    'hixhd2h9bgpm': (67718, 67611, 'CBDB 67611 為朱瞻垍（梁莊王，1411–1441），名字、身分皆非莊昶；本條 CBDB 67718 莊昶（江浦人，1437–1499）著作命中《定山集》。', []),
    'hixhd2h9bd15': (65738, 77299, 'CBDB 77299 李颙（潼關廳，1760–1812）與本條李顒（盩厔人，二曲先生，1627–1705，CBDB 65738）相隔一個世代；二曲集、悔過自新錄屬 65738。', []),
}
BOOK = '98y70ku6m8'

recs, _, _ = v.load_repo(ROOT, keep_raw=True)
changed = []

def save(r):
    open(os.path.join(ROOT, r.path), 'w', encoding='utf-8').write(v.dump(r.data, r.fmt))
    changed.append(r.path)

for eid, (own, alt, why, aliases) in PLAN.items():
    r = recs['Entity'][eid]; d = r.data
    ex = d['external_ids']
    assert ex['cbdb_id'] == own and ex.get('cbdb_id_alt') == [alt], (eid, ex)
    del ex['cbdb_id_alt']
    if aliases:
        names = {a['name'] for a in d['alt_names']}
        assert set(aliases) <= names
        d['alt_names'] = [a for a in d['alt_names'] if a['name'] not in aliases]
    d['ai_note'] = (d.get('ai_note') or '') + '\n\n' + D + '摘去 cbdb_id_alt [%d]。%s' % (alt, why)
    if APPLY: save(r)

r = recs['Book'][BOOK]; d = r.data
n = len(d['authors'])
d['authors'] = [a for a in d['authors'] if a.get('entity_id') != 'hixhd2h9bh83']
assert len(d['authors']) == n - 1
d['ai_note'] = (d.get('ai_note') or '') + ('\n\n2026-10-11 #541：摘去撰人「托克托」（脫脫 hixhd2h9bh83）。脫脫（1314–1355）為《宋史》《遼史》《金史》總裁，CBDB 28192 著作僅此三史相關，'
    '與蘇軾詩施顧注本無涉；本書撰人已有蘇軾、蘇轍，注者王宗稷、邵長衡、馮景，該行來源（《中國古籍總目》自動錄入）疑為誤抽。')
if APPLY: save(r)
print(('APPLY' if APPLY else 'DRY-RUN'), len(PLAN), '实体 + 1 Book')
