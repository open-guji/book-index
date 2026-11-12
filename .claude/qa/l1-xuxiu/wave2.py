import pickle,re,csv,collections,subprocess
from build_idx import norm_t
W=pickle.load(open('works.pkl','rb')); rows=pickle.load(open('rows_t.pkl','rb')); near=pickle.load(open('near.pkl','rb'))
SRC='d59f2ogb4bgi'
for r in rows: r['done']=len(r['cands'])==1 and any(b==SRC for a,b in W[r['cands'][0]]['ib'])
pickle.dump(rows,open('rows_t2.pkl','wb'))
