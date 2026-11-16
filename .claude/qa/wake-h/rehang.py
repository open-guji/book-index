# -*- coding: utf-8 -*-
import json, subprocess, os, sys
BI = '/tmp/wk-wake-h3'; QA = BI + '/.claude/qa/wake-h'
wid = json.load(open(QA + '/wid.json'))
P = 'Book/k/g/g/988g1xykgg-逸史日本明治九年大阪懷德堂刊本.json'
fp = os.path.join(BI, P)
if not os.path.exists(fp):
    os.makedirs(os.path.dirname(fp), exist_ok=True)
    open(fp,'wb').write(subprocess.run(['git','-C',BI,'show','origin/main:'+P],check=True,capture_output=True).stdout)
d = json.load(open(fp, encoding='utf-8'))
old = d['work_id']; assert old in ('d59f2moz6nsx', wid['@YISHI'])
if old != wid['@YISHI']:
    d['work_id'] = wid['@YISHI']
    a,b,c=d['revision'].split('.'); d['revision'] = '%s.%s.%d'%(a,b,int(c)+1); d['revised_at'] = '2026-11-15'
    d['ai_note'] = ((d.get('ai_note') or '') + '\n' if d.get('ai_note') else '') + '2026-11-15 和刻本專項第三輪（wake-h）：原誤掛存疑目通俗小說《逸史》(d59f2moz6nsx；褚人穫《隋唐演義》自序所稱袁㯠庵所藏之書)。本條實為日本中井竹山（積善）《逸史》十二卷首一卷之明治九年大阪懷德堂藏版刊本（版心「懷德堂」，故宮著錄十三冊），改掛新建 Work '+wid['@YISHI']+'。與日本館藏明治九年吉田善藏刊本是否同一印次未能定，另見新建 Book，不合併。'
    open(fp, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
print('rehung', P)
