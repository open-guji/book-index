# 去重方案部分 4：4a-α乙 第 1 批（子部／集部／未分类样本 20 组）

基线 main `e3f2a4d74dd34c7f84b0c22c5deab930ff39b431`。口径：`ai-team/domain/目录与资源/设计/2026-10-正式库全面去重方案/部分4-Work层无责任者与弱证据.md`（4a-α 修订节）、00 文件 Work 节 A 档、`.claude/qa/正式库并条审查规则.md`。

**4a-α 规则**（候选脚本 `../cand_alpha.py`）：同题组（`scripts/dedup-census.py` 口径：去括注、异体归一）里，无责任者一侧是叢書线（GUJI-526）新建的叢書子目 Work——《總目》叢書部獨撰類著录子目时不重复撰人，所以「無責任者」只是著录省略；其 Book 所属 Collection 的首位撰者（角色撰／撰輯／著等）与组内**唯一**一条有责任者 Work 的首位责任者同名、朝代相容；卷数相同、一侧缺或差≤1；单行本自身卷数不齐（差>1）的组跳过；同一叢書内有两条同题子目的组跳过（疑异篇）；有责任者多于 1 条的组留给 3a。子目 Work 并入单行本 Work，子目 Book 随之改挂。

工具：`apply_4.py`（包装 `../dedup-confirmed-163/apply_batch.py`，复用 mergework：著录并入、Book.work_id 与引用改指、分类成员改指，被并者留墓碑、keeper 记 merged_in／merged_from）、`postfix_common.py`、`update_index.py`、`fix_draft.py`。冲突字段保留 keeper 原值，被并值入台账 `retained_alternatives`；被并者原 ai_note／description 存 `loser_original_notes`；互斥分类登记见 `分类互斥登记.tsv`。

善后提示：并后 keeper 下可能同时有 F 道「某某叢書本」Book 与叢書线子目 Book（同丛书不同著录），属部分 5 同 Work 同版本 Book，留给部分 5。

| 组 | 保留（单行本） | 并入子目条数 | 保留冲突字段数 | 分类互斥处理 |
|---|---|---:|---:|---:|
| 4a-d59fsjpn0gzl | □堂文集（顧家相） | 1 | 0 | 0 |
| 4a-d59fxpsf5csg | 一笑（俞樾） | 1 | 0 | 0 |
| 4a-d59fsg0bqt52 | 一粟齋試帖（易本烺） | 1 | 0 | 0 |
| 4a-d59fsfi142yp | 一經廬文鈔（姚配中） | 1 | 0 | 0 |
| 4a-d59fxqimrqwy | 一經廬琴學（姚配中） | 1 | 0 | 0 |
| 4a-d59f2ne4ez9f | 一菴語錄（唐樞） | 2 | 0 | 0 |
| 4a-d59fxv3fg001 | 丁年玉筍志（楊懋建） | 1 | 0 | 0 |
| 4a-d59fscerbny9 | 丁戊稿（羅振玉） | 1 | 0 | 0 |
| 4a-d59f2mu6sa9t | 丁戊筆記（陳宗起） | 1 | 0 | 0 |
| 4a-d59fscettkap | 丁頤生時文（丁午） | 1 | 0 | 0 |
| 4a-d59f2mwf09vm | 七經樓文鈔（蔣湘南） | 1 | 0 | 0 |
| 4a-d59fxu2sb6yq | 三一測（唐樞） | 2 | 0 | 0 |
| 4a-d59fsietq876 | 三十六芙蓉吟館尺牘（湯成彥） | 1 | 0 | 0 |
| 4a-d59fsielatj8 | 三峯草廬詩（郭柏蒼） | 1 | 0 | 0 |
| 4a-d59fxu2smfi8 | 三州學錄（胡薇元） | 1 | 0 | 0 |
| 4a-d59frydk1ptv | 三影閣箏語（張雲璈） | 1 | 0 | 0 |
| 4a-d59f2nhi5j40 | 三戌叢譚（茅元儀） | 1 | 0 | 0 |
| 4a-d59f2nizizuo | 三統術衍（錢大昕） | 3 | 0 | 0 |
| 4a-d59fxz4ho7wh | 三統術補衍（成孺） | 1 | 0 | 0 |
| 4a-d59f2mieks1s | 三魚堂文集（陸隴其） | 2 | 0 | 0 |

验证：audit-merge-ledger（--draft 草稿库已同步）T/L/P/R/D 全 0；check_v2、check-classification、check_promo_dup、check-duplicate-audit、build_derived --check-only 全 0。抽检见 `抽检.md`。回滚：revert 本 PR。
