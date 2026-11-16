import re,os
CH = dict(zip('学図属総関蔵国会経済広沢当号数対応芸医台専権歴','學圖屬總關藏國會經濟廣澤當號數對應藝醫臺專權歷'))
def conv(s): return ''.join(CH.get(c, c) for c in s)
def holders(n):
    s=open('/tmp/ndlc/ncid_%s.html'%n,encoding='utf-8',errors='ignore').read()
    t=re.sub(r'<script.*?</script>|<style.*?</style>','',s,flags=re.S);t=re.sub(r'<[^>]+>','\n',t);t=re.sub(r'[ \t　]+',' ',t)
    i=t.find('大学図書館所蔵');j=t.find('この図書・雑誌をさがす')
    out=[]
    for x in t[i:j].split('\n'):
        x=x.strip()
        if not x or len(x)>45 or re.match(r'^[\d,/]',x) or 'OPAC' in x or '所蔵' in x or '該当' in x or '絞り込み' in x: continue
        if re.search(r'(大学|大学校|図書館|図書室|博物館|研究所|図書情報館)',x) and not re.search(r'[A-Za-z0-9|]',x):
            x=x.replace('大学共同利用機関法人 人間文化研究機構 ','').replace('附属図書館 中央図書館','附属図書館').replace(' 大学院人文社会系研究科・文学部',' 大学院人文社会系研究科').replace('情報管理施設','').strip()
            out.append(conv(re.sub(r'\s+','',x)))
    return out
