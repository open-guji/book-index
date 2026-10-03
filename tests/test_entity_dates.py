"""S4 新 schema 吸收④：Entity.dates 迁移与校验的回归（overview#143）。

覆盖三件：
  1. migrate_dates.plan_dates() 的判断逻辑（机械迁移／floruit 补入／跳过）。
  2. migrate_dates 对临时假仓的真实读写（jio.ROOT monkeypatch，仿 test_entity_merge.py）。
  3. verify.py 的 dates_ok() 校验（整数、birth<=death、floruit 起<=止、与 birth_year/death_year 一致）。
"""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '.claude', 'qa'))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), '.claude', 'qa', 's4'))

import jio
import migrate_dates
import verify


# ---------- plan_dates() ----------

def test_plan_dates_mechanical_both():
    d = {'birth_year': 1077, 'death_year': 1144}
    assert migrate_dates.plan_dates(d) == {
        'birth': 1077, 'death': 1144, 'floruit': None, 'basis': '現行字段',
    }


def test_plan_dates_mechanical_birth_only():
    d = {'birth_year': 1077}
    out = migrate_dates.plan_dates(d)
    assert out == {'birth': 1077, 'death': None, 'floruit': None, 'basis': '現行字段'}


def test_plan_dates_mechanical_death_only():
    d = {'death_year': 1144}
    out = migrate_dates.plan_dates(d)
    assert out == {'birth': None, 'death': 1144, 'floruit': None, 'basis': '現行字段'}


def test_plan_dates_negative_year_bce_preserved():
    """公元前用负数：机械迁移原样搬运，不做符号变换。"""
    d = {'birth_year': -145, 'death_year': -86}
    out = migrate_dates.plan_dates(d)
    assert out['birth'] == -145 and out['death'] == -86


def test_plan_dates_floruit_from_index_year():
    d = {
        'external_ids': {'cbdb_id': 3670},
        'dynasty_basis': 'cbdb:index_year=1019→北宋',
    }
    out = migrate_dates.plan_dates(d)
    assert out == {'birth': None, 'death': None, 'floruit': [1019, 1019], 'basis': 'cbdb:index_year'}


def test_plan_dates_no_cbdb_no_dates_field():
    """无 birth_year/death_year，也无 cbdb_id：无可迁移之资料。"""
    d = {'dynasty': '宋'}
    assert migrate_dates.plan_dates(d) is None


def test_plan_dates_cbdb_present_but_no_index_year_in_basis():
    """有 cbdb_id 但 dynasty_basis 不含 index_year：取不到旁证，不补。"""
    d = {'external_ids': {'cbdb_id': 123}, 'dynasty_basis': 'CBDB 123 c_dy=24（2026-09-06 CBDB enrich）'}
    assert migrate_dates.plan_dates(d) is None


def test_plan_dates_skips_when_dates_already_present():
    d = {'birth_year': 1, 'dates': {'birth': 1, 'death': None, 'floruit': None, 'basis': '現行字段'}}
    assert migrate_dates.plan_dates(d) is None


def test_plan_dates_skips_when_birth_after_death_in_legacy_fields():
    """既存壞資料（生年晚於卒年）不该被机械复制进 dates（回归：hixhd2h9bib6／劉俊）。"""
    d = {'birth_year': 1425, 'death_year': 1408}
    assert migrate_dates.plan_dates(d) is None


def test_plan_dates_birth_death_take_priority_over_floruit():
    """生卒与 cbdb_id 同时存在时走机械迁移，不补 floruit（birth/death 与 floruit 不共存）。"""
    d = {
        'birth_year': 1142, 'death_year': 1219,
        'external_ids': {'cbdb_id': 92982},
        'dynasty_basis': 'cbdb:index_year=1180→唐',
    }
    out = migrate_dates.plan_dates(d)
    assert out['basis'] == '現行字段' and out['floruit'] is None


# ---------- migrate on a temp fake repo ----------

def _write(root, rel, data):
    p = os.path.join(root, rel)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, 'w', encoding='utf-8') as f:
        f.write(json.dumps(data, ensure_ascii=False, indent=2) + '\n')


def test_migrate_writes_dates_and_keeps_birth_year(monkeypatch):
    tmp = tempfile.mkdtemp(prefix='migrate_dates_test_')
    eid = 'zzztestent01'
    rel = f'Entity/{eid[-3]}/{eid[-2]}/{eid[-1]}/{eid}-測試.json'
    _write(tmp, rel, {'id': eid, 'type': 'entity', 'birth_year': 1000, 'death_year': 1066})
    os.makedirs(os.path.join(tmp, 'index', 'entities'))
    _write(tmp, 'index/entities/z.json', {eid: {'path': rel}})

    monkeypatch.setattr(jio, 'ROOT', tmp)
    n_mech = n_floruit = 0
    for eid2, dates in _run_migrate_collect(tmp):
        pass

    d = json.load(open(os.path.join(tmp, rel), encoding='utf-8'))
    assert d['dates'] == {'birth': 1000, 'death': 1066, 'floruit': None, 'basis': '現行字段'}
    assert d['birth_year'] == 1000 and d['death_year'] == 1066, 'birth_year／death_year 须原样保留，不删'

    # 冪等：再跑一次不应改动（已有 dates 即跳过）
    before = open(os.path.join(tmp, rel), encoding='utf-8').read()
    for eid2, dates in _run_migrate_collect(tmp):
        pass
    after = open(os.path.join(tmp, rel), encoding='utf-8').read()
    assert before == after, '已有 dates 的记录重跑应保持不变（冪等）'


def _run_migrate_collect(tmp):
    """跑一遍 iter_entity_rels + plan_dates + 落盘，回传本轮实际写入的 (eid, dates) 列表。"""
    out = []
    for eid, rel in migrate_dates.iter_entity_rels():
        d, fmt = jio.load(rel)
        dates = migrate_dates.plan_dates(d)
        if dates is None:
            continue
        d['dates'] = dates
        jio.save(rel, d, fmt)
        out.append((eid, dates))
    return out


def test_migrate_leaves_real_repo_untouched(monkeypatch):
    """monkeypatch jio.ROOT 后跑迁移，不应碰到真仓（回归：D1 那类补丁不彻底的坑）。"""
    real_root = os.path.dirname(HERE)
    assert os.path.isdir(os.path.join(real_root, '.git')), '须在真 book-index 仓下跑'

    tmp = tempfile.mkdtemp(prefix='migrate_dates_isolation_')
    eid = 'zzzisoent002'
    rel = f'Entity/{eid[-3]}/{eid[-2]}/{eid[-1]}/{eid}-測試.json'
    _write(tmp, rel, {'id': eid, 'type': 'entity', 'birth_year': 1})
    os.makedirs(os.path.join(tmp, 'index', 'entities'))
    _write(tmp, 'index/entities/z.json', {eid: {'path': rel}})

    monkeypatch.setattr(jio, 'ROOT', tmp)
    _run_migrate_collect(tmp)

    import subprocess
    out = subprocess.run(['git', 'status', '--porcelain'], cwd=real_root,
                          capture_output=True, text=True, check=True)
    assert 'zzzisoent002' not in out.stdout


# ---------- verify.py dates_ok() ----------

def test_dates_ok_none_when_no_dates_field():
    assert verify.dates_ok({}) is None


def test_dates_ok_accepts_valid_dates():
    assert verify.dates_ok({'dates': {'birth': 1000, 'death': 1066, 'floruit': None, 'basis': '現行字段'}}) is None


def test_dates_ok_accepts_valid_floruit():
    assert verify.dates_ok({'dates': {'birth': None, 'death': None, 'floruit': [1019, 1019], 'basis': 'cbdb:index_year'}}) is None


def test_dates_ok_rejects_non_integer():
    err = verify.dates_ok({'dates': {'birth': '1000', 'death': None, 'floruit': None, 'basis': 'x'}})
    assert err is not None and 'birth' in err


def test_dates_ok_rejects_birth_after_death():
    err = verify.dates_ok({'dates': {'birth': 1100, 'death': 1000, 'floruit': None, 'basis': 'x'}})
    assert err is not None and 'birth > death' in err


def test_dates_ok_rejects_floruit_start_after_end():
    err = verify.dates_ok({'dates': {'birth': None, 'death': None, 'floruit': [1100, 1000], 'basis': 'x'}})
    assert err is not None and '起 > 止' in err


def test_dates_ok_rejects_floruit_wrong_shape():
    err = verify.dates_ok({'dates': {'birth': None, 'death': None, 'floruit': [1000], 'basis': 'x'}})
    assert err is not None


def test_dates_ok_rejects_inconsistency_with_legacy_fields():
    d = {'birth_year': 1000, 'dates': {'birth': 999, 'death': None, 'floruit': None, 'basis': '現行字段'}}
    err = verify.dates_ok(d)
    assert err is not None and '不一致' in err


def test_dates_ok_consistent_with_legacy_fields_passes():
    d = {'birth_year': 1000, 'death_year': 1066,
         'dates': {'birth': 1000, 'death': 1066, 'floruit': None, 'basis': '現行字段'}}
    assert verify.dates_ok(d) is None


def test_dates_ok_allows_negative_bce_years():
    assert verify.dates_ok({'dates': {'birth': -145, 'death': -86, 'floruit': None, 'basis': '現行字段'}}) is None
