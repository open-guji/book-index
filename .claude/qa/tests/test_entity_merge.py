#!/usr/bin/env python3
"""entity_merge.py 的最小回归。在临时目录里搭一个假仓（keeper／loser 各一个
Entity，一部 Work 指着 loser），跑一次真的 merge()，核三件事：
  1. loser 记录档被删
  2. keeper.merged_in 里能查到 loser
  3. 那部 Work 的 authors[].entity_id 从 loser 改成了 keeper

**monkeypatch 是 monkeypatch `jio.ROOT` 这一个属性**——entity_merge.py 里
所有路径都是即时读 `jio.ROOT`（不在模块顶层缓存成本地变量），所以补丁在
调用 merge() 时才生效即可；这正是 D1 踩过的坑（只改了调用处引用的那个
`ROOT` 局部变量，`jio` 自己那份没跟着变，结果函数内部还是走到了真仓）。

跑法：
    python3 test_entity_merge.py
真跑，不 skip；断言失败就是 AssertionError，退出码非 0。
"""
from __future__ import annotations
import json
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.dirname(HERE))  # 上一层 .claude/qa/，jio.py／entity_merge.py 在那里


def _write(root: str, rel: str, data: dict) -> None:
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def _shard(entity_or_work_id: str) -> str:
    return '/'.join(list(entity_or_work_id[-3:]))


def run() -> None:
    tmp = tempfile.mkdtemp(prefix='entity_merge_test_')
    try:
        keeper_id = 'zzzkeeper01'
        loser_id = 'zzzloser002'
        work_id = 'zzzwork0003'

        keeper_rel = f'Entity/{_shard(keeper_id)}/{keeper_id}-测试正主.json'
        loser_rel = f'Entity/{_shard(loser_id)}/{loser_id}-测试异写.json'
        work_rel = f'Work/{_shard(work_id)}/{work_id}-测试書.json'

        _write(tmp, keeper_rel, {
            'id': keeper_id, 'type': 'entity', 'subtype': 'people',
            'primary_name': '測試正主', 'works': [], 'alt_names': [],
        })
        _write(tmp, loser_rel, {
            'id': loser_id, 'type': 'entity', 'subtype': 'people',
            'primary_name': '測試異寫',
            'works': [{'work_id': work_id, 'role': '撰'}],
            'alt_names': [{'name': '測試字', 'type': '字'}],
        })
        _write(tmp, work_rel, {
            'id': work_id, 'type': 'work', 'title': '測試書',
            'authors': [{'name': '測試異寫', 'role': '撰', 'entity_id': loser_id}],
        })

        # 关键一步：monkeypatch jio.ROOT，让 entity_merge 全部指向临时仓
        import jio
        import entity_merge
        old_root = jio.ROOT
        jio.ROOT = tmp
        try:
            summary = entity_merge.merge(
                loser_id, keeper_id,
                reason='回归测试：验证并条落盘正确', rule='test',
                date='2026-09-26',
            )
        finally:
            jio.ROOT = old_root

        # 1) loser 记录档被删
        assert not os.path.exists(os.path.join(tmp, loser_rel)), \
            f'loser 档应已删除：{loser_rel}'

        # 2) keeper.merged_in 含 loser
        with open(os.path.join(tmp, keeper_rel), encoding='utf-8') as f:
            keeper_after = json.load(f)
        merged_ids = [m.get('id') for m in (keeper_after.get('merged_in') or [])]
        assert loser_id in merged_ids, f'keeper.merged_in 应含 {loser_id}，实际 {merged_ids}'

        # 2b) works[]／alt_names 也应并入
        keeper_wids = {w['work_id'] for w in keeper_after.get('works', [])}
        assert work_id in keeper_wids, 'keeper.works[] 应并入 loser 的 work_id'
        keeper_alt = {a['name'] for a in keeper_after.get('alt_names', [])}
        assert '測試字' in keeper_alt, 'keeper.alt_names 应并入 loser 的別名'

        # 3) Work 的 authors[].entity_id 改繫到 keeper
        with open(os.path.join(tmp, work_rel), encoding='utf-8') as f:
            work_after = json.load(f)
        eids = [a.get('entity_id') for a in work_after.get('authors', [])]
        assert eids == [keeper_id], f'Work.authors[].entity_id 应全部改成 {keeper_id}，实际 {eids}'

        assert summary['redirected_works'] == [work_id]
        assert summary['keeper_stale_works'] == [], \
            'keeper 起始 works=[]，不该报出 stale（这条本身也顺带验证了 verify_ground_truth 无假阳性）'

        print('OK：loser 已删、keeper.merged_in 含 loser、Work 改繫成功、works/alt_names 并入正确')

        # --- 第二段：验 stale-keeper 侦测（2026-09-26 那次真吃过的亏）---
        # 造一个「keeper2」，自己 works[] 写着 work2，但 work2 的 authors[]
        # 其实指着别人（keeper3）——这正是 D4 道第一轮误选 keeper 的现场重现。
        keeper2_id = 'zzzkeepr02'
        keeper3_id = 'zzzkeepr03'
        work2_id = 'zzzwork0004'
        keeper2_rel = f'Entity/{_shard(keeper2_id)}/{keeper2_id}-测试stale.json'
        keeper3_rel = f'Entity/{_shard(keeper3_id)}/{keeper3_id}-测试真主.json'
        work2_rel = f'Work/{_shard(work2_id)}/{work2_id}-测试書二.json'
        _write(tmp, keeper2_rel, {
            'id': keeper2_id, 'type': 'entity', 'subtype': 'people',
            'primary_name': '測試stale', 'works': [{'work_id': work2_id, 'role': '撰'}],
        })
        _write(tmp, keeper3_rel, {
            'id': keeper3_id, 'type': 'entity', 'subtype': 'people',
            'primary_name': '測試真主', 'works': [{'work_id': work2_id, 'role': '撰'}],
        })
        _write(tmp, work2_rel, {
            'id': work2_id, 'type': 'work', 'title': '測試書二',
            'authors': [{'name': '測試真主', 'role': '撰', 'entity_id': keeper3_id}],
        })
        jio.ROOT = tmp
        try:
            stale = entity_merge.verify_ground_truth(
                keeper2_id, [{'work_id': work2_id, 'role': '撰'}])
        finally:
            jio.ROOT = old_root
        assert stale == [work2_id], (
            f'verify_ground_truth 应侦测出 {work2_id} 不反向指回 {keeper2_id}'
            f'（它其实指着 {keeper3_id}），实际返回 {stale}')
        print('OK：verify_ground_truth 正确侦测出 stale 单向边（keeper 自称有此书，书不认账）')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    run()
