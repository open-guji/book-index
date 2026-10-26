#!/usr/bin/env python3
"""早稲田挂接盲检交来的 Work 数据疑误（/mnt/project-files/waseda-a4/Work数据疑误-早稲田盲检.tsv）中有把握者的修正。
用法：apply.py [--apply]"""
import glob, json, os, sys, datetime
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
TODAY = datetime.date.today().isoformat()
SRC = '早稲田挂接盲检（A4）交来疑误，3c 串核'
PER = {'明': 'ming', '清': 'qing', '元': 'liao-jin-yuan'}
# (目錄, id, 作者位改動 {舊名: {欄: 新值 / None 刪}}, 作品朝代或 None, 依據)
OPS = [
    ('Work', 'd59f6eqonpj6', {'申光漢': {'dynasty': '朝鮮'}}, '朝鮮', '申光漢（1484–1555）朝鮮人，千頃堂著錄小注「吏曹判書…議政府左叅贊」係朝鮮官制；原標「元」誤'),
    ('Work', 'd59fy3sdsa2o', {'崔致遠': {'dynasty': '新羅'}}, '新羅', '崔致遠（857–?）新羅人，總目題「唐崔致遠撰」係以在唐所作；原標「清」誤'),
    ('Work', 'd59f2mztdatc', {'楊慎': {'dynasty': '明'}}, '明', '楊慎（1488–1559）明人；原標「清」係清胡蔚增訂本之代'),
    ('Work', 'd59fz050tji9', {'陳齡': {'dynasty': '清'}}, '清', '總目著錄「清陳齡撰」；原撰人朝代「明」誤'),
    ('Work', 'd59fxroa0jy9', {'沈延銓': None}, '元', '總目著錄「元吾丘衍撰；明何震續」，無沈延銓；首位誤混入之沈延銓刪去，作品朝代從吾丘衍'),
    ('Work', 'd59fy1gndgqo', {'嶽飛': {'name': '岳飛', 'original_name': '嶽飛'}}, None, '總目著錄作「宋岳飛撰」，「嶽」為誤寫'),
    ('Work', 'd59fxzfhh7gh', {'潘霨增': {'name': '潘霨', 'original_name': '潘霨增', 'role': '增輯', 'entity_id': 'hixi8u64udqa'}}, None, '「潘霨增」係「潘霨 增輯」拆錯'),
    ('Work', 'd59fyjs9dkao', {'潘霨增': {'name': '潘霨', 'original_name': '潘霨增', 'role': '增輯', 'entity_id': 'hixi8u64udqa'}}, None, '「潘霨增」係「潘霨 增輯」拆錯'),
    ('Work', 'd59fxtzatq80', {'於光華': {'name': '于光華', 'original_name': '於光華'}}, None, '總目著錄作「清于光華編」'),
    ('Work', 'd59f6eteczk2', {'吳仕期': {'dynasty': '明'}}, '明', '總目著錄「明吳仕期輯」，朝代原缺'),
    ('Work', 'd59fy3sx4zr4', {'柳得恭': {'dynasty': '朝鮮'}}, '朝鮮', '總目著錄「朝鮮柳得恭撰」，朝代原缺'),
    ('Work', 'd59fxt117xtt', {'高橋二郎': {'dynasty': '日本'}}, '日本', '總目著錄「日本高橋二郎譯述」，朝代原缺'),
]
for b in ('993hyg632a', '993hyghbls', '99573y3qww', '993wkopog0', '993hygsk5c'):
    OPS.append(('Book', b, {'潘霨增': {'name': '潘霨', 'original_name': '潘霨增', 'role': '增輯', 'entity_id': 'hixi8u64udqa'}}, None, '「潘霨增」係「潘霨 增輯」拆錯'))
apply = '--apply' in sys.argv
for typ, i, aops, wdyn, basis in OPS:
    p = glob.glob(os.path.join(ROOT, typ, i[-3], i[-2], i[-1], i + '-*.json'))[0]
    d = json.load(open(p, encoding='utf-8'))
    log = []
    new = []
    for a in d.get('authors', []):
        if a.get('name') in aops:
            op = aops[a['name']]
            if op is None:
                log.append('刪 authors「%s」' % a['name']); continue
            for k, v in op.items():
                if a.get(k) == v: continue
                if k == 'role' and a.get('role') == v: continue
                if k == 'entity_id' and a.get('entity_id') not in (None, 'hixiclpep14k'): continue
                log.append('%s「%s」→「%s」' % (k, a.get(k, ''), v)); a[k] = v
            a['name_basis' if 'name' in op else 'dynasty_basis'] = '%s：%s' % (SRC, basis)
        new.append(a)
    d['authors'] = new
    if wdyn and d.get('dynasty') != wdyn:
        log.append('作品朝代「%s」→「%s」' % (d.get('dynasty', ''), wdyn))
        d['dynasty'] = wdyn; d['dynasty_basis'] = 'manual：%s：%s' % (SRC, basis)
        if wdyn in PER:
            d['period'] = PER[wdyn]; d['period_basis'] = '據作品朝代「%s」（%s）' % (wdyn, SRC)
        else:
            d.pop('period', None); d.pop('period_basis', None)
    print(typ, i, d.get('title'), '；'.join(log) or '（無改動）')
    if not log or not apply: continue
    r = (d.get('revision') or '1.0.0').split('.'); r[2] = str(int(r[2]) + 1); d['revision'] = '.'.join(r)
    d['revised_at'] = TODAY
    d['ai_note'] = (d.get('ai_note') or '') + '；%s（%s）：%s' % (SRC, TODAY, '；'.join(log))
    with open(p, 'w', encoding='utf-8') as f:
        json.dump(d, f, ensure_ascii=False, indent=2); f.write('\n')
