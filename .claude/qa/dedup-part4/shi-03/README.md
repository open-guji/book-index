# 去重方案部分 4：4a-α 史部收尾 shi-03（93 组 125 条）

基线 main `d96dbd79e95f49abaf46a44248e305234dd0eb7a`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/部分4-Work层无责任者与弱证据.md`（4a-α 修订节）、00 文件 Work 节 A 档、`.claude/qa/正式库并条审查规则.md`。

**4a-α 规则**（候选脚本 `../cand_alpha.py`）：同题组（`scripts/dedup-census.py` 口径：去括注、异体归一）里，无责任者一侧是叢書线（GUJI-526）新建的叢書子目 Work——《總目》叢書部獨撰類著录子目时不重复撰人，所以「無責任者」只是著录省略；其 Book 所属 Collection 的首位撰者（角色撰／撰輯／著等）与组内**唯一**一条有责任者 Work 的首位责任者同名、朝代相容；卷数相同、一侧缺或差≤1；单行本自身卷数不齐（差>1）的组跳过；同一叢書内有两条同题子目的组跳过（疑异篇）；有责任者多于 1 条的组留给 3a。子目 Work 并入单行本 Work，子目 Book 随之改挂。

工具：`apply_4.py`（包装 `../dedup-confirmed-163/apply_batch.py`，复用 mergework：著录并入、Book.work_id 与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`postfix_common.py`、`update_index.py`、`fix_draft.py`。冲突字段保留 keeper 原值，被并值入台账 `retained_alternatives`；被并者原 ai_note／description 存 `loser_original_notes`；互斥分类登记见 `分类互斥登记.tsv`。

善后提示：并后 keeper 下可能同时有 F 道「某某叢書本」Book 与叢書线子目 Book（同丛书不同著录），属部分 5 同 Work 同版本 Book，留给部分 5。

| 组 | 保留（单行本） | 并入子目条数 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---:|---:|---:|
| 4a-d59fyrsax2bl | 武漢戰紀（王樹柟） | 1 | 0 | 0 |
| 4a-d59fyt1rtiwx | 歷代宗廟圖考（王原） | 1 | 0 | 0 |
| 4a-d59f2mdca6td | 歷代帝王宅京記（顧炎武） | 2 | 0 | 0 |
| 4a-d59fysqfu801 | 殷頑錄（楊陸榮） | 1 | 0 | 0 |
| 4a-d59f2nfqh4ap | 毘陵正學編（毛憲） | 1 | 0 | 0 |
| 4a-d59fyrryfklc | 永歷紀年（黃宗羲） | 2 | 0 | 0 |
| 4a-d59f2meljlkw | 求古錄（顧炎武） | 1 | 0 | 0 |
| 4a-d59fyrtft5hd | 江南闈（孟森） | 2 | 0 | 0 |
| 4a-d59f2njnvm68 | 江漢叢談（陳士元） | 1 | 0 | 0 |
| 4a-d59fyrtnxbls | 河南山東山西闈（孟森） | 2 | 0 | 0 |
| 4a-d59fyrkzgrup | 治史緒論（劉鹹炘） | 1 | 0 | 0 |
| 4a-d59fyrqczwn4 | 浚川公移集（王廷相） | 1 | 0 | 0 |
| 4a-d59fyrqczwn5 | 浚川駁稿集（王廷相） | 1 | 0 | 0 |
| 4a-d59fyszlgyki | 浯溪紀遊詩（楊翰） | 1 | 0 | 0 |
| 4a-d59fyfhj3ta9 | 深牧庵日涉錄（蕭士瑋） | 1 | 0 | 0 |
| 4a-d59f2md460ow | 滇行日記（李澄中） | 1 | 0 | 0 |
| 4a-d59f2nhpygw1 | 滇載記（楊慎） | 3 | 0 | 0 |
| 4a-d59fy3r9io00 | 漢書人表考校補（蔡雲） | 1 | 0 | 0 |
| 4a-d59fxp7z3rpe | 漢書彙鈔（蕭光遠） | 1 | 0 | 0 |
| 4a-d59fxwcq3sow | 澳門紀畧跋（俞正燮） | 1 | 0 | 0 |
| 4a-d59fyrjymrr4 | 濟南竹枝詞（王初桐） | 2 | 0 | 0 |
| 4a-d59fye04l7nk | 焦里堂先生年譜（王永祥） | 1 | 0 | 0 |
| 4a-d59fyrpw53b5 | 牧沔紀畧（李輈） | 1 | 0 | 0 |
| 4a-d59f2mwq8tfm | 王山遺響（張貞生） | 1 | 0 | 0 |
| 4a-d59fyzs0wrnm | 王深寧先生年譜（陳僅） | 1 | 0 | 0 |
| 4a-d59fyzs0wrnl | 王紫稼考（孟森） | 2 | 0 | 0 |
| 4a-d59fyn62fbwh | 甲癸夢痕記（李桓） | 1 | 0 | 0 |
| 4a-d59fyndc0935 | 異姓諸侯表（鄭曉） | 1 | 0 | 0 |
| 4a-d59fxv8d241u | 當差紀畧（李輈） | 1 | 0 | 0 |
| 4a-d59f2ndf4n41 | 疑年錄（錢大昕） | 1 | 0 | 0 |
| 4a-d59fyrtk6h34 | 皇明遜國記（鄭曉） | 1 | 0 | 0 |
| 4a-d59fybukfgn4 | 皇朝聖師考（鄭曉如） | 1 | 0 | 0 |
| 4a-d59fyt7fyq69 | 直文淵閣諸臣表（鄭曉） | 1 | 0 | 0 |
| 4a-d59fybd34ykh | 篷櫳夜話（李日華） | 2 | 0 | 0 |
| 4a-d59fyrndb18h | 紫泥日記（黃彭年） | 2 | 0 | 0 |
| 4a-d59fxy2ll62p | 經籍會通（胡應麟） | 1 | 0 | 0 |
| 4a-d59fxr4cdyww | 綱目隨筆（鄒樹榮） | 1 | 0 | 0 |
| 4a-d59fyt6wm0hs | 綸扉稿（高拱） | 2 | 0 | 0 |
| 4a-d59fyt1d5ddu | 緬甸東北兩路地形考（俞正燮） | 1 | 0 | 0 |
| 4a-d59fyrncok5c | 總河近事考（俞正燮） | 1 | 0 | 0 |
| 4a-d59f2ngf4r2a | 績語堂碑錄（魏錫曾） | 1 | 0 | 0 |
| 4a-d59fyt88zsow | 續人表考校補（蔡雲） | 1 | 0 | 0 |
| 4a-d59f2ng9ttz6 | 續吳錄（劉鳳） | 1 | 0 | 0 |
| 4a-d59fyrkp5xxc | 續校讎通義（劉鹹炘） | 1 | 0 | 0 |
| 4a-d59f2nezxy4i | 聖駕南巡日錄（陸深） | 1 | 0 | 0 |
| 4a-d59fyrt8mozl | 臨安旬制記（張道） | 1 | 0 | 0 |
| 4a-d59fyo34n94w | 自述錄（鈕澤晟） | 1 | 0 | 0 |
| 4a-d59fyt6s8ow2 | 臺中疏草（江東之） | 2 | 0 | 0 |
| 4a-d59fxp7056v5 | 舂陵褒貞錄（汪輝祖） | 2 | 0 | 0 |
| 4a-d59fxt3adngg | 舊唐書勘同（張道） | 1 | 0 | 0 |
| 4a-d59fxpwo3mrl | 船山學譜（王永祥） | 1 | 0 | 0 |
| 4a-d59fyrq076dd | 茂名公牘（王原） | 1 | 0 | 0 |
| 4a-d59f2nfnz85e | 荒史（陳士元） | 1 | 0 | 0 |
| 4a-d59fyh7hebr5 | 荒書（費密） | 1 | 0 | 0 |
| 4a-d59fxsf5zda8 | 薊旋錄（李日華） | 2 | 0 | 0 |
| 4a-d59fyrknaio1 | 藝風藏書記（繆荃孫） | 1 | 0 | 0 |
| 4a-d59f2ne6aebk | 蜀都雜抄（陸深） | 1 | 0 | 0 |
| 4a-d59fyt3sjthe | 螙仙泉譜（湯螙仙） | 1 | 0 | 0 |
| 4a-d59fyzrxh5oh | 袁了凡斬蛟記考（孟森） | 2 | 0 | 0 |
| 4a-d59f2mp1zsoy | 補三史藝文志（金門詔） | 1 | 0 | 0 |
| 4a-d59fy3sj3bb5 | 補宋書食貨志（郝懿行） | 1 | 0 | 0 |
| 4a-d59fyszdcsg0 | 西泠舊事百詠（潘炤） | 1 | 0 | 0 |
| 4a-d59fyko47g1s | 西海紀行卷（潘飛聲） | 1 | 0 | 0 |
| 4a-d59fxvybxs00 | 西遊錄注（李文田） | 1 | 0 | 0 |
| 4a-d59fyt28oc8y | 解餉隨筆（鈕澤晟） | 1 | 0 | 0 |
| 4a-d59fyro1cb28 | 言官錄（李輈） | 1 | 0 | 0 |
| 4a-d59fyerz7gg0 | 訥溪年譜（周怡） | 1 | 0 | 0 |
| 4a-d59f2nbzmhhc | 諸史拾遺（錢大昕） | 3 | 0 | 0 |
| 4a-d59f2mwpmcci | 譎觚十事（顧炎武） | 3 | 0 | 0 |
| 4a-d59fxv8qhbep | 讀國語蠡述（李澄宇） | 1 | 0 | 0 |
| 4a-d59fxv8173ep | 賓退紀談（李桓） | 1 | 0 | 0 |
| 4a-d59fyrumknwg | 輿圖摘要（李日華） | 1 | 0 | 0 |
| 4a-d59fyjqibp4w | 退菴自訂年譜（梁章鉅） | 2 | 0 | 0 |
| 4a-d59fyrv9zgn4 | 遊薩克遜日記（潘飛聲） | 1 | 0 | 0 |
| 4a-d59fxt3d6sch | 遼史索隱（陳漢章） | 2 | 0 | 0 |
| 4a-d59f2nj89r0g | 遼小史（楊循吉） | 1 | 0 | 0 |
| 4a-d59f2nkyp7nn | 鄭端簡公奏議（鄭曉） | 1 | 0 | 0 |
| 4a-d59fyt6h05c1 | 金石一跋（武億） | 2 | 0 | 0 |
| 4a-d59fyzs75iip | 金聖歎考（孟森） | 2 | 0 | 0 |
| 4a-d59fyt27fe2o | 金陵百四十八景（湯螙仙） | 1 | 0 | 0 |
| 4a-d59fyrnlqfwh | 鎮沅紀畧（江東之） | 2 | 0 | 0 |
| 4a-d59fyrs5m134 | 閒閒錄案（孟森） | 2 | 0 | 0 |
| 4a-d59f2nipur5s | 閩部疏（王世懋） | 1 | 0 | 0 |
| 4a-d59fyrt6r9q9 | 隆武紀年（黃宗羲） | 2 | 0 | 0 |
| 4a-d59fypxiraio | 集古錄補目補（陳漢章） | 2 | 0 | 0 |
| 4a-d59fyt2eam0x | 集課記（毛奇齡） | 3 | 0 | 0 |
| 4a-d59fyt1mtq80 | 靈巖小志（李炤祿） | 1 | 0 | 0 |
| 4a-d59fyrsj18g1 | 順天闈（孟森） | 2 | 0 | 0 |
| 4a-d59fyt0ffqps | 食貨書（馬徵麐） | 2 | 0 | 0 |
| 4a-d59fysytdlog | 養恬齋筆記（高驤雲） | 1 | 0 | 0 |
| 4a-d59fyzs0wrnk | 魏陳思王年譜（丁晏） | 1 | 0 | 0 |
| 4a-d59fyrt6r9q8 | 魯紀年（黃宗羲） | 2 | 0 | 0 |
| 4a-d59fyrtk6h35 | 黃帝政教考（文廷式） | 1 | 0 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR。
