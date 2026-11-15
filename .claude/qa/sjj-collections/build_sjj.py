#!/usr/bin/env python3
"""十三经纵向补全：补建丛编 Collection（11-15，车道 a11-sjj-coll）。

所有事实取自 CiNii Books 的丛书母记录与子记录（ci.nii.ac.jp/ncid/<NCID>，2026-11-15 抓取）；
核不实的不建。成员挂接见 attach_members.py。
用法：build_sjj.py [--apply]   默认乾跑，--apply 才写文件，并把新 id 存到 ids.json
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
CI_YAN_NOTE = '據 CiNii Books（ci.nii.ac.jp）母記錄與子記錄核定，未核原書。'

add('lunyu', '無求備齋論語集成', additional_titles=['論語集成'], authors=YAN,
    description={'text': '嚴靈峯編輯，臺北藝文印書館 1966 年 10 月影印（線裝，帙入，凡三十函）。彙集歷代及日本江戶、民國論語注疏、輯佚、考證，兼收敦煌唐寫本、漢石經等，CiNii 著錄子目 143 條。儒家網轉載林桂榛（2012）整理之全目作 137 種，二者差在同題異版（如《論語考文補遺》清刊、日刊各一條）之分計。',
                 'sources': ['CiNii Books BA55450983', '儒家網轉載林桂榛《無求備齋論語集成》目錄 https://www.rujiazg.com/article/2514']},
    publication_info={'publisher': '藝文印書館', 'place': '臺北', 'year': '1966', 'year_iso': '1966', 'details': '影印；嚴靈峯編輯；1966.10'},
    dating={'year': 1966, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄出版年「1966.10」'},
    count={'juan': None, 'ce': None, 'zhong': 143, 'han': 30, 'source': 'CiNii Books BA55450983 關連文獻 143 件；函數取子記錄「第N函」最大值 30'},
    sources=[CINII('BA55450983')])

add('laozi', '無求備齋老子集成', additional_titles=['老子集成'], authors=YAN,
    description={'text': '嚴靈峯編輯，藝文印書館影印。分初編（1965，一百十五件，十八函）與續編（1970，一百九十九件，三十函），兩編合計 CiNii 著錄 314 條，為老子研究最大之單一影印集成，兼收敦煌寫本、石刻、日本江戶講義與校勘。本條為兩編之總名條，成員登於初編、續編。',
                 'sources': ['CiNii Books BA46443739（初編）', 'CiNii Books BA55202482（續編）']},
    publication_info={'publisher': '藝文印書館', 'place': '臺北', 'year': '1965-1970', 'details': '初編 1965.3；續編 1970.7'},
    dating={'year_range': [1965, 1970], 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄初編 1965.3、續編 1970.7'},
    count={'juan': None, 'ce': None, 'zhong': 314, 'han': 48, 'source': '初編 115 件／18 函加續編 199 件／30 函（CiNii Books 母記錄）；314 為著錄條數，含同題異本'},
    sources=[CINII('BA46443739'), CINII('BA55202482')])

add('laozi1', '無求備齋老子集成初編', parent='laozi', authors=YAN,
    description={'text': '嚴靈峯編輯，藝文印書館 1965 年 3 月影印（線裝，函入，凡十八函）。CiNii 著錄一百十五件，收道德經石刻、敦煌寫本、河上公註、想爾注、趙孟頫書老子及朝鮮、日本傳本等。', 'sources': ['CiNii Books BA46443739']},
    publication_info={'publisher': '藝文印書館', 'place': '臺北', 'year': '1965', 'year_iso': '1965', 'details': '影印；1965.3'},
    dating={'year': 1965, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄出版年「1965.3」'},
    count={'juan': None, 'ce': None, 'zhong': 115, 'han': 18, 'source': 'CiNii Books BA46443739 關連文獻 115 件；18 函取注記「第18函」'},
    sources=[CINII('BA46443739')])

add('laozi2', '無求備齋老子集成續編', parent='laozi', authors=YAN,
    description={'text': '嚴靈峯編輯，藝文印書館 1970 年 7 月影印（和裝，帙入，凡三十函）。CiNii 著錄一百九十九件，多收日本江戶諸家老子講義、國字解、訓點及清、民國考校之作。', 'sources': ['CiNii Books BA55202482']},
    publication_info={'publisher': '藝文印書館', 'place': '臺北', 'year': '1970', 'year_iso': '1970', 'details': '影印；1970.7'},
    dating={'year': 1970, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄出版年「1970.7」'},
    count={'juan': None, 'ce': None, 'zhong': 199, 'han': 30, 'source': 'CiNii Books BA55202482 關連文獻 199 件；函數取子記錄「第N函」最大值 30'},
    sources=[CINII('BA55202482')])

add('laolie', '無求備齋老列莊三子集成補編', authors=YAN,
    description={'text': '嚴靈峯編輯，成文出版社有限公司影印，序署 1982 年，凡五十六冊，CiNii 著錄四十六條，專補老子、列子、莊子三子集成所未收之本，以莊子類為多。藝文印書館先前所印《無求備齋莊子集成》初編（1972.5，三十冊）、續編（1974.12，四十二冊）與本編相承，後二者本次未建。',
                 'sources': ['CiNii Books BN15377573', 'CiNii Books BA46441904（莊子集成初編）', 'CiNii Books BA55208456（莊子集成續編）']},
    publication_info={'publisher': '成文出版社有限公司', 'place': '臺北', 'year': '1982', 'details': '影印；1982 序'},
    dating={'year': 1982, 'certainty': 'inferred', 'source': 'catalog', 'basis': 'CiNii Books 著錄「[1982序]」，據序署年定'},
    count={'juan': None, 'ce': 56, 'zhong': 46, 'han': None, 'source': 'CiNii Books BN15377573：56冊；關連文獻 46 件'},
    sources=[CINII('BN15377573')])

add('mengzi10', '無求備齋孟子十書', additional_titles=['孟子十書'], authors=YAN,
    description={'text': '嚴靈峯編輯，藝文印書館 1969 年 5 月影印（和裝，帙入，凡六函）。十種：孟子白文、孟子趙注（趙岐）、孟子叢說（許謙）、孟子注疏附孟子音義（孫奭）、孟子集注（朱熹）、孟子字義疏證附標點排印本（戴震）、孟子集註纂箋（趙順孫）、孟子平議（俞樾）、孟子札記（朱亦棟）、孟子正義（焦循）。全目只十種，並非大型集成。', 'sources': ['CiNii Books BA55212985']},
    publication_info={'publisher': '藝文印書館', 'place': '臺北', 'year': '1969', 'year_iso': '1969', 'details': '影印；1969.5'},
    dating={'year': 1969, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄出版年「1969.5」'},
    count={'juan': None, 'ce': None, 'zhong': 10, 'han': 6, 'source': 'CiNii Books BA55212985 關連文獻 10 件；函數取「第1—6函」'},
    sources=[CINII('BA55212985')])

add('yijing', '無求備齋易經集成', additional_titles=['易經集成'], authors=YAN,
    description={'text': '嚴靈峯編輯，成文出版社 1976 年影印，精裝一百九十五冊，為易類大型集成。CiNii 僅有母記錄，未著錄子目，故本條暫不列成員；子目待據館藏目錄補。', 'sources': ['CiNii Books BA55149007']},
    publication_info={'publisher': '成文出版社', 'place': '臺北', 'year': '1976', 'year_iso': '1976', 'details': '影印；精裝'},
    dating={'year': 1976, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄出版年「1976」'},
    count={'juan': None, 'ce': 195, 'zhong': None, 'han': None, 'source': 'CiNii Books BA55149007 冊次列至第195冊'},
    sources=[CINII('BA55149007')])

add('rb', '日本名家四書註釋全書', additional_titles=['日本名家四書注釋全書', '四書註釋全書'], authors=[{'name': '關儀一郎', 'role': '編纂'}],
    description={'text': '關儀一郎編纂，東洋圖書刊行會出版，江戶儒者之大學、中庸、論語、孟子註釋彙編，含正編十冊（1922—1926，學庸部二、論語部六、孟子部二）與續編三冊（1927—1930，學庸、論語、孟子各一），共十三冊。1973 年鳳出版影印合為十三卷；2011 年起大空社重印論語部入「論語」叢書。無求備齋論語集成所收日本江戶諸家，CiNii 注記多稱據日本東洋圖書刊行會排印本影印。',
                 'sources': ['CiNii Books BN05006112（正編）', 'CiNii Books BN05007749（續編）', 'CiNii Books BN12767108（鳳出版 1973）']},
    publication_info={'publisher': '東洋圖書刊行會', 'year': '1922-1930', 'details': '正編 1922-1926；續編 1927-1930'},
    dating={'year_range': [1922, 1930], 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄正編 1922-1926、續編 1927-1930'},
    count={'juan': None, 'ce': 13, 'zhong': None, 'han': None, 'source': '正編 10 冊（CiNii BN05006112 列學庸部1—2、孟子部1—2、論語部1—6）加續編 3 冊（BN05007749）；鳳出版 1973 影印為 13 卷（BN12767108）'},
    sources=[CINII('BN05006112'), CINII('BN05007749'), CINII('BN12767108')])

add('rb1', '日本名家四書註釋全書正編', parent='rb', authors=[{'name': '關儀一郎', 'role': '編纂'}],
    description={'text': '東洋圖書刊行會 1922—1926 年刊，十冊：學庸部二、孟子部二、論語部六。', 'sources': ['CiNii Books BN05006112']},
    publication_info={'publisher': '東洋圖書刊行會', 'year': '1922-1926'},
    dating={'year_range': [1922, 1926], 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄「1922-1926」'},
    count={'juan': None, 'ce': 10, 'zhong': None, 'han': None, 'source': 'CiNii Books BN05006112 列學庸部1—2、孟子部1—2、論語部1—6 共 10 冊'},
    sources=[CINII('BN05006112')])

add('rb2', '續日本名家四書註釋全書', parent='rb', authors=[{'name': '關儀一郎', 'role': '編纂'}],
    description={'text': '東洋圖書刊行會 1927—1930 年刊，三冊（學庸部、論語部、孟子部各一）。CiNii 見其子記錄有西島蘭溪、照井全都、東條一堂、增島蘭園、海保漁村諸家之作。', 'sources': ['CiNii Books BN05007749']},
    publication_info={'publisher': '東洋圖書刊行會', 'year': '1927-1930'},
    dating={'year_range': [1927, 1930], 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄「1927-1930」'},
    count={'juan': None, 'ce': 3, 'zhong': None, 'han': None, 'source': 'CiNii Books BN05007749 冊次「第1—3冊」'},
    sources=[CINII('BN05007749')])

KJ = [('daxue', '大學', 8, '1-8', '1989.2', 1989), ('zhongyong', '中庸', 9, '9-17', '1989.2', 1989), ('lunyu', '論語', 17, '18-34', '1990.2', 1990),
      ('mengzi', '孟子', 14, '35-48', '1991.2', 1991), ('shu', '書經', 22, '49-70', '1993', 1993), ('shi', '詩經', 16, '71-86', '1995.2', 1995),
      ('yi', '易經', 37, '87-123', '1996.11-1997.11', None), ('li', '禮記', 10, '124-133', '1998.12', 1998), ('chunqiu', '春秋', 12, '134-145', '1998.12', 1998)]
NCID_KJ = {'daxue': 'BN04222451', 'zhongyong': 'BN04222950', 'lunyu': 'BN0529811X', 'mengzi': 'BN06696195', 'shu': 'BN10226504', 'shi': 'BA48794971', 'yi': 'BA69583307', 'li': 'BA6958481X', 'chunqiu': 'BA69585357'}
add('kj', '韓國經學資料集成', authors=[{'name': '成均館大學校大東文化研究院', 'role': '編'}],
    description={'text': '成均館大學校大東文化研究院編，成均館大學校出版部 1989—1998 年陸續影印出版，朝鮮經學著述彙編，按經分部：大學（1—8）、中庸（9—17）、論語（18—34）、孟子（35—48）、書經（49—70）、詩經（71—86）、易經（87—123）、禮記（124—133）、春秋（134—145）共一百四十五冊，另有總目錄一冊。本條為總名條，各部各立子條。CiNii 著錄中未見孝經、周禮、儀禮之部。',
                 'sources': ['CiNii Books BN04222633（總目錄）', 'CiNii Books 各部記錄（BN04222451、BN04222950、BN0529811X、BN06696195、BN10226504、BA48794971、BA69583307、BA6958481X、BA69585357）']},
    publication_info={'publisher': '成均館大學校出版部', 'year': '1989-1998'},
    dating={'year_range': [1989, 1998], 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 各部出版年 1989.2 至 1998.12'},
    count={'juan': None, 'ce': 145, 'zhong': None, 'han': None, 'source': 'CiNii Books 各部冊次號 1—145 相接（8+9+17+14+22+16+37+10+12），另有總目錄'},
    sources=[CINII('BN04222633')])
for k, nm, n, rng, yr, y in KJ:
    add('kj_' + k, '韓國經學資料集成·' + nm, parent='kj', authors=[{'name': '成均館大學校大東文化研究院', 'role': '編'}],
        description={'text': '《韓國經學資料集成》' + nm + '部，第' + rng + '冊，共' + str(n) + '冊，成均館大學校出版部 ' + yr + ' 年出版。', 'sources': ['CiNii Books ' + NCID_KJ[k]]},
        publication_info={'publisher': '成均館大學校出版部', 'year': yr},
        dating=({'year': y, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄出版年「' + yr + '」'} if y else {'year_range': [1996, 1997], 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄出版年「1996.11-1997.11」'}),
        count={'juan': None, 'ce': n, 'zhong': None, 'han': None, 'source': 'CiNii Books ' + NCID_KJ[k] + ' 叢書號「' + rng + '」'},
        sources=[CINII(NCID_KJ[k])])

add('xjwxjc', '孝經文獻集成', authors=[{'name': '吴平', 'role': '主編'}, {'name': '李善強', 'role': '主編'}, {'name': '霍艷蓉', 'role': '主編'}],
    description={'text': '吳平、李善強、霍艷蓉主編，廣陵書社 2011 年 12 月出版，三十冊，影印歷代孝經著述，附孝經研究論文索引與文獻存目。', 'sources': ['CiNii Books BB09012484']},
    publication_info={'publisher': '廣陵書社', 'year': '2011', 'year_iso': '2011', 'details': '2011.12'},
    dating={'year': 2011, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄出版年「2011.12」'},
    count={'juan': None, 'ce': 30, 'zhong': None, 'han': None, 'source': 'CiNii Books BB09012484 頁數／冊數「30冊」'},
    sources=[CINII('BB09012484')])

add('xjwxck', '孝經文獻叢刊', authors=[{'name': '曾振宇', 'role': '主編'}, {'name': '江曦', 'role': '主編'}],
    description={'text': '曾振宇、江曦主編，上海古籍出版社。第一輯 2021 年 2 月出版，CiNii 著錄《古文孝經指解（外二十三種）》上下、《孝經通釋（外三種）》、《孝經義疏補》、《孝經集解（外二種）》上下、《孝經古注說》，五個題名七冊，均為點校整理本。第二輯（2025，含江曦《孝經學著述總目》）CiNii 未見，據他處研究資料，未核。', 'sources': ['CiNii Books BC08767923']},
    publication_info={'publisher': '上海古籍出版社', 'year': '2021-', 'details': '第1輯 2021.2'},
    dating={'year': 2021, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄第1輯出版年「2021.2」'},
    sources=[CINII('BC08767923')])

add('mzwxjc', '孟子文獻集成', authors=[{'name': '孟子文獻集成編纂委員會', 'role': '編纂'}],
    description={'text': '孟子文獻集成編纂委員會編纂，山東人民出版社 2016 年 1 月起陸續出版，影印孟子歷代文獻，按卷（冊）計。CiNii 已著錄至第六十六卷（2018 年 3 月）。宋元卷、明代輯之種數與總規模，據他處報道，未核。', 'sources': ['CiNii Books BB21756753', '儒家網報道 https://www.rujiazg.com/article/5336']},
    publication_info={'publisher': '山東人民出版社', 'year': '2016-', 'details': '2016.1 起'},
    dating={'year': 2016, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄首卷出版年「2016.1-」'},
    sources=[CINII('BB21756753')])

add('ywhj', '域外漢籍珍本文庫', authors=[{'name': '域外漢籍珍本文庫編纂出版委員會', 'role': '編'}],
    description={'text': '域外漢籍珍本文庫編纂出版委員會編，西南師範大學出版社、人民出版社 2008 年 10 月起影印出版，國家「十一五」重大文化出版工程項目。按輯、部（經史子集）編排：第一輯分經史子集四部、第二輯經部、第四輯經部與子部、第五輯集部與經部等；另有叢編系列，如《日本五山版漢籍善本集刊》（2012）、《高麗大藏經初刻本輯刊》（2012）、《朝鮮版漢籍善本萃編 北京大學圖書館藏》（2014）、《韓國成均館大學尊經閣藏漢籍珍本叢刊》（16冊，2016）、《日藏明人別集珍本叢刊》（2017）。',
                 'sources': ['CiNii Books BA90002914', 'CiNii Books BB09144033', 'CiNii Books BB19089689', 'CiNii Books BB23001637']},
    publication_info={'publisher': '西南師範大學出版社、人民出版社', 'year': '2008-', 'details': '2008.10 起'},
    dating={'year': 2008, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄首批出版年「2008.10-」'},
    sources=[CINII('BA90002914'), CINII('BB19089689'), CINII('BB23001637')])

add('wuwei', '武威漢簡', additional_titles=['武威漢簡儀禮', '武威磨嘴子漢簡'], parent_id=CH_UP, authors=[{'name': '甘肅省博物館', 'role': '整理'}, {'name': '中國科學院考古研究所', 'role': '整理'}],
    description={'text': '甘肅武威磨嘴子漢墓出土之新莽時期簡牘，以《儀禮》最古寫本著稱。《儀禮》簡共四百六十九枚：甲本木簡 398 枚，含《士相見》《服傳》《特牲》《少牢》《有司》《燕禮》《泰射》七篇；乙本木簡 37 枚，僅《服傳》一篇；丙本竹簡 34 枚，僅《喪服》一篇。整理報告為甘肅省博物館、中國科學院考古研究所編著《武威漢簡》（文物出版社 1964；中華書局 2005 新版）。研究見張煥君、刁小龍《武威漢簡〈儀禮〉整理與研究》（武漢大學出版社 2009）。',
                 'sources': ['CiNii Books BA33959422（文物出版社 1964）', 'CiNii Books BA76135554（中華書局 2005）', 'CiNii Books BB0120977X', '維基百科「儀禮」條出土版本節 https://zh.wikipedia.org/wiki/儀禮']},
    publication_info={'publisher': '文物出版社', 'place': '北京', 'year': '1964', 'year_iso': '1964', 'details': '整理報告 1964.9；中華書局 2005.9 新版'},
    dating={'year': 1964, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄整理報告出版年「1964.9」'},
    sources=[CINII('BA33959422'), CINII('BA76135554')],
    ai_extra='出土年份：本庫「出土簡帛」總集條作 1959，本次未能在可抓取之書目頁核實，未寫入本條；藏地待核。庫內有 Work「儀禮武威漢簡殘編附釋文」（d59f2pv8zksg，續修四庫影印 1964 年版），其 Book 待建，建成後在成員側加 contained_in 指向本條。')

add('minban', '明版閩刻十三經注疏', authors=[{'name': '中國社會科學院歷史研究所文化室', 'role': '編'}],
    description={'text': '中國社會科學院歷史研究所文化室編，東方出版社 2011 年 7 月出版，八冊，影印明閩刻本十三經注疏。', 'sources': ['CiNii Books BB10366790']},
    publication_info={'publisher': '東方出版社', 'year': '2011', 'year_iso': '2011', 'details': '2011.7'},
    dating={'year': 2011, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄出版年「2011.7」'},
    count={'juan': None, 'ce': 8, 'zhong': None, 'han': None, 'source': 'CiNii Books BB10366790 頁數／冊數「8冊」'},
    sources=[CINII('BB10366790')])

add('gjrz', '國際儒藏·韓國編四書部', additional_titles=['國際儒藏韓國編四書部'], authors=[{'name': '國際儒藏韓國編四書部編纂委員會', 'role': '編'}],
    description={'text': '國際儒藏韓國編四書部編纂委員會編，華夏出版社與中國人民大學出版社 2010 年 9 月出版，十六冊，為韓國四書類著述彙編。', 'sources': ['CiNii Books BB05289169']},
    publication_info={'publisher': '華夏出版社、中國人民大學出版社', 'year': '2010', 'year_iso': '2010', 'details': '2010.9'},
    dating={'year': 2010, 'certainty': 'attested', 'source': 'catalog', 'basis': 'CiNii Books 著錄出版年「2010.9」'},
    count={'juan': None, 'ce': 16, 'zhong': None, 'han': None, 'source': 'CiNii Books BB05289169 頁數／冊數「16册」'},
    sources=[CINII('BB05289169')])


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
    ids_file = HERE / 'ids.json'
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
        d['ai_note'] = '十三經縱向補全（' + TODAY + '）：' + CI_YAN_NOTE + (sp.get('ai_extra') and ('\n' + sp['ai_extra']) or '')
        d['revision'] = '1.0.0'; d['revised_at'] = TODAY
        p = ROOT / mintid.path_for(ids[k], title_file(sp['title']), 'Collection')
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(V.dump(d, (2, '\n')), encoding='utf-8')
    print('已写', len(keys))


if __name__ == '__main__':
    main()
