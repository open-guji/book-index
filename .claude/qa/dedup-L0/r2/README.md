# L0 第二轮（2026-11-12 晚）

- 基线：带白名单普查 Work 未判同题组 230（共 675 条；史 156／子 37／集 22／經 15），多数是当天 L1 据《續修四庫全書總目提要》新建的无撰人 Work 与库中已有带撰人条同书（建条查重时没做「畧／略、谿／溪、丘／邱」等异体归一）。
- 先把第一轮 `L0-收口.tsv` 里被并 id 映射到 keeper（11 行），否则白名单边挂在墓碑上不起作用。
- 卷宗每塊列最多 3 条代表，4 个子 agent 判：A 11／B 147／C 6／D 71（一条挂两则提要的续修条 2 对由 B 降 D，须先拆）。盲检 40 对 A/B：40 SAME。
- 并 158 组 158 条（`mergework.py --by L0`），9 条 keeper 删「別無他證」句，promotions 19 处改指；C/D 77 对登 `dedup-judged/L0-第二轮.tsv`。
- 人物：A12 #2279 新建清張恒、清王琰与旧条同名，登 `2.1续.tsv` 分立。
- 门禁：check_v2／check_schema ERROR 0；audit-merge-ledger T/L/P/R/D 全 0；check_promo_dup 0；check-classification 0；check-duplicate-audit PASS；普查 Work 未判组 230→8，人物同名组全员已登记。
- 判定员报的数据问题（未动，转相关车道）：续修条一条挂两则提要（d59gc4iouwff、d59gc4ipslyq、d59gc4ip64wi、d59gc4io8fa0、d59gc4iphdjy、d59gc4iqf31s、d59gc4ircss2）；丛书编者被记成撰人（鄧士龍、沈節甫、羅振玉、錢徵／蔡爾康等）；多处 Book 版本串误拼佛藏刻本文字（如 994bqt0dtt、994d7k46pt、993wltlrlt、993mz5bksg、994bqjyi2o、994py9nv28、99465d7abl）；族谱、北征記、鄒子、金石存、水西紀略等塊内混了不同书需拆；G125 黃奭輯《晉紀》（白帖引）d59fyv5mhiww 与 d59fyivzvj0g、d59fyq7eakn5 疑同辑本。
