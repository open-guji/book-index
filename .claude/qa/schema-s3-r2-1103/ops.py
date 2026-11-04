import os,json,sys,collections as C
root,mode,apply,types=sys.argv[1],sys.argv[2],sys.argv[3]=='apply',sys.argv[4].split(',')
SITES={k:v.get('short_name') for k,v in json.load(open(os.path.join(root,'schema','resource-sites.json'),encoding='utf8'))['sites'].items()}
stats=C.Counter(); changed=[]; skipped=[]
def dumps(r,ind): return json.dumps(r,indent=ind,ensure_ascii=False)
def need(raw):
    return {'r2':'"short_name"','r3':'"zhsy_id"','r4':'"url"'}[mode] in raw
for t in types:
    for dp,dn,fn in os.walk(os.path.join(root,t)):
        for f in fn:
            if not f.endswith('.json'): continue
            p=os.path.join(dp,f); raw=open(p,encoding='utf8').read()
            if not need(raw): continue
            r=json.loads(raw); mod=False
            if mode=='r2':
                for x in r.get('resources') or []:
                    if isinstance(x,dict) and 'short_name' in x and SITES.get(x.get('id'))==x['short_name']:
                        del x['short_name']; stats['short_name']+=1; mod=True
            elif mode=='r3':
                if 'zhsy_id' in r:
                    new={}
                    for k,v in r.items():
                        if k=='zhsy_id': new['external_ids']={'zhsy_id':v}
                        else: new[k]=v
                    assert 'external_ids' not in r
                    r=new; stats['zhsy']+=1; mod=True
            elif mode=='r4':
                rs=r.get('resources')
                if isinstance(rs,list):
                    by=C.defaultdict(list)
                    for i,x in enumerate(rs):
                        if isinstance(x,dict) and x.get('url'): by[x['url']].append(i)
                    drop=set()
                    for u,ix in by.items():
                        if len(ix)>1:
                            score=lambda i:(len(rs[i]),'metadata' in rs[i])
                            keep=max(ix,key=lambda i:(score(i),-i))
                            for i in ix:
                                if i!=keep: drop.add(i)
                            print('dup',os.path.relpath(p,root),[rs[i]['id'] for i in ix],'keep',rs[keep]['id'])
                    if drop:
                        r['resources']=[x for i,x in enumerate(rs) if i not in drop]; stats['dup_removed']+=len(drop); mod=True
            if not mod: continue
            ind=None
            for i in (2,1,4):
                if raw==dumps(json.loads(raw),i)+'\n' or raw==dumps(json.loads(raw),i): ind=i; nl=raw.endswith('\n'); break
            if ind is None: skipped.append(p); continue
            changed.append(p)
            if apply: open(p,'w',encoding='utf8').write(dumps(r,ind)+('\n' if nl else ''))
print(mode,dict(stats),'files',len(changed),'skipped',len(skipped))
