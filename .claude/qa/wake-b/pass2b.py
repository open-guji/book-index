# -*- coding: utf-8 -*-
import sys,re,os,json
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import ndl
import xml.etree.ElementTree as ET
Q={'d59f2njbpd6r':['史記評林'],'d59f2nk4f7cy':['靈樞注證發微','黃帝內經靈樞'],'d59f2hti96v6':['句解南華真經'],'d59f282rkphd':['周易王弼注'],
'd59f2hs3oqv4':['易學啟蒙通釋'],'d59f2hq3kxdv':['詩童子問'],'d59gduogi8n4':['老子道德經妄言','老子妄言'],'d59fxra6glq8':['古文孝經'],
'd59f2pt7msxs':['扁鵲倉公傳彙考'],'d59f2pvvgnwg':['脈粹'],'d59f28k96d51':['海上仙方'],'d59fxv1ayv41':['魁本大字評音句讀周易'],
'd59f28klz3es':['莊子音義'],'d59f2hrw71ts':['婦人良方'],'d59fxsp0kykg':['春秋左傳屬事']}
def yr(r):
    m=re.search(r'(1[5-9]\d\d)',r['date'] or '') or re.search(r'(1[5-9]\d\d)',r['issued'] or '')
    return int(m.group(1)) if m else None
out={}
for wid,qs in Q.items():
    res=[];seen=set()
    for q in qs:
        for p in ({'title':ndl.jp(q),'from':1500,'until':1912,'cnt':100},{'any':ndl.jp(q)+' 和古書','cnt':100}):
            data=ndl.fetch(p)
            try: root=ET.fromstring(data)
            except Exception: continue
            for it in root.iter('item'):
                g=lambda tg:(it.findtext(tg,namespaces=ndl.NS) or '').strip()
                rid=(it.findtext('link') or '').split('/')[-1]
                if rid in seen: continue
                seen.add(rid)
                r={'rid':rid,'title':g('dc:title'),'creator':g('dc:creator'),'pub':g('dc:publisher'),'date':g('dc:date'),'issued':g('dcterms:issued'),'ext':g('dc:extent'),'vol':g('dcndl:volume'),'cat':'/'.join(c.text for c in it.findall('category'))}
                y=yr(r)
                if y and y<=1912 and ndl.jp(q) in ndl.jp(r['title']): r['y']=y;res.append(r)
    out[wid]=res;print(wid,len(res),flush=True)
json.dump(out,open('/tmp/wb2_cand2.json','w'),ensure_ascii=False)
