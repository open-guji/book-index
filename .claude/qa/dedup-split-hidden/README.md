# 隐性错并 Book 拆分（E／F／G 道，源记录分属 ≥2 个总目丛书实例且未挂 Collection）

口径、依据见 `split_hidden.py` 文档字符串与 ai-team 去重方案 00 文件第七节（用户 2026-10-28 定：一个 Book＝一个版本；不同丛书实例＝不同版本；分册不作拆分依据）。
规模（main d8c48fa810b）：可拆 6,489 个原 Book，新建约 18,939 个；存疑 102（已挂 1 个 Collection 97、无丛书源记录带馆藏 3、人工终判 2）；另 55 个已挂 ≥2 Collection 的归拆回-二。
用法：`split_hidden.py --parsed <parsed> [--only ids|--skip ids] [--limit-new N] --out <批目录> [--apply]`。

## 批次
- batch-01（样本）：20 个原 Book（随机，seed 7）拆为 75 个，新建 55。门禁：build_derived --check-only fatal 0、dangling 0；check_v2 75 档 ERROR 0；check-classification 0；check_promo_dup 0；check-duplicate-audit PASS。独立子 agent 全检 20 个：错拆 0、provenance 错归/漏/重 0、字段误改 0；2 处「版本项只写『清抄本』『明抄本』、丛书实例不同」按保守口径不并，待后续判断。
- batch-02：445 个原 Book 拆出新建 1,000 个（main c21f2e4eebe）。门禁：check_v2 1,445 档 ERROR 0；check-classification 0；check_promo_dup 0；build_derived fatal 0／dangling 0；check-duplicate-audit PASS。独立子 agent 抽检 50 个（11%）：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0。
- batch-03：364 个原 Book 新建 1,000 个。门禁：check_v2 ERROR 0；check-classification 0；check_promo_dup 0；build_derived fatal 0／dangling 0；check-duplicate-audit PASS。独立子 agent 抽检：50 个原 Book（197 个新 Book）错拆 0、provenance 错归漏重 0；edition 清空为设计内处理；8 对「清抄本」同名丛书不同实例按保守不并
- batch-04：356 个原 Book 新建 1,000 个（main c6ef9e22f6）。门禁：check_v2 1,356 档 ERROR 0；check-classification 0；check_promo_dup 0；build_derived --check-only fatal 0／dangling 0；check-duplicate-audit PASS。独立子 agent 抽检 50 个原 Book（126 个新 Book）：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；2 对「清抄本」同名丛书不同实例按保守不并（98xzgas4qo、98y4inv9j7）。剩约 5,304 个原 Book 待拆。
- batch-05：364 个原 Book 新建 1,000 个。门禁同前全过（check_v2 ERROR 0；check-classification 0；check_promo_dup 0；build_derived fatal 0／dangling 0；check-duplicate-audit PASS）。独立子 agent 抽检 50 个原 Book（132 个新 Book）：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；3 个 book（98y4kxc7b7、98y4kjwzya、98y4jxfwub）「清抄本」同名丛书不同实例按保守不并。剩约 4,940 个原 Book。
- batch-06：375 个原 Book 新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book（131 个新 Book）：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；9939jzu0hs「清抄本」同名丛书不同实例保守不并；5 个 book（9939k89f5s、993apec6bl、993bygkhdu、993aqw162o、98ybmrghs1）刊刻者年代同、仅版本标签不同（刻本对重修本等），按口径拆开。剩约 4,565 个原 Book。
- batch-07：376 个原 Book 新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book（149 个新 Book）：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；993fpl2uiq「清抄本」同名丛书不同实例保守不并；另 14 个 book 仅版本标签不同（刻本对补修本等）按口径拆开。剩约 4,189 个原 Book。
