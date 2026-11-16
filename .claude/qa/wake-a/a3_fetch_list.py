# -*- coding: utf-8 -*-
import sys, json; sys.path.insert(0,'/tmp/wa3')
import a3lib
Q=['周易','易經','易経','易','尚書','書經','書経','書集傳','書集伝','詩經','詩経','毛詩','詩集傳','詩集伝','韓詩外傳','韓詩外伝','古文尚書','易程傳','伊川易傳','周易程傳','周易本義','易傳','書傳','詩傳','詩緝','詩序','禹貢','洪範','周易傳義','程朱傳義','訓點周易','訓點尚書','訓點毛詩','標註','首書周易','首書','詩經集註','詩經集傳','書經集註','周易集註','周易注疏','尚書注疏','毛詩注疏','毛詩正義','尚書正義','周易正義','周易兼義']
out={}
for t in Q:
    st=1; tot=None; n=0
    while True:
        j=a3lib.getj(a3lib.q(t,st))
        if not j: print('FAIL',t,st); break
        tot=a3lib.total(j); its=a3lib.items(j); n+=len(its)
        if not its or st*200>=tot or st>=15: break
        st+=1
    print(t,tot,n,flush=True)
