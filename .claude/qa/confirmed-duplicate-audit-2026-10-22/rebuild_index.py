import sys,pathlib,json,subprocess,time,collections,argparse,gzip
D=pathlib.Path(__file__).resolve().parent
ap=argparse.ArgumentParser();ap.add_argument('mode',choices=['before','after']);ap.add_argument('--root',required=True,type=pathlib.Path);ap.add_argument('--text-index',required=True,type=pathlib.Path);ap.add_argument('--state-dir',required=True,type=pathlib.Path);args=ap.parse_args();R=args.root.resolve();A=args.state_dir.resolve();A.mkdir(parents=True,exist_ok=True)
sys.path.insert(0,str(R/'build'));import build_derived as B;import v2common as V;import textindex as TX
mode=args.mode;t=time.time();print('loading repository',mode,flush=True)
recs,sidecars,problems=V.load_repo(str(R));assert not problems,problems
print('loaded',round(time.time()-t),flush=True)
cls,cls_problems,_=B.load_classification(str(R));assert not cls_problems,cls_problems;promos=B.load_promotions_all(str(R));ti=TX.load(str(args.text_index));b=B.Build(recs,classification=cls,promotions=promos,text_index=ti)
shards=B.build_index(recs,promos,b)
if mode=='before':
 (A/'expected-index-before.json').write_text(json.dumps(shards,ensure_ascii=False))
 (A/'build-before.json').write_text(json.dumps({'dangling':dict(b.dangling),'dangling_text':b.dangling_text_ids,'source_checks':B.source_checks(recs),'index_drift':B.index_drift(str(R),shards)},ensure_ascii=False,indent=2))
 print('baseline stored',round(time.time()-t),flush=True)
else:
 old=json.loads((A/'expected-index-before.json').read_text());writes={};delta=collections.Counter();preexisting=collections.Counter()
 for rel,expected in shards.items():
  current=json.loads((R/rel).read_text());nxt=dict(current)
  for i,val in expected.items():
   if old[rel].get(i)!=val:
    nxt[i]=val;delta[rel.split('/')[1]]+=1
   elif current.get(i)!=val:preexisting[rel.split('/')[1]]+=1
  if nxt!=current:writes[rel]=dict(sorted(nxt.items()))
 subprocess.run(['git','hash-object','-w','--stdin-paths'],cwd=R,input=''.join(n+'\n' for n in writes).encode(),stdout=subprocess.DEVNULL,check=True)
 B.write_index(str(R),writes)
 import sealindex as SI
 sm,sp,st=SI.derive(((i,r.data) for i,r in recs['Book'].items()),b.R['Entity']);seal_files=SI.files(sm,sp);seal_changes=SI.drift(str(R),seal_files)
 subprocess.run(['git','hash-object','-w','--stdin-paths'],cwd=R,input=''.join(n+'\n' for n,kind in seal_changes if (R/n).exists()).encode(),stdout=subprocess.DEVNULL,check=True)
 SI.write(str(R),seal_files);assert not SI.drift(str(R),seal_files)
 # Native IDs remain resolvable; promoted draft IDs retain their old audit mapping.
 mapping=json.loads((D/'merge-map.json').read_text());plan=json.loads(gzip.decompress((D/'merge-plan.json.gz').read_bytes()))
 failures=[]
 for p in plan:
  for i in p['losers']:
   if b.resolve_live(i)!=p['keeper']:failures.append(['redirect',i])
  if p['type']=='Book':
   target=b.R['Book'][p['keeper']]['work_id']
   if target not in b.R['Work'] or b.R['Work'][target].get('merged_into'):failures.append(['book work',p['keeper'],target])
 text_merges={i:b.resolve_live(i) for i in ti if i in mapping}
 promo_merges={i:v for i,v in promos.items() if v in mapping}
 report={'index_entries_changed':dict(delta),'index_files_changed':list(writes),'preexisting_index_drift_retained':dict(preexisting),'redirect_failures':failures,'merged_ids_in_book_text':text_merges,'promotion_targets_preserved':len(promo_merges),'source_checks':B.source_checks(recs),'dangling':dict(b.dangling),'dangling_text':b.dangling_text_ids}
 (A/'build-after.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
 assert not failures,failures
 print({k:v for k,v in report.items() if k not in ('dangling','dangling_text','source_checks','index_files_changed')},flush=True);print('DONE',round(time.time()-t),flush=True)
