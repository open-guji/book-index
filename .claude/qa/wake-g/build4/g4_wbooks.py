import subprocess,sys,json,re
ids=sys.argv[1:]
rx='"work_id": "(%s)"'%'|'.join(ids)
fs=subprocess.run(['git','-c','core.quotepath=false','grep','-l','-E',rx,'origin/main','--','Book'],capture_output=True,text=True,cwd='/tmp/wk-g4').stdout.split('\n')
p=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,cwd='/tmp/wk-g4')
for f in fs:
    if not f: continue
    p.stdin.write((f+'\n').encode());p.stdin.flush()
    h=p.stdout.readline().split();n=int(h[2]);d=p.stdout.read(n);p.stdout.read(1)
    j=json.loads(d); dt=j.get('dating') or {}
    print(j['id'],j['work_id'],j['title'][:18],'|',(j.get('edition') or '')[:48],'|',dt.get('year') if isinstance(dt,dict) else '', '|',','.join(x.get('institution','')[:6] for x in j.get('provenance',[]))[:40])
