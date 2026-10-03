# [qing→weijin/sanguo] cross：合流帶入之單向邊 7 條，皆非本道權限（period=jin/three-kingdoms）

批22 推送後 `verify.py --strict` 見單向邊（entity 指 work 而 work 不指回）7 條，經核 `git stash`
排除本道本批修改後仍在，確係合流自 origin/main 帶入（非本道所生）：

| entity | 姓名 | period | work |
|---|---|---|---|
| hixhd2h9bhuy | 譙周 | three-kingdoms | d59f27souy9t |
| hixhd2h9bmt4 | 劉寔 | jin | d59f27wqmrya |
| hixhd2h9bjfj | 顧夷 | jin | d59f9nmhsu10 |
| hixhd2h9bet2 | 葛洪 | jin | d59f27ulj5s2 |
| hixhd2h9bmjw | 賈充 | jin | d59f29mnof0g、d59f9nmlux3a |
| hixhd2h9bnps | 傅彪 | jin | d59f27tw8xs4 |

六entity皆 jin／three-kingdoms 期，非本道（qing/modern）權限，未動，記此轉交 weijin／sanguo
道核辦（entity.works 列有此 work_id，而該 work 之 authors[].entity_id 未指回，或已改繫他人／
解繫而 entity 側未同步移除）。

按：`verify.py`（非 --strict）視單向邊為非閘控項（見其 `main()`：`bad = missing or drift_w or
drift_e or (a.strict and (...))`），故 `pushmain.sh` 之推送閘未因此變紅，本道批22仍照常推送；
惟收工前之 `--strict` 全清仍賴此類殘留清乾淨，故報之。

— qing 道，2026-09-06
