# C1b（2026-09-30）：詞表改用《中國古籍總目》

- `../../../classific.json` 已換成總目詞表；Work 的 `classification` 路徑已按 `c1b_migrate.py` 遷移（2,439 部；`basis`／`source` 不動）。
- **本目錄其余腳本（`crosswalk.py`、`vocab.py`、`s_tier.py`、`siku.py`、`build_classification.py`、`ingest_x2.py`、`patch_from_results.py`）仍是舊詞表（正史類、集評類、說叢類、詔令類／奏議類、詞曲類…）的產物，對照表輸出的類名不再合法**。它們保留為歷史記錄；**新一輪分類（overview#285）須先把「志書類目→總目類表」的映射重寫再用**，不要直接跑舊 crosswalk。
- 重跑遷移：`python3 c1b_migrate.py`（試運行）／`--apply`（真改）；已遷移者不變（冪等）。
