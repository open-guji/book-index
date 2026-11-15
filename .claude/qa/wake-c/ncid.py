import re,sys
from ndl import get
from detail import detail
def holders(ncid):
    t=get('https://ci.nii.ac.jp/ncid/'+ncid)
    if not t: return None
    s=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S); s=re.sub(r'<[^>]+>','\n',s); s=re.sub(r'\n\s*\n+','\n',s)
    a=s.find('大学図書館所蔵'); b=s.find('該当する所蔵館はありません')
    seg=s[a:b] if a>=0 else ''
    seg=seg.replace('\n',' ')
    return re.sub(r'\s+',' ',seg)[:400]
def ncid_of(i):
    t=get('https://ndlsearch.ndl.go.jp/books/'+i) or ''
    m=re.search(r'NACSIS書誌ID（NCID）\s*(?:<[^>]+>\s*)*([A-Z]{2}[0-9]{7}[0-9X])',t)
    return m.group(1) if m else None
