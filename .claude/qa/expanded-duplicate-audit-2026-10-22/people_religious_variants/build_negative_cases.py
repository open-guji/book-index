import json,pathlib
P=pathlib.Path(__file__).parent;A=json.loads((P/'prefix-records.json').read_text())
specs=[
('PRV-N001','separate',['hixhd2h9bmqo','hixhd2h9boze'],'元古梅禪師語錄作者與新唐書藝文志已著錄之元海集作者時代不相容；保持分立。'),
('PRV-N002','separate',['hixhd2h9btxl','hixi8u5zul81'],'唐船子和尚德誠與清聽香讀畫山房遺稿作者德誠不可只刪釋字合併。'),
('PRV-N003','separate',['hixi8u5ywvjj','hixhd2h9boz9'],'清杜鵑集作者與宋史藝文志已載錢塘平越州錄作者元宏不能合為一人；後者確切朝代未定，不誤稱已證為宋人。'),
('PRV-N004','separate',['hixi8u5so4pt','hixhd2h9bi28'],'明漢月三峯法藏與唐華嚴法藏的著述、時代均不相容。'),
('PRV-N005','open',['hixhgyrw4wo1','hixi8u5so4pt'],'僅題法藏山居集，是否明漢月之山居詩須核正文及卷數；不憑山居題名逕繫。'),
('PRV-N006','open',['hixhd2h9btwc','hixhd2h9bgrn'],'來復條同掛蒲庵/澹游集與來陽伯集/來陽伯詩集/耦園圖詠，疑混僧人來復和俗人來復；逐書重繫前不可整體合併。'),
('PRV-N007','open',['hixhd2h9bfys','hixhd2h9bgob'],'洪恩條混雪浪齋集與靈濟真人文集；後者千頃堂小注明作元道士編輯南唐二徐乩筆，與明長干寺雪浪僧身份不相容。須先分離該 Work。'),
('PRV-N008','open',['hixhgyrw4xt7','hixhd2h9bi14'],'大艤條掛宣宗文集、仁宗文集，同時掛博山和尚信地説和禪警語；帝王文集之目錄引文沒有大艤署名，疑跨條作者繼承污染，重繫前不可合併。'),
('PRV-N009','open',['hixhd2h9bmwy','hixhd2h9bv89','hixhd2h9brwd'],'法雲至少存在不同時代僧人；唐釋法雲條又掛憨予暹禪師語錄，疑已污染。宋翻譯名義集作者與十王正業論作者不得只因去釋前綴而合併。')]
out=[]
for cid,status,ids,why in specs:
 out.append({'case_id':cid,'cluster_id':cid,'type':'Entity','status':status,'keeper':ids[0],'losers':ids[1:],'why':why,'records':[{'id':i,'path':A[i]['path'],'sha256':A[i]['sha256'],'primary_name':A[i]['record']['primary_name']} for i in ids],'related_work_ids':list(dict.fromkeys(w['record']['id'] for i in ids for w in A[i]['works'])),'evidence':[{'kind':'repository_original_catalogue_entries','snapshot':'prefix-records.json','support':why}],'work_review':{'coverage':'all current live Work.authors[].entity_id references scanned','snapshots':'prefix-records.json'},'apply_blockers':[why]})
(P/'cases-negative.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
a=json.loads((P/'cases.json').read_text())+json.loads((P/'cases-prefix.json').read_text())+out
if (P/'cases-third.json').exists(): a+=json.loads((P/'cases-third.json').read_text())
(P/'cases-all.json').write_text(json.dumps(a,ensure_ascii=False,indent=2)+'\n')
print({s:sum(c['status']==s for c in a) for s in ['confirmed','open','separate']})
