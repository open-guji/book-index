#!/usr/bin/env python3
"""Refresh only affected Entity entries using the official builder projection/writer.
A full index refresh would incorporate pre-existing main drift unrelated to this batch.
"""
import json,pathlib,sys,subprocess
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT/'build'));import build_derived as B
ledger=json.loads((HERE/'merges.json').read_text());shards={};rows=[]
for rec in ledger['records']:
 typ=rec['path'].split('/')[0];old=rec['before'];new=json.loads((ROOT/rec['path']).read_text())
 if typ!='Entity':
  assert B.index_entry(old,typ,rec['path'])==B.index_entry(new,typ,rec['path'])
  continue
 rel=f"index/entities/{B.shard_of(new['id']):x}.json"
 if rel not in shards:
  raw=(ROOT/rel).read_bytes();subprocess.run(['git','hash-object','-w','--stdin'],input=raw,cwd=ROOT,check=True,stdout=subprocess.DEVNULL);shards[rel]=json.loads(raw)
 before=shards[rel][new['id']];after=B.index_entry(new,typ,rec['path'])
 assert before==B.index_entry(old,typ,rec['path']), 'unexpected prior index drift '+new['id']
 rows.append({'id':new['id'],'path':rel,'before':before,'after':after,'changed':before!=after});shards[rel][new['id']]=after
written=B.write_index(str(ROOT),shards)
(HERE/'index-validation.json').write_text(json.dumps({'official_functions':['index_entry','write_index'],'entries':rows,'files_written':written,'work_projection_unchanged':1},ensure_ascii=False,indent=2)+'\n')
print(json.dumps({'index_files_written':written,'entries_changed':sum(r['changed'] for r in rows)}))
