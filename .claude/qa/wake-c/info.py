import sys
from detail import detail
from ncid import holders, ncid_of
for i in sys.argv[1:]:
    d=detail(i)
    if 'err' in d: print(i,'ERR'); continue
    print(d['id'],'|',d['title'][:60],'|',d['pub'],'|',d['date'],'|',d['call'],'|',d['note'][:90])
    if not i.startswith('R100000002'):
        n=ncid_of(i); print('   NCID',n, holders(n)[:250] if n else '')
