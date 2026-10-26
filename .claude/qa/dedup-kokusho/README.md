# 国書等日本馆藏线索：同题多 Work 核并

来源：国書／内閣／NDL 存疑档里「同一馆藏记录配到两个以上同题 Work」的线索（DUP_WORK_SUSPECT、GROUP_SPLIT、MULTI_WORK、同 group_key），见 bim `docs/馆藏资源挂接/报告/A2-国書存疑升档-20261026.md`、`A2-内閣NDL存疑升档-20261026.md` 的交去重清单。

- 去掉已判对（dedup-judged）、部分 4 占用 id、开放 PR 涉及的 id、已互挂 related_works 的，得 9,604 对；其中两侧或一侧是叢書子目的归 3a 第二轮／子目线，这里只做非子目的 648 对（同题同著者 26、一侧无著者 544、双无著者 78）。
- 判法：4 份并行逐对初判（口径 00-通用口径与门禁 第一节 + 部分 4 判定），并 47 对；另一个复核员对 47 对 100% 独立从严复核，维持 28 对。其中 4 对已被别的线并过，2 对与已判 D 存疑冲突、1 对卷数凭推断，剔掉，落 b-01 共 20 组。
- 全部 648 对的结论登记在 `../dedup-judged/国書线索.tsv`（C 分立 352、D 存疑 276、并 20）。
- 跑法：`run_batch.sh b-01 <分支>`（从最新 main 重放，含 postfix_common、update_index、fix_draft 与全部门禁）。

## Work 漏著者补著者（authors-01）

国書／内閣／NDL 挂接复核与盲检里判「Work 漏著者」（馆藏本另题注、编、评、辑者，Work 著者栏没有）的 294 行，跟 merged_into 后落到 196 个 Work（去掉占用与开放 PR 的剩 194 个）。5 个子 agent 逐个核：**只有 Work 自己的著录（indexed_by 的 author_info／summary）明文写到此人是本书责任者才补**，只见于馆藏一方的、只是校订／训点／序跋的、注本评本对原书的，一律不补。初判补 81 个 Work；再机械剔掉「Work 有多条带著者著录、其中有一条没写此人」的 13 个（防止把某个注本条目的注者错加到原书 Work 上），并手剔 3 个（徐無黨／劉孝標两条原书通行注、陰中夫姓氏系推断），落 67 个 Work、74 人次。

`add_authors.py`：只在 authors 末尾追加（原有「佚名」占位去掉），不挂 entity_id（留给 2.2续／2.3 从 main 重跑），revision 升 minor，ai_note 加【馆藏线索补著者】一行；台账 `authors-01/applied.json`，判定表 `authors-01/plan.tsv`（第一列为「核补文件-序号」）。
