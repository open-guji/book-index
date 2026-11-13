# L0 第七轮 Book 同版本重复（2026-11-13）

## 候选
- 普查「同 Work 同版本名」5,783 组之外另起一路：同一 Work、同一叢書 Collection（含同 volume_index）下有两条以上 Book 的组 10,330 个。
- 先剔除国立故宫善本旧籍、两部敦煌遗书（馆藏型 Collection，多条 Book 多为不同藏本），以及版本项互相冲突的组；版本项须一致或一侧为空，且非空者以「本」结尾；题名经 t2s 和刊刻前缀归一后相同。余 5,477 组。

## 判定
- 盲检 40 组：37 SAME、3 UNSURE。按 UNSURE 的类型整类剔除：
  - 卷数（measure_info）不合：262 组
  - 两条都带馆藏（provenance），可能是丛书内确收两处：613 组
  - 說郛、稗海系 Collection：95 组
  - 题名或著录带节录、节选、摘钞、残：15 组
- 余 4,492 组，并 4,494 条 Book。

## 并法
- keeper 取带馆藏者，其次取有版本项、字段多者。
- 被并方的 contained_in、indexed_by、sources、provenance、resources 并入 keeper；keeper 缺的 edition、measures、dating、authors 等由被并方补。
- 被并方留墓碑（merged_into＋merged_basis）。
- promotions 改指 1,035 个文件；草稿库 40 条墓碑 merged_into 另 PR 改指。
- 被并 Book 在 Work、Collection、Entity 和 book-text 中都无引用。

## 未做
- 题名不同的 274 组（多为异体字、题名详略之差）。
- 以上剔除的 985 组。
