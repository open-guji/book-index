import json,sys
B=json.load(open('books.json'))
for w in sys.argv[1:]:
    print(w)
    for b in B[w]:
        e=b['edition'] or ''
        if any(k in e for k in '日本和江戶寬延享安永天明文政天保嘉永明治正德享保元祿寶'): print('   ',b['id'],e,b['year'],b['prov'][:3])
