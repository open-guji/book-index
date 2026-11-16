# -*- coding: utf-8 -*-
"""wake-b 第三輪：載入 origin/main 中日本刊本 Book 與全庫 Work 題名索引（緩存到 /tmp/wb3_*.json）"""
import json,subprocess,os,sys,re
REPO='/tmp/wk-wake-b3'
def git(*a,inp=None):
    return subprocess.run(['git','-c','core.quotepath=false','-C',REPO]+list(a),capture_output=True,input=inp).stdout
def load_jp_books(refresh=False):
    f='/tmp/wb3_jpbooks.json'
    if os.path.exists(f) and not refresh: return json.load(open(f))
    out=git('grep','-z','-l','-E',r'"edition": "[^"]*(日本|和刻|倭刻|江戶|江户|五山|古活字|慶長|元和|寬永|寛永|正保|慶安|承應|明曆|萬治|寬文|延寶|天和|貞享|元祿|寶永|正德|享保|元文|寬保|延享|寬延|寶曆|明和|安永|天明|寬政|享和|文化|文政|天保|弘化|嘉永|安政|萬延|文久|元治|慶應|明治)','origin/main','--','Book')
    ps=[p[len('origin/main:'):] for p in out.decode().split('\0') if p]
    inp=''.join('origin/main:%s\n'%p for p in ps).encode()
    raw=git('cat-file','--batch',inp=inp)
    res=[];i=0
    while i<len(raw):
        j=raw.index(b'\n',i);h=raw[i:j].split();n=int(h[2]);body=raw[j+1:j+1+n];i=j+1+n+1
        d=json.loads(body);d['_path']=ps[len(res)];res.append(d)
    json.dump(res,open(f,'w'),ensure_ascii=False);return res
if __name__=='__main__':
    r=load_jp_books(True);print(len(r))
