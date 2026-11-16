import sys,re,json,collections
sys.path.insert(0,'/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3')
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3/'
jp=json.load(open(S+'jpbooks.json'))
REIGN={'慶長':1596,'元和':1615,'寛永':1624,'寬永':1624,'正保':1644,'慶安':1648,'承応':1652,'承應':1652,'明暦':1655,'明曆':1655,'万治':1658,'萬治':1658,'寛文':1661,'寬文':1661,'延宝':1673,'延寶':1673,'天和':1681,'貞享':1684,'元禄':1688,'元祿':1688,'宝永':1704,'寶永':1704,'正徳':1711,'正德':1711,'享保':1716,'元文':1736,'寛保':1741,'寬保':1741,'延享':1744,'寛延':1748,'寬延':1748,'宝暦':1751,'寶曆':1751,'明和':1764,'安永':1772,'天明':1781,'寛政':1789,'寬政':1789,'享和':1801,'文化':1804,'文政':1818,'天保':1830,'弘化':1844,'嘉永':1848,'安政':1854,'万延':1860,'萬延':1860,'文久':1861,'元治':1864,'慶応':1865,'慶應':1865,'明治':1868}
KN={'元':1,'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10}
def kn(s):
    if s.isdigit(): return int(s)
    if s=='元': return 1
    if '十' in s:
        a,b=s.split('十'); return (KN.get(a,1) if a else 1)*10+(KN.get(b,0) if b else 0)
    return KN.get(s)
def years(txt):
    ys=set(int(m) for m in re.findall(r'(?<!\d)(1[5-9]\d\d)(?!\d)',txt))
    for m in ([] if re.match(r'\s*(明|清|宋|元|唐|金|遼|民國|民国|南宋|北宋)',txt) else re.finditer(r'(%s)\s*([0-9]+|元|[一二三四五六七八九十]+)\s*年?'%'|'.join(REIGN),txt)):
        n=kn(m.group(2))
        if n: ys.add(REIGN[m.group(1)]+n-1)
    return ys
def book_years(b):
    ys=years((b['edition'] or ''))
    d=b.get('dating') or {}
    if isinstance(d,dict) and d.get('year'): ys.add(d['year'])
    return ys
jpby=collections.defaultdict(list)
for b in jp: jpby[b['work']].append(b)
def plan(work,rx,cand='cand1.json',extra_works=()):
    c=json.load(open(S+cand)); rx=re.compile(rx)
    ex=[b for w in (work,)+tuple(extra_works) for b in jpby.get(w,[])]
    print('--- Work',work,'existing JP books:',len(ex))
    for b in ex: print('   DB',b['id'],b['edition'][:40],sorted(book_years(b)),','.join(b['prov'])[:30])
    for k,o in enumerate(c):
        if rx.search(o['tc']):
            dup=[b['id'] for b in ex if o['y'] in book_years(b)]
            print(k,o['tc'][:20],o['y'],'/'.join(o['ps'])[:34],'n=%d'%len(o['ncids']),'|',o['au'][:22],'|DUP:'+','.join(dup) if dup else '')
if __name__=='__main__':
    plan(sys.argv[1],sys.argv[2],*(sys.argv[3:4]))
