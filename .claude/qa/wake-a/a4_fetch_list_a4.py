import sys; sys.path.insert(0,'/tmp/wa4')
import a4lib
Q='周易 易經 易経 周易本義 周易傳義 易傳 尚書 書經 書経 書集傳 詩經 詩経 毛詩 詩集傳 詩集伝 韓詩外傳 韓詩外伝 周禮 周礼 儀禮 儀礼 禮記 礼記 春秋 左傳 左伝 左氏傳 左氏伝 春秋左氏傳 公羊傳 穀梁傳 論語 論語集注 論語集解 孟子 孟子集注 大學 大学 中庸 四書 四書集註 孝經 孝経 古文孝經 爾雅 五經 四書五經 十三經 九經 經書 经書 古文尚書 禮記集説 春秋左氏傳校本 論語義疏 論語徵 論語古義 孟子正義 周易注疏 毛詩注疏 尚書正義 禮記正義 春秋集傳 左氏會箋 孝經鄭注'.split()
for t in Q:
    p=1;n=0
    while True:
        j=a4lib.getj(a4lib.q(t,p))
        if not j: print('FAIL',t,p,flush=True);break
        its=a4lib.items(j);tot=a4lib.total(j);n+=len(its)
        if not its or p*200>=tot or p>=8: break
        p+=1
    print(t,tot,n,flush=True)
