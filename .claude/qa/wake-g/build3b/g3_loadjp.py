import subprocess,json,sys
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3/'
paths=[l.rstrip('\n') for l in open(S+'jpbook_paths.txt')]
p=subprocess.Popen(['git','cat-file','--batch'],stdin=subprocess.PIPE,stdout=subprocess.PIPE,cwd='/tmp/wk-wake-g3')
out=[]
for pa in paths:
    p.stdin.write(('origin/main:'+pa+'\n').encode());p.stdin.flush()
    h=p.stdout.readline().split()
    n=int(h[2]);d=p.stdout.read(n);p.stdout.read(1)
    j=json.loads(d)
    out.append({'path':pa,'id':j.get('id'),'title':j.get('title'),'work':j.get('work_id'),'edition':j.get('edition'),'dating':j.get('dating'),'prov':[x.get('institution') for x in j.get('provenance',[])],'src':[ (x.get('source') or '') for x in j.get('provenance',[])],'pub':j.get('publisher') or j.get('publishers')})
json.dump(out,open(S+'jpbooks.json','w'),ensure_ascii=False)
print(len(out)); print(out[0])
