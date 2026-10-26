#!/usr/bin/env python3
"""方志-并 拆混记录（2026-10-26）：一条 Work 混进别的修次或另一部书的著录、Book、资源，先拆再并。
逐条方案见同目录 plan-a.json（M01–M08）、plan-b.json（M09–M16），由两个子 agent 只读研究得出；本脚本照方案执行，
字段改写只做方案里证据明确的项。新 Work id 由 mintid.py 车道 fangzhi 预先铸好写死。

    python3 split_fz.py [--apply]     # cwd 为正式库根
"""
import glob, json, re, sys
TODAY = '2026-10-26'
APPLY = '--apply' in sys.argv
TAG = '去重方案方志-并 拆混記錄'
cache, created = {}, {}


def path(i, fam='Work'):
    p = glob.glob(f'{fam}/{i[-3]}/{i[-2]}/{i[-1]}/{i}-*.json')
    assert len(p) == 1, (i, p)
    return p[0]


def rec(i, fam='Work'):
    if i not in cache:
        cache[i] = [path(i, fam), json.load(open(path(i, fam), encoding='utf-8'))]
        assert not cache[i][1].get('merged_into'), ('墓碑', i)
    return cache[i][1]


def bump(d):
    a, b, c = (d.get('revision') or '1.0.0').split('.')
    d['revision'] = '%s.%d.0' % (a, int(b) + 1); d['revised_at'] = TODAY


def note(i, s, fam='Work'):
    d = rec(i, fam)
    d['ai_note'] = ((d['ai_note'] + '\n\n') if d.get('ai_note') else '') + '%s %s：%s' % (TODAY, TAG, s)


def tgt(i):
    return created[i][0] if i in created else rec(i)


def pop_ib(w, expect, src=None):
    d = rec(w)
    hits = [k for k, e in enumerate(d['indexed_by']) if expect in (e.get('title_info', '') + e.get('author_info', '')) and (src is None or e.get('source') == src)]
    assert len(hits) == 1, (w, expect, hits)
    return d['indexed_by'].pop(hits[0])


def move_ib(w, expect, to, src=None, why=''):
    e = pop_ib(w, expect, src)
    for k in ('misattached', 'misattached_note'):
        e.pop(k, None)
    if why:
        e['note'] = ((e['note'] + '；') if e.get('note') else '') + '%s 自 %s 移來：%s' % (TODAY, w, why)
    t = tgt(to)
    if any(x.get('source') == e.get('source') and x.get('source_bid') == e.get('source_bid') and x.get('title_info') == e.get('title_info') for x in t.get('indexed_by') or []):
        return 'dup'
    t.setdefault('indexed_by', []).append(e)
    return 'moved'


def drop_ib(w, expect, other, src):
    """重複著錄：other 已有同書目同一條（繁簡寫法可不同），本條刪去不移。"""
    e = pop_ib(w, expect, src)
    assert any(x.get('source') == e.get('source') and x.get('source_bid') == e.get('source_bid') and len(x.get('title_info', '')) == len(e.get('title_info', ''))
               for x in rec(other).get('indexed_by') or []), ('對方無同條', w, other, e['title_info'])


def move_book(b, frm, to, why):
    d = rec(b, 'Book')
    assert d['work_id'] == frm, (b, d['work_id'], frm)
    d['work_id'] = to
    note(b, '%s；work_id 由 %s 改指 %s。' % (why, frm, to), 'Book'); bump(d)


def move_res(frm, url_part, to):
    d = rec(frm)
    hits = [r for r in d.get('resources') or [] if url_part in r.get('url', '')]
    assert len(hits) == 1, (frm, url_part, len(hits))
    r = hits[0]; d['resources'].remove(r)
    g = r.get('group')
    if g and not any(x.get('group') == g for x in d['resources']) and g in (d.get('resource_groups') or {}):
        gv = d['resource_groups'].pop(g)
        if not d['resource_groups']: d.pop('resource_groups')
    else:
        gv = None
    t = tgt(to)
    if not any(x.get('url') == r.get('url') for x in t.get('resources') or []):
        t.setdefault('resources', []).append(r)
        if gv is not None: t.setdefault('resource_groups', {}).setdefault(g, gv)


def desc(i, text, sources):
    rec(i)['description'] = {'text': text, 'sources': sources}


def new_work(i, src, nw, cls_from):
    a0 = nw['authors'][0]
    d = {'schema_version': 1, 'id': i, 'type': 'work', 'title': nw['title'], 'authors': nw['authors'],
         'dynasty': a0['dynasty'], 'dynasty_basis': 'author_propagation',
         'period': {'明': 'ming', '清': 'qing'}[a0['dynasty']], 'period_basis': '據 authors[0].dynasty「%s」' % a0['dynasty'],
         'juan_count': {'number': nw['juan']}, 'measures': [{'number': nw['juan'], 'unit': '卷'}], 'measure_info': nw['measure_info'],
         'description': {'text': nw['description'], 'sources': ['中國古籍總目']}, 'indexed_by': [],
         'related_works': nw.get('related_works', []),
         'ai_note': '%s %s新建：自 %s 拆出（%s）。' % (TODAY, TAG, src, nw['why']), 'revision': '1.0.0', 'revised_at': TODAY}
    created[i] = (d, cls_from)


touched_ids = []
def done(*ids):
    for i in ids:
        if i not in created:
            bump(rec(i)); touched_ids.append(i)

# ── M01 永順府志 d59f2n7golxc：同治魏式曾增修本拆出，新建 N1 ──
N1, N2, N3, N4 = 'd59g2k8yudq8', 'd59g2k8yudq9', 'd59g2k8yudqa', 'd59g2k8yudqb'
P = {p['mid']: p for f in ('plan-a.json', 'plan-b.json') for p in json.load(open(__file__.rsplit('/', 1)[0] + '/' + f, encoding='utf-8'))}
def nw(mid):
    return [m['new_work'] for m in P[mid]['move'] if m.get('target') == 'NEW'][0]
W = 'd59f2n7golxc'
new_work(N1, W, dict(nw('M01'), why='[同治]魏式曾增修、郭鑑襄增纂本，與乾隆張天如原修本非同一修次'), W)
move_ib(W, '[同治]永順府志', N1)
move_book('9951h8enep', W, N1, '同治增修增刻本，隨著錄移至新建 Work')
note(W, '總目「[同治]永順府志十二卷首一卷」（魏式曾增修、郭鑑襄增纂）著錄與 Book 9951h8enep 屬同治增修本，移至新建 %s；本條專指乾隆張天如修本。' % N1); done(W)

# ── M02 泰安州志 d59f2nkqwa9s：萬曆任弘烈修本拆出，新建 N2 ──
W = 'd59f2nkqwa9s'
new_work(N2, W, dict(nw('M02'), why='[萬曆]任弘烈修、段廷選纂六卷本，與康熙鄒文郁增修四卷本非同一修次'), W)
move_ib(W, '[萬曆]泰安州志', N2)
for b in ('9951hwr5s0', '9951hwfx8h'):
    move_book(b, W, N2, '[萬曆]泰安州志六卷，隨著錄移至新建 Work')
move_res(W, 'File:%EF%BC%88%E8%90%AC%E6%9B%86', N2)
move_res(W, 'fid=412000001414', N2)
d = rec(W); d['juan_count'] = {'number': 4}; d['measures'] = [m if m.get('unit') != '卷' else {'number': 4, 'unit': '卷'} for m in d.get('measures') or []]
d['measure_info'] = '四卷'; d['dynasty'] = '清'; d['period'] = 'qing'; d['dynasty_basis'] = 'edition'; d['period_basis'] = '康熙增修本'
note(W, '萬曆任弘烈修、段廷選纂六卷本之總目著錄、Book 9951hwr5s0／9951hwfx8h、維基共享（萬曆）泰安州志 PDF 與國圖 412000001414 移至新建 %s；卷數 6→4、朝代明→清（本條為康熙九年重刊之鄒文郁增修本）。' % N2); done(W)

# ── M03 湖廣通志 d59f2mdaq03k：明史魏裳條重複刪去，识典康熙本改掛 ──
W = 'd59f2mdaq03k'
drop_ib(W, '魏裳', 'd59f2ncywf0g', '明史藝文志')
move_res(W, 'book/HY0170', 'd59fyobpzdhd')
desc(W, '清邁柱等監修、夏力恕等纂，一百二十卷首一卷，雍正十一年成，合湖南、湖北為一書。有清雍正十一年刻本、四庫全書本。見著錄於《欽定四庫全書總目》。', ['欽定四庫全書總目'])
note(W, '明史藝文志「魏裳《湖廣通志》九十八卷」為明修另書，d59f2ncywf0g 已有同條，刪去；识典 HY0170（康熙二十三年刻本）改掛 d59fyobpzdhd；description 原「佚文見引」「亡佚」不實（本書今存），改寫。'); done(W, 'd59fyobpzdhd')

# ── M04 鳳臺縣志 d59f2mqhhybl：書目答問條屬嘉慶李兆洛志 ──
W = 'd59f2mqhhybl'
move_ib(W, '鳳臺縣志', 'd59f2ndsv30h', '書目答問', '書目答問所著為安徽鳳臺李兆洛嘉慶志')
desc(W, '清林荔修，有清乾隆四十八年（癸卯）刊本（故宮）。', ['國立故宮博物院善本舊籍'])
note(W, '書目答問「鳳臺縣志」一條實為安徽鳳臺李兆洛嘉慶志，移至 d59f2ndsv30h；本條為山西鳳臺林荔修乾隆志，description 改寫。'); note('d59f2ndsv30h', '自 %s 移入書目答問「鳳臺縣志」一條（李兆洛）。' % W); done(W, 'd59f2ndsv30h')

# ── M05 山東通志 d59f2nje79c0：四庫總目三十六卷條屬雍正岳濬志，重複刪去 ──
W = 'd59f2nje79c0'
drop_ib(W, '三十六卷', 'd59f2nuuuvi9', '欽定四庫全書總目')
d = rec(W); d['juan_count'] = {'number': 40}; d['measures'] = [m if m.get('unit') != '卷' else {'number': 40, 'unit': '卷'} for m in d.get('measures') or []]; d['measure_info'] = '四十卷'
desc(W, '明陸釴等纂修，四十卷，嘉靖十二年刊。見著錄於《明史藝文志》《國史經籍志》，《四庫全書存目叢書》影印山東省圖書館藏明嘉靖刻本。', ['明史藝文志', '國史經籍志', '四庫全書存目叢書'])
note(W, '四庫總目「《山東通志》三十六卷」屬雍正岳濬志，d59f2nuuuvi9 已有同條，刪去；卷數 36→40，description 改寫（去三十六卷與不實之佚文句）。'); done(W)

# ── M06 天臺山志 d59f2gikadxc：明史僧傳燈條屬天台山方外志 ──
W = 'd59f2gikadxc'
move_ib(W, '传灯', 'd59f6em6ys5i', '明史藝文志', '明史作《天台山志》二十九卷，即傳燈《天台山方外志》')
desc(W, '不著撰人，一卷。四庫總目據書中稱前至元，定為元順帝時人作。見著錄於《欽定四庫全書總目》《元史藝文志》，有明正統道藏本。', ['欽定四庫全書總目', '元史藝文志'])
note(W, '明史藝文志「僧傳燈《天台山志》二十九卷」為傳燈《天台山方外志》，移至 d59f6em6ys5i；description 改寫。'); note('d59f6em6ys5i', '自 %s 移入明史藝文志「僧傳燈《天台山志》二十九卷」一條。' % W); done(W, 'd59f6em6ys5i')

# ── M07 東阿縣志 d59fyp0ieuip：康熙四年原修本拆出，新建 N3 ──
W = 'd59fyp0ieuip'
new_work(N3, W, dict(nw('M07'), why='康熙四年劉沛先修、王吉臣纂原修本，與康熙五十四年劉廷瑾增修本非同一修次'), W)
move_ib(W, '王吉臣', N3)
move_book('99484fkb29', W, N3, '康熙四年原修本，隨著錄移至新建 Work')
note(W, '總目康熙四年劉沛先修、王吉臣纂原修本著錄與 Book 99484fkb29 移至新建 %s；本條專指康熙五十四年增修本。早先併入之 1exp05o4w68e8 亦屬原修本，其墓碑未改指。' % N3); done(W)

# ── M08 盛京通志 d59f2n023y0w：雍正三十三卷本拆出，新建 N4 ──
W = 'd59f2n023y0w'
new_work(N4, W, dict(nw('M08'), why='雍正呂耀曾、王河修三十三卷本，與乾隆元年四十八卷本非同一修次'), W)
move_ib(W, '[雍正]盛京通志', N4)
move_book('9951isa4n4', W, N4, '雍正三十三卷本，隨著錄移至新建 Work')
note(W, '總目「[雍正]盛京通志三十三卷首一卷」著錄與 Book 9951isa4n4 移至新建 %s。' % N4); done(W)

# ── M09 河南志 d59f2hez3gg2：總目大典輯本著錄與三 Book 屬元河南志 ──
W, T = 'd59f2hez3gg2', 'd59f2n4yh0xs'
move_ib(W, '河南志不分卷', T, '中國古籍總目', '總目題宋宋敏求纂修，實為徐松永樂大典輯本，即元河南志')
for b in ('9951gr8lj4', '9951gqxczk', '9951gqxczl'):
    move_book(b, W, T, '徐松永樂大典輯本《河南志》，即元河南志')
move_res('d59f2hjmenlt', 'wikisource.org/wiki/%E6%B2%B3%E5%8D%97%E5%BF%97', T)
note(W, '總目「[宋]河南志不分卷」著錄與 Book 9951gr8lj4／9951gqxczk／9951gqxczl 為徐松大典輯本（元河南志），移至 %s；本條專指已佚之宋敏求《河南志》二十卷。' % T)
note('d59f2hjmenlt', '维基文库「河南志」頁（元佚名撰、徐松輯）改掛 %s。' % T)
note(T, '自 %s 移入總目大典輯本著錄與三個 Book，自 d59f2hjmenlt 移入维基文库頁。' % W); done(W, T, 'd59f2hjmenlt')

# ── M10 河南通志 d59f2mdb18n4：明史、國史經籍志鄒守愚條重複刪去，识典順治本改掛 ──
W = 'd59f2mdb18n4'
drop_ib(W, '鄒守愚', 'd59f2ndji2v8', '明史藝文志')
drop_ib(W, '四十五卷', 'd59f2ndji2v8', '國史經籍志')
for h in ('book/HY0122', 'book/HY4295'):
    move_res(W, h, 'd59fynr6i6m8')
d = rec(W); d['description']['sources'] = [s for s in d['description'].get('sources', []) if s not in ('明史藝文志', '國史經籍志')]
note(W, '明史、國史經籍志「鄒守愚《河南通志》四十五卷」屬嘉靖志，d59f2ndji2v8 已有同條，刪去；识典 HY0122、HY4295（順治十七年刻本）改掛 d59fynr6i6m8。'); done(W, 'd59fynr6i6m8')

# ── M11 畿輔通志 d59f2md9sagw：宣統石印本 Book 屬同治志，作者改回雍正志修纂人 ──
W = 'd59f2md9sagw'
move_book('988g7w3d36', W, 'd59f2n79i5fk', '清宣統二年石印本為同治李鴻章修、黃彭年纂畿輔通志')
d = rec(W)
d['authors'] = [{'name': '唐執玉', 'role': '修', 'dynasty': '清'}, {'name': '李衛', 'role': '修', 'dynasty': '清', 'entity_id': 'hixhd2h9bo6n'},
                {'name': '陳儀', 'role': '纂', 'dynasty': '清'}, {'name': '田易', 'role': '纂', 'dynasty': '清'}]
desc(W, '唐執玉、李衛等修，陳儀、田易等纂。一百二十卷。雍正七年奉詔重修，雍正十三年成書刊行，收入四庫全書。', ['欽定四庫全書總目'])
note(W, '故宮宣統二年石印本 Book 988g7w3d36 屬同治志，移至 d59f2n79i5fk；隨之帶入之作者「黃彭年總纂」改為雍正志修纂人（據總目「清唐執玉、李衞修;清陳儀、田易纂」），description 改寫。'); done(W)

# ── M13 桂林志 d59f2ngj6ygw：明史陳璉條屬 d59f6esa3dhe ──
W = 'd59f2ngj6ygw'
move_ib(W, '陳璉', 'd59f6esa3dhe', '明史藝文志')
d = rec(W)
for e in d['indexed_by']:
    e.pop('misattached', None); e.pop('misattached_note', None)
d['dynasty'] = '南宋'; d['dynasty_basis'] = 'author_propagation'
d['description']['sources'] = [s for s in d['description'].get('sources', []) if s != '明史藝文志']
d['description']['text'] = re.sub(r'《明史藝文志》', '', d['description']['text']).replace('》》', '》').replace('《宋史藝文志》《宋史藝文志補》', '《宋史藝文志》《宋史藝文志補》')
t = rec('d59f6esa3dhe')
if t.get('authors') and not t['authors'][0].get('dynasty'): t['authors'][0]['dynasty'] = '明'
note(W, '明史藝文志「陳璉《桂林志》三十卷」為明修另書，移至 d59f6esa3dhe；宋志條 misattached 標記摘去（09-05 已判真源）；dynasty 明→南宋（撰人江文叔）。'); note('d59f6esa3dhe', '自 %s 移入明史藝文志陳璉條，authors[0].dynasty 補「明」。' % W); done(W, 'd59f6esa3dhe')

# ── M14 金華府志 d59f2mdiu681：四庫總目不著撰人三十卷條屬萬曆志 ──
W = 'd59f2mdiu681'
move_ib(W, '金華府志', 'd59f2nfdd5oh', '欽定四庫全書總目', '提要題不著撰人，書中記隆慶、萬曆間事；存目叢書據萬曆刻本影印，定為王懋德本')
desc(W, '張藎（清）修，沈麟趾等纂。三十卷。康熙二十二年刻。本書收入《國立故宮博物院善本舊籍》（清康熙二十三年刊本）。', ['國立故宮博物院善本舊籍'])
for a in rec(W).get('authors') or []:
    if a.get('name') == '張蓋': a['name'] = '張藎'
note(W, '四庫總目「金華府志三十卷」不著撰人、記隆萬間事，屬萬曆王懋德本，移至 d59f2nfdd5oh；description 改寫，誤字張蓋→張藎。'); note('d59f2nfdd5oh', '自 %s 移入四庫總目「金華府志三十卷」一條。' % W); done(W, 'd59f2nfdd5oh')

# ── M15 和州志 d59f2hg0v66a：書目答問章學誠條屬乾隆和州志 ──
W = 'd59f2hg0v66a'
e = pop_ib(W, '和州志', '書目答問'); e['author_info'] = '章學誠'
e['note'] = '%s 自 %s 移來；author_info 原剖分誤作他書名，改章學誠。' % (TODAY, W)
rec('d59fyns9iuip').setdefault('indexed_by', []).append(e)
desc(W, '劉禹錫撰。八卷。見著錄於《國史經籍志》。其著錄之文作「《和州志》八卷（劉禹錫）」。本書惟《國史經籍志》一志著錄，別無他證。', ['國史經籍志'])
note(W, '書目答問「和州志」一條為章學誠乾隆志，移至 d59fyns9iuip。所繫 entity hixhd2h9biij 為北宋同名劉禹錫（1097–1144），國史經籍志此條所指待考，未動。'); note('d59fyns9iuip', '自 %s 移入書目答問「和州志」一條。' % W); done(W, 'd59fyns9iuip')

# ── M16 攝山志 d59f2ndy648w：國史經籍志金鑾二卷條屬明金鑾攝山志 ──
W = 'd59f2ndy648w'
move_ib(W, '攝山志', 'd59f6emste6a', '國史經籍志')
desc(W, '陳毅（清）撰，汪志伊刪補。八卷首一卷。乾隆五十五年蘇州府署刻。見著錄於《清史稿藝文志》。', ['清史稿藝文志'])
t = rec('d59f6emste6a')
if t.get('authors') and not t['authors'][0].get('dynasty'): t['authors'][0]['dynasty'] = '明'
note(W, '國史經籍志「《攝山志》二卷」為明金鑾書，移至 d59f6emste6a；description 改寫。'); note('d59f6emste6a', '自 %s 移入國史經籍志「攝山志二卷」一條。' % W); done(W, 'd59f6emste6a')

if not APPLY:
    print('乾跑：改 %d 檔，新建 %d' % (len(cache), len(created))); sys.exit()
for i, (p, d) in cache.items():
    open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
for i, (d, src) in created.items():
    p = 'Work/%s/%s/%s/%s-%s.json' % (i[-3], i[-2], i[-1], i, re.sub(r'[\[\]［］]', '', d['title']))
    import os; os.makedirs(os.path.dirname(p), exist_ok=True)
    open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
    for cp in glob.glob('classification/*/members/*.json'):
        s = open(cp, encoding='utf-8').read()
        if '"%s"' % src in s:
            c = json.loads(s); row = [r for r in c['members'] if r[0] == src][0]
            c['members'].append([i] + row[1:]); c['members'].sort()
            rows = ',\n    '.join(json.dumps(m, ensure_ascii=False) for m in c['members'])
            open(cp, 'w', encoding='utf-8').write('{\n  "node": %s,\n  "members": [\n    %s\n  ]\n}\n' % (json.dumps(c['node'], ensure_ascii=False), rows))
print('寫 %d 檔，新建 %d' % (len(cache), len(created)))
