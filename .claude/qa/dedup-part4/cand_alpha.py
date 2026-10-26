"""4a-α 候选：叢書子目（無責任者）Work → 同題、所屬叢書撰者＝唯一有責任者 Work 首位責任者。"""
exec(open(__import__('os').path.join(__import__('os').path.dirname(__file__),'feat.py')).read())
import json
OKROLE={'撰','撰輯','著','輯撰','撰并輯','纂','編撰','撰著'}
DYN_EQ=lambda a,b: (not a) or (not b) or a==b or a in b or b in a
def jrel(aj,js):
    aj=set(aj)-{None}; js=set(js)-{None}
    if not aj or not js: return '一侧缺'
    if aj&js: return '同'
    return '差1' if min(abs(a-b) for a in aj for b in js)<=1 else '悬殊'
out=[]; skip=collections.Counter()
for g in groups:
    if g['判定']!='未判' or g['类别'] not in ('一侧有一侧无','同首位'): continue
    ids=g['ids'].split(',')
    fs={i:feat(i) for i in ids}
    named=[f for f in fs.values() if f['fa']]; anon=[f for f in fs.values() if not f['fa']]
    if len(named)!=1: skip['有责任者多于1条(等3a)']+=1; continue
    N=named[0]; kw=W[N['id']]
    nj=({N['juan']}|N['bjuan'])-{None}
    if nj and max(nj)-min(nj)>1: skip['单行本卷数不齐']+=1; continue
    losers=[]; ev=[]
    for f in anon:
        w=W[f['id']]
        if w.get('authors') and '【獨撰子目补撰人】' not in (w.get('ai_note') or ''): skip['anon 有佚名类authors']+=1; continue
        if not f['congshu']: skip['anon 非叢書子目']+=1; continue
        if not f['cols'] or f['nbooks']==0: skip['anon 无丛书book']+=1; continue
        cols=[C[c[0]] for c in f['cols']]
        def ca(c):
            a=[x for x in c.get('authors') or [] if isinstance(x,dict)]
            return a[0] if a else {}
        if not all(norm_name(ca(c).get('name'))==N['fa'] for c in cols): skip['丛书撰者≠有责任者']+=1; continue
        roles={ca(c).get('role') for c in cols}
        if not roles<=OKROLE: skip['丛书角色非撰(%s)'%'/'.join(sorted(r or '' for r in roles))]+=1; continue
        secs=f['secs']
        if not secs or not all(s.startswith('叢書部/獨撰類') for s in secs): skip['anon 著录非叢書部/獨撰類']+=1; continue
        cd={ca(c).get('dynasty') or '' for c in cols}
        if not all(DYN_EQ(d,N['dyn']) for d in cd): skip['朝代不合']+=1; continue
        jr=jrel({f['juan']}|f['bjuan'],{N['juan']}|N['bjuan'])
        if jr=='悬殊': skip['卷数悬殊']+=1; continue
        if '敦煌' in (kw.get('ai_note') or ''): skip['敦煌']+=1; continue
        losers.append(f['id'])
        edhit=[e for e in N['eds'] if e and any(e.rstrip('本')[:4] and (c.get('title') or '').startswith(e.rstrip('本')[:4]) for c in cols)]
        ev.append('《%s》（%s）为叢書子目，所屬叢書%s撰者%s（%s）；卷數%s%s'%(f['title'],f['id'],'、'.join('《%s》（%s）'%(c.get('title'),c['id']) for c in cols),
            ca(cols[0]).get('name'),ca(cols[0]).get('dynasty') or '朝代缺',jr,'；單行本 Work 已有同叢書版本 Book「%s」'%edhit[0] if edhit else ''))
    seen=collections.Counter(c[0] for f in anon if f['id'] in losers for c in f['cols'])
    if any(v>1 for v in seen.values()): skip['同一叢書内同题多条(疑异篇)']+=1; continue
    if not losers: continue
    out.append(dict(bulei=g['部类'],key=g['题名键'],keeper=N['id'],keeper_title=N['title'],author=W[N['id']]['authors'][0].get('name'),dyn=N['dyn'],
                    losers=losers,evidence=ev,partial=len(losers)<len(anon)))
print(len(out),'组', sum(len(o['losers']) for o in out),'条被并'); print(skip.most_common())
print(collections.Counter(o['bulei'] for o in out))
json.dump(out,open(__import__('os').environ.get('P4WORK','/tmp/p4')+'/alpha.json','w'),ensure_ascii=False,indent=1)
