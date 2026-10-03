#!/usr/bin/env python3
"""協調者每輪之收件：拉 main，列 inbox 未讀（不在 _ledger.json 者），印 status 概覽。
  python3 .claude/qa/coordinator.py            # 只看
  python3 .claude/qa/coordinator.py --ack F1 F2 # 把列出之編號記入 ledger（已處理）
"""
import argparse, glob, json, os, subprocess, datetime
HERE=os.path.dirname(os.path.abspath(__file__)); ROOT=os.path.abspath(os.path.join(HERE,'..','..'))
LEDGER=os.path.join(HERE,'inbox','_ledger.json')
def main():
    ap=argparse.ArgumentParser(); ap.add_argument('--ack',nargs='*',default=[]); ap.add_argument('--no-pull',action='store_true'); a=ap.parse_args()
    if not a.no_pull:
        subprocess.run(['git','-C',ROOT,'fetch','-q','origin','main']); subprocess.run(['git','-C',ROOT,'merge','-q','--no-edit','origin/main'])
    led=json.load(open(LEDGER)) if os.path.exists(LEDGER) else {}
    files=sorted(glob.glob(os.path.join(HERE,'inbox','*','*.md')))
    unread=[f for f in files if os.path.relpath(f,ROOT) not in led]
    print(f'inbox：共 {len(files)}，未讀 {len(unread)}')
    for i,f in enumerate(unread,1):
        rel=os.path.relpath(f,ROOT); first=open(f).readline().strip()
        print(f'  [{i}] {rel}\n      {first[:160]}')
    if a.ack:
        now=datetime.datetime.now(datetime.timezone.utc).isoformat(timespec='seconds')
        for tok in a.ack:
            k=int(tok.lstrip('F'))-1
            if 0<=k<len(unread): led[os.path.relpath(unread[k],ROOT)]=now
        os.makedirs(os.path.dirname(LEDGER),exist_ok=True); json.dump(led,open(LEDGER,'w'),ensure_ascii=False,indent=1)
        print('已記', len(a.ack))
    print('\nstatus：')
    for f in sorted(glob.glob(os.path.join(HERE,'status','*.json'))):
        if os.path.basename(f).startswith('_'): continue
        s=json.load(open(f)); c=s.get('counts',{})
        tot=lambda k: sum(v.get(k,0) for v in c.values())
        print(f"  {s['lane']:12s} {s.get('state','?'):8s} 批{s.get('batch',0):<3} found {tot('found'):5d} fixed {tot('fixed'):5d} res {tot('researched'):4d} rec {tot('recorded'):4d}  {s.get('updated_at','')[:16]}  {s.get('focus','')[:40]}")
    ki=glob.glob(os.path.join(HERE,'known-issues','*.json')); print(f'known-issues：{len(ki)} 檔')
if __name__=='__main__': main()
