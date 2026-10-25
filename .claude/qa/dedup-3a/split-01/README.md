# 3a 混记录拆分（split-01）

部分 3a 并条时登记了 9 处「需拆分／清理」的混记录（见 `../存疑-<部>.tsv` 末列）。三个子 agent 只读原文逐处研究，方案见 `plan-ji.json`（集部）、`plan-shi.json`（史部）、`plan-jz.json`（經子）；执行脚本 `split_apply.py`（新 Work id 由 `mintid.py` 车道 dedup3a 铸），`split_post.py` 为 check_v2 V07 补正。

| 组 | Work | 处理 |
|---|---|---|
| G0806 | d59fyuadth4w 唐荆川先生文集 | 石韞玉選一卷本（明八家文選子目）著录与 Book 994y4r47wg 拆出，新建 d59g24d8rsw0 |
| G0313 | d59fxwsx6ww0 東坡詩選（孟濤輯） | 譚元春選十二卷本 3 个 Book 改挂已有 d59f2nj97h1c（同一文盛堂刻本，补著录）；陳訏選一卷本（宋十五家詩選）新建 d59g24d8rsw1，并从 d59fyicx5c01 移入同本 Book 994188c54x；沈德潛選二卷本新建 d59g24d8rsw2；鄭德徵輯本重复著录删去。明刻本 993fq3szcy、国图无版本 993fq4fgg1 选者不明，暂留 |
| G0940 | d59fxywkoge8 劍南詩鈔（楊大鶴選六卷） | 宋詩鈔初集本一卷著录与 Book 993htraiv4 归 d59fyid32ubk |
| G0534 | d59fxu434pvk 今水經 | 黃錫齡注《今水經注要覽》三卷著录与 Book 9955zzq801 拆出，新建 d59g24d8rsw3（与 d59fyt0b2f40《水經要覽》互链 related）；薛鳳昌编本即梨洲遺著彙刊本，留下；Book 9956ar3q4g 撰者误字黃宗義→黃宗羲 |
| G0610 | d59f2mdca6tc 雲南通志（乾隆） | 删《國史經籍志》十七卷明修本著录（正主 d59f2ncxc8hs 已有）；康熙志 Book 9979895f9f 改挂 d59f2n7qzfup；description 改写 |
| G0005 | d59fyro6c35s 晉畧 | 「晉畧二卷」（史論彙函甲編節本）依库例挂原书不拆，只删重复著录一条 |
| G0518 | d59f2hgz79xd 易章句（呂大臨） | 宋志「《易章句》十卷又《外編》一卷《占法》」属程迥（顶真格），改繫 d59f2hjwe8zn《沙隨易章句》；description 去龔原 |
| G0715 | d59fxqo6uoe8 蓮鬚閣集 | 六卷是《乾坤正氣集》所收选本，依库例挂原书，不拆（另 PR 并 d59fyicpyvi9） |
| G0751 | 緯畧 | 說郛一卷节本依库例（全库 1,274 个說郛本 Book 挂原书）挂原书，不动 |

拆后可并的三组（G0518、G0534、G0715）另开 PR 并条。

`../../dedup-judged/3a.tsv`：部分 3a 判为分立（C）或存疑（D）的 362 对，供普查 `--whitelist` 用。
