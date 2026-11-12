"""地方志总目提要 1996 ↔ 现库方志 Work 匹配分类。用法：python3 classify.py <book_index_json/tiyao_data/地方志總目1996.json> <out.json>
键 = (年号/朝代前缀, 去年份与繁简差后的题名)。类别见 README。只读。"""
import sys,json,re,os,collections
sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
from norm import split
yr=re.compile(r'^(?:[元二三四五六七八九十廿卅百]+年)(?:[春夏秋冬]?[修刻抄稿鈔])?')
V=str.maketrans('碍赣临乡县图记庙续纪总齐灵阳龙宁兴荣储湾沟岭罗蕲蒋汉与浒陕阴','礙贛臨鄉縣圖記廟續紀總齊靈陽龍寧興榮儲灣溝嶺羅蘄蔣漢與滸陝陰')
def key(t):
    rg,b=split(t); return rg,yr.sub('',b.translate(V))
def isfz(secs): return any(('方志' in s or '地理類' in s) for _,s in secs)
def load_works(root='.'):
    R=[]
    for r,_,fs in os.walk(os.path.join(root,'Work')):
        for f in fs:
            if not f.endswith('.json'): continue
            p=os.path.join(r,f); d=json.load(open(p))
            if d.get('merged_into'): continue
            secs=[(i.get('source'),i.get('section') or '') for i in d.get('indexed_by',[]) if isinstance(i,dict)]
            R.append((d['id'],d.get('title',''),d.get('dynasty',''),secs,p))
    return R
def classify(L,R):
    idx=collections.defaultdict(list); idx2=collections.defaultdict(list)
    for r in R:
        k=key(r[1]); idx[k].append(r); idx2[k[1]].append(r)
    cnt=collections.Counter(key(x['bookName']) for x in L); res=[]
    for x in L:
        k=key(x['bookName']); c=idx.get(k,[]); cf=[r for r in c if isfz(r[3])]
        if k[0]=='': cls='E无年号前缀'
        elif len(cf)==1 and cnt[k]==1 and len(c)==1: cls='A唯一对唯一'
        elif cf and cnt[k]>1: cls='B1总目内重名'
        elif len(cf)>1: cls='B2库内多候选'
        elif c and not cf: cls='B3命中非方志类Work'
        elif idx2.get(k[1]): cls='D同题异朝或库内无年号'
        else: cls='C库内无'
        res.append({'cls':cls,'sort':x['sort'],'bookName':x['bookName'],'page':x.get('summaryPage'),'ids':[r[0] for r in c]})
    return res
if __name__=='__main__':
    L=json.load(open(sys.argv[1])); res=classify(L,load_works())
    json.dump(res,open(sys.argv[2],'w'),ensure_ascii=False,indent=1)
    print(collections.Counter(r['cls'] for r in res))
