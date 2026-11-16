import json,re,collections
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/'
rows=json.load(open(S+'e_cand80.json'))
JE='慶長|元和|寛永|寬永|正保|慶安|承応|承應|明暦|明曆|万治|萬治|寛文|寬文|延宝|延寶|天和|貞享|元禄|元祿|宝永|寶永|正徳|正德|享保|元文|寛保|寬保|延享|寛延|寬延|宝暦|寶曆|明和|安永|天明|寛政|寬政|享和|文化|文政|天保|弘化|嘉永|安政|万延|萬延|文久|元治|慶応|慶應|明治|天正|文禄|文祿'
def norm(s):
    s=s.replace('徳','德').replace('經','經').replace('経','經').replace('傳','傳').replace('伝','傳').replace('観','觀').replace('齊','齋').replace('斎','齋').replace('眞','真').replace('寛','寬').replace('巻','卷').replace('釈','釋').replace('説','說').replace('註','注').replace('點','点').replace('國','国').replace('解','解').replace('義','義').replace('宝','寶')
    return s
out=collections.OrderedDict()
for n,t,au,pb,y,lib,ser in rows:
    m=re.search(r'\[(1[5-9]\d\d)\]',y) 
    if not m: continue
    if not re.search(JE,y) : continue
    yy=int(m.group(1))
    core=re.sub(r'[,，]?\s*\d+[巻卷册冊篇].*$','',t); core=norm(core)
    pbs=tuple(sorted(norm(p.strip()).replace('湏','須') for p in re.split(r'[:：,，、]|ほか',pb) if p.strip()))
    key=(core,pbs,yy)
    out.setdefault(key,[]).append((n,t,au,pb,y,lib,ser))
print(len(out))
json.dump([[list(k[:2])+[k[2]],v] for k,v in out.items()],open(S+'e_clusters.json','w'),ensure_ascii=False)
