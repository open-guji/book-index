import sys,json,re
sys.path.insert(0,'.')
from g3_cinii import search
ERAS='慶長 元和 寛永 寬永 正保 慶安 承応 承應 明暦 明曆 万治 萬治 寛文 寬文 延宝 延寶 天和 貞享 元禄 元祿 宝永 寶永 正徳 正德 享保 元文 寛保 寬保 延享 寛延 寬延 宝暦 寶曆 明和 安永 天明 寛政 寬政 享和 文化 文政 天保 弘化 嘉永 安政 万延 萬延 文久 元治 慶応 慶應 明治'.split()
def isjp(i):
    y=i['yr']
    return any(y.lstrip('[').startswith(e) for e in ERAS)
def scan(qs,maxp=5,out='scan.json'):
    res={}
    try: res=json.load(open(out))
    except: pass
    for q in qs:
        if q in res: continue
        got=[];seen=set();tot=None
        for p in range(1,maxp+1):
            t,it=search(q,p)
            tot=t
            if not it: break
            got+=it
            if len(it)<200: break
        jp=[i for i in got if isjp(i)]
        res[q]=dict(tot=tot,n=len(got),jp=jp)
        print(q,tot,len(got),len(jp),flush=True)
        json.dump(res,open(out,'w'),ensure_ascii=False)
if __name__=='__main__':
    qs=[l.strip() for l in open(sys.argv[1]) if l.strip()]
    scan(qs,out=sys.argv[2])
