# 本名／字／號：19:00 批次字段與執行候選複核

固定 main：`c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。只寫本目錄；原生資料、共用檢查點、分支、提交均未改。兩組既有確認案維持 confirmed，一組舊 open 增補排除證據，累計仍 **15 confirmed／2 separate／5 open**；本輪身份新增確認0、實施合併0。`PNA-1900-001/002/003` 分別 supersedes `PNA-A001/A002/R015`，不得重複計數。

已讀 PLAN、Astra 報告與候選方案，以及固定 main 的《正式庫並條審查規則》、`entity_merge.py`、`audit-merge-ledger.py`、Entity JSON schema、builder/index_entry/v2common。10份原檔用固定 main tree Git blob SHA1 與完整舊 checkout 原字節一致，再存 SHA256；漂移0。不是憑舊 checkout 日期推定 current main。

## 可供根代理實施前複核的交付

- `candidate-ledger.json`：正式審計腳本所需 `merges`／`cluster_id`／`type=people`／`preconditions` 結構；4個完整人物原值按原 owner 保留，附兩個已知精確引用改指。
- `field-ledger.json`：**59條字段行**，包括兩側原本相同、獨有及管理字段；每行有 before/after 與 presence，缺字段不誤當 null。
- `candidate-records.json`：**4 Entity＋2 Work** 的精確擬寫內容，未寫回。日期為候選日期；若改日執行要刷新 `revised_at`／`merged_in.at`。
- `source-snapshots.json`、`source-validation.json`：10檔完整原值與雙散列。
- `index-review.json`：直接抽取並執行 main 官方 `index_entry` 對4人物前後投影，全部相同。
- `prepare_review.py`：只讀原生資料、只寫本目錄的可復現生成器；沒有 apply 選項。

## 逐字段策略與必要修正

| 案 | keeper ← loser | 精確人物變化 | 來源／歷史保留 |
|---|---|---|---|
| 錢易／錢希白 | hixhd2h9bhe7 ← hixhd2h9blpt | 只增錢希白／別稱、merged_in、revised_at | keeper description.sources、ai_note、外部ID、籍貫及日期全部原值保留；loser舊updated_at等完整入台賬 |
| 喻樗／喻子材 | hixhd2h9bhcp ← hixhd2h9bppr | 只增喻子材／別稱、merged_in、revised_at | keeper子才／子材兩字與湍石／玉泉兩號不改；loser乙等建人及未定代長ai_note逐字存原owner台賬 |

墓碑明確只留8項：`schema_version,id,type,subtype,primary_name,revision,revised_at,merged_into`。loser `updated_at` 不進墓碑，但完整原值在台賬，不靠 git 歷史。keeper既有 `updated_at` 保留；不冒稱其日期/號/外部ID本輪重新驗證。`dates.floruit=[969,969]` 仍註明來自 cbdb:index_year，不順手改為生年；喻樗卒1180不在本案重新認定。

既有 `entity_merge.py` **不會自動加入 loser.primary_name 為別稱**，只聯集 loser.alt_names，因此必須加本次兩個明確別稱動作。現行腳本也沒有完整人物字段無損審計；官方 L 主要檢 Work/Book，不能把 T/L/P/R 綠燈視為人物 ai_note 已存證。此處完整原值＋59行台賬補足該盲點。兩loser無出邊、獨有外部ID、description.sources 或既有 merged_in，故無額外聯集值；一旦 precondition 改變就重做字段審查。

兩處已知改指仍為《洞微志》`Work/9/1/f/d59f2hket91f-洞微志.json` 與《豐公逸事》`Work/7/i/9/d59f2psls7i9-豐公逸事.json` 的 `/authors/0/entity_id`，name/role/dynasty/source/basis 等皆不變。全引用搜尋由根代理集中進行；本子路沒有重掃，也不把兩處清單宣稱為自行完成的全庫證明。根代理的正式／草稿／文本掃描應附於實施台賬後才能放行。

## 官方索引與驗證門檻

官方 `index_entry(Entity)` 不收 alt_names、merged_in、merged_into。兩墓碑原本也無可投影的朝代／日期／外部ID；兩 keeper 既有投影字段不變。兩Work僅改 entity_id，而索引作者使用 name，故**本兩組預期倉內 index內容增量為0**。不得手工刪 loser索引條目或用自製索引覆蓋。派生 `_build/entry` 中人物作品反查及作者卡片會更新；原生 Entity 不寫 works/_works。

固定main builder的 `--text-index` 已是必填。舊方案只列 `--check-only` 不足；正確執行門檻示意（在實施工作樹，填實際台賬及已驗證文本索引目錄）：

```bash
AUDIT_BASE=c6dd8356d613fc5614beb88f0a61a3d04cfb069e
AUDIT_LEDGER=.claude/qa/expanded-duplicate-audit-2026-10-22/people_names_aliases/hourly-20261022T1900/candidate-ledger.json
AUDIT_TEXT_INDEX=/workspace/scratch/0bc7226fa660/book-text-ref/index/texts
python3 scripts/audit-merge-ledger.py --ledger "$AUDIT_LEDGER" --base "$AUDIT_BASE" --draft /path/to/verified/book-index-draft
# 實際變更路徑含中文須解碼；另外核實讀入檔數非0。
git -c core.quotePath=false diff --name-only "$AUDIT_BASE" -- Work Book Collection Entity classification promotions curation recommended.json > /tmp/pna-changed-paths.txt
test -s /tmp/pna-changed-paths.txt
python3 .claude/qa/check_v2.py --paths - < /tmp/pna-changed-paths.txt
python3 scripts/check-classification.py
python3 build/build_derived.py --text-index "$AUDIT_TEXT_INDEX" --write-index
python3 build/build_derived.py --text-index "$AUDIT_TEXT_INDEX" --check-only
```

T/L/P/R任一ERROR不得放行，D有活動殘留須另PR或清零，promotions只能改production_id的既定映射，歷史台賬與正文舊ID不能全域替換。`--write-index` 後逐檔看diff，與本批無關的既有漂移要分開說明。合main後重驗新引用。

本輪已過：10原檔雙散列、4候選Entity必填鍵／允許字段／別稱枚舉／merged_in字段結構斷言、4人物官方索引投影前後一致。**未跑全JSON schema／check_v2／T/L/P/R／分類／全量builder**：原生資料未寫；system及primary runtime均無jsonschema模組，未把有限結構斷言報成完整schema通過。

## 一個 open 的新增排除證據

柳宗直／柳正夫仍 open。新查[張南軒先生文集卷六《西漢蒙求跋》](https://www.shidianguji.com/zh/book/CADAL01024476/chapter/1l3f0fa2xfkss)正文284–304行：開篇舉宗直《西漢文類》作先例，接著轉述東平侯彦明的新編。搜尋摘要把篇題與首句接在一起，容易被誤讀為宗直作《西漢蒙求》，正文不能支持此橋接。這也不授權把庫中柳正夫的書直接改繫侯彦明；仍須柳正夫原刻／序跋之本名、籍貫或官歷證據。兩Entity與兩Work均保留。
