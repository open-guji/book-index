"""把正式库 Work/Book/Collection 读成精简结构，缓存 pickle。"""
import json,glob,os,pickle,sys
ROOT=sys.argv[1] if len(sys.argv)>1 else __import__('os').path.abspath(__import__('os').path.dirname(__file__)+'/../../..')
OUT=__import__('os').environ.get('P4WORK','/tmp/p4')+'/cache.pkl'
W,B,C={},{},{}
for t,store in (('Work',W),('Book',B),('Collection',C)):
    for p in glob.glob(os.path.join(ROOT,t,'*/*/*/*.json')):
        d=json.load(open(p,encoding='utf-8'))
        if d.get('merged_into'): continue
        d['_path']=os.path.relpath(p,ROOT)
        store[d['id']]=d
print({k:len(v) for k,v in (('W',W),('B',B),('C',C))})
pickle.dump((W,B,C),open(OUT,'wb'))
