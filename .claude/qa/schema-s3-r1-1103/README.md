# 资源整理 R1：单成员资源组 → 资源 `label`（2026-11-03，S3）

`apply_r1.py <仓根> apply <Work|Book>`：组里只有 1 条资源的组，把组标题写成该资源的 `label`（组有 `description` 的并入 `details`），删这条的 `group`／`group_role` 和 `resource_groups` 里的该组；组键未登记（悬空）的单条只删 `group`／`group_role`。JSON 缩进、键序不动。
回滚：`git revert` 对应 PR（每档改前的内容都在 git 里）。
Work：55,252 项（30,223 档；其中 690 项为悬空组，无 label）。Book 另一个 PR。
