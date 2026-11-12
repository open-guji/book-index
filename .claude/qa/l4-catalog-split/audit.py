import sys,pickle,random,collections
S="/tmp/claude-0/-home-user/6391c0cf-8f64-5490-8408-a53b15323acd/scratchpad/"
idx=pickle.load(open(S+"idx.pkl","rb"))
key,g,n=sys.argv[1],sys.argv[2],int(sys.argv[3])
rows=[l.rstrip("\n").split("\t") for l in open(S+key+"-ledger.tsv",encoding="utf-8")]
rows=[r for r in rows if r[0]==g]
random.seed(7); 
for r in random.sample(rows,min(n,len(rows))):
    c=r[6].split(",")[0]; v=idx[c]
    print(r[2],"|",r[3],r[4][:6],r[5],"=>",v["t"],v["a"][:2],v["p"],"srcs",len(v["src"]))
