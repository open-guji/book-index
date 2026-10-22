# BOOK-0010 殘餘關係獨立覆核

**結論：維持待核；重做 PR #1213 時不應保留 `993avdq3up → 9954l761oh` 的合併。** 這不是認定兩個1911年版本確實不同，而是最新main已明確暫緩，且尚缺解決Work歸屬的新證據。

讀取基線：`origin/main` = `bc2bb3fcda98a30781b46ddca8b7783dd58a7d97`。本檢查全部以git show讀該提交，未使用PR工作樹的已合併資料作基準。四個源檔全文及SHA-256見 `residual-book-review.json`。

## 已能確定與尚不能確定

兩Book共享上圖instance `weihm5fjpthkojsa`及國圖item `mitttw8ez0uzzu7t`；題名、1911江西開智書局影印明拓本版本、卷數、出版信息、原著錄和館藏相同。責任者歐陽修／歐陽脩只有異體差別。因此它們有強烈的同源元記錄重出證據，並無不同版本的正面證據。

但兩條的所屬Work不是可忽略的管理字段：

|Book|所屬Work|原始證據|
|---|---|---|
|`9954l761oh`|`d59f2hnysjr6` 瀧岡阡表|`subtype=article`、歐陽修「作」、維基文庫文章正文、collected_in文集關係|
|`993avdq3up`|`d59fxry7f9xc` 歐陽文忠公瀧岡阡表|總目子部藝術類書畫之屬，責任者「宋歐陽修書」，唯一著錄為1911影印明拓本|

`schema/book.md`明定Book.work_id是Work與Book關係的唯一存儲側。把993墓碑指向995、並保留995的文章work_id，會把這個有效版本入口固定到文章Work，書法Work失去原有效Book入口。即使keeper字段不改，操作仍然在選定建模歸屬。

## 為何舊E3註記不能解除阻塞

995的E3第803批ai_note說「同題同作者」而把藝術類著錄追加到既有Work；這記錄的是導入推論，不是獨立書影核對，也不是後續明確裁定文章／書法模型的證據。用它證明現在應保留同一掛接，等於用待審結論回證自身。

最新main兩處文件對此已有明確決定：

- `.claude/qa/正式库并条审查规则.md`將一側文章Work、另一側碑刻Work列為不並，直接點名BOOK-0010。
- `.claude/qa/reports/duplicate-audit-2026-10-21/merges.json`的`deferred.BOOK-0010`明記同一拓本元記錄重複，但要先裁定建模及唯一work_id，暫不合併。

所以這唯一未覆蓋關係不是main漏做，而是main刻意延後。沒有新增文獻／建模裁決時，不能把它作為PR1213尚待落地的確證合併。

## 下一步

維持main兩Book、兩Work現狀，保留本案待核。取得原instance與館藏書影，裁定影印拓本應掛文章還是書法Work，或需如何表達兩層關係；明定唯一work_id並記錄依據後，再對同instance Book去重及更新引用。此檢查未改原生、索引、Git，也沒有提出先合再補模型的方案。
