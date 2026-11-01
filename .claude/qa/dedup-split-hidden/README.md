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
- batch-08：446 个原 Book 新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book（192 个拆后 Book 含 keeper；新建 142）：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；993gjrcow2「清抄本」同名丛书不同实例保守不并；4 个 book 仅版本标签不同按口径拆开。剩约 3,743 个原 Book。
- batch-09：155 个原 Book（多为扇出很大的丛书子目）新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book：错拆 0、provenance 错归漏重 0、字段误改 0；「该并未并」1 个（993iqr0o3k：《醫要集覽（醫藥輯覽）九種》两实例版本项仅『明刻本』、刊刻者空、年代『明』无年份，按脚本 spec 判据不算具体版本项，同『清抄本』保守不并，设计内）；12 个 book 仅版本标签不同按口径拆开。剩约 3,588 个原 Book。
- batch-10：114 个原 Book（大扇出）新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；993j1ec35s（《醫要集覽（醫藥輯覽）九種》两实例仅『明刻本』）保守不并，设计内；6 个 book 仅版本标签不同按口径拆开。剩约 3,474 个原 Book。
- batch-11：152 个原 Book 新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；保守不并 0；7 个 book 仅版本标签不同按口径拆开。剩约 3,322 个原 Book。
- batch-12：125 个原 Book 新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；993kdsql1c「清抄本」保守不并，设计内；20 组仅版本标签不同按口径拆开。剩约 3,197 个原 Book。
- batch-13：351 个原 Book 新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；保守不并 0；2 个 book 仅版本标签不同按口径拆开。剩约 2,846 个原 Book。
- batch-14：493 个原 Book 新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；3 个 book（99418c2znl、9943vaexoh、99433lq77l）仅『清抄本』『明刻本』无刊刻者年份保守不并，设计内；11 个 book 仅版本标签不同按口径拆开。剩约 2,353 个原 Book。
- batch-15：561 个原 Book 新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；2 个 book（994b90ssn5、994back3r4，《名臣寧攘要編》仅『明刻本』）保守不并，设计内；5 个 book 仅版本标签不同按口径拆开。剩约 1,792 个原 Book。
- batch-16：385 个原 Book 新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；保守不并 0；17 个 book 仅版本标签不同按口径拆开。剩约 1,407 个原 Book。
- batch-17：325 个原 Book 新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；9951w83ytc（《鄭學十八種》三实例仅『清抄本』）保守不并，设计内；23 个 book 仅版本标签不同按口径拆开。剩约 1,082 个原 Book。
- batch-18：321 个原 Book 新建 1,000 个。门禁同前全过。独立子 agent 抽检 50 个原 Book：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；9954fu9dz4（六子書／纂圖互註五子／六子 仅『明刻本』）保守不并，设计内；4 个 book 仅版本标签不同按口径拆开。剩约 761 个原 Book。
- batch-19：418 个原 Book 新建 1,000 个。抽检（首次生成）发现 1 例漏并：99569788ox「七種爭奇」两实例版本项相同（清春語堂刻本），因源记录 series_title 为 None 而按 series_id 各成一组。已改 split_hidden.py key()：series_title 缺时用丛书头记录 title.name，并重生成本批；新口径下独立子 agent 抽检 50 个原 Book 及全批 418 个拆分 Book 全量漏并检查：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；保守不并 6 个（仅标签无刊刻者年份，设计内）；37 个仅版本标签不同。batch-04～18 可能有同类残留（源记录无 series_title 且头记录同名同具体版本项），另扫补并。剩约 343 个原 Book。
- batch-20（末批）：343 个原 Book 新建 882 个。门禁同前全过。独立子 agent 抽检 50 个原 Book 及全批 343 个拆分漏并检查：错拆／该并未并 0、provenance 错归漏重 0、字段误改 0；保守不并 0；18 个仅版本标签不同。同时全局扫 batch-04～18（4,899 个原 Book、19,899 个部分）按新口径 key() 无残留漏并。
- 收尾：可拆的 6,489 个原 Book 已全部拆完（batch-01～20 共新建约 18,900 个 Book）。剩存疑 102（见各批 存疑.tsv、最后一批为准）：已挂 1 个 Collection 97、无丛书源记录带馆藏（疑单行本混入）3、人工终判 2，另 55 个已挂 ≥2 Collection 的归拆回-二；不在本串内处理，待 Collection 补建一并判。
