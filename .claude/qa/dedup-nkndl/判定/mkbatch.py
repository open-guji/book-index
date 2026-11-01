import json,re,subprocess,collections
P=json.load(open('pairs.json'))
init=[l.rstrip('\n').split('\t') for l in open('并.tsv',encoding='utf-8')]
rev=[l.rstrip('\n').split('\t') for l in open('复核_结果.tsv',encoding='utf-8')]
extra=[('d59f2gonez9d','d59fxwojvev5','（段外线索：同一陳澔 entity 同书异题）'),('d59f2ht2yk8z','d59fxwycwt1c','')]
base=subprocess.check_output(['git','-C','/home/user/book-index','rev-parse','origin/main'],text=True).strip()
groups=[];judged=[];seen=collections.Counter()
for k,r in enumerate(rev,1):
    if k<=len(init):
        i=init[k-1]; a,b=i[1],i[2]; src='对 '+i[0]; ini=i[6]; grade=i[5]
    else:
        a,b,_=extra[k-len(init)-1]; src='段外线索'; ini='初判员段外发现同 entity 同书'; grade='A'
    if r[1]!='维持' or k==26:
        why=r[3] if r[1]=='否' else '說郛一卷節錄本對五卷本，節本不並（K14），复核维持被本串从严否'
        judged.append(f'{a}\t{b}\t{"C" if k in (15,26) else "D"}\t台湾国图线索 复核{k:02d}（{src}）：初判并，复核否：{why}'); continue
    kp=r[2]; lo=b if kp==a else a
    seen[kp]+=1; seen[lo]+=1
    ev=f'初判（{grade}）：{ini}；独立复核维持：{r[3]}'
    groups.append({'case_id':f'T{k:02d}','cluster_id':f'ncltw-T{k:02d}','type':'work','keeper':kp,'losers':[lo],
      'keeper_source':'台湾国图挂接线索同题配多 Work（bim docs/馆藏资源挂接/报告/C3续-臺灣國圖存疑與越南漢喃挂接-20261026.md 交去重清单）',
      'evidence':ev,'why':ev,'rule':'去重线索（台湾国图）：同题、著者同人或一侧无著者而著录互证，按 3a／部分 4 证据口径逐对判＋独立复核并'})
print(len(groups),[x for x,c in seen.items() if c>1])
json.dump({'groups':groups},open('batch.json','w'),ensure_ascii=False,indent=1)
open('judged_rev.tsv','w',encoding='utf-8').write('\n'.join(judged)+'\n')
