#!/usr/bin/env python3
"""production 内部并 Entity（两侧都已是 production 记录，没有 draft 侧的场合）。

D4-Entity清账道（2026-09-26）写：draft 仓（book-index-draft）已于 09-14 清空、
promotions.json 亦空之后，本项目「entity 重出待併」这一类活就只剩这一种形状——
不再是「draft 升格顺带并入 production」（那条路走 book-index-manager 的
promote + merged_from/_promoted_to，见 C-entity-併條执行 先例），而是
**两个都已经在 production 里的 Entity，判定是同一人，把 loser 并进 keeper**。

用法：
    python3 entity_merge.py <loser_id> <keeper_id> --reason "..." [--rule "..."] [--dry]

动作：
  1. 找 loser / keeper 的记录档（按 id 末三字定分片路径的既有规则，
     与 reindex.py 的 misplaced() 同一套算法）。
  2. **先验 ground truth，不信 keeper 自己 `works[]` 写的**：keeper 现有
     `works[]` 里的每一条，去查该 Work 的 `authors[].entity_id` 是否真的指回
     keeper——不是就印一行 WARN（不阻断，因为这未必是本次要并的这条的错，
     但操作者必须看见）。**这条校验是 2026-09-26 用血换来的**：D4 道第一轮
     merge 时选的 4 个「keeper」自己也是 stale 单向边（`works[]` 里写着的
     work 早就被改繫到别人了），名字相同、`works[]` 非空，看着像真作者，
     其实是另一个陈年孤本——第二轮才靠这条校验揪出来，回炉重并了一次。
     判据来自 `verify.py` 的「單向邊」检查同一件事（entity 说它有这本书，
     书不认这个 entity），这里在并之前对 keeper 自己先做一遍。
  3. 全库扫 `Work`／`Book`／`Collection`，把 `authors[].entity_id == loser_id` 的都改成
     `keeper_id`（grep 先筛路径，再逐个精确解析 authors[] 确认命中，避免
     grep 撞见同码但非 entity_id 字段的假阳性）。
  4. **schema-v2（2026-10-07，overview#459 F6-3）起不再写 `Entity.works`**：人物的作品列表
     由 `Work.authors[].entity_id` 反查、build 生成 `_works`，第 3 步改繫即足。
     记录里若还残留旧 `works[]`（迁移后新进的旧格式批），本工具不并、不改，只报。
  5. `keeper.alt_names` 并入 `loser.alt_names`（按 `name` 精确字符串去重，
     不做模糊/异体归并——那是 qa_entity.py 的 NAM02 或人工核查该做的事）。
  6. `keeper.external_ids` 补 `loser` 有而 `keeper` 缺的键（不覆盖 keeper
     已有值）。
  7. `keeper` 加一条 `merged_in` 记录（字段形状仿 `Work.merged_in` 既有先例：
     `id`／`primary_name`／`at`／`by`／`rule`／`why`）。若 `loser` 自己也带着
     更早的 `merged_in`（链式并条：A 先并入 loser，今 loser 再并入 keeper），
     一并搬到 keeper，不许丢账。
  8. `loser` 改写为墓碑（tombstone）：只留 `schema_version`／`id`／`type`／`subtype`／
     `primary_name`／`merged_into`／`revision`／`revised_at`（schema/entity.md〈merged_into〉）。
     **不删档**（2026-10-09 目录经理定，overview#409）：墓碑可逆，旧 id 仍能解析到 keeper。
  9. **不在这里跑 build/verify**——批量跑完这一批之后手动跑
     `python3 build/build_derived.py --write-index` 与
     `python3 .claude/qa/verify.py`，再 `pushmain.sh`。

这不是 `book-index-manager` 的 `promote` 那条路（那条路是 draft→production，
写 `promotions.json`），也不改 SCHEMA.md——「production 内部并 Entity」这个
形状目前没有正式 schema 定义，`merged_in` 只是抄 Work 那边已有的先例，
是否要写进 SCHEMA.md 由协调者另定。

只测过 Entity；不要拿去并 Work／Book／Collection，那几类各有自己的併条工具
（`mergework.py` 等）。
"""
from __future__ import annotations
import argparse
import datetime
import glob
import os
import subprocess
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__))))
import jio  # noqa: E402


def find_path(eid: str) -> str:
    """按 id 末三字定分片路径找记录档，返回相对 jio.ROOT 的路径。"""
    sub = os.path.join('Entity', *list(eid[-3:]))
    hits = glob.glob(os.path.join(jio.ROOT, sub, f'{eid}-*.json'))
    if len(hits) != 1:
        raise SystemExit(f'找不到或有歧义: {eid} in {sub} -> {hits}')
    return os.path.relpath(hits[0], jio.ROOT)


def scan_referencing_works(eid: str):
    """全库找 authors[].entity_id == eid 的 Work。grep 先筛路径（快），
    再逐个精确解析 authors[] 确认命中（grep 只保证字符串命中，可能撞见
    同码但不是 entity_id 字段的假阳性，例如混进了别的字段或 ai_note 正文）。
    返回 [(相对路径, dict, fmt), ...]。"""
    out = subprocess.run(
        ['grep', '-lr', eid] + [os.path.join(jio.ROOT, t) for t in ('Work', 'Book', 'Collection')
                                 if os.path.isdir(os.path.join(jio.ROOT, t))],
        capture_output=True, text=True,
    ).stdout.strip()
    paths = [p for p in out.splitlines() if p]
    hits = []
    for p in paths:
        rel = os.path.relpath(p, jio.ROOT)
        d, fmt = jio.load(rel)
        au = d.get('authors') or []
        if any(isinstance(a, dict) and a.get('entity_id') == eid for a in au):
            hits.append((rel, d, fmt))
    return hits


def verify_ground_truth(entity_id: str, works: list) -> list[str]:
    """keeper 自己 works[] 里的每一条，查真实 Work 档的 authors[].entity_id
    是否指回 entity_id。返回不指回者的 work_id 列表（stale 单向边）。
    这条校验只读不写——发现了要不要现在就治，由调用者判断。"""
    stale = []
    for w in works or []:
        if not isinstance(w, dict) or not w.get('work_id'):
            continue
        wid = w['work_id']
        hits = glob.glob(os.path.join(jio.ROOT, 'Work', *wid[-3:], f'{wid}-*.json'))
        if not hits:
            continue  # 悬空引用是 qa_entity.py 的 WRK05 该管的事，不在本函数职责内
        rel = os.path.relpath(hits[0], jio.ROOT)
        d, _ = jio.load(rel)
        au = d.get('authors') or []
        back_ids = {a.get('entity_id') for a in au if isinstance(a, dict) and a.get('entity_id')}
        if entity_id not in back_ids:
            stale.append(wid)
    return stale


TOMBSTONE_KEYS = ('schema_version', 'id', 'type', 'subtype', 'primary_name',
                  'merged_into', 'revision', 'revised_at')


def tombstone(loser: dict, keeper_id: str, date: str) -> dict:
    """被并方的墓碑：只留 TOMBSTONE_KEYS（schema/entity.md〈merged_into〉）。"""
    t = {'schema_version': loser.get('schema_version', 1), 'id': loser['id'],
         'type': loser.get('type', 'entity')}
    if loser.get('subtype'):
        t['subtype'] = loser['subtype']
    t['primary_name'] = loser.get('primary_name')
    t['merged_into'] = keeper_id
    t['revision'] = loser.get('revision') or '1.0.0'
    t['revised_at'] = date
    return t


def merge(loser_id: str, keeper_id: str, *, reason: str, rule: str = '',
          date: str | None = None, dry: bool = False, by: str = 'D4-Entity清账') -> dict:
    """执行一次 production 内部 Entity 并条。返回一份摘要 dict，供调用者
    （CLI 或测试）核对结果，不打印任何东西——打印是 main() 的事。"""
    date = date or datetime.date.today().isoformat()

    loser_rel = find_path(loser_id)
    keeper_rel = find_path(keeper_id)
    loser, lfmt = jio.load(loser_rel)
    keeper, kfmt = jio.load(keeper_rel)
    if loser.get('merged_into'):
        raise SystemExit(f'{loser_id} 已是墓碑（merged_into={loser["merged_into"]}），不可再并')
    if keeper.get('merged_into'):
        raise SystemExit(f'keeper {keeper_id} 是墓碑（merged_into={keeper["merged_into"]}），请改并入其目标')

    summary = {
        'loser_id': loser_id, 'loser_name': loser.get('primary_name'), 'loser_rel': loser_rel,
        'keeper_id': keeper_id, 'keeper_name': keeper.get('primary_name'), 'keeper_rel': keeper_rel,
        'keeper_stale_works': verify_ground_truth(keeper_id, keeper.get('works')),
        # 旧格式残留（schema-v2 后源档不该有 works）：只报不并
        'legacy_works': {'keeper': len(keeper.get('works') or []), 'loser': len(loser.get('works') or [])},
    }

    # 找出所有指着 loser 的 Work
    refs = scan_referencing_works(loser_id)
    summary['redirected_works'] = [d.get('id') for _, d, _ in refs]

    # works[]：schema-v2 起不写（由 authors 反查），见文首第 4 条
    summary['added_works'] = []

    # alt_names 并入（精确字符串去重）
    keeper_alt_names = {a.get('name') for a in (keeper.get('alt_names') or []) if isinstance(a, dict)}
    added_alts = []
    for a in (loser.get('alt_names') or []):
        if isinstance(a, dict) and a.get('name') not in keeper_alt_names:
            keeper.setdefault('alt_names', []).append(a)
            keeper_alt_names.add(a.get('name'))
            added_alts.append(a.get('name'))
    summary['added_alt_names'] = added_alts

    # external_ids 补缺不覆盖
    filled_ext = []
    lext = loser.get('external_ids') or {}
    kext = keeper.setdefault('external_ids', {}) if lext else keeper.get('external_ids', {})
    for k, v in lext.items():
        if k not in kext or kext.get(k) in (None, ''):
            kext[k] = v
            filled_ext.append(k)
    if lext:
        keeper['external_ids'] = kext
    summary['filled_external_ids'] = filled_ext

    # merged_in 记录（仿 Work.merged_in 先例）——链式并条一并搬过去
    # 幂等：上次中途失败（keeper 已写、墓碑未写）后重跑，不重复记账
    have = {m.get('id') for m in (keeper.get('merged_in') or []) if isinstance(m, dict)}
    chained = [r for r in (loser.get('merged_in') or []) if not (isinstance(r, dict) and r.get('id') in have)]
    for rec in chained:
        keeper.setdefault('merged_in', []).append(rec)
        have.add(rec.get('id') if isinstance(rec, dict) else None)
    summary['chained_merged_in'] = len(chained)
    if loser_id not in have:
        keeper.setdefault('merged_in', []).append({
            'id': loser_id,
            'primary_name': loser.get('primary_name'),
            'at': date,
            'by': by,
            'rule': rule,
            'why': reason,
        })

    summary['dry'] = dry
    if dry:
        return summary

    # 落盘顺序：改繫的 Work → keeper → loser 墓碑。各档原子写（jio.save）；中途失败可原样重跑补完
    # （改繫已完成的不会再命中，keeper.merged_in 去重，最后写墓碑）。
    # 落盘：Work 改繫
    for rel, d, fmt in refs:
        for a in (d.get('authors') or []):
            if isinstance(a, dict) and a.get('entity_id') == loser_id:
                a['entity_id'] = keeper_id
        jio.save(rel, d, fmt)

    # 落盘：keeper
    jio.save(keeper_rel, keeper, kfmt)

    # loser 改写为墓碑（不删档）
    jio.save(loser_rel, tombstone(loser, keeper_id, date), lfmt)
    summary['tombstoned'] = True
    return summary


def _print_summary(s: dict) -> None:
    print(f"loser  {s['loser_id']}  {s['loser_name']}  {s['loser_rel']}")
    print(f"keeper {s['keeper_id']}  {s['keeper_name']}  {s['keeper_rel']}")
    if s['keeper_stale_works']:
        print(f"⚠️  WARN：keeper 自己 works[] 里有 {len(s['keeper_stale_works'])} 条不反向指回 keeper"
              f"（stale 单向边，可能是陈年孤本，不一定是本次要并的这条的错，但请核实）："
              f" {s['keeper_stale_works']}")
    print(f"待改繫 Work：{len(s['redirected_works'])} 部  {s['redirected_works']}")
    lw = s.get('legacy_works') or {}
    if lw.get('keeper') or lw.get('loser'):
        print(f"⚠️  旧格式 works[] 残留（keeper {lw.get('keeper')}、loser {lw.get('loser')} 条）：本工具不并不改，"
              "请先跑迁移（build/migrate_v2.py）或 check_v2.py 查")
    print(f"alt_names 并入新增 {len(s['added_alt_names'])} 条")
    print(f"external_ids 补缺：{s['filled_external_ids']}")
    if s['chained_merged_in']:
        print(f"链式并条：loser 自带 merged_in {s['chained_merged_in']} 条一并搬入 keeper")
    if s['dry']:
        print('--dry：不落盘')
    else:
        print(f"已写墓碑 {s['loser_rel']}（merged_into → {s['keeper_id']}）")
        print('DONE')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('loser_id')
    ap.add_argument('keeper_id')
    ap.add_argument('--reason', required=True)
    ap.add_argument('--rule', default='')
    ap.add_argument('--date', default=None)
    ap.add_argument('--by', default='D4-Entity清账', help='merged_in.by，写并条的道名')
    ap.add_argument('--dry', action='store_true')
    args = ap.parse_args()
    s = merge(args.loser_id, args.keeper_id, reason=args.reason, rule=args.rule,
              date=args.date, dry=args.dry, by=args.by)
    _print_summary(s)


if __name__ == '__main__':
    main()
