# 不同译本／不同书挂同一 Work 的拆分（split-02）

来源：5b-研 单元在 Book 层逐对核时发现的「Work 疑混」9 对，外加康熙、雍正两部《黔陽縣志》同挂（ai-team `去重方案/5b-研/同馆同卷78对-逐对判定.tsv`）。子 agent 只读原文出方案 `plan-yi.json`，执行脚本 `split_apply.py`（新 Work id 由 `mintid.py` 车道 dedup3a 铸）。

| Work | 处理 |
|---|---|
| d59fyh384um8 大乘起信論（實叉難陀二卷） | 真諦一卷译本 8 个 Book 拆出，新建 d59g2foxbpj4；蕭士瑋解本 99400f25mp 改挂 d59f2ngp4gsh《起信論解》 |
| d59fyew93f29 攝大乘論釋（世親釋、玄奘譯） | 真諦譯十五卷本 4 个 Book 新建 d59g2foxbpj5；無性釋 5 个 Book 新建 d59g2foxbpj6；普寧藏笈多玄奘合录本改挂 d59fyew8s6io《攝大乘論釋論》 |
| d59fy74cz08x 大乘四法經 | 《菩薩修行四法經》2 个 Book 改挂 d59fy8mow001 |
| d59f27x5axhf 大般涅槃經（北本） | 南本三十六卷 6 个 Book 改挂 d59f7z49cf7s；《三國藝文志》安法賢譯二卷一条移出，新建 d59g2foxbpj7（佚）；description 改写 |
| d59fybkjl3i8 佛說須賴經（白延譯） | 支施崘譯 3 个 Book 改挂 d59f2q3jpp1c；白延本 3 个 Book 的 sources 删去串入的对方源记录 |
| d59fy741f85c 大乘百福相經 | 《大乘百福莊嚴相經》6 个 Book 改挂 d59fy741qgox |
| d59f2n2bw4cg 黔陽縣志 | [康熙] 本著录与 3 个 Book 拆出，新建 d59g2foxbpj8；本条今指 [雍正] 本（题名暂未改） |

未做、留给后续：
- Book 993xtgn75s 曾在 2026-10-19 Book 层查重时并入笈多本、无性本记录（merged_from 11so52epypekj、11so52epypeki），应在 Book 层拆回（交「拆回」串）。
- d59fyx1h1cld《起信論解》与 d59f2ngp4gsh 同书，可并；d59f2pz05ce9、d59f2q2eid4x（國史經籍志百福二经）可分别与对应 Work 并。
- 黔陽縣志 d59f2n2bw4cg 题名宜改「[雍正]黔陽縣志」并补王光電增輯；其 commons 同治本资源宜移 d59fynqeetq9。
