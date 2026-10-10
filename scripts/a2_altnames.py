"""A2：4 個 Entity 的 alt_names 缺 type 者——查實為並條串入的他人之名，自本條刪除並記 ai_note。"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'build'))
import v2common as v

root = os.path.join(os.path.dirname(__file__), '..')
D = '2026-10-10 alt_names 缺 type 覈修：'
PLAN = {
    'hixhd2h9bixi': (['蕭維禎'], D + '刪「蕭維禎」。此名乃 2026-08 前誤繫之 entity 名（《不真空論》ai_note：「Entity原繫蕭維禎，實為誤關聯」），並條時被當別名帶入，非僧肇之名；另無 Entity 可掛，僅刪。'),
    'hixhd2h9bhv4': (['崔志'], D + '刪「崔志」。此名乃誤繫之 entity 名（《法性論》ai_note：「Entity原繫崔志，實為誤關聯」），並條時被當別名帶入，非釋慧遠之名；庫中「崔志元」(hixhd2h9bq61) 為另一人，不能據以掛靠，僅刪。'),
    'hixhd2h9bntz': (['通儒'], D + '刪「通儒」。查 CBDB 與全庫 Entity，無人以「通儒」為名號，其餘出現處皆為文中泛稱（通儒碩學），不能確定歸屬，僅刪。'),
    'hixhd2h9be38': (['蔡德晉', '吳高增', '玉亭', '繼長'], D + '刪「蔡德晉」「吳高增」「玉亭」「繼長」。查 CBDB：本條 cbdb_id=79111 應是（宜黃人，1638-1727）自有別名僅敬非、敬齋；蔡德晉＝CBDB 125397（無錫人，字仁錫／宸錫）、吳高增＝CBDB 78522（秀水人，生1706，別名敬齋／玉亭／繼長）係二人，cbdb_aliases 所謂「人工判定同一人」不成立（生年相差甚遠、籍貫各異）。庫中暫無此二人之 Entity，故僅刪不掛。遺留待決：仁錫、宸錫（字，亦屬蔡德晉）、external_ids 之 cbdb_aliases 125397／78522，及 authors 仍繫本條之《禮經本義》d59f2ma5q3gh（蔡德晉）、《行唐縣新志》d59f2mznfshs、《蘭亭志》d59f2mshx0cg（吳高增）、《三合便覽》d59f2mxhegoz（敬齋）——待另行拆分 Entity 後改繫。'),
}
recs, _, _ = v.load_repo(root, keep_raw=True)
for eid, (names, note) in PLAN.items():
    r = recs['Entity'][eid]
    alts = r.data['alt_names']
    for n in names:
        hit = [a for a in alts if a['name'] == n]
        assert len(hit) == 1 and 'type' not in hit[0], (eid, n)
    r.data['alt_names'] = [a for a in alts if a['name'] not in names]
    r.data['ai_note'] = r.data.get('ai_note', '').rstrip('\n') + '\n\n' + note
    assert all('type' in a for a in r.data['alt_names']), eid
    open(os.path.join(root, r.path), 'w', encoding='utf-8').write(v.dump(r.data, r.fmt))
    print(eid, '刪', names)
