# -*- coding: utf-8 -*-
import sys,json; sys.path.insert(0,'/tmp/wa3')
import a3lib
def detail(ncid):
    j=a3lib.getj('https://ci.nii.ac.jp/ncid/%s.json'%ncid)
    if not j: return None
    g=j['@graph'][0]
    def v(x):
        if isinstance(x,list): return [(i.get('@value') if isinstance(i,dict) else i) for i in x]
        return x
    return dict(ncid=ncid,title=(v(g.get('dc:title')) or [''])[0],alt=g.get('dcterms:alternative'),cre=g.get('dc:creator'),pub=v(g.get('dc:publisher')),ext=g.get('dcterms:extent'),date=g.get('dc:date'),pd=g.get('prism:publicationDate'),note=g.get('cinii:note'),lang=g.get('dc:language'),
        owners=[(o.get('foaf:name'),o.get('@id','')[-8:]) for o in g.get('bibo:owner',[])],own=g.get('cinii:ownerCount'),part=[ (p.get('dc:title') if isinstance(p,dict) else p) for p in (g.get('dcterms:isPartOf') or [])][:2] if isinstance(g.get('dcterms:isPartOf'),list) else None)
if __name__=='__main__':
    sel=json.load(open('/tmp/wa3/groups_sel2.json')); out={}
    n=int(sys.argv[1]) if len(sys.argv)>1 else 4
    for s in sel:
        for nc in s['ncids'][:n]:
            if nc not in out: out[nc]=detail(nc)
        print(s['head'],s['year'],flush=True)
        json.dump(out,open('/tmp/wa3/details.json','w'),ensure_ascii=False)
