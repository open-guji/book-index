import sys,re
sys.path.insert(0,'/tmp/wf5b/.claude/qa/wake-f')
from q2 import get
def page(rid):
    t=get('https://ndlsearch.ndl.go.jp/books/'+rid)
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    t=re.sub(r'<[^>]+>','|',t); t=re.sub(r'\s+',' ',t); t=re.sub(r'(\| ?)+','|',t)
    return t
if __name__=='__main__':
    for r in sys.argv[1:]:
        t=page(r); i=t.find('タイトル'); print('==',r,len(t)); print(t[max(i,0):max(i,0)+1100])
