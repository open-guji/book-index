#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""對選定 (work idx, year) 簇取 NCID JSON 詳情（緩存），打印要點。"""
import json, sys, re, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetch3, analyze2
S = fetch3.S
SEL = [(1,1777),(7,1794),(8,1803),(35,1821),(35,1825),(35,1866),(36,1801),(37,1724),(43,1818),(46,1647),(46,1683),(46,1819),(46,1823),(48,1855),(48,1866),(66,1821),(66,1850),(71,1759),(74,1639),(84,1668),(84,1823),(84,1827),(84,1844),(86,1832),(90,1843),(90,1855),(98,1842),(112,1723),(125,1793),(126,1739),(129,1682)]
works = json.load(open(S + '/a_works.json'))
def detail(ncid):
    j = fetch3.getj('https://ci.nii.ac.jp/ncid/%s.json' % ncid)
    if not j: return None
    g = j['@graph'][0]
    def v(x):
        if isinstance(x, list): return [ (i.get('@value') if isinstance(i, dict) else i) for i in x]
        return x
    return dict(ncid=ncid, title=v(g.get('dc:title'))[0] if g.get('dc:title') else '', alt=g.get('dcterms:alternative'), cre=g.get('dc:creator'), pub=v(g.get('dc:publisher')), ext=g.get('dcterms:extent'), date=g.get('dc:date'), pd=g.get('prism:publicationDate'), note=g.get('cinii:note'), lang=g.get('dc:language'),
                owners=[(o.get('foaf:name'), o.get('@id', '')[-8:]) for o in g.get('bibo:owner', [])], own=g.get('cinii:ownerCount'))
if __name__ == '__main__':
    out = {}
    for wi, y in SEL:
        w = works[wi]
        # find the index by i
        w = [x for x in works if x['i'] == wi][0]
        lst = fetch3.items(fetch3.getj(fetch3.q(w['title'])))
        rec = [x for x in lst if x.get('dc:date') == str(y)]
        ids = []
        for x in rec:
            t = analyze2.nz(re.sub(r'[,，]?\s*\d+[巻卷篇冊]?.*$', '', x['title']))
            ids.append((int(x.get('cinii:ownerCount') or 0), x['@id'][-10:]))
        ids = [n for _, n in sorted(ids, reverse=True)][:int(sys.argv[1]) if len(sys.argv) > 1 else 5]
        out['%d|%d' % (wi, y)] = [detail(n) for n in ids]
    json.dump(out, open(S + '/a_ncid.json', 'w'), ensure_ascii=False)
    print('done')
