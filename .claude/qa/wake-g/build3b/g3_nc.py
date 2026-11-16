import json,re,subprocess,os,time,sys
sys.path.insert(0,'/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3')
NC='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3/nc/'
os.makedirs(NC,exist_ok=True)
UA='Mozilla/5.0 (X11; Linux x86_64) research-script'
def fetch(ncid):
    f=NC+ncid+'.json'
    if os.path.exists(f) and os.path.getsize(f)>200:
        try: return json.load(open(f))
        except: pass
    for k in range(4):
        time.sleep(1.1*(k+1))
        r=subprocess.run(['curl','-sS','-m','40','-A',UA,'https://ci.nii.ac.jp/ncid/%s.json'%ncid],capture_output=True)
        try:
            j=json.loads(r.stdout.decode('utf8','ignore'))
            json.dump(j,open(f,'w'),ensure_ascii=False); return j
        except Exception: pass
    return None
def L(x):
    if x is None: return []
    return x if isinstance(x,list) else [x]
def val(x):
    if isinstance(x,dict): return x.get('@value') or x.get('foaf:name') or ''
    return str(x)
def info(ncid):
    f2=NC+ncid+'.info'
    if os.path.exists(f2): return json.load(open(f2))
    j=fetch(ncid)
    if not j: return None
    e=[g for g in j['@graph'] if g.get('@type')=='bibo:Book' or 'dc:title' in g]
    e=e[0]
    owners=[]
    for o in L(e.get('bibo:owner')):
        n=val(o.get('foaf:name')) if isinstance(o,dict) else str(o)
        owners.append(n)
    r=dict(ncid=ncid,title=val(L(e.get('dc:title'))[0]) if e.get('dc:title') else '',creator=val(e.get('dc:creator')),pub=[val(p) for p in L(e.get('dc:publisher'))],
        date=val(e.get('dc:date')),pd=[val(x) for x in L(e.get('prism:publicationDate'))],extent=val(e.get('dcterms:extent')),owners=owners,notes=[val(x) for x in L(e.get('cinii:note'))],
        alt=[val(x) for x in L(e.get('dcterms:alternative'))],series=[val(x) for x in L(e.get('dcterms:isPartOf') or e.get('dc:relation'))] ,nown=e.get('cinii:ownerCount'))
    json.dump(r,open(f2,'w'),ensure_ascii=False)
    try: os.remove(NC+ncid+'.json')
    except: pass
    return r
if __name__=='__main__':
    for n in sys.argv[1:]: print(json.dumps(info(n),ensure_ascii=False,indent=1))
