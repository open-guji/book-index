from pathlib import Path
import json,gzip,collections,hashlib
O=Path(__file__).resolve().parent;R=O.parents[3];cs=json.loads((O/'cases.json').read_text());cl=json.loads((O/'classification-decisions.json').read_text());books=json.load(gzip.open(O/'related-books-before.json.gz','rt'))
changes={'MR-006':('9951cgevwg','关联Book新增张承燮辑，Book contMap 与Work author_info不一致；仅凭同一卷与括注不足排除后人另辑家训，先核正文/目录。'),'MR-019':('993j2647i9','关联Book出现吴金寿编，Work 总目汇总仅列薛雪撰而未体现此层；先核是否另一选编医案，禁止整条吸收。')}
for c in cs:
 if c.get('keeper') and c['type']=='Work':
  c['related_book_ids']=[x['record']['id'] for x in books if x['record']['work_id'] in [c['keeper']]+c['losers']]
  c['own_text_assets']={}
 if c['case_id'] in changes:
  bid,why=changes[c['case_id']];c['status']='open';c['counterreview_reason']=why;c['counterreview_book']=next(x for x in books if x['record']['id']==bid);c.pop('machine_decision',None);cl.pop(c['keeper'],None)
ids={i for c in cs if c['status']=='confirmed' and c['type']=='Work' for i in [c['keeper']]+c['losers']};stats={'baseline_head':'bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca','active_work_scanned':266045,'masters_work_with_source_section':36833,'book_files_scanned':381716,'alias_candidates':98,'cases':len(cs),'decisions':dict(collections.Counter(c['type']+'_'+c['status'] for c in cs)),'confirmed_work_related_books':sum(x['record']['work_id'] in ids for x in books),'all_reviewed_related_books':len(books),'native_data_mutated':False,'book_text_cross_reference_scan_complete':False}
(O/'cases.json').write_text(json.dumps(cs,ensure_ascii=False,indent=2)+'\n');(O/'classification-decisions.json').write_text(json.dumps(cl,ensure_ascii=False,indent=2)+'\n');(O/'stats.json').write_text(json.dumps(stats,ensure_ascii=False,indent=2)+'\n')
# Validate source guards and that IDs are unique across proposed merges.
seen=set()
for c in cs:
 for x in c['records']:assert hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['sha256']
 if c['status']=='confirmed':
  for i in [c['keeper']]+c['losers']:assert i not in seen;seen.add(i)
print(json.dumps(stats,ensure_ascii=False))
