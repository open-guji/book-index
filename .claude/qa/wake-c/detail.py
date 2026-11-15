import sys,re
from ndl import get
def detail(i):
    t=get('https://ndlsearch.ndl.go.jp/books/'+i)
    if not t: return {'id':i,'err':1}
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',t,flags=re.S)
    t=re.sub(r'<[^>]+>',' ',t); t=re.sub(r'\s+',' ',t)
    d={'id':i}
    m=re.search(r'タイトル (.*?) (著者・編者|出版事項|出版年)',t); d['title']=m.group(1) if m else ''
    m=re.search(r'出版事項 (.*?) 出版年',t); d['pub']=m.group(1) if m else ''
    m=re.search(r'出版年月日等 (.*?) (出版年|出版年（W3CDTF）)',t); d['date']=m.group(1) if m else ''
    m=re.search(r'連携機関・データベース (.*?)(少なく表示|国立国会図書館サーチ)',t); d['holder']=m.group(1)[:150] if m else ''
    m=re.search(r'請求記号 (\S+)',t); d['call']=m.group(1) if m else ''
    m=re.search(r'一般注記 (.*?) (コレクション|著作権|連携機関|対象|件名)',t); d['note']=m.group(1)[:100] if m else ''
    m=re.search(r'所蔵館 (.*?) (書誌情報|請求)',t); 
    d['ndlhold']='国立国会図書館' if re.search(r'国立国会図書館.{0,40}(デジタル|所蔵|請求記号)',t) and ('R100000002' in i or 'R100000001' in i or 'R100000039' in i) else ''
    return d
if __name__=='__main__':
    for i in sys.argv[1:]: print(detail(i))
