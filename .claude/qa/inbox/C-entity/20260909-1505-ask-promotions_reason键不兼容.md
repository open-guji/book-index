# ask：promotions.json 加 reason 键——不会报错，但会被静默吃掉

## 一句话

`PromotionRecord`（`book_index_manager/promotion.py`）是**冻结的三字段
dataclass**（`production_id`／`type`／`promoted_at`），`PromotionsStore.save()`
**每次保存都会把整个 promotions.json 重新过一遍 `from_dict()`→`to_dict()`**——
不只是本进程touch的条目，是磁盘上全部 135,472 条都要经过这个往返。任何条目上
多出的键（包括我要加的 `reason`）在这个往返里**直接消失**，不报错、不留痕迹。

## 证

`promotion.py`：

```python
@dataclass(frozen=True)
class PromotionRecord:
    production_id: str
    type: str
    promoted_at: str

    def to_dict(self) -> dict:
        return {"production_id": ..., "type": ..., "promoted_at": ...}  # 只这三键

    @classmethod
    def from_dict(cls, d: dict) -> "PromotionRecord":
        return cls(production_id=d["production_id"], type=d["type"], promoted_at=d["promoted_at"])
        # 只读这三键，其余的 d[...] 一律不看
```

`PromotionsStore.save()`：

```python
def save(self):
    promotions = self.load()
    merged = self._read_disk()      # ← 把磁盘全档 135,472 条都跑一遍 from_dict()
    for k in self._touched:
        merged[k] = promotions[k] if k in promotions else merged.pop(k, None)
    ...
    sorted_items = {k: merged[k].to_dict() for k in sorted(merged.keys())}  # ← 再跑一遍 to_dict()
    ...
```

`_read_disk()` 对**磁盘上的每一条**（不分是否本次改动）都过一遍
`PromotionRecord.from_dict(rec)`，多余键在这一步就已经读丢；`to_dict()`
再把幸存的三键写回。也就是说：**只要任何一次 `book-index promote` 或任何
调用 `PromotionsStore.save()` 的脚本跑过一次**（哪怕它跟我这批毫无关系，
只是升格了别的东西），**我加的 `reason` 键就会在那一次 save 里被整档抹掉**
——不是"这条被改"，是"重写时这个字段没被读进对象，自然也就没被写出去"。

这不是"多一个键就报错"的那种硬性 schema，是**更隐蔽的一种**：
不报错、看起来一切正常、`reason` 就是消失了。协调者原话"若有任何一处是
严格 schema 校验……立刻停下报我，不要自行改那处代码"——本处虽不报错，
但效果等同（甚至更隐蔽），故先停下不动手，不擅自去改 `PromotionRecord`
（那是 book-index-manager 仓的代码，不在本道写域，改了也影响全项目其它
用这个类的地方）。

**`validate-promotions-fast.py`（另一份更快的校验脚本）与 `redirect-e2e.cjs`
（网站侧 redirect 测试）都只是拿 `json.load()` 当普通 dict 用，没有走
`PromotionRecord`，本身不会因为多一个键报错**——问题专出在 `PromotionsStore`
这一条写入路径上。kaiyuanguji-web 网站侧的打包/读取代码本道拿不到
（不在本道 session 的仓列表里），未能核实，如实告知。

## 建议的默认做法（等裁，未执行）

**不改 `promotions.json` schema。** 把"这是归并而非真升格"的说明改放
production 侧 `merge_history` 条目自己的 `reason` 字段（已经在方案里，
`{"merged_from": draft_id, "primary_name": ..., "date": ..., "reason": "..."}"`
本就带这个字段，且 Entity JSON 文件全库没有类似 `PromotionRecord` 那种
强 schema 往返，这条信息放这里不会被谁的一次保存悄悄冲掉）。

`promotions.json` 仍按现状三键写（`production_id`／`type`／`promoted_at`），
与"真升格"条目在格式上完全一样——**能追问的依据留在 `merge_history` 里，
不留在 `promotions.json` 里**，代价是从 `promotions.json` 本身看不出
一条是升格还是归并，但从 production 侧entity的 `merge_history` 能看出来，
只是查的位置换了一处，不是信息彻底消失。

## 等裁，未执行任何数据改动

第一批（A2 77 条）尚未开始执行——按协调者裁决"开工第一件事是核实兼容性……
若不兼容立刻停下报我"，本道先做完这一步就停在这里，等裁：

1. 认可上面"不改 promotions.json、reason 放 merge_history"的默认做法，直接继续执行；或
2. 另有办法（比如先请另一道去改 `book_index_manager.PromotionRecord` 加第四个可选字段，
   本道等那边改完、发布新版本后再继续）；或
3. 其它安排。
