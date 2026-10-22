from pathlib import Path
import json, sqlite3, hashlib, subprocess
OUT=Path(__file__).parent
ROOT=OUT.parents[1]
BASE='c6dd8356d613fc5614beb88f0a61a3d04cfb069e'
def save(n,v): (OUT/n).write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def source(sid,title,url,pointer,excerpt,kind='primary_text_transcription'):
    v=dict(source_id=sid,title=title,url=url,pointer=pointer,excerpt=excerpt,accessed='2026-10-22',kind=kind,excerpt_sha256=hashlib.sha256(excerpt.encode()).hexdigest(),archive_scope='short reviewed excerpt, not full page or facsimile')
    save('sources/'+sid+'.json',v)
    return v
sources=[
source('S01','釋氏要覽自序','https://www.shidianguji.com/zh/book/JDLS0016/chapter/1ll6f254wb8lb','turn38view1 L8–10','錢唐月輪山居講經論賜紫沙門釋道誠編集'),
source('S02','宋史藝文志道家附釋氏','https://www.xuoda.com/ls/songshi/2559.htm','turn48view2 L283–284','僧道誠《釋氏須知》三卷；僧道誠《釋氏要覽》三卷'),
source('S03','DILA 人名規範 A001542','https://authority.dila.edu.tw/person/search.php?aid=A001542','turn30view3 L4–43；慧悟大師、三著作、CBDB與Wikidata對照','道誠；慧悟大師；《尼蒙求》一卷 (遺失)','institutional_authority_record'),
source('S04','清史稿卷148方外','https://zh.wikisource.org/zh-hant/清史稿/卷148','turn48view0 L153','冬關詩鈔六卷。通復撰。'),
source('S05','四庫全書總目提要卷181冬關詩鈔','https://zh.wikisource.org/wiki/四庫全書總目提要/卷181','turn40view3 L643–647','國朝釋通複撰。通複字文可，嘉興人。'),
source('S06','冬關詩鈔卷一','https://www.shidianguji.com/zh/book/CADAL02066038/chapter/1lalk20us4t1l','turn38view3 L6–8','冬關詩鈔卷一；嘉禾釋通復文可著。同里盛遠宜山輯'),
source('S07','金山志略緣起','https://www.shidianguji.com/zh/book/HY0162/chapter/1k2kgkqhc4h7f','turn34view3 L6末署；前文自記箬菴問和尚及清初進山繼席','峕大清康熙二十年歲次辛酉月朔曰，嗣臨濟正宗圜祖第二十一代孫行海撰。'),
source('S08','佛祖統紀卷18','https://deerpark.app/cbeta/T2035/18','turn47view0 L61–77；CBETA轉錄的法嗣名目，非完整行海傳','佛光照法師法嗣南屏下第七世；雪岑行海法師'),
source('S09','DILA 人名規範 A013860','https://authority.dila.edu.tw/person/search.php?aid=A013860','turn46view1 L8–27；南宋、佛光法照、雪岑集','雪岑行海；咸淳三年（1267）住嘉興先福寺。','institutional_authority_record'),
source('S10','CiNii 雪岑和尚續集','https://ci.nii.ac.jp/ncid/BB12786436','turn46view2 L135–137、225；作者與所影印本年代','(宋釋) 行海撰；「雪岑和尚續集」: 江戸寛文5年(1665)刊本影印','institutional_catalogue'),
source('S11','開元釋教錄卷六','https://zh.wikisource.org/zh-hant/開元釋教録_(四庫全書本)/卷06','turn45view0 L232–236；大吉義二卷或四卷、浄度一卷及同一譯者傳','大吉義神咒經二卷；浄度三昧經一卷；沙門釋曇曜未詳何許人也')]
specs=[
('001','釋道誠／僧道誠','PRV-B-C11961','confirmed',['S01','S02','S03'],'宋志兩書同署僧道誠，《釋氏要覽》自序署錢唐月輪山釋道誠並有天禧紀年；規範庫明確連接慧悟大師、尼蒙求、釋氏須知、要覽以及當前CBDB53758/Wikidata Q45679936。兩條所代表人物同一，不是僅去僧/釋前綴。','hixhd2h9bikf',['hixhd2h9boyw'],'保留慧悟大師、CBDB manual及其pending_accept來源字串、錢塘地名引用、原ai_note/管理歷史；不把原宋志name_basis歷史中的舊ID改寫。兩部Work仍分立；其撰/集責任表述另核，不藉人物並條默改。'),
('002','通復／釋通復','PRV-B-C11981','confirmed',['S04','S05','S06'],'清史稿方外列冬關詩鈔六卷通復，四庫同題六卷署釋通複字文可，原集卷首署嘉禾釋通復文可、盛遠輯。通復Entity所繫唯一Work原始indexed_by就是該清史稿條，因此可識別同人；現題傳經室賦是獨立題名污染。','hixhd2h9bk0g',['hixhd2h9biq8'],'先核d59f2nukva4h從冬關詩鈔改為傳經室賦的原變更來源；不得將傳經室賦當作通復真著述傳播。冬關詩草稿本與詩鈔刻本的作品範圍未證相同，不合併Work。通復/通複異體要保留原著錄形式。'),
('003','清釋行海／宋釋行海','PRV-B-C11992','separate',['S07','S08','S09','S10'],'金山志略緣起由清康熙二十年行海自署臨濟圜祖第二十一代孫，並自敘清初金山繼席。佛祖統紀所列雪岑行海是佛光照法嗣，機構規範及雪岑集書目明繫南宋。年代、師承、著作均分立；寬文1665是宋集刊本年代，不是作者生存朝代。',None,[],'保留兩人物和各自Work作者邊；可另補號/師承來源以防再撞，但不把清行海改成宋。雪岑集自序與NDL原影像本輪未取到，未宣稱直接讀過其自序。'),
('004','曇曜／釋曇曜','PRV-B-C12760','confirmed',['S11'],'開元錄在同一沙門釋曇曜條直接列大吉義神咒經二卷或四卷、浄度三昧經一卷，並繫和平三年北臺譯事，與兩Entity各自補魏書來源及兩Work一一對合。釋是前綴，昭玄統是此人的職稱。','hixhjhaxs4qo',['hixhjhaw7y0y'],'兩Work現role撰與來源譯本不符，需另署源修正；大吉義二/四卷差別需保留各來源。淨度為一卷第四譯且闕，不與其他譯者二/三卷本、北台淨度三昧經機械併書；也不將吉迦夜替換為曇曜。')]
c=sqlite3.connect('file:/workspace/scratch/0bc7226fa660/audit/broad-current.sqlite?mode=ro',uri=True);c.row_factory=sqlite3.Row
manifest=json.loads(c.execute("select value from metadata where key='manifest'").fetchone()[0]);assert manifest['base']==BASE and manifest['errors']==[]
candidates=json.loads((OUT.parent/'broad-20261022/candidates.json').read_text());bycid={v['candidate_id']:v for v in candidates}
cases=[];ids=set()
for num,label,cid,status,ss,why,keeper,losers,gate in specs:
    ca=bycid[cid];assert not ca['prior_case_ids'];ids.update(ca['ids'])
    cases.append(dict(case_id='PRV-2022-'+num,type='people',group=label,status=status,new_case=True,candidate_ids=[cid],ids=ca['ids'],source_ids=ss,decision=why,keeper_candidate=keeper,loser_candidates=losers,remaining_gates=[gate,'Execution requires fresh-main hashes, full native types/classification/promotions/drafts and nonempty 16-shard book-text references, lossless person field ledger and actual post-write schema/check_v2/classification/official-index/builder plus T/L/P/R validation.'],native_merge_count=0))
prior=[];prior_files=[]
for p in ROOT.rglob('cases*.json'):
    if OUT in p.parents or 'broad-' in str(p):continue
    prior_files.append(str(p.relative_to(ROOT)))
    try:v=json.loads(p.read_text())
    except ValueError:continue
    def check(v):
        if isinstance(v,dict):
            if 'case_id' in v and any(i in json.dumps(v,ensure_ascii=False) for i in ids): prior.append(dict(file=str(p.relative_to(ROOT)),case_id=v['case_id']))
            else:
                for w in v.values():check(w)
        elif isinstance(v,list):
            for w in v:check(w)
    check(v)
assert not prior,prior
rows={};refs=[]
def walk(v,p=''):
    if isinstance(v,dict):
        for k,w in v.items():yield from walk(w,p+'/'+k.replace('~','~0').replace('/','~1'))
    elif isinstance(v,list):
        for j,w in enumerate(v):yield from walk(w,p+'/'+str(j))
    elif isinstance(v,str):
        for i in ids:
            if v==i:yield dict(pointer=p,target=i,match='exact')
            elif i in v:yield dict(pointer=p,target=i,match='embedded_text')
for r in c.execute('select * from records'):
    if r['id'] in ids or any(i in r['data'] for i in ids):
        r=dict(r);rows[r['id']]=r
        if r['id'] not in ids:
            d=json.loads(r['data']);refs.append(dict(id=r['id'],type=r['type'],name=r['name'],path=r['path'],inactive=bool(d.get('merged_into') or d.get('retired')),hits=list(walk(d))))
checks=[]
for r in rows.values():
    raw=r['data'].encode();sha=hashlib.sha256(raw).hexdigest();blob=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    assert sha==r['sha256'] and blob==r['blob_sha']
    actual=subprocess.run(['git','show',BASE+':'+r['path']],check=True,capture_output=True).stdout
    assert actual==raw
    dest=OUT/'snapshots'/(r['id']+'.json');dest.write_bytes(raw)
    r['data']=json.loads(r['data']);r['raw_snapshot']='snapshots/'+dest.name
    checks.append(dict(id=r['id'],path=r['path'],sha256=sha,blob_sha=blob,exact_git_show_bytes_match=True))
for ca in cases:
    ca['records']=[{k:rows[i][k] for k in ['id','name','path','sha256','blob_sha','raw_snapshot']} for i in ca['ids']]
    ca['known_references']=[v for v in refs if any(h['target'] in ca['ids'] for h in v['hits'])]
save('cases.json',cases);save('sources.json',sources);save('source-snapshots.json',dict(base=BASE,source_manifest=manifest,records=list(rows.values())))
save('known-references.json',dict(scope='All records in readonly census: Entity and Work ONLY; no claim about Book/Collection/classification/promotions/draft/book-text',references=refs))
ledger=[]
for i in sorted(ids):
    for k,v in rows[i]['data'].items():ledger.append(dict(entity_id=i,pointer='/'+k,before=v,disposition='preserve_or_archive_exact_before_any_future_merge',snapshot=rows[i]['raw_snapshot']))
save('field-ledger.json',dict(executable=False,scope='All top-level pre-change values for 8 people; no after-values, no merge executed',rows=ledger))
save('validation.json',dict(base=BASE,new_groups=4,confirmed=3,separate=1,open=0,native_merge_count=0,snapshot_count=len(rows),entity_count=8,related_record_count=len(refs),exact_bytes_checks=checks,prior_cases_checked_files=prior_files,prior_matches=prior,coverage=manifest['stats'],full_crossrepo_validation=False,native_postwrite_checks='not_run_no_native_changes',scope_restrictions=['Only this hourly output directory written','No git index/branch/native data mutation','No old1876 map','BOOK-0010 deferred','No PR1216 people, no Feng, no Minghuang proposal']))
print(json.dumps(dict(groups=4,confirmed=3,separate=1,open=0,snapshots=len(rows),refs=len(refs),ledger_rows=len(ledger)),ensure_ascii=False))
