import json,re,sys,ndl
E="慶長1596 元和1615 寬永1624 寛永1624 正保1644 慶安1648 承應1652 明曆1655 萬治1658 寬文1661 寛文1661 延寶1673 天和1681 貞享1684 元祿1688 寶永1704 正德1711 享保1716 元文1736 寬保1741 延享1744 寬延1748 寶曆1751 明和1764 安永1772 天明1781 寬政1789 寛政1789 享和1801 亨和1801 享保1716 文化1804 文政1818 天保1830 弘化1844 嘉永1848 安政1854 萬延1860 文久1861 元治1864 慶應1865 明治1868".split()
E={x[:-4]:int(x[-4:]) for x in E}
CN="一二三四五六七八九十"
def cn(s):
    s=s.replace('元','一'); n=0
    if '十' in s:
        a,b=s.split('十'); n=(CN.index(a)+1 if a else 1)*10+(CN.index(b)+1 if b else 0)
    else: n=CN.index(s)+1
    return n
def year(ed):
    m=re.search('(%s)(元|[一二三四五六七八九十]+|[0-9]+)年'%'|'.join(E),ed)
    if m:
        n=int(m.group(2)) if m.group(2).isdigit() else cn(m.group(2)); return E[m.group(1)]+n-1
    m=re.search('(%s)'%'|'.join(E),ed)
    return None
if __name__=='__main__':
    d=json.load(open('shard7.json'))
    for r in d:
        y=year(r['edition'])
        print(r['id'],r['title'],r['edition'][:30],y)
