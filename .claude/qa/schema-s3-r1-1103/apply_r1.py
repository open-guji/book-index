import os,json,sys,collections as C
root=sys.argv[1]; apply=len(sys.argv)>2 and sys.argv[2]=='apply'
stats=C.Counter(); changed=[]; skipped=[]; dangling_multi=[]
def dumps(r,ind): return json.dumps(r,indent=ind,ensure_ascii=False)
for t in sys.argv[3].split(','):
    for dp,dn,fn in os.walk(os.path.join(root,t)):
        for f in fn:
            if not f.endswith('.json'): continue
            p=os.path.join(dp,f)
            raw=open(p,encoding='utf8').read()
            if '"group"' not in raw: continue
            r=json.loads(raw)
            rs=r.get('resources'); rg=r.get('resource_groups') or {}
            if not isinstance(rs,list): continue
            cnt=C.Counter(x.get('group') for x in rs if isinstance(x,dict) and x.get('group'))
            singles={g for g,n in cnt.items() if n==1}
            for g,n in cnt.items():
                if n>1 and g not in rg: dangling_multi.append((p,g))
            if not singles: continue
            ind=None
            for i in (2,1,4):
                if raw==dumps(r,i)+'\n' or raw==dumps(r,i): ind=i; nl=raw.endswith('\n'); break
            if ind is None: skipped.append(p); continue
            newrs=[]
            for x in rs:
                g=x.get('group') if isinstance(x,dict) else None
                if g in singles:
                    info=rg.get(g)
                    y={}
                    for k,v in x.items():
                        if k=='group':
                            if info and info.get('label'): y['label']=info['label']
                        elif k=='group_role': pass
                        else: y[k]=v
                    if info and info.get('description'):
                        d=info['description']; y['details']=(y['details']+'；'+d) if y.get('details') else d; stats['desc_merged']+=1
                    if not info: stats['dangling_single']+=1
                    stats['single_to_label']+=1
                    newrs.append(y)
                else: newrs.append(x)
            r['resources']=newrs
            for g in singles: rg.pop(g,None)
            if rg: r['resource_groups']=rg
            elif 'resource_groups' in r: del r['resource_groups']
            changed.append(p)
            if apply: open(p,'w',encoding='utf8').write(dumps(r,ind)+('\n' if nl else ''))
print(dict(stats),'files',len(changed),'skipped',len(skipped),'dangling_multi',len(dangling_multi))
json.dump({'changed':[os.path.relpath(c,root) for c in changed],'skipped':[os.path.relpath(c,root) for c in skipped],'dangling_multi':[(os.path.relpath(a,root),b) for a,b in dangling_multi]},open('/tmp/claude-0/s/r1_manifest.json','w'),ensure_ascii=False)
