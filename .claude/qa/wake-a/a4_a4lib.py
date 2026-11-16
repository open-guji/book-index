# -*- coding: utf-8 -*-
import json, os, sys, time, urllib.parse, subprocess, hashlib
CACHE='/tmp/wa4cache'
def getj(url, jsonmode=True):
    f=os.path.join(CACHE,'c_'+hashlib.md5(url.encode()).hexdigest()+'.json')
    if os.path.exists(f) and os.path.getsize(f)>50: return json.load(open(f,encoding='utf8'))
    delay=4
    for _ in range(6):
        time.sleep(2.0)
        r=subprocess.run(['curl','-sS','-m','40','-A','Mozilla/5.0 (research; book-index)','-w','\n%{http_code}',url],capture_output=True)
        out=r.stdout.decode('utf8','ignore'); body,_,code=out.rpartition('\n')
        if code=='200':
            try: j=json.loads(body)
            except Exception: j=None
            if j is not None:
                open(f,'w',encoding='utf8').write(body); return j
        print('retry',code,url[:90],file=sys.stderr); time.sleep(delay); delay*=2
    return None
def q(title,p=1):
    return 'https://ci.nii.ac.jp/books/opensearch/search?title=%s&format=json&count=200&year_from=1868&year_to=1911&p=%d'%(urllib.parse.quote(title),p)
def items(j):
    try: return j['@graph'][0].get('items',[])
    except Exception: return []
def total(j):
    try: return int(j['@graph'][0].get('opensearch:totalResults'))
    except Exception: return -1
