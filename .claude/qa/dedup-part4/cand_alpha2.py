"""4a-α2 候选：3b/3a 交来的「同一首位 Entity、同题同署名、含叢書子目」组（多为同一作者全集的不同叢書版本各建一条子目）。
用法：P4WORK=... python3 cand_alpha2.py <清单.tsv>  → $P4WORK/alpha2.json（候选）与 alpha2-skip.tsv（不并，dedup-judged 格式）
规则：组内每条子目所属叢書的首位撰者（撰類角色）＝该 Work 首位责任者；组内非子目 Work 至多 1 条（有则作 keeper，否则取 Book 最多、id 最早的子目）；
同一叢書下不得有两条同题子目；全组已知卷数（含题下 title_info）须全同（抽检见一卷本只收两卷本之一的情形，差 1 也不并）；题名键≤2 字的泛名须全组卷数齐全且相同；朝代相容；敦煌不碰。"""
import sys
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'feat.py')).read())
import json
OKROLE={'撰','撰輯','著','輯撰','撰并輯','纂','編撰','撰著'}
DYN_EQ=lambda a,b: (not a) or (not b) or a==b or a in b or b in a
def fa_raw(w):
    au=[a for a in w.get('authors') or [] if isinstance(a,dict)]
    return (norm_name(au[0].get('name')) if au else ''), (au[0].get('dynasty') if au else '') or w.get('dynasty') or ''
def ca(c):
    a=[x for x in c.get('authors') or [] if isinstance(x,dict)]
    return a[0] if a else {}
out=[]; skip=[]; why=collections.Counter()
for line in open(sys.argv[1]):
    if line.startswith('#'): continue
    ent,key,_,mem=line.rstrip('\n').split('\t')[:4]
    ids=re.findall(r'(d59f[0-9a-z]{8})',mem)
    ids=[i for i in ids if i in W and not W[i].get('merged_into')]
    if len(ids)<2: why['已并或缺']+=1; continue
    fs={i:feat(i) for i in ids}
    def no(r):
        why[r]+=1; skip.extend((ids[0],j,'存疑','4a-α2：%s（同 Entity 同题同名组，含叢書子目）'%r) for j in ids[1:])
    sub=[i for i in ids if fs[i]['congshu'] and fs[i]['cols']]; non=[i for i in ids if i not in sub]
    if len(non)>1: no('非子目 Work 多于 1 条'); continue
    names={fa_raw(W[i])[0] for i in ids}
    if len(names)!=1 or '' in names: no('首位署名不一'); continue
    nm=names.pop(); bad=False; seen=collections.Counter()
    for i in sub:
        for cid,_,_ in fs[i]['cols']:
            c=C[cid]; seen[cid]+=1
            if norm_name(ca(c).get('name'))!=nm or ca(c).get('role') not in OKROLE: bad=True
    if bad: no('叢書首位撰者非本人或角色非撰'); continue
    if any(v>1 for v in seen.values()): no('同一叢書下同题多条(疑异篇)'); continue
    dy={fa_raw(W[i])[1] for i in ids}-{''}
    if any(not DYN_EQ(a,b) for a in dy for b in dy): no('朝代不合'); continue
    js=[({fs[i]['juan']}|fs[i]['bjuan'])-{None} for i in ids]
    alls=set().union(*js)
    if len(alls)>1: no('卷数不一'); continue
    if len(key)<=2 and (any(not j for j in js) or len(alls)!=1): no('泛名且卷数不全'); continue
    if any('敦煌' in (W[i].get('ai_note') or '') for i in ids): no('敦煌'); continue
    if non: k=non[0]
    else: k=sorted(sub,key=lambda i:(-fs[i]['nbooks'],i))[0]
    losers=[i for i in ids if i!=k]
    ev=['《%s》（%s）为叢書子目，所屬叢書%s撰者%s'%(fs[i]['title'],i,'、'.join('《%s》（%s）'%(c[1],c[0]) for c in fs[i]['cols']),ca(C[fs[i]['cols'][0][0]]).get('name')) if fs[i]['cols'] else '《%s》（%s）同署名'%(fs[i]['title'],i) for i in losers]
    ev.append('全组卷數%s'%('、'.join(map(str,sorted(alls))) or '缺'))
    out.append(dict(bulei='α2',key=key,keeper=k,keeper_title=W[k]['title'],author=W[k]['authors'][0].get('name'),dyn=fa_raw(W[k])[1],losers=losers,evidence=ev,partial=False))
print(len(out),'组',sum(len(o['losers']) for o in out),'条被并'); print(why.most_common())
P=__import__('os').environ.get('P4WORK','/tmp/p4')
json.dump(out,open(P+'/alpha2.json','w'),ensure_ascii=False,indent=1)
open(P+'/alpha2-skip.tsv','w').write(''.join('\t'.join(r)+'\n' for r in skip))
