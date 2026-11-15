#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""NDL Search OpenSearch 與 CiNii 查詢輔助：ndl.py <題名> [責任者]"""
import sys, urllib.parse, urllib.request, time, re, xml.etree.ElementTree as ET
UA = 'Mozilla/5.0 (book-index research; wake-d)'
def get(u):
    r = urllib.request.Request(u, headers={'User-Agent': UA})
    with urllib.request.urlopen(r, timeout=40) as f: return f.read().decode('utf-8', 'replace')
NS = {'dc': 'http://purl.org/dc/elements/1.1/', 'dcndl': 'http://ndl.go.jp/dcndl/terms/', 'rdf': 'http://www.w3.org/1999/02/22-rdf-syntax-ns#', 'dcterms': 'http://purl.org/dc/terms/'}
def ndl(title, creator='', cnt=20):
    q = {'title': title, 'cnt': cnt}
    if creator: q['creator'] = creator
    x = get('https://ndlsearch.ndl.go.jp/api/opensearch?' + urllib.parse.urlencode(q))
    root = ET.fromstring(x); out = []
    for it in root.iter('item'):
        g = lambda t: [e.text for e in it.findall(t, NS) if e.text]
        link = (it.find('link').text if it.find('link') is not None else '')
        out.append(dict(title=' '.join(g('dc:title')), creator='/'.join(g('dc:creator')), pub='/'.join(g('dc:publisher')), date='/'.join(g('dc:date')+g('dcterms:issued')), ext='/'.join(g('dc:extent')), link=link, cat=','.join(g('dcndl:materialType')) ))
    return out
def cinii(q, count=20):
    h = get('https://ci.nii.ac.jp/books/search?' + urllib.parse.urlencode({'q': q, 'count': count}))
    out = []
    for blk in h.split('<li class="')[1:]:
        m = re.search(r'href="/ncid/([A-Z0-9]+)"[^>]*>(.*?)</a>', blk, re.S)
        if not m: continue
        g = lambda c: ' '.join(re.sub(r'<[^>]+>', '', x).strip() for x in re.findall(r'class="%s">(.*?)</(?:span|p)>' % c, blk, re.S))
        lib = re.search(r'所蔵館(\d+)館', blk)
        out.append((m.group(1), re.sub(r'<[^>]+>', '', m.group(2)).strip(), g('item_subData item_authordata'), g('pblc'), g('pblcdt'), lib.group(1) if lib else ''))
    return out
if __name__ == '__main__':
    t = sys.argv[1]; c = sys.argv[2] if len(sys.argv) > 2 else ''
    for r in ndl(t, c): print('NDL', r['title'], '|', r['creator'], '|', r['pub'], '|', r['date'], '|', r['ext'], '|', r['link'])
    time.sleep(1)
    for r in cinii(t + " " + c): print("CINII", *r)

def raw(title, creator='', want=None):
    q = {'title': title, 'cnt': 50}
    if creator: q['creator'] = creator
    x = get('https://ndlsearch.ndl.go.jp/api/opensearch?' + urllib.parse.urlencode(q))
    res = []
    for it in x.split('<item>')[1:]:
        if want and want not in it: continue
        res.append(it)
    return res

def holders(ncid):
    h = get('https://ci.nii.ac.jp/ncid/' + ncid)
    t = re.sub(r'<script.*?</script>|<style.*?</style>', '', h, flags=re.S)
    t = re.sub(r'<[^>]+>', ' ', t); t = re.sub(r'\s+', ' ', t)
    i = t.find('書誌事項'); j = t.find('大学図書館所蔵'); k = t.find('この図書・雑誌をさがす')
    bib = t[i:j]; hold = t[j:k]
    note = t[k:t.find('Tweet')]
    return bib.strip(), hold.strip(), note.strip()
