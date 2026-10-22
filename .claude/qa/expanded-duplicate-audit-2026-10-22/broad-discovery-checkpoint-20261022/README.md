# 全量发现输入与六路候选持久检查点

固定main：`c6dd8356d613fc5614beb88f0a61a3d04cfb069e`。这是一份候选发现快照，不是并条映射。

`validation.json`独立验证全部322748条活跃记录：266045 Work、56703 Entity，其原始JSON字节SHA256、Git blob SHA1及main全树OID均匹配，0错误。其中人物子类52806条。扫描数据库未保存进仓库，可用当前脚本从该不可变提交重新建立。

## 重建

在完整、可读的book-index checkout上执行（未检出的文件须先checkout；脚本对工作区变更读取固定base原blob）：

```sh
python build_broad_current.py --repo /path/to/book-index --base c6dd8356d613fc5614beb88f0a61a3d04cfb069e --out /tmp/guji-discovery.sqlite
python validate_snapshot.py --repo /path/to/book-index --db /tmp/guji-discovery.sqlite --out /tmp/discovery-validation.json
python census_broad.py --db /tmp/guji-discovery.sqlite --out /tmp/guji-census
```

六路脚本是原发现脚本，保留当时绝对工作路径以复现上下文；移到其他机器时须调整脚本中的ROOT/DB/OUT。压缩队列可直接解压继续逐案审查，不需要重扫。manifest.json逐文件保存原路径、保存路径和解压后SHA256；未入库的大型原档缓存可按固定main及候选ID重新获取。人工已审原档保存在各路hourly-20261022T2000中。

## 范围和统计

- Work同题而作者或责任层次不同很常见，23983个同题组不能算23983组重复。
- “同题＋具名首位责任者”和“同题＋同来源长摘要”并集608对、394个连通组，涉及855记录。两规则重叠已排除；连通性也不是可合并性。
- 65841个活跃Work未挂四部分类；强规则候选中198对两侧都无四部分类。这部分必须继续单独审查，不能由经史子集各路覆盖率替代。
- 人物扫描4,143对来自多个有重叠的发现规则。较前2,573对的增量主要来自目录原文名／字／号承接检索，片段解析可产生误报，必须核完整段落。
- 六路候选队列之间范围重叠，不得求和作为总重复量。正式研究统计以current-rollup.json和替代关系为准。
