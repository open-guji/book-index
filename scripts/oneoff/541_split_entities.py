"""overview#541：误并实体拆分。默认干跑，--apply 才写。

1. 應是 hixhd2h9be38：卸去并入的蔡德晉（CBDB 125397）、吳高增（CBDB 78522）之字与 cbdb_id_alt。
2. 劉俊 hixhd2h9bib6：卸去并入的劉儁（CBDB 66803）之异体名与 cbdb_id_alt。
3. 新建 Entity：蔡德晉、吳高增、劉儁（id 由 mintid 鑄，机器段 2010 专给本次，不与既有车道相撞）。
4. 改繫 4 部 Work 的 authors[].entity_id：禮經本義→蔡德晉；行唐縣新志、蘭亭志→吳高增；三合便覽摘除（见 ai_note）。
读写走 build/v2common.py（保格式）。不动 revision／revised_at 于既有记录；新记录 revision 1.0.0。
"""
import os, sys, copy, json
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..'))
sys.path.insert(0, os.path.join(ROOT, 'build'))
sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
import v2common as v
import mintid

APPLY = '--apply' in sys.argv
TODAY = '2026-10-10'
D = '2026-10-10 #541 誤並拆分：'

YINGSHI, LIUJUN = 'hixhd2h9be38', 'hixhd2h9bib6'
W_LIJING, W_XINGTANG, W_LANTING, W_SANHE = 'd59f2ma5q3gh', 'd59f2mznfshs', 'd59f2mshx0cg', 'd59f2mxhegoz'

# 以下三个 id 由 mintid.mint('Entity', lane=机器段 2010) 于 2026-10-10 鑄出并固定，干跑／真跑一致
NEW = {'caidejin': 'hixi3r9yd0jk', 'wugaozeng': 'hixi3r9yd0jl', 'liujun2': 'hixi3r9yd0jm'}
for _i in NEW.values():
    assert mintid.idtype(_i) == 'Entity' and mintid.parse(_i)['machine'] == 2010, _i


def entity(eid, name, alt, dynasty, period, place, place_basis, cbdb, dates, note):
    d = {'schema_version': 1, 'id': eid, 'type': 'entity', 'subtype': 'people', 'primary_name': name, 'alt_names': alt,
         'dynasty': dynasty}
    if dates:
        d['dates'] = dates
    d.update({'external_ids': {'cbdb_id': cbdb, 'cbdb_match': 'manual', 'cbdb_source': '#541 自誤並條拆出，CBDB API 逐項核對'},
              'updated_at': TODAY + 'T00:00:00+00:00', 'period': period, 'period_basis': '據 dynasty「%s」自動歸併' % dynasty,
              'native_place': place, 'native_place_basis': place_basis, 'revision': '1.0.0', 'revised_at': TODAY, 'ai_note': note})
    return d


NEW_ENTITIES = {
    NEW['caidejin']: entity(
        NEW['caidejin'], '蔡德晉',
        [{'name': '仁錫', 'type': '字'}, {'name': '宸錫', 'type': '字'}, {'name': '敬齋', 'type': '號'}],
        '清', 'qing', '無錫', 'CBDB 125397 籍貫(基本地址) 無錫', 125397, None,
        D + '自「應是」hixhd2h9be38 拆出。CBDB 125397 蔡德晉（無錫人，字仁錫／宸錫，室名別號敬齋，IndexYear 1699，無生卒年）。'
            '《四庫全書總目》著錄《禮經本義》：「德晉字仁錫，無錫人。雍正丙午舉人，乾隆初以楊名時薦官司務。」與 CBDB 吻合。'
            '原誤入「應是」條之 alt_names 仁錫、宸錫與 cbdb_id_alt 125397 已一併卸除。'),
    NEW['wugaozeng']: entity(
        NEW['wugaozeng'], '吳高增',
        [{'name': '敬齋', 'type': '別名'}, {'name': '玉亭', 'type': '別名'}, {'name': '繼長', 'type': '別名'}],
        '清', 'qing', '秀水', 'CBDB 78522 籍貫(基本地址) 秀水（浙江）', 78522,
        {'birth': 1706, 'basis': 'CBDB 78522 YearBirth 1706（《清代人物生卒年表》康熙45年～？），無卒年'},
        D + '自「應是」hixhd2h9be38 拆出。CBDB 78522 吳高增（秀水人，生 1706，別名敬齋／玉亭／繼長；CBDB 標「未詳」型，此處按庫例記「別名」）。'
            '《行唐縣新志》（纂修）、《蘭亭志》（輯）二書原繫「應是」，改繫本條；依據為同名、同朝代、庫中同名唯一，**未覆核原書**，待人審。'),
    NEW['liujun2']: entity(
        NEW['liujun2'], '劉儁',
        [{'name': '劉雋', 'type': '異體'}, {'name': '子士', 'type': '字'}, {'name': '子奇', 'type': '字'},
         {'name': '愍節', 'type': '諡號'}, {'name': '節愍', 'type': '諡號'}],
        '明', 'ming', '江陵', 'CBDB 66803 籍貫(基本地址) 江陵', 66803,
        {'death': 1408, 'basis': 'CBDB 66803 YearDeath 1408（永樂六年卒），無生年'},
        D + '自「劉俊」hixhd2h9bib6 拆出。CBDB 66803 劉儁（江陵人，永樂六年卒，別名劉雋；字子士、子奇；諡愍節）。'
            '與劉俊（CBDB 198612，新鄉人，天順元年進士，生 1425）是二人。別名類型按 CBDB 重定（原併入時全標「異體」）。'
            '《禮記評》d59f2nipjif4 撰人作「劉雋」，該條 09-04 已摘除對劉俊之繫，本次**不**改繫到本條（未核實是否同人）。'),
}

recs, _, _ = v.load_repo(ROOT, keep_raw=True)
changed, created = [], []


def save(r):
    open(os.path.join(ROOT, r.path), 'w', encoding='utf-8').write(v.dump(r.data, r.fmt))
    changed.append(r.path)


# 1. 應是
r = recs['Entity'][YINGSHI]; d = r.data
before = copy.deepcopy(d)
assert [a['name'] for a in d['alt_names']] == ['敬非', '敬齋', '仁錫', '宸錫'], d['alt_names']
assert d['external_ids'].get('cbdb_id_alt') == [125397, 78522] and d['external_ids']['cbdb_id'] == 79111
d['alt_names'] = [a for a in d['alt_names'] if a['name'] not in ('仁錫', '宸錫')]
del d['external_ids']['cbdb_id_alt']
d['ai_note'] += ('\n\n' + D + '三人錯並（應是／蔡德晉／吳高增）。卸除屬蔡德晉之字 仁錫、宸錫與 external_ids.cbdb_id_alt [125397, 78522]；'
                 '蔡德晉、吳高增已各立獨立 Entity（%s、%s）。「敬齋」CBDB 79111 本人亦有，保留。《禮經本義》《行唐縣新志》《蘭亭志》改繫新條，《三合便覽》摘除繫連。'
                 % (NEW['caidejin'], NEW['wugaozeng']))
if APPLY: save(r)

# 2. 劉俊
r = recs['Entity'][LIUJUN]; d = r.data
assert d['external_ids'].get('cbdb_id_alt') == [66803]
drop = {'劉儁', '劉雋', '子士', '子奇', '愍節', '節愍'}
assert drop <= {a['name'] for a in d['alt_names']}
d['alt_names'] = [a for a in d['alt_names'] if a['name'] not in drop]
del d['external_ids']['cbdb_id_alt']
d['ai_note'] += ('\n\n' + D + '卸除屬劉儁（CBDB 66803）之 alt_names 劉儁、劉雋、子士、子奇、愍節、節愍與 cbdb_id_alt [66803]；劉儁已立獨立 Entity（%s）。'
                 % NEW['liujun2'])
if APPLY: save(r)

# 3. 改繫 Work
def reauthor(wid, new_id, note):
    r = recs['Work'][wid]; d = r.data
    assert len(d['authors']) == 1 and d['authors'][0]['entity_id'] == YINGSHI, d['authors']
    if new_id:
        d['authors'][0]['entity_id'] = new_id
    else:
        del d['authors'][0]['entity_id']
    d['ai_note'] = (d.get('ai_note') or '') + '\n\n' + D + note
    if APPLY: save(r)

reauthor(W_LIJING, NEW['caidejin'], '撰人蔡德晉原誤繫「應是」，改繫蔡德晉 %s（《四庫全書總目》提要：德晉字仁錫，無錫人，與 CBDB 125397 吻合）。' % NEW['caidejin'])
reauthor(W_XINGTANG, NEW['wugaozeng'], '纂修吳高增原誤繫「應是」，改繫吳高增 %s（同名、同朝代、庫中同名唯一；未覆核原書，待人審）。' % NEW['wugaozeng'])
reauthor(W_LANTING, NEW['wugaozeng'], '輯者吳高增原誤繫「應是」，改繫吳高增 %s（同名、同朝代、庫中同名唯一；未覆核原書，待人審）。' % NEW['wugaozeng'])
reauthor(W_SANHE, None, '輯者「敬齋」原誤繫「應是」，摘除 entity_id。「敬齋」是蔡德晉、吳高增、應是三人共有之別號，不能憑別名繫連；'
                        '本書為滿文乾隆五十七年（1792）富氏刻本，而應是卒於 1727 年，與本書年代不合。待人審實際撰人後再繫。')

# 4. 新 Entity
for eid, rec in NEW_ENTITIES.items():
    rel = mintid.path_for(eid, rec['primary_name'])
    created.append(rel)
    if APPLY:
        os.makedirs(os.path.dirname(os.path.join(ROOT, rel)), exist_ok=True)
        open(os.path.join(ROOT, rel), 'w', encoding='utf-8').write(v.dump(rec, recs['Entity'][YINGSHI].fmt))

print(('APPLY' if APPLY else 'DRY-RUN'), '改既有 %d 个，新建 %d 个' % (2 + 4, len(created)))
for p in created: print('  新建', p)
print(json.dumps(NEW, ensure_ascii=False))
