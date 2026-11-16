import json,cs_wake_e3 as c,sys,os
Q=['老子','老子道德經','老子鬳齋口義','老子翼','老子道德經 河上公','老子 訓點','老子 首書','莊子','南華眞經','莊子鬳齋口義','莊子翼','莊子 訓點','莊子 首書','列子','沖虛至德眞經','列子 訓點','荀子','荀子 訓點','荀子增註','韓非子','韓子','韓非子 訓點','孫子','孫子 訓點','孫子兵法','孫子十家註','孫子國字解','魏武註孫子','墨子','管子','管子 訓點','淮南子','淮南鴻烈解','呂氏春秋','吳子','六韜','三略','黃石公三略','司馬法','尉繚子','武經七書','武經直解','文子','鬼谷子','商君書','晏子春秋','公孫龍子','尹文子','慎子','鶡冠子','陰符經','新語','說苑','新序','論衡','抱朴子','山海經','世說新語','顏氏家訓','法言','太玄經','鹽鐵論','賈子新書','孔叢子','孫臏兵法','孫子 諺義','孫子 解']
out={}
fn='/tmp/claude-0/-home-user/899c0af0-484b-5c15-91e5-4641de15fdd6/scratchpad/e_harvest.json'
if os.path.exists(fn): out=json.load(open(fn))
for q in Q:
    for pg in range(1,6):
        k='%s|%d'%(q,pg)
        if k in out: continue
        r=c.search(q,pg)
        if r is None: break
        out[k]=r[0]
        json.dump(out,open(fn,'w'),ensure_ascii=False)
        print(k,len(r[0]),flush=True)
        if len(r[0])<200: break
