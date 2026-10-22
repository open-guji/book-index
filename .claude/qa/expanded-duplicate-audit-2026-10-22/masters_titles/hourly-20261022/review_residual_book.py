from pathlib import Path
import subprocess,json,hashlib
out=Path(__file__).resolve().parent
ref='origin/main';sha=subprocess.check_output(['git','rev-parse',ref],text=True).strip()
ids={'Book':['993avdq3up','9954l761oh'],'Work':['d59f2hnysjr6','d59fxry7f9xc']};records=[]
for kind,items in ids.items():
 for i in items:
  folder=kind+'/'+ '/'.join(i[-3:]); paths=subprocess.check_output(['git','-c','core.quotePath=false','ls-tree','-r','--name-only',ref,folder],text=True).splitlines();p=next(p for p in paths if i in p)
  b=subprocess.check_output(['git','show',ref+':'+p]);records.append({'id':i,'path':p,'sha256':hashlib.sha256(b).hexdigest(),'record':json.loads(b)})
rulepath='.claude/qa/正式库并条审查规则.md';rule=subprocess.check_output(['git','show',ref+':'+rulepath])
ledgerpath='.claude/qa/reports/duplicate-audit-2026-10-21/merges.json';ledgerbytes=subprocess.check_output(['git','show',ref+':'+ledgerpath]);ledger=json.loads(ledgerbytes)
by={r['id']:r['record'] for r in records};a=by['993avdq3up'];b=by['9954l761oh'];diff={k:{'993avdq3up':a.get(k),'9954l761oh':b.get(k)} for k in a.keys()|b.keys() if a.get(k)!=b.get(k)}
x={'case_id':'BOOK-0010-residual-review','review_date':'2026-10-22','base_ref':ref,'base_commit':sha,'status':'open','disposition':'defer_do_not_merge','proposed_old_relation':{'loser':'993avdq3up','keeper':'9954l761oh'},'records':records,'source_rules':{'path':rulepath,'sha256':hashlib.sha256(rule).hexdigest(),'relevant_text':'不并：外部标识矛盾而无法解释的、一侧挂文章 Work 另一侧挂碑刻 Work 的（如 BOOK-0010）。'},'upstream_ledger':{'path':ledgerpath,'sha256':hashlib.sha256(ledgerbytes).hexdigest(),'deferred':ledger['deferred'].get('BOOK-0010')},'book_field_differences':diff,'positive_identity_evidence':{'same_instance':'weihm5fjpthkojsa','same_item':'mitttw8ez0uzzu7t','same_title':a['title']==b['title'],'same_edition':a['edition']==b['edition'],'same_publication_info':a['publication_info']==b['publication_info'],'same_indexed_by':a['indexed_by']==b['indexed_by'],'same_provenance':a['provenance']==b['provenance']},'blocking_model_conflict':{'article_work':'d59f2hnysjr6','article_evidence':'subtype=article; author role=作; 維基文庫文本及collected_in文集關係。','calligraphy_work':'d59fxry7f9xc','calligraphy_evidence':'總目子部/藝術類/書畫之屬/書；author_info宋歐陽修書；版本1911影印明拓本。','effect_of_old_merge':'Book.work_id為Work↔Book唯一存儲側。保留9954的article work_id並將993設墓碑，會消除書法Work的有效版本入口；keeper原值不變不等於未作建模選擇。'},'old_note_assessment':'E3第803批ai_note只記早先同題同作者導入與掛接推論，不是獨立書影/目錄核對或明確模型裁決；其結論恰為待裁事項，不能以它循環回證。','safe_action':'本次重做PR不保留這個merge；維持最新main兩活躍Book與兩Work，將案例列待核。','next_steps':['以原instance及館藏書影核定版本作為文章文本版本、書法作品版本，或庫模型需雙層關係。','依schema確定唯一work_id及文章/書法Work之明確關係，記錄可重現書目依據或專案建模裁決。','裁決後再決定同instance Book的keeper、引用與派生索引；不先用墓碑固定有爭議的歸屬。'],'native_data_modified':False,'git_modified':False,'merge_authorized_by_review':False}
(out/'residual-book-review.json').write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
print('base',sha,'diff fields',list(diff),'deferred',ledger['deferred'].get('BOOK-0010'))
