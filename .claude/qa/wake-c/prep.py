import json,glob,os
SP='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad'
d=json.load(open(SP+'/shard2.json')); ws={x['work'] for x in d}; W={}
for p in glob.glob('/home/user/book-index/Work/*/*/*/*.json'):
    i=os.path.basename(p).split('-')[0]
    if i in ws:
        j=json.load(open(p)); W[i]={'title':j['title'],'authors':[a.get('name') for a in j.get('authors',[])]}
json.dump(W,open('works.json','w'),ensure_ascii=False,indent=1)
