import re,sys
def parse(act,n):
    par=list(range(n));D=set()
    def f(x):
        while par[x]!=x: x=par[x]
        return x
    for p in act.split(';'):
        p=p.strip()
        if p.startswith('M'):
            for e in p[1:].split(','):
                a,b=e.strip().split('>');par[f(int(a))]=f(int(b))
        elif p.startswith('D'):
            for e in p[1:].split(','):
                a,b=e.strip().split('-');D.add(frozenset((int(a),int(b))))
    return par,f,D
def merged(act,n):
    par,f,D=parse(act,n)
    return frozenset(frozenset(i for i in range(n) if f(i)==r) for r in set(f(i) for i in range(n)) if sum(f(i)==r for i in range(n))>1), D
tot=dis=0
for s in ['merge','c1','c2']:
    mine={};cur=None;n={}
    for l in open(f'/tmp/claude-0/review/sample_{s}.txt'):
        m=re.match(r'## (\S+)',l)
        if m: cur=m.group(1);n[cur]=0;continue
        if re.match(r'  \d+\. ',l): n[cur]+=1
        m=re.match(r'  我方判定：(\S.*?)(  |$)',l)
        if m: mine[cur]=m.group(1)
    for l in open(f'/tmp/claude-0/review/verdict_{s}.tsv'):
        k,a,*r=l.rstrip('\n').split('\t')
        tot+=1
        ma,md=merged(mine[k],n[k]); va,vd=merged(a,n[k])
        if ma!=va:
            dis+=1;print(s,k,'mine:',mine[k],'| them:',a,'|',r[0] if r else '')
        elif md!=vd: print('  (D差)',s,k,mine[k],'|',a)
print(tot,dis)
