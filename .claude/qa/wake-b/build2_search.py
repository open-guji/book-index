# -*- coding: utf-8 -*-
# 對每個 Work 查 NDL Search（含 CiNii 聚合）1600-1912 年間的相關記錄，輸出候選
import json,sys,re,os,time
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ndl
W=json.load(open('/tmp/wb2_works.json'))
def yr(r):
    m=re.search(r'(1[5-9]\d\d)',r['date'] or '') or re.search(r'(1[5-9]\d\d)',r['issued'] or '')
    return int(m.group(1)) if m else None
out={}
for w in W:
    t=w['title']; key=ndl.jp(t)[:8]
    res=[]
    seen=set()
    qs=[{'title':ndl.jp(t)[:20],'from':1500,'until':1912,'cnt':100}]
    if w['authors']: qs.append({'title':ndl.jp(t)[:20],'creator':ndl.jp(w['authors'][0]),'cnt':100})
    for q in qs:
        data=ndl.fetch(q)
        import xml.etree.ElementTree as ET
        try: root=ET.fromstring(data)
        except Exception: continue
        for it in root.iter('item'):
            g=lambda tg:(it.findtext(tg,namespaces=ndl.NS) or '').strip()
            link=it.findtext('link') or ''
            rid=link.split('/')[-1]
            if rid in seen: continue
            seen.add(rid)
            r={'rid':rid,'title':g('dc:title'),'creator':g('dc:creator'),'pub':g('dc:publisher'),'date':g('dc:date'),'issued':g('dcterms:issued'),'ext':g('dc:extent'),'vol':g('dcndl:volume'),'cat':'/'.join(c.text for c in it.findall('category'))}
            y=yr(r)
            if y and y<=1912 and key in ndl.jp(r['title']) :
                r['y']=y;res.append(r)
    out[w['id']]=res
    print(w['id'],t,len(res),flush=True)
json.dump(out,open('/tmp/wb2_cand.json','w'),ensure_ascii=False)
