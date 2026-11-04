# 资源整理 R2／R3／R4 脚本（2026-11-03，S3）

`ops.py <仓根> r2|r3|r4 apply <类型,…>`：r2 删与 schema/resource-sites.json 相同的 resources[].short_name；r3 Book zhsy_id→external_ids；r4 同档重复 URL 去重。回滚：git revert 对应 PR。
