"""2.1 第一批：176 组待核判定里的 12 组人物同人 + 凌義渠/淩義渠、余翔/佘翔、謝顯道/謝良佐 + 來復改挂（PRV-N006）。
每组：先做「解繫／撤错误 CBDB 字号籍贯」预修，再并条。证据见 /mnt/project-files/总目/去重研究/待核判定-20261025/人物-*.tsv"""
G = [
 dict(cid='PNA-R018', keeper='hixhd2h9bhum', losers=['hixhd2h9bovo'], ev='同一人（俞琰字玉吾）：俞玉吾唯一著作《卦爻象占分類》出《元史藝文志》，保留方已繫同書；《元史藝文志》《補遼金元藝文志》自注「俞琰，字玉吾，吳縣人」；姓同、朝代同、著作同。'),
 dict(cid='PNA-R019', keeper='hixhd2h9bh14', losers=['hixhd2h9br6v'], ev='同一人（李杲號東垣）：保留方 alt_names 已有號「東垣」，李東垣唯一所繫《東垣十種醫書》即託名李杲之叢編；姓同、朝代同（金/金元）、醫家同。'),
 dict(cid='PNA-H005', keeper='hixhd2h9bhqe', losers=['hixi8u5qspby'], ev='同一人（朱敦儒字希真）：朱希真唯一著作《樵歌詞拾遺》（總目宋朱希真撰）與保留方《樵歌》《樵歌拾遺》同屬樵歌系；保留方 alt_names 已有字「希真」，姓同宋代同。'),
 dict(cid='PRV-R011', keeper='hixhd2h9be7k', losers=['hixhd2h9be1h'], ev='同一人（丘濬，清避諱作邱濬）：兩條共繫《大學衍義補》d59f2nleb30j（國史經籍志作丘濬、四庫作邱濬），另《重編瓊臺稿》《家禮儀節》等亦兩名互見；保留方 alt_names 已有「邱濬」，均為明人。'),
 dict(cid='PRV-N005', keeper='hixi8u5so4pt', losers=['hixhgyrw4wo1'], ev='同一人（明三峰漢月法藏）：法藏唯一著作千頃堂「法藏山居集，字於密，無錫人」，與釋法藏《三峯藏禪師山居詩》《漢月禪師詩集》同人；法名同、明代同。'),
 dict(cid='PRV-N007', keeper='hixhd2h9bfys', losers=['hixhd2h9bgob'], ev='同一人（雪浪洪恩）：洪恩所繫《金剛經解義》《心經說》（明史藝文志）與釋洪恩《金剛解義》《心經説》（千頃堂）書目全同，《雪浪齋集》注「字三懷，上元人，居長干寺」。',
      pre=[('unlink','d59f6ela6v40','hixhd2h9bgob','《靈濟真人文集》為元道士編南唐二徐乩筆，不屬洪恩'),
           ('strip','hixhd2h9bgob',['external_ids','dates','native_place*','alt_names:從仁,一'],'被並方誤配 CBDB 203211（字從仁、黃梅、生1510），不帶入保留方')]),
 dict(cid='PRV-N008', keeper='hixhd2h9bi14', losers=['hixhgyrw4xt7'], ev='同一人（博山大艤）：明史藝文志「大艤《禪警語》《宗教答響》《歸正錄》《博山語錄》二十二卷」與千頃堂「釋大艤」名下書目全同。',
      pre=[('unlink','d59f2nf096v7','hixhd2h9bi14','《仁宗文集》為明史志承上條作者污染，非大艤'),('unlink','d59f2ndzqf41','hixhd2h9bi14','《宣宗文集》同上')]),
 dict(cid='PRV-N009', keeper='hixhd2h9brwd', losers=['hixhd2h9bmwy'], ev='部分同人：唐僧法雲。新唐志「僧法雲辨量三教論三卷，又十王正業論十卷」，國史經籍志兩書都注「僧法雲」，bmwy 的《辨量三教論》與 brwd 的《十王正業論》是同一唐僧。',
      pre=[('unlink','d59f2nmhy3uo','hixhd2h9bmwy','清《憨予暹禪師語錄》作者為清釋法雲，非唐僧'),('strip','hixhd2h9bmwy',['alt_names:普潤'],'「普潤」號屬宋平江景德寺法雲（《翻譯名義集》作者，CBDB 24400），非唐僧，不帶入')]),
 dict(cid='PRV-H002', keeper='hixhjhavlgxw', losers=['hixhjhayeltw','hixi5fxknyts','hixi5fxknytr'], ev='同一人（北魏菩提流支／留支）：四條都是北魏／東魏譯師，DILA A001357 名菩提流支別名菩提留支；總目著錄「東魏釋菩提流支（菩提留支）譯」自證兩寫同人。',
      post=[('rename','hixhjhavlgxw','菩提流支')]),
 dict(cid='PRV-H005', keeper='hixhd2f8wakd', losers=['hixi5vzpexvm'], ev='同一人（吳騫，「鶱」為錄入異寫）：兩條總目 person_uri 相同（ty5reoa5vy6mm37x），吳鶱名下 19 部總目 author_info 原文皆作「清吳騫撰／輯」，多為拜經樓著述，正是海寧吳騫（1733–1814）。'),
 dict(cid='PRV-H1900-R012', keeper='hixhd2h9bixi', losers=['hixhjtdcdfk4'], ev='同一人（後秦／東晉僧肇）：釋僧肇所繫《般若無知論》《涅槃無名論》與保留方《不真空論》《物不遷論》同屬肇論系，DILA A001598 列釋僧肇為別名；晉／東晉兼容。'),
 dict(cid='PRV-H2000-003', keeper='hixi4wwpzyfe', losers=['hixhgyrw4vy6'], ev='「成宗」是孤懸殘條：唯一來源是千頃堂「成宗實録（暢師文修）」誤把題首當撰人而建，原 Work 已並入《成宗實錄》，ai_note 自承失引用；保留方（元成宗鐵穆耳）alt_names 已有廟號「成宗」。'),
 dict(cid='PRV-H2000-005', keeper='hixhd2h9bn9r', losers=['hixhi4q6aznz'], ev='同一人（劉宋東安寺慧嚴，惠／慧通用）：補宋書藝文志同時著錄「老子注二卷，釋惠嚴注」和「大般涅槃經三十六卷，釋慧嚴等譯」，總目作「南朝宋釋慧嚴等再治」。',
      pre=[('strip','hixhd2h9bn9r',['external_ids','native_place*','alt_names:文惠大師'],'保留方誤配 CBDB 53643（文惠大師、金谿，應是宋代僧），撤'),
           ('strip','hixhi4q6aznz',['alt_names:釋慧嚴等'],'「釋慧嚴等」是著錄殘語，不作別名帶入')],
      post=[('rename','hixhd2h9bn9r','釋慧嚴')]),
 dict(cid='P2-L001', keeper='hixhgyrw4v0h', losers=['hixi8u5so4kd'], ev='同一人（凌義渠）：淩義渠名下《淩忠介公集》《淩忠介詩集》《淩忠介公文集》與保留方《凌忠介公集》《凌忠介公遺集》同書名同謚「忠介」（保留方 alt_names 已有忠介）；淩／凌 異體，均明人。'),
 dict(cid='P2-L002', keeper='hixhd2h9bfn2', losers=['hixhd2h9bouh'], ev='形近異寫（佘翔）：余翔唯一所繫《薜荔園詩集》現作者已更正為佘翔（莆田，明，CBDB 128385），余翔為該 Work 作者名錄入之誤的遺留條，名下 0 引用。'),
 dict(cid='P2-L003', keeper='hixhd2h9bog5', losers=['hixhd2h9bl7c'], ev='字號：謝顯道為謝良佐之字，保留方 alt_names 已有「顯道」，姓同；被並方為空殼條（無朝代、無著作引用）。'),
]
FIX_ONLY = [  # 不並，只改挂
 dict(cid='PRV-N006', pre=[('relink','d59f2nej34le','hixhd2h9bgrn','hixhd2h9btwc','《蒲庵集》屬元末明初僧釋來復'),('relink','d59f6ejm9atd','hixhd2h9bgrn','hixhd2h9btwc','《澹遊集》屬釋來復'),
   ('strip','hixhd2h9bgrn',['external_ids','alt_names:見心','native_place*'],'來復（陽伯，明後期俗人）誤帶釋來復的 CBDB 128670／見心／豐城，撤')],
   ev='兩條不能整併：bgrn 的總目 uri 與多數著作（《來陽伯詩集》等）是明後期俗人來復（陽伯）；釋來復 btwc（1319–1391，見心，豐城）是元末明初僧。《蒲庵集》《澹遊集》應改繫 btwc。'),
]
