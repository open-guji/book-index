import ndl,re,json,time,os
J2T=str.maketrans({'大':'大','学':'學','図':'圖','医':'醫','総':'總','属':'屬','経':'經','国':'國','関':'關','会':'會','蔵':'藏','歴':'歷','広':'廣','辺':'邊','対':'對','与':'與','応':'應','条':'條','済':'濟','発':'發','写':'寫','気':'氣','実':'實','覚':'覺','両':'兩','当':'當','体':'體','礼':'禮','徳':'德','両':'兩','経':'經','単':'單','専':'專','済':'濟','仏':'佛','薬':'藥','済':'濟','来':'來','画':'畫','営':'營','圏':'圈','鉄':'鐵','万':'萬','参':'參','観':'觀','数':'數','岡':'岡','斎':'齋','党':'黨','団':'團','験':'驗','読':'讀'})
CACHE='hold_cache.json'
C=json.load(open(CACHE)) if os.path.exists(CACHE) else {}
def parse(h):
    h=h.replace('&emsp;',' ').replace('&nbsp;',' ')
    h=re.sub(r'^大学図書館所蔵\s*件\s*/\s*全\s*\d+\s*件\s*','',h)
    h=h.split('該当する所蔵館')[0]
    out=[]
    for seg in h.split('OPAC'):
        seg=seg.strip()
        if not seg: continue
        tk=seg.split()
        inst=tk[0]; i=1
        if len(tk)>1 and re.search(r'(図書館|図書室|研究所|文庫|研究科|館|室|センター)$',tk[1]) and not re.match(r'[\d卷巻]',tk[1]): inst+=' '+tk[1]; i=2
        if len(tk)>2 and i==2 and re.search(r'(図書館|図書室|文庫|館|室)$',tk[2]) and not tk[1].endswith('館') : inst+=' '+tk[2]; i=3
        call=' '.join(tk[i:])[:60]
        out.append((inst,call))
    return out
def get(n):
    if n not in C:
        b,h,no=ndl.holders(n); C[n]={'bib':b[:300],'hold':h,'note':no[:500]}; json.dump(C,open(CACHE,'w'),ensure_ascii=False); time.sleep(1)
    return C[n]
if __name__=='__main__':
    import sys
    for n in sys.argv[1:]:
        c=get(n); print(n,c['bib'][:90]); print('   ',[(a.translate(J2T),b) for a,b in parse(c['hold'])])
