# -*- coding: utf-8 -*-
"""和刻本專項第四輪 wake-b-4：「存疑」批再核。
用法：python3 build4_wake_b.py [--apply]
輸入：cuny4_input.tsv（各片台賬中判「存疑」的行）；b4_accept.py（人工確認同版的 NCID）；b4_reasons.py（其餘保留存疑的原因）。
動作：對確認同版者，按 NCID 書誌取所藏館，追加到 Book.provenance（不刪原館藏）；revision patch+1。"""
import json,os,re,subprocess,sys
HERE=os.path.dirname(os.path.abspath(__file__));BI=os.path.abspath(os.path.join(HERE,'../../..'))
sys.path.insert(0,HERE)
import b3_cinii as c, ndl
from b4_accept import ACC
APPLY='--apply' in sys.argv
TODAY='2026-11-16'
CN='https://ci.nii.ac.jp/ncid/'
INV={v:chr(k) for k,v in ndl.M.items()}
EXTRA={'関':'關','広':'廣','国':'國','対':'對','続':'續','両':'兩','属':'屬','総':'總','図書館':'圖書館','大学':'大學','経':'經','済':'濟','学':'學','蔵':'藏','覚':'覺','応':'應','万':'萬','党':'黨','団':'團','会':'會','区':'區','県':'縣','医':'醫','薬':'藥','芸':'藝','礼':'禮','辺':'邊','斎':'齋','沢':'澤','気':'氣','竜':'龍','徳':'德','歴':'歷','図':'圖','専':'專','国立':'國立'}
def lib(n):
    n=re.sub(r'\s+','',n or '');out=''
    for ch in n: out+=EXTRA.get(ch,INV.get(ch,ch))
    return out
def core(s):
    s=s.replace('日本','')
    for w in ('附屬圖書館','附屬','圖書館','中央','總合','圖書室','學術情報中心'): s=s.replace(w,'')
    return s
def git_show(p): return subprocess.run(['git','-C',BI,'show','origin/main:'+p],capture_output=True).stdout.decode('utf-8')
def paths_for(ids):
    out=subprocess.run(['git','-C',BI,'-c','core.quotepath=false','ls-tree','-r','--name-only','origin/main','--','Book'],capture_output=True).stdout.decode('utf-8').split('\n')
    m={}
    for p in out:
        f=os.path.basename(p).split('-',1)[0]
        if f in ids: m[f]=p
    return m
ids=set(ACC)
PM=paths_for(ids)
miss=ids-set(PM)
assert not miss,miss
LEDGER=[];changed=[];stat={'補掛':0,'館藏條':0}
for bid in sorted(ACC):
    ncids,note=ACC[bid]
    p=PM[bid];raw=git_show(p);b=json.loads(raw)
    assert json.dumps(b,ensure_ascii=False,indent=2)+'\n'==raw,('roundtrip',bid)
    if bid=='988g8y6bcw':
        b['provenance']=[x for x in b['provenance'] if 'BC05969794' not in x.get('source','')]
        b['ai_note']+='\n和刻本第四輪（2026-11-16）複抽：BC05969794（武庫川女子大學，元文4[1739]中野總左衞門版）與寛保元年錦山房本非同版，已自本條 provenance 移除，未另立。'
    have=[core(x.get('institution','')) for x in b.get('provenance') or []]
    add=[];seen=set();srcs={}
    for n in ncids:
        d=c.ncid(n)
        assert d,('ncid',n)
        for o in d['owners']:
            k=lib(o['name'])
            if core(k) in have or k in seen: continue
            seen.add(k);add.append(k);srcs[k]=n
    if not add:
        LEDGER.append((bid,b['title'],'已有','—','—','、'.join(CN+n for n in ncids)));continue
    b.setdefault('provenance',[])
    if b['provenance'] is None: b['provenance']=[]
    for k in add: b['provenance'].append({'institution':k,'source':'CiNii Books '+CN+srcs[k]})
    if bid=='993ekxf3eq':
        b['dating']={'era':'日本','reign':'寶曆','year':1761,'certainty':'inferred','source':'edition','basis':'題名「日本寶曆十一年東都書肆崇文堂刻本」；CiNii 刊記「寳暦十一年辛巳九月」互證（原誤作 835）'}
    if bid=='988g0pbmrx':
        b['edition_type']='影印本'
        if b.get('description'): b['description']['text']+='日本館藏所據 CiNii 記錄為明治十六年印刷局據高山寺藏舊鈔本之影印（零本，卷二十七）。'
    v=b.get('revision','1.0.0').split('.');v[2]=str(int(v[2])+1);b['revision']='.'.join(v);b['revised_at']=TODAY
    line=('和刻本日本馆藏专项第四輪（%s，車道 wake-b-4，「存疑」再核）：據 CiNii Books 書誌（%s）核對題名、刊年、書肆與本條版本項一致，補掛日本館藏：%s；未核原書。%s'
          %(TODAY,'、'.join(CN+n for n in ncids),'、'.join(add),note))
    b['ai_note']=(b['ai_note']+'\n' if b.get('ai_note') else '')+line
    changed.append((p,b))
    stat['補掛']+=1;stat['館藏條']+=len(add)
    LEDGER.append((bid,b['title'],'補掛','、'.join(add),'、'.join(CN+n for n in ncids),b['edition']))
print(stat)
if APPLY:
    for p,b in changed:
        fp=os.path.join(BI,p);os.makedirs(os.path.dirname(fp),exist_ok=True)
        open(fp,'w',encoding='utf-8').write(json.dumps(b,ensure_ascii=False,indent=2)+'\n')
    open(os.path.join(HERE,'changed_paths4.txt'),'w').write('\n'.join(p for p,_ in changed)+'\n')
    json.dump(LEDGER,open('/tmp/wb4_ledger_part.json','w'),ensure_ascii=False)
