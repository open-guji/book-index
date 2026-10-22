#!/usr/bin/env python3
"""Rebuild this research-only report metadata from pinned raw snapshots; no native writes."""
from pathlib import Path
import json,hashlib
OUT=Path(__file__).resolve().parent
SHA='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
def read(n):return json.loads((OUT/n).read_text())
def write(n,x):(OUT/n).write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
rows=read('current-records.json')['records']+read('title-neighborhood-records.json')['records']
by={r['record']['id']:r for r in rows}
for r in rows:
 b=r['raw_text'].encode();assert hashlib.sha256(b).hexdigest()==r['sha256'];assert hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest()==r['git_blob']

def member(i):return {k:v for k,v in by[i].items() if k not in ('record','raw_text')}|{'id':i}
def fields(i):
 r=by[i]['record'];decisions={'schema_version':'不改schema；本輪研究未寫原生資料','id':'原ID仍為活動Work；不作墓碑','type':'Work粒度；不能以同題直接合Book','title':'保留原題；相同題名不足排除不同輯本','authors':'佚名／空值不能作同一責任者證據；不得從序作者推作撰者','indexed_by':'所有原著錄及分類、版本、館藏提示逐項保留；空版本不自動填充','ai_note':'保留生成來源串及原auto-split理由；不把自動判語當獨立書誌證據','revision':'未改','revised_at':'未改；不是內容身份證據','related_works':'關聯不等於同一；若將來並入關聯對象，須顯式處理自邊且保留舊邊台帳'}
 return {k:{'value':v,'decision':decisions.get(k,'保留；未授權原生修訂')} for k,v in r.items()}
base={'type':'Work','status':'open','verdict':'open','upstream_sha':SHA,'implemented':False,'merge_eligible':False,'keeper':None,'losers':[],'review_depth':'pinned_native_records_field_audit_and_primary_source_review'}
c1=base|{'case_id':'H-1900-001','supersedes_case_id':'H-C010','title':'公門不費錢功德錄：兩項漂移與叢書子目範圍','members':[member(i) for i in ['d59fz73hih34','d59fym9z61hc']],
'reason':'兩個候選核心著錄未變，漂移只新增向候選另一成員的related邊。版本不明的n2htu6i0tvy33r07仍無母叢書或序跋可定位，不能僅憑同題一卷、清佚名確認全組。同題鄰域另有天壤閣二條及叢書集成一條，已取得具體叢書關係和天壤閣原典書影，但不擴大為整題名合併。',
'evidence':[{'kind':'pinned_native_drift','locator':'upstream-drift-review.json[0]','fact':'d59fym9z61hc僅related_works追加d59fz73hih34；原指向甘峻卿輯本之邊本就存在。'}, {'kind':'pinned_native_book','ids':['994q45lxxc','99459zupkx','9945a05y4g'],'fact':'前者edition空、無contained_in，源n2htu6i0tvy33r07；後二者分別天壤閣叢書本和叢書集成初編本。館藏與版本不能互補成未有證據的單一版本。'}, {'kind':'pinned_native_title_neighborhood','ids':['d59fyh7lgetd','d59fyi36ap6q','d59fy3pv9gjk'],'fact':'三Work分屬天壤閣叢書二十種增刊六種、天壤閣叢書二十種、叢書集成初編四千一百七種；都有相應Book/contained_in，不是原H-C010兩成員。'}, {'kind':'external_primary_catalogue_and_scanned_prefaces','reference_ids':['EXT-1900-G1','EXT-1900-G2'],'fact':'東京大學目錄以明刑弼教錄子目著錄一卷本；PDF第3頁見補刊公門不費錢功德錄序及光緒六年王懿榮署，第14頁版心/刊牌見公門不費錢功德錄與天壤閣叢書。'}],
'field_audit':{i:fields(i) for i in ['d59fz73hih34','d59fym9z61hc']},
'counterevidence_and_resolution':['原相關d59fyna62n0g為甘峻卿輯不費錢功德錄三卷附錄一卷、光緒二十五年津逮樓本；題名少公門但卷數、責任者、刊本均不同，本輪不得當作省題整條合併。','相關邊只是舊判疑，不是定同證據；其note所稱具名/他源不能代替正文核查。','天壤閣叢書子目可形成後續較強候選小組，但不能連帶證明缺版次的d59fz73hih34。','序作者、補刊者與全書撰者須分開，未將王懿榮或序中人物補入authors。'],
'defer_reason':'版本不明成員尚缺能連到天壤閣本的原始目錄層級或卷首；全引用、promotions、草稿、正文資產未做。',
'next_steps':['取得n2htu6i0tvy33r07原始instance母叢書/版次及中科院、上圖藏本卷首，不以館藏名重合代替。','先對天壤閣兩個子目Work及d59fym9z61hc形成範圍明確的候選小組，讀其父Collection，核增刊關係及叢書集成重印說明。','若身份定同，所有contained_in、來源與館藏保留；Book不隨Work自動合併；關聯改指自邊須台帳化處理。']}
c2=base|{'case_id':'H-1900-002','supersedes_case_id':'H-C082','title':'太康地記：說郛節錄、王謨輯本與版本不明條','members':[member(i) for i in ['d59fz73mi9s0','d59fybc8uxvk']],
'reason':'漂移只新增related_works兩邊；讀到王謨輯本的三種版本及直接Book後，原編、節錄、後世輯佚層次已明確需要區分。版本不明的中科院本仍不能確定屬說郛本或王謨輯本。畢沅總序證明古書異名及輯佚歷史，並不證明現存各輯本範圍全等。',
'evidence':[{'kind':'pinned_native_drift','locator':'upstream-drift-review.json[1]','fact':'d59fybc8uxvk新增到王謨輯本d59fymcjka9t和候選d59fz73mi9s0的related邊；其他字段未變。'}, {'kind':'pinned_native_book','ids':['994q3jg3cw','9952lyvjeo'],'fact':'前者源wzd8w3gfe7ng7bfp，版本空、無contained_in；後者源60sfvux3q30wsop5，明記說郛本。'}, {'kind':'pinned_native_related_work','ids':['d59fymcjka9t','9945egx5vk','9945egx5vl','9945eglxc1'],'fact':'王謨角色為輯，原文保有晉□□撰；重訂漢唐地理書鈔、漢唐地理書鈔、漢唐地理書鈔存本三版本不能視為晉原書的無差別複本。'}, {'kind':'external_primary_transcription','reference_id':'EXT-1900-T1','fact':'畢沅乾隆四十九年總序將地志/地記/地理記/土地記視為舊書異稱，同時明言所輯佚文及附錄；只證原書題名沿革與輯本性質。'}],
'field_audit':{i:fields(i) for i in ['d59fz73mi9s0','d59fybc8uxvk']},
'counterevidence_and_resolution':['王謨是清代輯者，不是晉代原撰者；Work作者傳播所得清代斷代不能覆蓋原作時代。','同為一卷不能證明說郛節錄與王謨輯本材料、附錄完全相同。','現有說郛Work已連多個叢書子目Book，有一百卷及一百二十卷不同叢書提示；不把這些版本機械合Book。'],
'diagnostic_changes':[{'id':'9945egx5vl','fields':['edition_type','publication_info'],'issue':'《漢唐地理書鈔》叢書名被拆作抄本、year=漢、抄錄者=唐地理書；原總目只是漢唐地理書鈔本，屬確定解析污染，須另修並保留原串。'}, {'id':'9945eglxc1','fields':['publication_info','ai_note'],'issue':'year=漢、刊刻者=唐地理書同為叢書名誤析；把存本後綴推成後印/補刻亦缺獨立證據。'}],
'defer_reason':'缺版次中科院本未定位；說郛、王謨各本卷首目錄與輯文範圍未逐條比對，不將原作同一等同現行Work全部內容可合。',
'next_steps':['取wzd8w3gfe7ng7bfp原始版本及中科院藏本索書號、母叢書、卷首。','依Book contained_in逐本核說郛版本及材料範圍，再與王謨輯本序跋/目錄比對。','先單獨修復漢唐地理書鈔名稱誤析，保留原author_info的晉撰/清輯層次，不由錯誤publication year推斷書年代。','全引用與book-text資產門檻交根代理；若未通過，不作keeper或刪ID。']}
write('cases.json',[c1,c2])
write('validation.json',{'upstream_sha':SHA,'snapshot_records':len(rows),'native_work_records':sum(r['record']['type']=='work' for r in rows),'native_book_records':sum(r['record']['type']=='book' for r in rows),'sha256_and_git_blob_recomputed':True,'title_neighborhood_unread':0,'drift_records_fully_read':2,'case_ids':['H-1900-001','H-1900-002'],'superseded_case_ids':['H-C010','H-C082'],'effective_count_delta':{'confirmed':0,'separate':0,'open':0},'effective_history_counts_after':{'confirmed':9,'separate':3,'open':101,'total':113},'implemented_merges':0,'coverage_boundary':'fixed-title tree neighborhood only, not global reference audit; no native changes or post-write schema/builder runs','review_rules_read':'.claude/qa/正式库并条审查规则.md at pinned main'})
