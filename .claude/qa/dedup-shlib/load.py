import pickle,json,os,re,collections,csv
R='/home/user/book-index/'
W,B=pickle.load(open('bi.pkl','rb'))
inst2W,zw2W=pickle.load(open('bridge.pkl','rb'))
def live(w,d=0):
    while w in W and W[w]['merged'] and d<10: w=W[w]['merged']; d+=1
    return w if w in W else None
A6='/home/user/book_index_json/library_data/_匹配/上海圖書館藏書/A6-研究-20261025/'
rows=list(csv.reader(open(A6+'去重候选-同一上图work对多Work.tsv'),delimiter='\t'))[1:]
groups={}
for r in rows:
    ws=sorted(set(filter(None,(live(w) for w in zw2W.get(r[0],{})))))
    groups[r[0]]=dict(ws=ws,eg=r[3],old=int(r[1]))
