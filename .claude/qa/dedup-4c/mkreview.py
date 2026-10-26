"""从 4c_table.json 选出需逐条复核的国图 Book，写成文字卷宗分批（供子 agent 判）。
选取：他候选著者合／现挂无著者／现挂著者异／现挂著者合但他候选亦合；国图无著者者只取「他候选有同年 Book 或年号合、现挂不合」。
用法：P4WORK=<目录> python3 .claude/qa/dedup-4c/mkreview.py [批数]"""
import json,os,sys
P=os.environ.get('P4WORK','/tmp/p4'); N=int(sys.argv[1]) if len(sys.argv)>1 else 10
rows=json.load(open(P+'/4c_table.json'))
sel=[]
for r in rows:
    cur=r['cands'].get(r['cur'],{})
    if r['cat'] in('他候选著者合','现挂无著者·无他候选合','现挂著者异·无他候选合'): sel.append(r)
    elif r['cat']=='现挂著者合' and r['others']: sel.append(r)
    elif r['cat']=='国图无著者':
        sy=[k for k,i in r['cands'].items() if k!=r['cur'] and i['same_year']]
        er=[k for k,i in r['cands'].items() if k!=r['cur'] and r['reign'] and set(r['reign'])&set(i['reign'])]
        curok=cur.get('same_year') or (r['reign'] and set(r['reign'])&set(cur.get('reign',[])))
        if (sy or er) and not curok: sel.append(r)
sel.sort(key=lambda r:(r['nlc_title'],r['book']))
def fw(k,i,cur):
    mark='*现挂' if k==cur else ' '
    return f"  {mark} {k} 《{i['title']}》 著者[{';'.join('/'.join(x or '' for x in a) for a in i['authors'])}] 总目著者原文[{i['author_info'][:80]}] 卷{i['juan']} 本{i['nbooks']}{' 年号'+','.join(i['reign']) if i['reign'] else ''}{' 有同年Book' if i['same_year'] else ''}{' 叢書子目' if i['congshu'] else ''} 分类{i['section'][:1]} 版本{i['eds'][:5]}"
def dossier(r):
    L=[f"== {r['book']} 〔初筛：{r['cat']}〕",f"国图：题名「{r['nlc_title']}」 责任者「{r['nlc_author']}」 版本项「{r['ver']}」{' 年号'+','.join(r['reign']) if r['reign'] else ''}；现挂 {r['cur']}"]
    noau=[]
    for k,i in r['cands'].items():
        if k==r['cur'] or i['has_auth'] or i['reign'] or i['same_year']: L.append(fw(k,i,r['cur']))
        else: noau.append(f"{k}(本{i['nbooks']}{',子目' if i['congshu'] else ''})")
    if noau: L.append(f"  无著者同题 Work {len(noau)} 个：{' '.join(noau[:12])}{' …' if len(noau)>12 else ''}")
    if r['cross']: L.append("  同著者异题 Work（著者名经繁化，或有误转）："+'；'.join(f"{w}《{t}》" for w,t,n,s in r['cross']))
    return '\n'.join(L)
size=-(-len(sel)//N); batches=[[]]
for r in sel:
    if len(batches[-1])>=size and r['nlc_title']!=batches[-1][-1]['nlc_title']: batches.append([])
    batches[-1].append(r)
os.makedirs(P+'/batches',exist_ok=True)
for n,b in enumerate(batches):
    open(f'{P}/batches/b{n:02d}.txt','w').write('\n\n'.join(dossier(r) for r in b)+'\n')
    print(n,len(b))
json.dump([r['book'] for r in sel],open(P+'/review_ids.json','w'))
print('合计',len(sel))
