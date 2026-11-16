import json,sys,re
jp=json.load(open('jpbooks.json'))
pat=re.compile(sys.argv[1])
for b in jp:
    if pat.search(b['title']) or (len(sys.argv)>2 and b['work'] in sys.argv[2:]):
        d=b.get('dating') or {}
        print(b['id'],b['work'],b['title'][:20],'|',b['edition'],'|',d.get('year') if isinstance(d,dict) else d,'|',','.join(b['prov'])[:50],'|',[re.sub(r'.*(ncid/[A-Z0-9]+).*',r'\1',s) for s in b['src'] if 'ncid' in s or 'R1000' in s])
