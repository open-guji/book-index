import subprocess,json,sys,re
S='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/g3/'
idx={}
for l in open(S+'works.txt'):
    m=re.match(r'(d59[a-z0-9]+)-',l)
    if m: idx[m.group(1)]=l.strip()
def path(wid):
    r=subprocess.run(['git','-c','core.quotepath=false','ls-tree','-r','--name-only','origin/main','--','Work'],capture_output=True,text=True,cwd='/tmp/wk-wake-g3')
