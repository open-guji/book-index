import sys,re
sys.path.insert(0,'/tmp/wf5b/.claude/qa/wake-f')
from q2 import get
from pg import page
def holders(ncid):
    t=get('https://ci.nii.ac.jp/ncid/'+ncid)
    s=re.sub(r'\s+',' ',re.sub(r'<[^>]+>','|',t))
    i=s.find('document.write(libraryFilteringSource)'); j=s.find('該当する所蔵館はありません')
    seg=s[i:j] if i>=0 and j>i else ''
    seg=re.sub(r'(\| ?)+','|',seg)
    return seg[:600], ('所蔵館はありません' in s)
for r in sys.argv[1:]:
    p=page(r)
    m=re.search(r'ncid/([A-Z]{2}[0-9X]{7,8})',p)
    ti=p[p.find('タイトル'):][:70]; pub=re.search(r'出版事項\|([^|]*)\|出版年月日等\|([^|]*)',p)
    print('==',r,ti,pub.groups() if pub else '')
    k=p.find('所蔵機関'); 
    if k>=0: print('  NDLholder:',p[k:k+120])
    if m:
        h,no=holders(m.group(1)); print('  ',m.group(1),'NOHOLD' if no and not h else h)
