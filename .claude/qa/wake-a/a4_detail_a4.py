# -*- coding: utf-8 -*-
import sys,json,re,os
sys.path.insert(0,'/tmp/wa4'); import a4lib
from cands_a4 import *
OUT='/tmp/wa4/details4.json'
def detail(ncid):
    j=a4lib.getj('https://ci.nii.ac.jp/ncid/%s.json'%ncid)
    if not j: return None
    g=j['@graph'][0]
    def v(x):
        if isinstance(x,list): return [(i.get('@value') if isinstance(i,dict) else i) for i in x]
        return x
    return dict(ncid=ncid,title=(v(g.get('dc:title')) or [''])[0],alt=g.get('dcterms:alternative'),cre=g.get('dc:creator'),pub=v(g.get('dc:publisher')),ext=g.get('dcterms:extent'),date=g.get('dc:date'),pd=v(g.get('prism:publicationDate')),note=g.get('cinii:note'),lang=g.get('dc:language'),
        owners=[(o.get('foaf:name'),o.get('@id','')[-8:]) for o in g.get('bibo:owner',[])],own=g.get('cinii:ownerCount'),part=g.get('dcterms:isPartOf') and [ (p.get('dc:title') if isinstance(p,dict) else p) for p in (g.get('dcterms:isPartOf') if isinstance(g.get('dcterms:isPartOf'),list) else [g.get('dcterms:isPartOf')])][:2])
if __name__=='__main__':
    ids=[l.strip() for l in open(sys.argv[1]) if l.strip()]
    out=json.load(open(OUT)) if os.path.exists(OUT) else {}
    for n,i in enumerate(ids):
        if i in out: continue
        out[i]=detail(i)
        if n%20==0:
            json.dump(out,open(OUT,'w'),ensure_ascii=False); print(n,len(ids),flush=True)
    json.dump(out,open(OUT,'w'),ensure_ascii=False); print('done')
