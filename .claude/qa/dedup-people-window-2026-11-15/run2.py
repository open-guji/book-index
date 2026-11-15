import sys,json,os
sys.path.insert(0,'.claude/qa')
import entity_merge as em, jio
P=[("hixhd2h9bmfo","hixhgyrw4xwg","錢升為錢陞異寫；錢陞條出處即《壺天玉露》提要，錢升名下正是該書"),
("hixicx4ygjye","hixictl6cawb","李願＝李愿，皆李晟之子、夏綏銀宥節度使"),
("hixicu5dc017","hixieoyd2onh","柳並＝柳并，皆蕭穎士友／弟子，唐"),
("hixhd2h9bl1r","hixhd2h9bfkd","妙聲＝釋妙聲，《總目》東臯錄提要同條：明釋妙聲，字九臯，吳縣；原妙聲條朝代「元」誤"),
("hixhd2h9btwh","hixhd2h9bmac","釋元賢＝元賢，皆《鼓山志》作者永覺元賢，明"),
("hixhd2h9bugt","hixhd2h9bjxc","靜福＝釋靜福，《總目》癸未夏抄「明釋靜福」；原靜福條朝代「清」誤"),
("hixhgyrw4w8i","hixi8us3ii74","李承勛＝李承勳，勳勛異寫，千頃堂書目著錄李承勛《李公奏議》，明人，李承勳條已有異體李承勛"),
("hixhd2h9bv0l","hixhd2h9bsyd","僧菩提達磨＝菩提達磨，同一傳說人物，兩條各托名一書"),
("hixhgyrw4xtd","hixiemd3m8ld","釋永昇＝永昇，明初僧，《雁山志》與「始輯雁山集」同一僧")]
led=[]
for l,k,why in P:
    ld,_=jio.load(em.find_path(l)); name=ld['primary_name']
    s=em.merge(l,k,reason=why,rule='人物去重窗口（兄弟線程自查古籍認定同人）',date='2026-11-15',by='A12-去重窗口')
    rel=em.find_path(k); kd,kf=jio.load(rel)
    have={(a if isinstance(a,str) else a.get('name')) for a in kd.get('alt_names') or []}
    if name!=kd['primary_name'] and name not in have:
        kd.setdefault('alt_names',[]).append({'name':name,'type':'別名','note':'人物去重窗口並條（A12 2026-11-15），記為著錄所見異稱'})
    for f in ('dynasty','period','dates','native_place'):
        if not kd.get(f) and ld.get(f): kd[f]=ld[f]
    kd['revised_at']='2026-11-15'; jio.save(rel,kd,kf)
    led.append({'keeper':k,'loser':l,'name':name,'why':why,'redirected_works':s['redirected_works']})
json.dump(led,open(os.path.join(os.path.dirname(os.path.abspath(__file__)),'ledger2.json'),'w'),ensure_ascii=False,indent=1)
print(len(led))
