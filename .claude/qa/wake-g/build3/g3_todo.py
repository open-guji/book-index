import json,re,sys
sys.path.insert(0,'.')
c1=json.load(open('cand1.json'));c2=json.load(open('cand2.json'))
C={'cand1.json':c1,'cand2.json':c2}
spec_log=sys.argv[1]; out=sys.argv[2]
rows=[]
txt=open(spec_log).read()
for m in re.finditer(r"\('(cand\d.json)', (\d+), '([^']*)', (\w+), \[(.*?)\]\)",txt):
    f,k,t,y,why=m.groups(); o=C[f][int(k)]
    rows.append(('未建·'+why.strip("'"),t,y,'/'.join(o['ps'])[:60],' '.join(o['ncids'][:3]),o['works'][0][0] if o['works'] else ''))
for m in re.finditer(r"^\s*\d+ (\d+) (\S+) (\d+)\|([^|]*)\|n=\d+ own=\d+ DUP:(\S+)",txt,re.M):
    k,t,y,p,d=m.groups()
    rows.append(('疑重複·未建','%s'%t,y,p,'cluster#'+k,'庫內同Work同年：'+d))
open(out,'w',encoding='utf-8').write('類別\t題名\t刊年\t出版者\tNCID\tWork/Book\n'+'\n'.join('\t'.join(map(str,r)) for r in rows)+'\n')
print(len(rows))
