"""C1b（overview#285，用户 2026-09-30 拍板）：旧词表 classification → 《中國古籍總目》词表。
用法：python3 c1b_migrate.py          # 试运行，写 out/c1b_迁移映射.csv、out/c1b_迁移清单.jsonl
      python3 c1b_migrate.py --apply  # 真改：只改 Work 的 classification 的 l1–l4，basis／source 不动，不动 revision
原则：能直接对上的直接改；不好分的放最近一层「未分類」；不逐本查看。
须在 classific.json 已换成新词表后运行（新路径按 classific.json 校验）。幂等：已是新路径者不变。"""
import json,glob,os,csv,collections,sys
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.abspath(os.path.join(HERE,'..','..','..')); OUT=os.path.join(HERE,'out'); BI=ROOT
os.makedirs(OUT,exist_ok=True)
UNC='未分類'
vocab=json.load(open(os.path.join(ROOT,'classific.json'),encoding='utf-8'))
VP=set()  # 所有合法前缀
for r in vocab:
    p=tuple(r[k] for k in ('cata_l1','cata_l2','cata_l3','cata_l4') if k in r)
    for i in range(1,len(p)+1): VP.add(p[:i])
# ---- 类级映射：(旧l1,旧l2) -> (新l1,新l2,默认新l3 或 None)
M2={
 ('史部','正史類'):('史部','紀傳類',None),
 ('史部','詔令類'):('史部','詔令奏議類','詔令之屬'),
 ('史部','奏議類'):('史部','詔令奏議類','奏議之屬'),
 ('史部','職官類'):('史部','政書類','職官之屬'),
 ('史部','別史類'):('史部',UNC,None),
 ('史部','載記類'):('史部',UNC,None),
 ('史部','外國史類'):('史部',UNC,None),
 ('史部','方誌類'):('史部','方志類','地志之屬'),
 ('史部','金石類'):('史部','金石考古類',None),
 ('子部','說叢類'):('子部','小說類','文言之屬'),
 ('子部','耶穌教類'):('子部','諸教類','基督教之屬'),
 ('子部','回回教類'):('子部','諸教類','伊斯蘭教之屬'),
 ('集部','集評類'):('集部','詩文評類',None),
 ('集部','詞曲類'):('集部',UNC,None),
 ('集部','小說類'):('子部','小說類','白話之屬'),
 ('經部','石經類'):('經部','總類','石經之屬'),
}
# ---- 属级映射：(旧l2,旧l3) -> (新l3,新l4)；None 表示丢到「未分類」
M3={
 # 經部
 ('四書類','論語之屬'):('論語',None),('四書類','大學之屬'):('大學',None),('四書類','中庸之屬'):('中庸',None),
 ('四書類','孟子之屬'):('孟子',None),('四書類','四書總義之屬'):('四書總義',None),
 ('禮類','周禮之屬'):('周禮',None),('禮類','儀禮之屬'):('儀禮',None),('禮類','禮記之屬'):('禮記',None),('禮類','三禮總義之屬'):('三禮總義',None),
 ('春秋類','左傳之屬'):('左傳',None),('春秋類','公羊傳之屬'):('公羊傳',None),('春秋類','穀梁傳之屬'):('穀梁傳',None),('春秋類','春秋總義之屬'):('春秋總義',None),
 ('詩類','三家詩之屬'):('三家詩之屬',None),
 ('小學類','訓詁之屬'):('訓詁之屬',None),('小學類','文字之屬'):('文字之屬',None),('小學類','音義之屬'):('音韻之屬',None),('小學類','文字總義之屬'):('總義之屬',None),
 # 史部
 ('傳記類','合傳之屬'):('總傳之屬',None),('傳記類','別傳之屬'):('別傳之屬',None),('傳記類','年譜之屬'):('年譜之屬',None),('傳記類','日記之屬'):('日記之屬',None),
 ('地理類','總誌之屬'):('總志之屬',None),('地理類','雜記之屬'):('雜志之屬',None),('地理類','專誌之屬'):('專志之屬',None),
 ('地理類','山水總錄之屬'):('山水志之屬','合志'),('地理類','山川之屬'):('山水志之屬','山'),('地理類','水道之屬'):('山水志之屬','水'),
 ('地理類','遊記之屬'):('遊記之屬',None),('地理類','中外交通之屬'):('中外雜記之屬',None),
 ('政書類','通制之屬'):('通制之屬',None),('政書類','儀制之屬'):('儀制之屬',None),('政書類','邦計之屬'):('邦計之屬',None),('政書類','邦交之屬'):('邦交之屬',None),
 ('政書類','軍政之屬'):('軍政之屬',None),('政書類','法令之屬'):('刑法之屬',None),('政書類','考工之屬'):('考工之屬',None),('政書類','學制之屬'):('科舉學校之屬',None),('政書類','雜錄之屬'):('雜錄之屬',None),
 ('職官類','官制之屬'):('職官之屬','官制'),('職官類','官箴之屬'):('職官之屬','官箴'),
 ('詔令類',None):('詔令之屬',None),
 # 子部
 ('儒家類','儒學之屬'):('儒學之屬',None),('儒家類','教學之屬'):('禮教之屬',None),('儒家類','修身之屬'):('禮教之屬','修身'),
 ('農家類','總錄之屬'):('綜論之屬',None),('農家類','蔬果花木之屬'):('園藝之屬',None),('農家類','畜牧水產之屬'):('牧養之屬',None),
 ('醫家類','總論之屬'):('綜論之屬',None),('醫家類','醫經之屬'):('醫經之屬',None),('醫家類','傷寒之屬'):('方論之屬','傷寒金匱'),
 ('醫家類','診法之屬'):('診法之屬',None),('醫家類','內科之屬'):('方論之屬','內科'),('醫家類','外科之屬'):('方論之屬','外科'),
 ('醫家類','五官科之屬'):('方論之屬','五官'),('醫家類','婦產科之屬'):('方論之屬','婦幼科'),('醫家類','兒科之屬'):('方論之屬','婦幼科'),
 ('醫家類','針炙之屬'):('鍼灸推拿之屬',None),('醫家類','養生之屬'):('養生之屬',None),('醫家類','本草之屬'):('本草之屬',None),
 ('醫家類','方劑之屬'):('方論之屬',None),('醫家類','醫案之屬'):('醫案醫話之屬',None),
 ('天文算法類','天文之屬'):('推步之屬','天文'),('天文算法類','曆法之屬'):('推步之屬','曆法'),('天文算法類','算法之屬'):('算書之屬','算法'),
 ('藝術類','書畫之屬'):('書畫之屬',None),('藝術類','法帖之屬'):('書畫之屬',None),('藝術類','摹印之屬'):('篆刻之屬',None),('藝術類','游藝之屬'):('游藝之屬',None),
 ('譜錄類','器物之屬'):('器用之屬','器物'),('譜錄類','食譜之屬'):('飲食之屬',None),('譜錄類','草木之屬'):('花木鳥獸之屬','花草樹木'),('譜錄類','鳥獸蟲魚之屬'):('花木鳥獸之屬','鳥獸蟲魚'),
 ('雜家類','雜學之屬'):('雜學雜說之屬',None),('雜家類','雜說之屬'):('雜學雜說之屬',None),('雜家類','雜考之屬'):('雜考之屬',None),('雜家類','雜纂之屬'):('雜纂之屬',None),
 ('類書類','類編之屬'):('類編之屬',None),('類書類','專編之屬'):('類編之屬','專編'),('類書類','韻編之屬'):('韻編之屬',None),
 ('說叢類','雜事之屬'):('文言之屬',None),('說叢類','異聞之屬'):('文言之屬',None),
 ('道家類','道德真經之屬'):('先秦之屬','老子'),('道家類','四子真經之屬'):('先秦之屬',None),
 # 集部
 ('別集類','漢迄隋之屬'):('漢魏六朝之屬',None),('別集類','唐五代之屬'):('唐五代之屬',None),('別集類','宋之屬'):('宋代之屬',None),('別集類','元之屬'):('金元之屬',None),
 ('別集類','明之屬'):('明代之屬',None),('別集類','清初之屬'):('清代之屬','清前期'),('別集類','清中之屬'):('清代之屬','清中期'),('別集類','清後之屬'):('清代之屬','清後期'),
 ('別集類','民國之屬'):('民國之屬',None),
 ('總集類','通代之屬'):('通代之屬',None),('總集類','斷代之屬'):('斷代之屬',None),('總集類','郡邑之屬'):('郡邑之屬',None),('總集類','族望之屬'):('氏族之屬',None),
 ('集評類','詞評之屬'):('@集部/詞類','詞話之屬'),('集評類','曲讕之屬'):('@集部/曲類','曲評曲話之屬'),
}
# 词表中家譜之屬 → 总目 譜牒類（独立）
SPECIAL={('傳記類','家譜之屬'):('史部','譜牒類',None,None)}
APPLY='--apply' in sys.argv
def _fmt(raw,d):
    for ind in (2,1,4):
        for nl in ('\n',''):
            if raw==json.dumps(d,ensure_ascii=False,indent=ind)+nl: return ind,nl
    return 2,'\n'
def new_path(c):
    l1,l2,l3,l4=[c.get(k,'') for k in ('l1','l2','l3','l4')]
    _p=tuple(x for x in (l1,l2,l3,l4) if x)
    if _p in VP and (l1,l2) not in M2 and (l2,l3) not in M3 and (l2,l3) not in SPECIAL: return (l1,l2,l3,l4),'已是总目路径（不变）'
    if (l2,l3) in SPECIAL: return SPECIAL[(l2,l3)],'拆出独立类'
    if not l2: return (l1,'','',''),'只到部（不变）'
    n1,n2,d3=M2.get((l1,l2),(l1,l2,None)); kind='类同名' if (n1,n2)==(l1,l2) else '类改名/并/拆'
    n3=n4=''
    if n2==UNC: return (n1,UNC,'',''),'放部下未分類'
    if l3:
        m=M3.get((l2,l3))
        if m and m[0].startswith('@'):
            a,b=m[0][1:].split('/'); return (a,b,m[1],''),'属→别类'
        if m: n3,n4=m[0],m[1] or ''
        elif d3 and (l2,None) in M3: n3=M3[(l2,None)][0]
        elif d3: n3=d3
        else: n3=UNC
        kind+='+属'+('对应' if m else '未分類')
        if d3 and not m and (n1,n2,d3) in VP: n3=d3
    else:
        if d3: n3=d3
    p=(n1,n2,n3,n4)
    # 合法性：不在词表则退到最近合法层 + 未分類
    q=tuple(x for x in p if x)
    while q and q not in VP: q=q[:-1]; kind+='|退层'
    if len(q)<len([x for x in p if x]):
        q=q+(UNC,) if q+(UNC,) in VP else q
    q=q+('',)*(4-len(q))
    return q,kind
def main():
    old=collections.Counter(); ex=[]
    tot=0
    for f in glob.glob(os.path.join(BI,'Work/*/*/*/*.json')):
        raw=open(f,encoding='utf-8').read(); d=json.loads(raw); d0=json.loads(raw)
        if d.get('merged_into'): continue
        c=d.get('classification')
        if not c or not c.get('l1'): continue
        tot+=1
        oldp=tuple(c.get(k,'') for k in ('l1','l2','l3','l4'))
        newp,kind=new_path(c)
        old[(oldp,newp,kind)]+=1
        if oldp!=newp:
            ex.append(dict(id=d['id'],title=d.get('title'),old=list(oldp),new=list(newp),kind=kind))
            if APPLY:
                fmt=_fmt(raw,d0)
                c['l1'],c['l2'],c['l3'],c['l4']=newp
                open(f,'w',encoding='utf-8').write(json.dumps(d,ensure_ascii=False,indent=fmt[0])+fmt[1])
    w=csv.writer(open(os.path.join(OUT,'c1b_迁移映射.csv'),'w',newline='',encoding='utf-8-sig'))
    w.writerow(['旧 l1/l2/l3/l4','新 l1/l2/l3/l4','部数','类别','是否变化'])
    for (o,n,k),v in sorted(old.items(),key=lambda x:(-x[1])):
        w.writerow(['/'.join(x for x in o if x),'/'.join(x for x in n if x),v,k,'变' if o!=n else '不变'])
    with open(os.path.join(OUT,'c1b_迁移清单.jsonl'),'w',encoding='utf-8') as fo:
        for e in ex: fo.write(json.dumps(e,ensure_ascii=False)+'\n')
    ch=sum(1 for e in ex)
    print('已分类',tot,'变化',ch,f'{ch/tot:.1%}')
    byk=collections.Counter(e['kind'] for e in ex)
    for k,v in byk.most_common(): print(v,k)
    bad=[e for e in ex if tuple(x for x in e['new'] if x) not in VP]
    print('新路径不在词表:',len(bad),bad[:3])
    unc=sum(1 for e in ex if UNC in e['new'])
    print('落入未分類:',unc)
main()
