# -*- coding: utf-8 -*-
import json,re,collections,sys
d=json.load(open('/tmp/wa4/details4.json'))
SHIN=str.maketrans({'経':'經','伝':'傳','礼':'禮','学':'學','国':'國','点':'點','巻':'卷','斎':'齋','衛':'衞','説':'說','叙':'敍','釈':'釋','読':'讀','訳':'譯','証':'證','訂':'訂','義':'義','広':'廣','対':'對','辺':'邊','気':'氣','関':'關','写':'寫','鈔':'鈔','荘':'莊','庄':'莊','辞':'辭','懐':'懷','両':'兩','蔵':'藏','効':'效','覧':'覽','当':'當','観':'觀','党':'黨','単':'單','応':'應','図':'圖','数':'數','独':'獨','総':'總','与':'與','済':'濟','体':'體','門':'門','来':'來','恆':'恒','亀':'龜','舘':'館','邨':'村'})
def nz(s): return re.sub(r'[\s\[\]\(\)（）　]','',(s or '').translate(SHIN))
def eraY(v):
    for s in (v['pd'] or []):
        if not s: continue
        s=str(s)
        m=re.search(r'明治(\d+)(?:\.\d+)?(?:[-–]\d+)?\s*\[(\d{4})(?:\.\d+)?(?:-\d{4})?\]',s)
        if m and not s.strip().startswith('['):
            n=int(m.group(1)); y=int(m.group(2))
            return n,y,(1867+n==y),s
    return None
def run():
    out=[]
    for k,v in d.items():
        if not v: continue
        e=eraY(v)
        if not e: continue
        out.append((k,v,e))
    return out
if __name__=='__main__':
    r=run(); print(len(r))
    bad=[x for x in r if not x[2][2]]
    print('mismatch',len(bad))
