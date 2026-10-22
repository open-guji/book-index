#!/usr/bin/env python3
"""Read pinned Git objects and write only this research directory."""
import collections
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

OUT = Path(__file__).resolve().parent
LANE = OUT.parent
ROOT = LANE.parents[3]
BASE = 'bfaf3cfb3b9b0475fc9fd8d2ce216c291ebc9cca'
HEAD = 'c6dd8356d'

def git(*args):
    return subprocess.check_output(['git', '-c', 'core.quotePath=false', *args], cwd=ROOT, timeout=45)

def write(name, value):
    (OUT/name).write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n')

original = json.loads((LANE/'cases.json').read_text())
hourly = json.loads((LANE/'hourly-20261022/cases.json').read_text())
superseded = {x['supersedes_case_id'] for x in hourly}
effective = [x for x in original if x['case_id'] not in superseded] + hourly
case_by_id = {x['case_id']:x for x in effective}
paths_by_case = {c['case_id']:list(c.get('paths',{}).values())+[m['path'] for m in c.get('members',[])] for c in effective}
paths = sorted({p for ps in paths_by_case.values() for p in ps})

def tree(rev, paths):
    out = git('ls-tree','-r','-z',rev,'--',*paths)
    return {row.split(b'\t',1)[1].decode():row.split(b'\t',1)[0].decode().split()[2] for row in out.split(b'\0') if row}

observed_mode = '--from-observed-comparison' in sys.argv
archive = ROOT.parent/'book-index'
head = 'c6dd8356d613fc5614beb88f0a61a3d04cfb069e' if observed_mode else git('rev-parse',HEAD).decode().strip()
if observed_mode:
    # The successful 2026-10-22 Git-tree comparison covered all 225 paths and
    # returned exactly these two changed blobs. Archive bytes are usable only
    # after matching the inherited SHA256; this does not treat archive HEAD as main.
    hashes={}
    for c in effective:
        hashes.update({p:c['sha256'][i] for i,p in c.get('paths',{}).items()})
        hashes.update({m['path']:m['sha256'] for m in c.get('members',[])})
    before={}
    for p in paths:
        raw=(archive/p).read_bytes()
        assert hashlib.sha256(raw).hexdigest()==hashes[p], 'archive not equivalent: '+p
        before[p]=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    now=dict(before)
    now['Work/1/h/c/d59fym9z61hc-公門不費錢功德錄.json']='6549ed21b77929ad5b918dab79ec5f5e11df82c5'
    now['Work/x/v/k/d59fybc8uxvk-太康地記.json']='d30f5f62ae3d851f90b8c58bf07d7047b67d4b09'
else:
    before, now = tree(BASE,paths), tree(head,paths)
drift = [{'path':p,'baseline_git_blob':before.get(p),'current_git_blob':now.get(p),'case_ids':[k for k,v in paths_by_case.items() if p in v]} for p in paths if before.get(p)!=now.get(p)]
coverage = []
for c in effective:
    cp = paths_by_case[c['case_id']]
    coverage.append({'case_id':c['case_id'],'status':c['status'],'review_depth_inherited':c.get('review_depth','historical_case_review'),
                     'current_paths':[{'path':p,'baseline_git_blob':before.get(p),'current_git_blob':now.get(p),'unchanged':before.get(p)==now.get(p)} for p in cp],
                     'check_kind':'pinned_git_tree_presence_and_blob_comparison; not a new bibliographical review'})

snapshots = []
selected = {}
for cid in ['H-C085','H-C092']:
    selected[cid] = []
    for m in case_by_id[cid]['members']:
        raw = (archive/m['path']).read_bytes() if observed_mode else git('show',head+':'+m['path'])
        assert not observed_mode or before[m['path']]==now[m['path']]
        r = json.loads(raw)
        row = {'id':r['id'],'path':m['path'],'sha256':hashlib.sha256(raw).hexdigest(),'git_blob':now[m['path']],'record':r,'snapshot_method':'archive bytes matched to inherited SHA256 and proven equal by pinned-main Git blob comparison' if observed_mode else 'git show pinned main'}
        snapshots.append(row)
        selected[cid].append({k:v for k,v in row.items() if k!='record'})

drift_records=[]
for d in drift:
    if observed_mode:
        d['content_inspection']='deferred: pinned-main git show timed out; changed blob is known, content not reviewed'
        continue
    try:
        raw=git('show',head+':'+d['path']);r=json.loads(raw)
        oldraw=git('show',BASE+':'+d['path']);old=json.loads(oldraw)
        d.update({'current_sha256':hashlib.sha256(raw).hexdigest(),'merged_into':r.get('merged_into'),'changed_top_level_fields':sorted(k for k in set(old)|set(r) if old.get(k)!=r.get(k))})
        drift_records.append({'path':d['path'],'baseline_record':old,'current_record':r})
    except (subprocess.TimeoutExpired,subprocess.CalledProcessError) as e:
        d['content_inspection']='deferred: '+type(e).__name__

refs = [
 {'reference_id':'EXT-Q1','title':'千頃堂書目卷六，四庫本第16a葉','url':'https://hhl.cnkgraph.com/Book/742/KR2n0010_006','retrieved_on':'2026-10-22','access':'full transcribed page read; linked scan timed out','locator':'WYG0676-0148a.png; web lines 326–335','quote':'晁瑮清丰县志十六卷；周万金内黄县志（俱嘉靖间修）','assessment':'原典轉錄明記卷數，且俱字所繫嘉靖間修提供時代印證；未冒稱目驗書影。'},
 {'reference_id':'EXT-Q2','title':'國圖0584《嘉靖新修清豐縣志》第二冊的公共影像元資料','url':'https://commons.wikimedia.org/wiki/File:NLC892-0584-208769_嘉靖新修清豐縣志_第2冊.pdf','retrieved_on':'2026-10-22','access':'search snippet only','assessment':'元資料列李汝寬、晁瑮纂修；只作輔證，非核讀首卷。'},
 {'reference_id':'EXT-L1','title':'續修龍虎山志卷上','url':'https://www.shidianguji.com/zh/mid-page/7520740202857332782','retrieved_on':'2026-10-22','access':'search snippet only; direct open inaccessible','quote':'元明善輯；張國祥續修；張顯庸仝修','assessment':'支持明代續修責任層次，不足單獨證明兩個Work同範圍。'},
 {'reference_id':'EXT-L2','title':'Collège de France library catalogue: 續修龍虎山志三卷','url':'https://omnia.college-de-france.fr/discovery/fulldisplay/alma990003581050107166/33CDF_INST%3A33CDF_INST','retrieved_on':'2026-10-22','access':'search snippet only; direct open inaccessible','assessment':'館目分列元明善撰、張國祥與張顯庸續撰；未核讀館目全頁。'},
 {'reference_id':'EXT-L3','title':'中國古籍總目檢索平臺，山水志之屬','url':'https://www.kaixims.jp/?category_mokuji=%E5%8F%B2%E9%83%A8%2C%E5%9C%B0%E7%90%86%E9%A1%9E%2C%E5%B1%B1%E6%B0%B4%E5%BF%97%E4%B9%8B%E5%B1%AC&page=7','retrieved_on':'2026-10-22','access':'search snippet only','assessment':'檢索摘要同時有龍虎山志三卷續編一卷與續修龍虎山志六卷，提示範圍異常，不能把六卷直接改成三卷或據此定分立。'}
]

cases=[
 {'case_id':'H-A001','supersedes_case_id':'H-C085','type':'Work','title':'清豐縣志／新修清豐縣志','status':'confirmed','verdict':'confirmed','review_depth':'current_native_records_and_primary_catalogue_transcription_compared','upstream_sha':head,
  'members':selected['H-C085'],'keeper':'d59f2njb2wao','losers':['d59f6ep8j2ti'],'implemented':False,'merge_eligible':False,
  'reason':'晁瑮的清豐縣志是嘉靖新修清豐縣志的省題著錄：兩條責任者同指hixhd2h9bn18，原典千頃堂卷六明記十六卷並繫嘉靖間修；總目條明列嘉靖新修清豐縣志十六卷、李汝寬修晁瑮纂、嘉靖三十七年本。題名、地域、纂者、卷數和修纂時代形成聯合證據，不只是刪掉新修二字。',
  'evidence':[{'kind':'pinned_native_record','id':'d59f6ep8j2ti','locator':'authors[0]; indexed_by[0]; juan_count','fact':'晁瑮entity_id、千頃堂省題、十六卷；舊indexed_by未抄卷數，不能把description當獨立證據。'},
              {'kind':'pinned_native_record','id':'d59f2njb2wao','locator':'indexed_by[0]; description; measures','fact':'總目明記十六卷、嘉靖、李汝寬修及晁瑮纂；四冊是裝訂冊數，並非另一部四卷書。'},
              {'kind':'external_primary_transcription','reference_id':'EXT-Q1','fact':'補齊原典十六卷與嘉靖時代證據。'}],
  'counterevidence_and_resolution':['新修不是普遍可刪前綴；本案以同一纂者、嘉靖和十六卷識別。','清代楊燝、高俊的同題縣志在舊ai_note明確另列，本案不涵蓋。','四冊與十六卷屬不同單位；不將measures四冊改寫成四卷。','李汝寬在原生authors缺漏，但總目author_info明記；必須保留其修的角色，不能只剩晁瑮。'],
  'field_decisions':{'title':'保留新修清豐縣志，清豐縣志加別題；嘉靖保留於版本和斷代證據。','authors':'晁瑮角色依總目為纂；補李汝寬修前先核Person身份，不臆配entity_id。','indexed_by':'兩側全部原著錄順序保留；千頃堂新取原文及葉碼另附說明，不靜默覆寫舊引文。','description':'刪除無根據的惟一志著錄、賴之以存表述；舊全文留快照/台帳。','measure_info':'十六卷與四冊同時有據留存，不互相替代。','resources':'國圖0584及resource_groups保留。','Book':'不提出任何Book合併；work_id改指與版本辨別分開。'},
  'defer_reason':'身份確證只完成研究；keeper方向仍須全部引用、正文資產與升格表核查，尚無可直接執行的合併台帳。',
  'next_steps':['查兩側全部Book/Collection/Entity/分類/promotions及草稿引用。','核book-text正文、整理本、輯佚及元資料後選定keeper並制定遷移。','查李汝寬Person，保留修/纂責任層次；原檔重算hash後按現行規則建立無損合併台帳並跑寫後驗證。']},
 {'case_id':'H-A002','supersedes_case_id':'H-C092','type':'Work','title':'龍虎山志／續修龍虎山志：元原編與明續修混掛','status':'open','verdict':'open','review_depth':'current_native_records_and_revision_scope_compared','upstream_sha':head,
  'members':selected['H-C092'],'implemented':False,'merge_eligible':False,'keeper':None,'losers':[],
  'reason':'同一元明善只是原編責任者，不能識別現存各修訂層。續修條原始著錄明列張國祥、張顯庸續撰，而龍虎山志條同時掛四庫所見明張國祥續修本、元刻三卷續編一卷與周召續編。候選由單純同作者近題提升為來源混掛的範圍拆辨案，沒有足夠證據整組合併或整組判成兩部完全獨立作品。',
  'evidence':[{'kind':'pinned_native_record','id':'d59f2ghntpfm','locator':'indexed_by[0].summary/edition','fact':'四庫全書存目叢書史部第228冊，北京圖書館藏明刻本；原文已記張國祥與張顯庸續撰，但authors只寫元明善。'},
              {'kind':'pinned_native_record','id':'d59f2gp07pj6','locator':'indexed_by[0].summary','fact':'四庫提要明言張國祥續修，並稱原本體例不可復考、此本多所竄亂非其舊；是修訂範圍的明確反證。'},
              {'kind':'pinned_native_record','id':'d59f2gp07pj6','locator':'indexed_by[3]','fact':'總目另記龍虎山志三卷續編一卷，續編周召；有元刻本與清影元抄本。'},
              {'kind':'external_catalogue_lead','reference_ids':['EXT-L1','EXT-L2','EXT-L3'],'fact':'明續修角色獲檢索印證；三卷/續編一卷/六卷須逐本核對，網頁未完整取到，不冒充書影證據。'}],
  'counterevidence_and_resolution':['兩條四庫/存目著錄有可能部分指向同一明續修本，故不逕判全組separate。','龍虎山志條又包含元本與周召續編，故不把整條當成明續修本合併。','同一元明善、同為三卷不能消除續修者與範圍衝突。'],
  'diagnostic_changes':['明續修兩人被塞進edition而未列authors；修前須校責任層次。','龍虎山志description稱本書之目賴四庫以存，與本條所記元刻、影元抄等實存本不相稱；須另修生成摘要。','兩條無資料變動，本輪只增加研究判據與拆辨次序。'],
  'defer_reason':'尚未核元刻/清影元抄、明刻續修本的序跋、目錄和正文邊界；已有混掛不能依現有Work粒度強行合併或分立。',
  'next_steps':['取得存目叢書史228明刻本卷首及三卷目錄，核張國祥/張顯庸所增範圍。','對照國圖元刻本與周召續編一卷，逐項映射Book及resources所對應文本。','先形成按修訂層的著錄/資源拆分修復案，再裁兩Work的部分重疊；保留所有舊引文及來源。']}
]
write('cases.json',cases)
write('references.json',refs)
write('current-records.json',snapshots)
write('upstream-drift-records.json',drift_records)
write('coverage.json',{'upstream_sha':head,'research_base':BASE,'old_effective_counts':dict(collections.Counter(c['status'] for c in effective)),
 'effective_case_count':len(effective),'unique_work_paths':len(paths),'present_paths':len(now),'unchanged_work_paths':sum(before.get(p)==now.get(p) for p in paths),'changed_work_paths':len(drift),'drift':drift,
 'confirmed_cases_not_implemented': [c['case_id'] for c in effective if c['status']=='confirmed' and all(before.get(p)==now.get(p) for p in paths_by_case[c['case_id']])],
 'coverage_method':'Pinned Git tree/blob equality checks all 113 inherited cases; bibliographical rereview only two selected cases. Inherited active records with identical blobs remain active.',
 'native_mutations':0,'new_cases_reviewed':2,'this_run_decisions':{'confirmed':1,'separate':0,'open':1},'effective_counts_after_replacement':{'confirmed':9,'separate':3,'open':101},'cases':coverage})
print(json.dumps({'head':head,'paths':len(paths),'drift':drift,'counts_after':{'confirmed':9,'separate':3,'open':101}},ensure_ascii=False))
