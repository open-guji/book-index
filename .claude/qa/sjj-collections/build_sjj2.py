#!/usr/bin/env python3
"""十三经纵向补全：补建丛编 Collection（11-15，车道 a11-sjj-coll）。

所有事实取自 CiNii Books 的丛书母记录与子记录（ci.nii.ac.jp/ncid/<NCID>，2026-11-15 抓取）；
核不实的不建。成员挂接见 attach_members.py。
用法：build_sjj2.py [--apply]   默认乾跑，--apply 才写文件，并把新 id 存到 ids2.json
"""
import argparse, datetime, glob, json, os, pathlib, re, sys
ROOT = pathlib.Path(__file__).resolve().parents[3]
sys.path[:0] = [str(ROOT / '.claude/qa'), str(ROOT / 'build')]
import mintid, v2common as V  # noqa: E401
TODAY = datetime.date.today().isoformat()
HERE = pathlib.Path(__file__).resolve().parent
LANE = 'a11-sjj-coll'
CINII = lambda n: {'id': n, 'name': 'CiNii Books', 'type': 'url', 'details': 'https://ci.nii.ac.jp/ncid/' + n}
CH_UP = '8rlcsybg2hih'  # 出土簡帛

# key -> spec；parent 用 key 引用，建后换 id
S = {}


def add(key, title, **kw):
    S[key] = dict(title=title, **kw)



YAN = [{'name': '嚴靈峯', 'role': '編'}]
CI_YAN_NOTE = '據 CiNii Books（ci.nii.ac.jp）母記錄核定，未核原書。'
def cat(**kw): return kw
def att(y, basis): return {'year': y, 'certainty': 'attested', 'source': 'catalog', 'basis': basis}

add('zhuang', '無求備齋莊子集成', additional_titles=['莊子集成'], authors=YAN,
    description={'text': '嚴靈峯編輯，藝文印書館影印。分初編（1972 年 5 月，三十冊）與續編（1974 年 12 月，四十二冊），合計七十二冊，彙集歷代莊子注釋、音義、校勘及日本傳本，與《老子集成》《列子集成》為嚴氏諸子集成之一。《老列莊三子集成補編》（成文 1982）補其所未收。本條為初編、續編之總名條。',
                 'sources': ['CiNii Books BA46441904（初編）', 'CiNii Books BA55208456（續編）']},
    publication_info={'publisher': '藝文印書館', 'place': '臺北', 'year': '1972-1974', 'details': '初編 1972.5；續編 1974.12'},
    dating={'year_range': [1972, 1974], 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄初編 1972.5、續編 1974.12'},
    count={'juan': None, 'ce': 72, 'zhong': None, 'han': None, 'source': 'CiNii Books 初編冊次 1—30、續編 1—42'},
    sources=[CINII('BA46441904'), CINII('BA55208456')])
add('zhuang1', '無求備齋莊子集成初編', parent='zhuang', authors=YAN,
    description={'text': '嚴靈峯編輯，藝文印書館 1972 年 5 月影印，精裝三十冊。', 'sources': ['CiNii Books BA46441904']},
    publication_info={'publisher': '藝文印書館', 'place': '臺北', 'year': '1972', 'year_iso': '1972', 'details': '1972.5'},
    dating=att(1972, 'CiNii Books 著錄出版年「1972.5」'),
    count={'juan': None, 'ce': 30, 'zhong': None, 'han': None, 'source': 'CiNii Books BA46441904 冊次 1—30'},
    sources=[CINII('BA46441904')])
add('zhuang2', '無求備齋莊子集成續編', parent='zhuang', authors=YAN,
    description={'text': '嚴靈峯編輯，藝文印書館 1974 年 12 月影印，精裝四十二冊。', 'sources': ['CiNii Books BA55208456']},
    publication_info={'publisher': '藝文印書館', 'place': '臺北', 'year': '1974', 'year_iso': '1974', 'details': '1974.12'},
    dating=att(1974, 'CiNii Books 著錄出版年「1974.12」'),
    count={'juan': None, 'ce': 42, 'zhong': None, 'han': None, 'source': 'CiNii Books BA55208456 冊次 1—42'},
    sources=[CINII('BA55208456')])
add('xun', '無求備齋荀子集成', additional_titles=['荀子集成'], authors=YAN,
    description={'text': '嚴靈峯編輯，成文出版社 1977 年 10 月影印，精裝，CiNii 冊次列至第 49 冊，彙集歷代荀子注釋、校勘及日本傳本。儒家網轉載之目錄見 https://www.rujiazg.com/article/2601。',
                 'sources': ['CiNii Books BA32675689', 'https://www.rujiazg.com/article/2601']},
    publication_info={'publisher': '成文出版社', 'place': '臺北', 'year': '1977', 'year_iso': '1977', 'details': '1977.10'},
    dating=att(1977, 'CiNii Books 著錄出版年「1977.10」'),
    count={'juan': None, 'ce': 49, 'zhong': None, 'han': None, 'source': 'CiNii Books BA32675689 冊次列至 49'},
    sources=[CINII('BA32675689')])
add('xjwxck2', '孝經文獻叢刊第二輯', parent_id='8rle3p1lu1w5',
    authors=[{'name': '曾振宇', 'role': '主編'}, {'name': '江曦', 'role': '主編'}],
    description={'text': '上海古籍出版社 2025 年 10 月出版（儒家網 2026-04 報導），點校整理本。已見子目：江曦《孝經學著述總目》；毛奇齡等《孝經問（外二種）》（郭征整理）；張敘等《孝經精義（外二種）》（李琳整理）；洪良品等《古文孝經薈解（外五種）》（徐國峰整理）；〔日〕片山兼山等《古文孝經孔傳參疏（外四種）》（李暢然、高暢整理）。冊數未載，CiNii 未見著錄。',
                 'sources': ['https://www.rujiazg.com/article/31812']},
    publication_info={'publisher': '上海古籍出版社', 'place': '上海', 'year': '2025', 'year_iso': '2025', 'details': '2025.10'},
    dating=att(2025, '儒家網 article/31812 載各分冊 2025 年 10 月出版'),
    sources=[{'id': 'rujiazg-31812', 'name': '儒家網', 'type': 'url', 'details': 'https://www.rujiazg.com/article/31812'}], ai_note='據儒家網報導，未核 CiNii／出版社目錄；冊數待補。'),
add('hkjs', '和刻本經書集成', authors=[{'name': '長澤規矩也', 'role': '編'}],
    description={'text': '長澤規矩也編，古典研究會刊，汲古書院發行，1975—1977 年，共七輯：正文之部四輯、古注之部三輯，影印日本江戶時代刊行（和刻）之儒家經書白文、訓點本與古注本。',
                 'sources': ['CiNii Books BN02087934']},
    publication_info={'publisher': '古典研究會；汲古書院', 'place': '東京', 'year': '1975-1977', 'details': '第1—4輯正文之部；第5—7輯古注之部'},
    dating={'year_range': [1975, 1977], 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄「1975-1977」'},
    count={'juan': None, 'ce': 7, 'zhong': None, 'han': None, 'source': 'CiNii Books BN02087934 第1—7輯'},
    sources=[CINII('BN02087934')])
add('hkgy', '和刻本中國古逸書叢刊', authors=[{'name': '金程宇', 'role': '編'}],
    description={'text': '金程宇編，鳳凰出版社 2012 年 12 月出版（南京大學域外漢籍研究所專刊），影印日本古鈔本、和刻本所存中國佚書及稀見本，如《文鏡秘府論》《古文真寶》《千家詩》等；CiNii 著錄關連文獻 54 件，編號見至第 70 號。',
                 'sources': ['CiNii Books BB12707779']},
    publication_info={'publisher': '鳳凰出版社', 'place': '南京', 'year': '2012', 'year_iso': '2012', 'details': '2012.12'},
    dating=att(2012, 'CiNii Books 著錄出版年「2012.12」'),
    count={'juan': None, 'ce': None, 'zhong': 54, 'han': None, 'source': 'CiNii Books BB12707779 關連文獻 54 件'},
    sources=[CINII('BB12707779')])
add('gzj', '漢籍國字解全書', additional_titles=['漢籍國字解全書 先哲遺著', '先哲遺著漢籍國字解全書', '漢籍国字解全書'],
    authors=[{'name': '早稻田大學編輯部', 'role': '編纂'}],
    description={'text': '早稻田大學出版部刊，收江戶儒者以日文（國字）注解漢籍之遺著，含四書五經、國語、戰國策、老莊荀墨管、楚辭等。CiNii 著錄：先哲遺著追補第31—45卷 1914—1917；第1—36卷再版 1926—1933；NDL 著錄第8卷 1927 年。總卷數 45（初版年未核）。',
                 'sources': ['CiNii Books BA34784233', 'CiNii Books BN15544642', 'NDL Search R100000039-I1904125']},
    publication_info={'publisher': '早稻田大學出版部', 'place': '東京', 'year': '1914-1933', 'details': '各卷印次不一，見說明'},
    dating={'year_range': [1914, 1933], 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄追補 1914-1917、再版 1926-1933；初版年未核'},
    count={'juan': 45, 'ce': None, 'zhong': None, 'han': None, 'source': 'CiNii Books BN15544642 列至第45巻'},
    sources=[CINII('BA34784233'), CINII('BN15544642')]),
add('cpcs', '昌平叢書', authors=[{'name': '京都帝國大學', 'role': '刊'}],
    description={'text': '京都帝國大學 1917 年據江戶幕府昌平坂學問所官版（學問所御版）重印，聖華房製版，限定三十部，另有《昌平叢書目録》。子目含《孝經鄭註》《孝經鄭氏解》《孝經鄭註補證》合刻、宋大家文抄、《誠齋詩話》等。',
                 'sources': ['CiNii Books BB20000514', 'CiNii Books BB19946519']},
    publication_info={'publisher': '京都帝國大學；聖華房', 'place': '京都', 'year': '1917', 'year_iso': '1917', 'details': '限定30部'},
    dating=att(1917, 'CiNii Books 著錄 [1917] 限定30部；原版為江戶昌平坂學問所官版'),
    sources=[CINII('BB20000514'), CINII('BB19946519')])
add('rlcs', '日本儒林叢書', authors=[{'name': '關儀一郎', 'role': '編'}],
    description={'text': '關儀一郎編，收江戶儒者經學與思想著作。CiNii 著錄鳳出版 1978 年 4 月本，正編合續編、續續編共十四卷（續編第 7—10 卷，續續編第 11—13 卷）；原本刊年未核。',
                 'sources': ['CiNii Books BA87962486', 'CiNii Books BA87962533', 'CiNii Books BA87962555']},
    publication_info={'publisher': '鳳出版', 'place': '東京', 'year': '1978', 'year_iso': '1978', 'details': '1978.4 影印；原本刊年未核'},
    dating=att(1978, 'CiNii Books 著錄鳳出版 1978.4 本；原本刊年未核'),
    count={'juan': 14, 'ce': None, 'zhong': None, 'han': None, 'source': 'CiNii Books BA87962486 第1—14卷'},
    sources=[CINII('BA87962486'), CINII('BA87962533'), CINII('BA87962555')]),
add('rz', '儒藏', authors=[{'name': '北京大學《儒藏》編纂與研究中心', 'role': '編纂'}],
    description={'text': '北京大學《儒藏》編纂與研究中心編纂，北京大學出版社出版的大型儒家典籍點校叢書。精華編中國部分 282 冊，收書 510 種（傳世文獻 458、出土文獻 52），已全部出版；全本《儒藏》另規劃韓國之部 89 種 37 冊、日本之部 51 種 18 冊、越南之部 20 種 2 冊（編纂中）。',
                 'sources': ['王博《傳承中華文明 推進全本〈儒藏〉編纂與研究》 https://www.aisixiang.com/data/143583.html']},
    publication_info={'publisher': '北京大學出版社', 'place': '北京'},
    sources=[{'id': 'aisixiang-143583', 'name': '愛思想', 'type': 'url', 'details': 'https://www.aisixiang.com/data/143583.html'}],
    ai_note='總名條；起訖年未核，不填 dating。'),
add('rz1', '《儒藏》精華編', additional_titles=['儒藏精華編', '《儒藏》精華編選刊', '儒藏精華編選刊'], parent='rz', authors=[{'name': '北京大學《儒藏》編纂與研究中心', 'role': '編纂'}],
    description={'text': '北京大學出版社出版，中國部分 282 冊、510 種（傳世文獻 458、出土文獻 52）；單行本以《〈儒藏〉精華編選刊》之名陸續出版，CiNii 著錄 134 件（至 2026.4 如《論語義疏》校點本）。',
                 'sources': ['CiNii Books BD05453926', 'https://www.aisixiang.com/data/143583.html']},
    publication_info={'publisher': '北京大學出版社', 'place': '北京'},
    count={'juan': None, 'ce': 282, 'zhong': 510, 'han': None, 'source': '王博文：精華編中國部分 282 冊 510 種；CiNii 選刊 134 件'},
    sources=[CINII('BD05453926'), {'id': 'aisixiang-143583', 'name': '愛思想', 'type': 'url', 'details': 'https://www.aisixiang.com/data/143583.html'}])



def title_file(t):
    return re.sub(r'[\s/\\［］\[\]（）()〔〕【】<>:"|?*、，。·]', '', t)[:60]


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--apply', action='store_true'); a = ap.parse_args()
    # 同名查重：全库 Collection 按 title 与 additional_titles（简繁异体归一）
    import opencc
    t2s = opencc.OpenCC('t2s')
    nz = lambda s: t2s.convert(re.sub(r'[\s·・（）()]', '', s))
    have = {}
    for f in glob.glob(str(ROOT / 'Collection/*/*/*/*.json')):
        c = json.load(open(f, encoding='utf-8'))
        for t in [c.get('title', '')] + (c.get('additional_titles') or []):
            have.setdefault(nz(t), []).append(c['id'])
    dup = {k: v['title'] for k, v in S.items() if nz(v['title']) in have}
    for k, t in dup.items(): print('库内已有同名，跳过：', t, have[nz(t)])
    keys = [k for k in S if k not in dup]
    ids_file = HERE / 'ids2.json'
    ids = json.load(open(ids_file)) if ids_file.exists() else {}
    need = [k for k in keys if k not in ids]
    if a.apply and need:
        for k, i in zip(need, mintid.mint('Collection', LANE, len(need))): ids[k] = i
        json.dump(ids, open(ids_file, 'w'), ensure_ascii=False, indent=1)
    print('待建', len(keys), '已有 id', len(ids))
    if not a.apply: return
    for k in keys:
        sp = S[k]
        d = {'schema_version': 1, 'type': 'collection', 'subtype': 'book_collection', 'id': ids[k], 'title': sp['title']}
        if sp.get('additional_titles'): d['additional_titles'] = sp['additional_titles']
        d['authors'] = sp['authors']
        d['description'] = sp['description']
        for f in ('publication_info', 'dating', 'count'):
            if sp.get(f): d[f] = sp[f]
        par = sp.get('parent_id') or (ids[sp['parent']] if sp.get('parent') else None)
        if par: d['contained_in'] = [{'id': par}]
        d['sources'] = sp['sources']
        d['ai_note'] = '十三經縱向補全（' + TODAY + '）：' + (sp.get('ai_note') or CI_YAN_NOTE)
        d['revision'] = '1.0.0'; d['revised_at'] = TODAY
        p = ROOT / mintid.path_for(ids[k], title_file(sp['title']), 'Collection')
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(V.dump(d, (2, '\n')), encoding='utf-8')
    print('已写', len(keys))


if __name__ == '__main__':
    main()
