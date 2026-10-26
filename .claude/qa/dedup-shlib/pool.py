import pickle,collections,json,sys
groups,info=pickle.load(open('feat.pkl','rb')); pairs=pickle.load(open('pairs.pkl','rb'))
Q='/home/user/book-index/.claude/qa/dedup-part4/候选/'
claimed=set()
for f in ['4a-alpha-3c74b458.json','4b-alpha-3c74b458.json']:
    for g in json.load(open(Q+f)): claimed|={g['keeper'],*g['losers']}
def sub(w): return '叢書' in info[w]['bu'] or info[w]['ci']
def show(w): i=info[w]; return f"{w} {i['t']}|{'/'.join((a[0] or '')+('#' if a[3] else '') for a in i['au'][:3])}|{i['dyn']}|j{i['juan']}|b{i['nb']}|{i['bu']}"
pool=[p for p in pairs if not p[3].startswith(('X','Z')) and not(sub(p[1]) or sub(p[2])) and p[1] not in claimed and p[2] not in claimed]
pickle.dump(pool,open('pool.pkl','wb'))
want=sys.argv[1:]
for p in pool:
    if p[3] in want: print(p[3],'|',len(groups[p[0]]['ws']),'\n   ',show(p[1]),'\n   ',show(p[2]))
