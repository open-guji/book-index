import json,subprocess,sys
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/shard5.json'
works={}
for x in json.load(open(S)): works.setdefault(x['work'],x['title'])
out={}
for w,t in works.items():
    r=subprocess.run(['git','-c','core.quotepath=false','grep','-l','-F','"work_id": "%s"'%w,'origin/main','--','Book'],capture_output=True,text=True).stdout.split('\n')
    bs=[]
    for l in r:
        if not l: continue
        p=l.split(':',1)[1]
        d=json.loads(subprocess.run(['git','show','origin/main:'+p],capture_output=True,text=True).stdout)
        bs.append({'id':d['id'],'title':d['title'],'ed':d.get('edition'),'y':(d.get('dating') or {}).get('year'),'jp':[x['institution'] for x in d.get('provenance',[])][:4]})
    wj=subprocess.run(['git','show','origin/main:'+subprocess.run(['git','-c','core.quotepath=false','ls-tree','-r','--name-only','origin/main','--','Work/'+w[-3]+'/'+w[-2]+'/'+w[-1]+'/'],capture_output=True,text=True).stdout.split('\n')[0]],capture_output=True,text=True).stdout
    out[w]={'title':t,'books':bs}
json.dump(out,open('/tmp/wf5b/.claude/qa/wake-f/exist2.json','w'),ensure_ascii=False,indent=1)
print(len(out))
