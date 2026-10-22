#!/usr/bin/env python3
"""Independent narrow checks supplement the official audit's missing Person loss checks."""
import hashlib,json,pathlib
ROOT=pathlib.Path(__file__).resolve().parents[3];HERE=pathlib.Path(__file__).resolve().parent
d=json.loads((HERE/'merges.json').read_text());byid={r['before']['id']:r for r in d['records']};errors=[];checks=0
for r in d['records']:
 actual=json.loads((ROOT/r['path']).read_text());assert actual==r['after'],r['path'];checks+=1
 if r['path'].startswith('Work/'):
  original=json.loads(json.dumps(r['before']));expected=json.loads(json.dumps(actual))
  for au in original.get('authors',[]):
   if au.get('entity_id') in d['mapping']:au['entity_id']=d['mapping'][au['entity_id']]
  assert expected==original,'non-reference Work mutation';checks+=1
for g in d['merges']:
 k=byid[g['keeper']]['after'];kb=byid[g['keeper']]['before'];assert not k.get('merged_into')
 assert k.get('dates')==kb.get('dates'),'unexpected date mutation';checks+=1
 for loser in g['losers']:
  old=byid[loser]['before'];t=byid[loser]['after'];assert t['merged_into']==g['keeper']
  assert old==g['original_records'][loser], 'original owner archive mismatch'
  assert old['primary_name'] in [a['name'] for a in k.get('alt_names',[])]
  assert loser in [x['id'] for x in k['merged_in']]
  for field,value in old.items():
   assert g['original_records'][loser][field]==value
   if field in ('dates','native_place','native_place_entity_id'):assert k.get(field)==value
   if field=='external_ids':
    for key,v in value.items():assert k['external_ids'][key]==v
   if field in ('dynasty_basis','period_basis'):assert value in k[field]
   if field=='description':
    for source in value.get('sources',[]):assert source in k.get('description',{}).get('sources',[])
   checks+=1
  if old.get('ai_note'):assert old['ai_note']==g['original_records'][loser]['ai_note']
 for field,value in kb.items():
  if field in ['id','primary_name','dates','native_place','native_place_entity_id','dynasty','period','updated_at']:assert k[field]==value
  if field=='external_ids':
   for key,v in value.items():assert k[field][key]==v
  if field=='description':
   for source in value.get('sources',[]):assert source in k[field].get('sources',[])
  if field=='ai_note':assert value in k[field]
  checks+=1
res={'pass':True,'checks':checks,'groups':len(d['merges']),'native_files':len(d['records']),'scope':'exact projected records; owner-attributed original preservation; aliases/history; no non-reference Work changes; stable dates/identifiers/sources'}
(HERE/'field-validation.json').write_text(json.dumps(res,ensure_ascii=False,indent=2)+'\n');print(json.dumps(res,ensure_ascii=False))
