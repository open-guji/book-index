# T66 报告（open-guji-core/overview#382）

只用库内证据；合并均经 `mergework.py` 先干跑再 `--apply`。

## 一、合并表（Work 数 95043 → 95039，差 4＝并掉 4 条）

| keeper | 被并 | 判据 | 备注 |
|---|---|---|---|
| d59f28jsy0w3 通曆（馬總） | d59f28jl53b7 唐通曆；d59f2q9sgk5c 馬揔通曆 | 同撰人（馬總＝馬揔，揔為總之異體；二者同 entity hixhd2h9bezh／新唐志无撰人而题「馬揔」）、卷数皆十卷；十五卷（直齋）与十卷之异，直齋已自释为后人续增五卷 | indexed_by 全保留（+國史經籍志《唐通曆》、+新唐志《馬揔通曆》）；卷数差异写入 ai_note；measures 仅留十五卷；**不搬**被并者 period_upper（焦竑／新唐志之界不适用于含五代续文之十五卷本）；additional_titles 增「唐通曆」「馬揔通曆」。注：國史經籍志本身已有《通歷》十卷（keeper 内）与《唐通曆》十卷两行，属焦竑重出 |
| d59f2hifn56o 淳祐玉峯志（凌萬頃） | d59f2hsdzksi 玉峯志（凌萬頃）；d59f2hpeapdt 玉峯志（項公澤） | 三条库内 period_basis 皆自述为南宋淳祐间昆山（玉峯）县志；凌萬頃纂、項公澤时知县事主修，同一志之人。故宫二条实为该志之阮元进呈钞本（Book 988g4d1s0a）与吳翌鳳手钞本（Book 988g4twlcb），版本属 Book | **keeper 取 d59f2hifn56o**：唯一有著录（续修四库）、卷数（三卷）、完整撰人、classification 的条。Books 与 resources 并入，Book.work_id 改指 keeper，_edition_count＝2。authors 增項公澤（修）。measures 不取被并者之「四冊」「二冊」（是各抄本册数，属 Book）；description 去「惟一志著錄，別無他證」句（失实） |

连带：Entity 宋凌萬頃（hixhd2h9bq0t，名前冠朝代之误）并入 凌萬頃（hixhd2h9bp0i，有 CBDB／Wikidata），以满足 keeper authors 与 Entity.works 双向一致。

`d59fpj2hzojn 玉峯續志`（邊實，一卷）另是一书，**未并**。

## 二、改名表

| Work | 原 | 改 | entity 处理 |
|---|---|---|---|
| d59f2gon3qpu 九經疑難 | 張伯文 | 張文伯 | entity hixhd2h9bmpr 本即「張文伯」（alt 含張伯文），仅作者名字串误，entity_id 不变 |
| d59f2gorh2bl 書齋夜話 | 俞琬 | 俞琰 | entity hixhd2h9bhum 本即「俞琰」，仅名字串误，entity_id 不变 |
| d59f2gl6vaio 梅磵詩話 | 韋安居 | 韋居安 | 错名 entity hixhd2h9bl2g 仅繫本书，并入已存在的正名 entity hixhd2h9bhqp 韋居安（works 反引同步），错名 entity 删除 |

indexed_by 内各志/提要的原文（如四庫「宋俞琬撰」、元史藝文志「韋安居」、補遼金元「張伯文」）为引文，**未改**。description 首句之名同改。

## 三、没动的及理由

- 玉峯續志 d59fpj2hzojn：邊實撰一卷续志，另书。
- 韋居安《梅磵詩話》的朝代：揅經室提要/四庫皆称「宋」，本条 authors[0].dynasty／period 仍承元史藝文志作「元」，而 entity 韋居安为南宋——两者不一致，超出本轮名改范围，已写入 ai_note，留待断代道复核。
- 被并者与 keeper 的其它冲突字段（revised_at、updated_at、period_basis 等）一律以 keeper 为准、不搬。
- 无拿不准而放弃的疑似重条；唯一取舍点是上述 period_upper 与 measures 的不搬。
- 库内既有 `Collection.contained_works[].title 漂移 2`、`單向邊 103`、2 个分片路径错位的 Book（cxbhq7g9us、0phe8c4i1i）均为本轮前已有，未动。

## 四、检验

- `verify.py`：OK（单向边 103 为本轮前已有，不入 FAIL）
- `backrefs.py --audit`：悬空 0
- `reindex.py --run --membership`：回写作者名漂移 4、删索引键 2（两个被删 entity）；其后 `reindex.py` 待回写 0
- Work 数 95043 → 95039

## 五、book-text 中引用被并 id 的文件（已改，用户许可目录拆分字段可改，原文不动）

| 文件 | 行 | 引用 |
|---|---|---|
| Work/m/i/o/d59f2hl0cmio/default/013.json | 414 | work_id d59f2q9sgk5c（新唐志「馬揔通曆十卷」）→ 应改 d59f28jsy0w3 |
| Work/9/3/6/d59f2nl40936/default/003.json | 6099 | work_id d59f28jl53b7（國史經籍志「《唐通曆》十卷（馬總）」）→ 应改 d59f28jsy0w3 |
| Work/m/y/o/d59f2msx7myo/default/005.json | 178 | work_ids 含 d59f2hsdzksi（揅經室「玉峯志三卷玉峯續志一卷」）→ 应改 d59f2hifn56o |

三处 work_id/work_ids 已于 book-text main 改指 keeper（仅此三行，目录拆分字段）。改后全仓再无被并 id。未发现 book-text 引用 d59f2hpeapdt、hixhd2h9bq0t、hixhd2h9bl2g。
