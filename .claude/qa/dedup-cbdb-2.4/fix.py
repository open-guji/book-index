#!/usr/bin/env python3
"""去重方案 2.4：CBDB 配错 9 项＋疑重号 3 项的修正（2026-11-01）。
    python3 fix.py [--apply]
逐项依据见同目录 README.md。每处改动记 ai_note；原值写 fix-report.json（回滚用）。
蕭鈞与 A12 新建的南齐衡阳王条并条另走 apply.py（见 README）。"""
import argparse, glob, json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); QA = os.path.dirname(HERE)
sys.path.insert(0, QA)
import jio  # noqa: E402

TAG = '2026-11-01 去重 2.4 CBDB 配错复核'
ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
report = []


def path_of(eid):
    p = glob.glob(os.path.join(jio.ROOT, 'Entity', '*', '*', '*', eid + '-*.json'))
    assert len(p) == 1, eid
    return os.path.relpath(p[0], jio.ROOT)


def edit(eid, why, mut):
    rel = path_of(eid); d, fmt = jio.load(rel)
    old = json.loads(json.dumps(d, ensure_ascii=False))
    mut(d)
    keys = sorted(k for k in set(old) | set(d) if old.get(k) != d.get(k))
    report.append({'id': eid, 'path': rel, 'changed': keys, 'old': {k: old.get(k) for k in keys}})
    jio.addnote(d, '%s：%s' % (TAG, why))
    if a.apply: jio.save(rel, d, fmt)


def set_cbdb(d, cid, src, wikidata=None):
    ex = {'cbdb_id': cid, 'cbdb_match': 'manual', 'cbdb_source': src}
    if wikidata: ex['wikidata_id'] = wikidata
    d['external_ids'] = ex


def place(d, name, pid, cid):
    d['native_place'] = name; d['native_place_entity_id'] = pid
    d['native_place_basis'] = 'CBDB %s index_addr（%s）' % (cid, TAG[:10])


def drop_place(d):
    for k in ('native_place', 'native_place_entity_id', 'native_place_basis'): d.pop(k, None)


def dates(d, **kw):
    if kw: d['dates'] = dict(kw, basis='現行字段')
    else: d.pop('dates', None)


# ---- 1 蕭鈞：cbdb 12260 是唐人；本条名下《蕭鈞集》撰人為齊武帝子衡陽王（473–494）----
def f_xiaojun(d):
    d.pop('external_ids', None); drop_place(d); d['dynasty'] = '南朝齊'
    d['dynasty_basis'] = '《蕭鈞集》撰人注：蕭鈞（473-494）齊武帝子，封衡陽王；%s' % TAG
edit('hixhd2h9bnk9', '摘去 cbdb_id=12260（唐人，長安，《新唐書·蕭瑀傳》從子；QTW 有其殘篇）及其 wikidata Q22813971（該項為唐中書舍人）、籍貫「長安」；名下《蕭鈞集》《音韻》撰人為南朝齊衡陽王蕭鈞，朝代由「唐」改「南朝齊」。CBDB 無此齊人，不寫 cbdb_id。', f_xiaojun)


# ---- 2 高綽：北魏条，cbdb 498527 是北齊南陽王（字仁通）----
def f_gaochuo(d):
    d.pop('external_ids', None)
    alt = [x for x in d.get('alt_names') or [] if x.get('name') != '仁通']
    if alt: d['alt_names'] = alt
    else: d.pop('alt_names', None)
edit('hixhjhtlitqc', '摘去 cbdb_id=498527（北齊高綽，武成帝子南陽王，字仁通，另有 A12 条 hixicu23niu7）及由它 enrich 來的字「仁通」：本条僅據《補南北史藝文志》「正始律令」撰人之一（北魏，正始 504–508），與北齊高綽（約 6 世紀中葉生）非一人。', f_gaochuo)


# ---- 3 王英 ----
def f_wangying(d):
    set_cbdb(d, 66848, '2.4 复核：CBDB 66848 王英（1376–1450，金谿人，字時彥，號泉坡，諡文安）；名下《王文安公詩集》《王文安公詩文集》《泉坡文集》皆其著', 'Q15916546')
    place(d, '金谿', 'hixi5whldkao', 66848); dates(d, birth=1376, death=1450)
    d['alt_names'] = [{'name': '時彥', 'type': '字'}, {'name': '泉坡', 'type': '號'}, {'name': '文安', 'type': '諡號'}]
edit('hixhd2h9biba', '原繫 cbdb 66846（合肥人，卒 1405，pending_accept 的歧義候選）、wikidata Q45517618 不合：名下《王文安公詩集》《王文安公詩文集》《泉坡文集》為王英（1376–1450，金谿人，字時彥，號泉坡，諡文安）著，改繫 cbdb 66848（wikidata Q15916546，CBDB 號與生卒相符），籍貫合肥改金谿，卒年 1405 改生 1376／卒 1450，補字號諡。《杏林摘要方》《明曆體略》二書（千頃堂書目、明史藝文志僅署「王英」）無證據證其為此人，亦無證其非，未動作者位，待核。', f_wangying)


# ---- 4 何士信：無證據，不動 ----
def f_hsx(d): pass
edit('hixhd2h9bkef', '復核 cbdb 699762（何士信，武進人，字敞甫，明；CBDB 2026-04 新錄，無生卒、著作、仕歷記錄）：本条僅存《圖説一卷綱領一卷》（千頃堂書目，period 未定），既無證據證其配錯，亦無證據證其屬實。cbdb_id 暫保留，標「未證實」，待有人查到敞甫著作再定；《小學集成》《小學書圖》已於 2.1续 改歸宋条 hixi8u5wq7rb。', f_hsx)


# ---- 5 韓奕：名下全是吳縣韓山人（字公望，號蒙齋）----
def f_hanyi(d):
    set_cbdb(d, 133243, '2.4 复核：CBDB 133243 韓奕（吳縣人，字公望，號蒙齋）；名下《韓山人集》《易牙遺意》等為其著')
    place(d, '吳縣', 'hixi4ui5iwao', 133243); dates(d)
    d['alt_names'] = [{'name': '公望', 'type': '字'}, {'name': '蒙齋', 'type': '號'}]
edit('hixhd2h9bexl', '原繫 cbdb 112541（元蕭山韓奕，1269–1318，字仲山）、wikidata Q45697743 不合：名下《韓山人集》《易牙遺意》《蒙齋集》等為吳縣韓奕（字公望，號蒙齋，韓山人）著。改繫 cbdb 133243；籍貫蕭山改吳縣；摘去屬 112541 的生卒 1269–1318、字「仲山」與 wikidata；補號「蒙齋」，字「公望」去 ambiguous 標。朝代「元」暫仍舊（《四庫全書總目》稱元人，CBDB 133243 記明），不屬配錯範圍，未改。', f_hanyi)


# ---- 6 王鞏：名下全是北宋王鞏（字定國，莘縣人）----
def f_wanggong(d):
    set_cbdb(d, 7084, '2.4 复核：CBDB 7084 王鞏（莘縣人，字定國，淸虛居士）；名下《聞見近錄》《甲申雜記》《論語注》等為其著', 'Q45365253')
    place(d, '莘縣', 'hixi6kf0aqkt', 7084); dates(d)
    d['dynasty'] = '北宋'; d['dynasty_basis'] = '《四庫全書總目》：鞏字定國，自號清虛先生，莘縣人，同平章事旦之孫；《論語注》經義考引秦觀序稱元豐二年坐蘇軾詩案；%s' % TAG
    d['period_basis'] = '據 dynasty「北宋」自動歸併'
    d['alt_names'] = [{'name': '定國', 'type': '字'}, {'name': '清虛居士', 'type': '號'}]
edit('hixhd2h9bijf', '原繫 cbdb 37922（南宋，四川人，卒 1236）、wikidata Q45433982 不合：名下《聞見近錄》《甲申雜記》《論語注》等為北宋王鞏（字定國，莘縣人，王旦之孫，蘇軾友）著。改繫 cbdb 7084（wikidata Q45365253）；朝代南宋改北宋；籍貫四川改莘縣；摘去卒年 1236；補字定國、號清虛居士；名下作品作者位朝代「南宋」同改「北宋」。《𠎣源類譜》（國史經籍志僅署「王鞏」）無證據，作者位未動。', f_wanggong)


# ---- 7 吳鎮（清）：松崖，狄道人 ----
def f_wuzhen(d):
    set_cbdb(d, 78178, '2.4 复核：CBDB 78178 吳鎮（1721–1797，狄道州人，字松崖）；名下《松崖文稿》《蘭山詩草》等松崖詩文為其著')
    place(d, '狄道州', 'hixi5wavgnbc', 78178); dates(d, birth=1721, death=1797)
    d['alt_names'] = [{'name': '信辰', 'type': '別名'}, {'name': '士安', 'type': '別名'}, {'name': '松崖', 'type': '號'}]
edit('hixhd2h9bi3w', '原繫 cbdb 55677（達縣人，生 1825，少岷；CBDB 另有 352335 同人重號）、wikidata Q45482817 不合：名下《松崖文稿》《蘭山詩草》《松花庵逸草》等為吳鎮（1721–1797，狄道州人，號松崖）著（2.1续 第二批已把 11 部松崖詩文改歸本条）。改繫 cbdb 78178；籍貫達縣改狄道州；生年 1825 改 1721／卒 1797；別名「少岷」（屬 55677）摘去，補信辰、士安、松崖（CBDB 78178 別名，類型 CBDB 作未詳）。', f_wuzhen)


# ---- 8 王真：唐，《道德經論兵要義述》作者，cbdb 175906 卒 621 不合 ----
def f_wangzhen(d):
    d.pop('external_ids', None); drop_place(d); dates(d)
edit('hixhd2h9bsbg', '摘去 cbdb_id=175906（中山人，卒 621，隋末唐初）、wikidata Q45679064、籍貫中山、卒年 621：名下《道德經論兵要義述》撰人王真為唐憲宗元和間人（上表進書），與卒於 621 者非一人；CBDB 唐人王真只此一號，無對應，不寫 cbdb_id。朝代唐仍舊。', f_wangzhen)


# ---- 9 王賓：吳中，長洲人，字仲光，號光菴 ----
def f_wangbin(d):
    set_cbdb(d, 126776, '2.4 复核：CBDB 126776 王賓（長洲人，字仲光，號光庵／光菴）；名下《光菴集》《吳中古蹟詩》《虎邱詩集》等為其著')
    place(d, '長洲', 'hixi5whkfuo2', 126776); dates(d)
    d['alt_names'] = [{'name': '仲光', 'type': '字'}, {'name': '光菴', 'type': '號'}, {'name': '光庵', 'type': '號'}]
edit('hixhd2h9bi6l', '原繫 cbdb 199150（淳安人，生 1432，字用之）、wikidata Q18235151 不合：名下《光菴集》《吳中古蹟詩》《虎邱詩集》《吳下名賢紀錄》《員峯稿》皆吳中作品，撰人為長洲王賓（字仲光，號光菴）。改繫 cbdb 126776；籍貫淳安改長洲；摘去生年 1432、行第「一」、字「用之」與 wikidata；補字仲光、號光菴／光庵。', f_wangbin)


# ---- 10 姜清：弋陽人，正德辛未進士，著《姜氏秘史》----
def f_jiangqing(d):
    set_cbdb(d, 201696, '2.4 复核：CBDB 201696 姜清（弋陽人，1483 生，字源甫，1511 進士）；與《姜氏秘史》撰人（弋陽人，正德辛未進士）相符')
    place(d, '弋陽', 'hixi636giu4l', 201696); dates(d, birth=1483)
    d['alt_names'] = [{'name': '源甫', 'type': '字'}, {'name': '七十', 'type': '行第'}] + [x for x in d.get('alt_names') or [] if x.get('name') == '姜淸']
    for m in d.get('merged_in') or []:
        if m['id'] == 'hixie9jn4kjk': m['why'] += '；2.4 復核（2026-11-01）：確係 cbdb 198616 配錯，已改繫 201696（弋陽，1511 進士）'
edit('hixhd2h9bi4n', '原繫 cbdb 198616（閿鄉人，生 1423，字子澄，景泰八年進士）、wikidata Q18118397 不合：名下《姜氏秘史》撰人姜清為弋陽人、正德辛未（1511）進士，與 CBDB 201696 相符（弋陽人，生 1483，字源甫，1511 進士），並條時 merged_in 已記「生年 1423 與正德辛未不合」。改繫 201696；籍貫閿鄉改弋陽；生年 1423 改 1483；字子澄、行第二（屬 198616）改字源甫、行第七十；摘去 wikidata。', f_jiangqing)


# ---- 疑重号 3：只更正 merged_in 說明，keeper 的 cbdb 不變 ----
def patch_why(eid, mid, add):
    def f(d):
        for m in d['merged_in']:
            if m['id'] == mid: m['why'] = m['why'] + '；' + add
    return f
edit('hixhd2h9bf1a', '「疑重号」復核：被并条 hixieo0bw852 的 cbdb_id 131764 在 CBDB 是楊言（句容人，隆慶二年進士，1568），不是張鼎思；張鼎思（130570，安陽人，1543–1603，萬曆五年丁丑進士）與其並非同人兩號。131764 是 A12 條 auto_v2 按「慎吾」別名誤配，並條時未帶入 keeper，keeper 的 cbdb 130570 不變。',
     patch_why('hixhd2h9bf1a', 'hixieo0bw852', '2.4 復核（2026-11-01）：131764 為 CBDB 楊言（1568 進士），非張鼎思，不是重號，無需處理'))
edit('hixhd2h9bdps', '「疑重号」復核：被并条 hixieqqa8bqc 的 cbdb_id 649875 在 CBDB 是茅連茹（CGED-Q 清代職官人物，任官 1808–1826），不是范泰恆；范泰恆（360883，河內人，乾隆乙丑 1745 進士）無重號，keeper 的 cbdb 360883 不變。',
     patch_why('hixhd2h9bdps', 'hixieqqa8bqc', '2.4 復核（2026-11-01）：649875 為 CBDB 茅連茹（CGED-Q 人物），非范泰恆，不是重號，無需處理'))

# ---- 王鞏名下作品：作者位朝代「南宋」改「北宋」----
for f in sorted(glob.glob(os.path.join(jio.ROOT, 'Work', '*', '*', '*', '*.json'))):
    if 'hixhd2h9bijf' not in open(f, encoding='utf-8').read(): continue
    rel = os.path.relpath(f, jio.ROOT); d, fmt = jio.load(rel); ch = []
    for x in d.get('authors') or []:
        if isinstance(x, dict) and x.get('entity_id') == 'hixhd2h9bijf' and x.get('dynasty') == '南宋':
            x['dynasty'] = '北宋'; ch.append('authors.dynasty')
    desc = d.get('description')
    if ch and isinstance(desc, dict) and '南宋王鞏' in (desc.get('text') or ''):
        desc['text'] = desc['text'].replace('南宋王鞏', '北宋王鞏'); ch.append('description.text')
    if ch:
        report.append({'id': d['id'], 'path': rel, 'changed': ch})
        jio.addnote(d, '%s：作者位王鞏（hixhd2h9bijf）朝代「南宋」改「北宋」，隨人物條由 cbdb 37922 改繫 7084。' % TAG)
        if a.apply: jio.save(rel, d, fmt)

json.dump(report, open(os.path.join(HERE, 'fix-report%s.json' % ('' if a.apply else '-dry')), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
print('%s：改 %d 处' % ('已改' if a.apply else '乾跑', len(report)))
