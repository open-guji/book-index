# sjj-members：無求備齋諸集成成員待辦（2026-11-15，車道 a11-sjj-members）

輸入 `../sjj-collections/members-todo.tsv`（CiNii 子記錄 496 條）；本目錄是處理腳本與判定記錄。

流程：`build_index.py`（流式讀 git 對象，產 `idx.pkl`，免整庫檢出）→ `analyze.py`（題名異體歸一＋撰人雙查，產 `res.pkl`）→
`build_members.py --idx idx.pkl [--apply]`（建 Work／Book、挂接）→ `finish.py`（把結果寫回 todo 兩列）→ `census_check.py`（本地模擬 dedup-census W 段）。

口徑：
- 新建 Work 須題名（vs 庫內，經 scan.VARIANTS／opencc／EX 歸一）＋撰人雙查皆無；近似題名、他書分卷（如四書某書之論語部）、版本層（唐寫本、石經、輯校本、同書不同署名）、責任者不明／存疑者一律不建，原因見 `members-todo.tsv` 末兩列。
- 同題異撰人：撰人名非同一人的異寫者另立，並登 `../dedup-judged/無求備齋成員補建.tsv`（C）。
- Book 只在注記明載單一影印底本（出版者／堂號／叢書名，或明記年份的刊鈔本）時建；`edition`＝底本＋「（丛編名影印，第N函）」，`contained_in` 帶 `volume_index`。
- 既有 Work 的 Book：只在底本與庫內 Book.edition 核心名唯一吻合時挂 `contained_in`；吻合不唯一、或庫內已有近似版本，一律不挂不建。
- 合冊著錄（一條 CiNii 記錄含多書）暫不拆。
