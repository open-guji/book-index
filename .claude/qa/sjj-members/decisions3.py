"""第三輪決策表（2026-11-15 sjj-members3）：用戶新口徑——古人（1912 前、含清人）著作的民國／昭和等排印本、鈔本也建 Book，掛到該古人著作 Work 下。

ITEMS：每項建一個 Book（或 attach 補挂既有 Book）。
  work     所掛 Work id
  edition  版本名（含影印丛編時由 build3 補「（丛編影印，函冊）」）
  etype    edition_type（可空）
  ncids    CiNii 子記錄 NCID（sources）
  rows     members-todo.tsv 行號（可空；外國線補建無行號）
  coll     丛編鍵 lunyu／laozi2／laolie（可空）
  vols     {行號: volume_index}
  note     ai_note 補充說明
ATTACH：給既有 Book 補挂 contained_in。
"""
ITEMS = [
 dict(key='r128', work='d59fyfeqwkch', edition='明謝氏小草齋鈔本排印本', etype='鉛印本', ncids=['BA55461560'], rows=[128], coll='lunyu', vols={128: '第5函'},
      note='CiNii 注記僅作「明謝氏小草齋鈔本排印本」，排印年份與出版者未載（據 1912 後新口徑：古人著作的近現代排印本建 Book）；CiNii 題名作「論語全解」，卷首書名「重廣陳用之學士眞本入經論語全解義」'),
 dict(key='r295', work='d59gdvbx6dy3', edition='日本明治三十三年（1900）排印本', etype='鉛印本', ncids=['BA55422842'], rows=[295], coll='laozi2', vols={295: '第28函'},
      note='CiNii 注記僅作「明治33年排印本」，出版者未載；此即該 Work（島田鈞一《老子講義》，明治 33 年）的初刊本，不晚於 1912'),
 dict(key='r297', work='d59gdvbx6dy4', edition='日本明治四十年（1907）排印本', etype='鉛印本', ncids=['BA55422525'], rows=[297], coll='laozi2', vols={297: '第27函'},
      note='CiNii 注記僅作「明治40年排印本」，出版者未載；此即該 Work（小宮山昌玄《老子講義》，明治 40 年）的初刊本，不晚於 1912'),
 dict(key='r311', work='d59gduogi8mr', edition='日本昭和七年（1932）排印本', etype='鉛印本', ncids=['BA55415315'], rows=[311], coll='laozi2', vols={311: '第24函'},
      note='CiNii 注記僅作「昭和7年排印本」（返點付），出版者未載；原著者東條弘（東條一堂，1778—1857）為江戶人，此為 1912 後排印本（新口徑：建 Book）'),
 dict(key='r322', work='d59gduogi8mw', edition='日本大正十二年（1923）排印本', etype='鉛印本', ncids=['BA5541145X'], rows=[322], coll='laozi2', vols={322: '第23函'},
      note='CiNii 注記僅作「大正12年排印本」，出版者未載；原書實為海保青陵（1755—1817）《老子國字解》，疑即東洋圖書刊行會《老子國字解全書》（關儀一郎編，1923.4；CiNii BA37856454）所收，未核對，故不寫出版者'),
 dict(key='r326', work='d59gduogi8n0', edition='日本昭和二年（1927）排印本', etype='鉛印本', ncids=['BA55409979'], rows=[326], coll='laozi2', vols={326: '第25函'},
      note='CiNii 注記僅作「昭和2年排印本」，出版者未載；原著者中井積德（1732—1817）為江戶人，此為 1912 後排印本（新口徑：建 Book）'),
 dict(key='r421', work='d59fyirbmnls', edition='民國十一年（1922）雙流李氏重刊諸子平議本', etype='刻本', ncids=['BA55255740'], rows=[421], coll='laozi2', vols={421: '第8函'},
      note='CiNii 注記作「民國11年雙流李氏重刊《諸子平議》本」（別題「諸子平議，卷8」）；重刊者僅署雙流李氏，未載堂號'),
 dict(key='r422', work='d59f2mhzldz5', edition='民國十九年（1930）石肇純手鈔本', etype='抄本', ncids=['BA5525522X'], rows=[422], coll='laozi2', vols={422: '第8函'},
      note='CiNii 注記作「民國19年石肇純手鈔本」；陳澧（1810—1882）為清人，此為民國手鈔本（新口徑：建 Book）'),
 dict(key='r425', work='d59gduogi8od', edition='民國五十八年（1969）「純常子枝語」打字本', etype=None, ncids=['BA5525158X'], rows=[425], coll='laozi2', vols={425: '第9函'},
      note='CiNii 注記作「民國58年「純上子枝語」打字本」（「純上子」當為「純常子」之誤），出版者未載；文廷式（1856—1904）《純常子枝語》中老子部分'),
 dict(key='r448', work='d59gduogi8on', edition='民國五十二年（1963）排印本', etype='鉛印本', ncids=['BA55222071'], rows=[448], coll='laozi2', vols={448: '第10函'},
      note='CiNii 注記作「民國52年排印本」，出版者未載；卷首書名「香草續校書」，于鬯（1854—1910）為清人'),
 dict(key='r431', work='d59fxud4pa80', edition='清宣統元年（1909）衍星社排印本', etype='鉛印本', ncids=['BA55246411'], rows=[431], coll='laozi2', vols={431: '第9函'},
      note='CiNii 題名作「點勘老子讀本」（2卷），注記「宣統元年衍星社排印本」；吳汝綸（1840—1903）點勘，與本 Work 題名「桐城吳先生點勘老子」按書名與責任者判為同書'),
 # ---- 外國線 SKIPPED 的和刻本／日本重刊本／日本排印本（Book 層）
 dict(key='f_gy1', work='d59f1ioj1tz4', edition='日本寬文八年（1668）荒川宗長刊、林羅山訓點《新刊公穀白文》本', etype='刻本', ncids=['BA85345376', 'BA86206262'], rows=[], coll=None, vols={},
      note='據 CiNii 兩條個別書誌：BA85345376（荒川宗長刊）、BA86206262（長谷川新兵衛・植村藤右衞門），均為寬文8年（1668）序刊同一刊本，7 冊，白文；序題「新刋公穀白文」（林恕序），訓點者林信勝（林羅山）；與《穀梁傳》為一套。穀梁傳同刊本庫內已有 993g967xmq（掛在 d59fxx8fxszl），故穀梁側不重建'),
 dict(key='f_gy2', work='d59f1ioj1tz4', edition='日本江戶後印本（攝陽河內屋茂兵衛等六肆，據寬文八年荒川宗長刊本後印，林羅山訓點《新刊公穀白文》）', etype='刻本', ncids=['BA82365559'], rows=[], coll=None, vols={},
      note='據 CiNii BA82365559：12卷7冊，出版者「攝陽河內屋茂兵衛等六肆」，版心有「永懷堂」，CiNii 判為寬文8年荒川宗長刊、長谷川新兵衛・植村藤右衛門本之後印（「後印カ」）；撰者何休、校者王道焜、訓點者林羅山，叢書名「新刊公穀白文」'),
 dict(key='f_gl2', work='d59ezajtfrb4', edition='日本江戶後印本（攝陽河內屋茂兵衛等六肆，據寬文八年荒川宗長刊本後印，林羅山訓點《新刊公穀白文》）', etype='刻本', ncids=['BA85661117'], rows=[], coll=None, vols={},
      note='據 CiNii BA85661117：12卷7冊，出版者「攝陽河內屋茂兵衛等六肆」，CiNii 判為寬文8年荒川宗長刊本之後印（「後印カ」）；撰者范寗、校者王道焜、訓點者林羅山，叢書名「新刊公穀白文」（與《公羊傳》一套）'),
 dict(key='f_lzy', work='d59f6ejkp43r', edition='日本明治四十四年（1911）冨山房《漢文大系》本（服部宇之吉校訂，與《莊子翼》合冊）', etype=None, ncids=['BN07706002'], rows=[], coll=None, vols={},
      note='據 CiNii BN07706002：《老子翼；莊子翼》服部宇之吉校訂，冨山房 1911.8，漢文大系第9卷；為明焦竑《老子翼》的日本校訂排印本，與《莊子翼》合冊，本 Book 指其《老子翼》部分'),
 dict(key='f_lzzw', work='d59ezkx8dt6o', edition='日本明治十五年（1882）內藤傳右衞門刊本（廣瀨範治校，溫故堂藏版）', etype='刻本', ncids=['BA58721668'], rows=[], coll=None, vols={},
      note='據 CiNii BA58721668：《老子正文》廣瀨範治校，內藤傳右衞門 1882.9，20丁，版心「溫故堂藏版」，和裝；為《老子》白文校刊本'),
]
ATTACH = [
 dict(book='994xymqoe9', coll='laolie', vol='第35冊', row=490, ncid='BN15411398'),
]
