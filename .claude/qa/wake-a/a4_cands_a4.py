# -*- coding: utf-8 -*-
import sys,json,re,os,glob
sys.path.insert(0,'/tmp/wa4'); import a4lib
CN=re.compile(r'書局|书局|中華|商務|石印|上海|廣東|廣州|點石|嫏嬛|琅嬛|楚南|皇華|粤東|粵東|掃葉|江西|奎章|廣雅|湖北|思賢|崇文|金陵|浙江|淮南|蘇州|成都|鴻寶|文瑞|錦章|醉六|積山|鴻文|同文|味經|善成|書業堂|會文堂|九思|五桂|二酉|觀古|共讀|學海堂|致用|臺灣|台灣|世界書|藝文|影印|新文豐|商务|鴻章|大成|文化|大東|廣益|掃葉山|寶善|中國|同治|光緒|通志堂|汲古|退補|蜚英|雙梧|聚珍|書院|官書|刻書|印書|北京|四庫|私製|扶桑使廨')
def load():
    seen={}
    for f in glob.glob(a4lib.CACHE+'/c_*.json'):
        try: j=json.load(open(f,encoding='utf8'))
        except Exception: continue
        try: g=j['@graph'][0]
        except Exception: continue
        if 'items' not in g or 'opensearch' not in j.get('@id',''): continue
        for x in g['items']: seen[x['@id'][-10:]]=x
    return seen
def pub(x):
    p=x.get('dc:publisher',[]); 
    return ' '.join(p) if isinstance(p,list) else p
if __name__=='__main__':
    s=load(); print(len(s))
    c=[x for x in s.values() if re.fullmatch(r'\d{4}',x.get('dc:date','') or '') and not CN.search(pub(x))]
    print(len(c))
