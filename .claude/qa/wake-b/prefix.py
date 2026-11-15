import re,html,sys
sys.path.insert(0,'.')
import lib
from concurrent.futures import ThreadPoolExecutor
ids={}
for l in open('/tmp/wb_ndl_raw.txt'):
    if l.startswith('  '):
        r=l.split('|')[0].strip();ids.setdefault(r.split('-')[0],r)
def j(r):
    d=html.unescape(lib.sru(r))
    sa=re.findall(r'seeAlso rdf:resource="([^"]+)"',d)
    lb=lib.libs(r)
    return r,lb,[s for s in sa if 'ndlsearch' not in s][:2]
with ThreadPoolExecutor(6) as ex:
    for r in ex.map(j,list(ids.values())): print(r)
