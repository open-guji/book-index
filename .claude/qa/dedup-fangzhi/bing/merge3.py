#!/usr/bin/env python3
"""与 main 冲突时逐键三方合并 Work JSON：ai_note 取 main 后接本分支新增段，列表取并集，revision 取大者加一，其余一侧未改取另一侧。

    git merge origin/main  # 出冲突后
    python3 merge3.py <冲突文件>…
"""
import json,subprocess,sys
def show(ref,p):
    r=subprocess.run(['git','show',f'{ref}:{p}'],capture_output=True,text=True); return json.loads(r.stdout) if r.returncode==0 else {}
def bump(a,b):
    x=max([tuple(map(int,v.split('.'))) for v in (a,b)]); return '%d.%d.%d'%(x[0],x[1],x[2]+1)
def m(B,O,T,k=''):
    if O==B: return T
    if T==B or O==T: return O
    if k=='revision': return bump(O,T)
    if k=='ai_note' and isinstance(O,str) and isinstance(T,str) and O.startswith(B or ''):
        return T+O[len(B or ''):]
    if isinstance(O,dict) and isinstance(T,dict):
        B=B if isinstance(B,dict) else {}; r={}
        for kk in list(T)+[x for x in O if x not in T]:
            if kk in O and kk in T: r[kk]=m(B.get(kk),O[kk],T[kk],kk)
            elif kk in T:
                if kk in B and B[kk]==T[kk]: continue  # ours deleted
                r[kk]=T[kk]
            else:
                if kk in B and B[kk]==O[kk]: continue
                r[kk]=O[kk]
        return r
    if isinstance(O,list) and isinstance(T,list):
        B=B if isinstance(B,list) else []
        rem=[x for x in B if x not in O]
        return [x for x in T if x not in rem]+[x for x in O if x not in B and x not in T]
    raise SystemExit(f'无法自动合并 {k}')
for p in sys.argv[1:]:
    B,O,T=show(':1',p),show(':2',p),show(':3',p)
    r=m(B,O,T); open(p,'w',encoding='utf-8').write(json.dumps(r,ensure_ascii=False,indent=2)+'\n'); print('ok',p)
