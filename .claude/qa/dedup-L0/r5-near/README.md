# L0 第五轮 近似题名（撰人名异体或形近讹字，2026-11-13）

## 候选
- 题名经 OpenCC t2s 与刊刻前缀归一后相同、但两侧撰人名不同的对。先机械筛出撰人名只差异体字或一两个形近字的 50 对。

## 判定与剔除
- 子 agent 判定：A 42、C 4、D 4。C/D 登在 `dedup-judged/L0-第五轮.tsv`。
- 判准：题名只差异体或刊刻前缀；撰人名只差异体或形近讹字；朝代、卷数不矛盾。蔡／黃、繼／經、薘／釴这类不是形近的，以及卷数差距大的，判 D。「[康熙]」「[乾隆]」两修之志判 C。
- 并查集合组后，两侧都被 book-text 引用的 6 组暂缓，登为「D待并」。
- 盲检 12 对：12 SAME。
- 并 35 组、36 条（`mergework.py --by L0`）。promotions 改指 10 个文件。
- 已登记对中含被并 id 的 17 对，换作 keeper 补登（判定照旧）。

## 撰人改正
keeper 撰人是讹字的，已从被并条移入正名与 entity，并在 ai_note 里注明：
- 王元祚→江元祚，王芽→王琛，黃二溥→黃仁溥，張伯瑞→張伯端，郭宏遠→郭弘遠，李業與→李業興，沈施→沈旋。

拿不准哪个是正名的 3 组，keeper 撰人照旧，在 ai_note 里记下另一写法：
- 張成教／張成敖，沈念慈／沈念茲，康敷鎔／康敷容。

## 并后成孤儿的人物 Entity（24 个，未动，交 A12 处理）
- hixhd2h9bke9 王元祚
- hixhd2h9bksa 顧體之
- hixhd2h9blic 孫蔣
- hixhd2h9bls6 李業與
- hixhd2h9bls8 王芽
- hixhd2h9bltf 獻士元
- hixhd2h9bltk 郭宏遠
- hixhd2h9bm2u 毛王
- hixhd2h9bmoq 劉或
- hixhd2h9bmor 孫練
- hixhd2h9bqe7 張成敖
- hixhd2h9br4v 李廷是
- hixhd2h9brct 杜門
- hixhd2h9brud 沈施
- hixhd2h9bsst 聶𫒋
- hixhd2h9bucl 陳鍚
- hixhgyrw4v07 冦天叙
- hixhgyrw4x4w 羅歙德
- hixhv2bxmxhd 樊鯈
- hixi8us2w160 黃二溥
- hixicabcm3n9 司馬承楨
- hixicld4dstx 王黻
- hixiclg00jke 張伯瑞
- hixiclg00jpn 呂道燨

## 未改
- 题名讹字建议（泰山道裏記、邯郸縣志、顧悦傳、新刻字學源流 等）要改文件名，本轮不动。
- 發矇記 d59f27v8mpz6 应并入 d59f27wtfwua（两侧都被 book-text 引用，暂缓）；不并入地理类《發蒙記》d59f27tuor29。
