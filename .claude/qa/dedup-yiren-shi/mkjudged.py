"""新-异人登记-史：由逐组材料（dossier.py 输出）与并批（merge-01/batch.json）生成 dedup-judged 登记。
用法：python3 mkjudged.py dossier.jsonl merge-01/batch.json 输出.tsv 基线sha
复核存疑对.tsv（同目录）里的对登 D。"""
import sys, json, re, csv
dos, plan, out, base = sys.argv[1:5]
import os
losers = {x for g in json.load(open(plan, encoding='utf-8'))['groups'] for x in g['losers']}
ANON = {'', '佚名', '不著撰人', '無名氏', '闕名'}
# 逐组判为存疑（D）的对：名近而无把握证同
D = {
    ('d59fy2dvixvl', 'd59fyt0e6sjl'): '《使蜀日記》方象瑛／方象豫：差一字，未見方象豫即方象瑛之證，存疑',
    ('d59f2hkwx0jn', 'd59f2ne5nxfn'): '《南遷錄》張舜民（宋，一卷）／張舜臣（國史經籍志繫明，二卷）：疑誤字，朝代與卷數不合，存疑',
    ('d59f2gelmxog', 'd59f6efgfe2q'): '《秋浦類集》施少愚／楊少愚：差一字，無他證，存疑',
    ('d59f28668yyp', 'd59f9nmm65mo'): '《幼童傳》劉昭（梁，十卷）／劉劭（文廷式補晉志）：昭／劭形近，朝代不合，存疑',
    ('d59fxt7ltngg', 'd59fy0zotgch'): '《從政錄》同為清汪喜荀撰，然總目一條四卷入集部別集、一條二卷抄本入子部雜家，卷數與部類俱異，未敢並，存疑',
    ('d59f2gpcp79d', 'd59fxruyd3i8'): '《忠義集》趙景良（元，七卷）／趙忠良（總目繫清）：疑總目誤字，朝代不合，存疑',
}
for l in open(os.path.join(os.path.dirname(os.path.abspath(__file__)), '复核存疑对.tsv'), encoding='utf-8'):
    if not l.startswith('#'):
        a, b, why = l.rstrip('\n').split('\t')
        D.setdefault((a, b), '独立复核疑同书而无直接书证（%s），存疑待核' % why)
w = open(out, 'w', encoding='utf-8')
w.write('# 新-异人登记-史（首位责任者异姓／朝代不同，史部，非子目非譜志）同题不并对；基线 book-index main %s；'
        '逐组材料与口径见 .claude/qa/dedup-yiren-shi/README.md\n' % base)
stat = {}
def first(x):
    a = x['authors'][0] if x['authors'] else {}
    return a.get('name') or '', a.get('entity_id'), a.get('dynasty') or x.get('dynasty') or ''
for l in open(dos, encoding='utf-8'):
    g = json.loads(l)
    m = [x for x in g['members'] if x['id'] not in losers]
    if len(m) < 2:
        continue
    ids = [x['id'] for x in m]
    by = {x['id']: x for x in m}
    p = {i: i for i in ids}
    def f(i):
        while p[i] != i:
            i = p[i]
        return i
    edges = []
    for (a, b), note in D.items():
        if a in by and b in by:
            edges.append((a, b, 'D', note)); p[f(a)] = f(b)
    t = g['title']
    zk = bool(re.search(r'(硃卷|朱卷|貢卷|拔卷|試卷|墨卷|薦卷|闈卷|闈藝|行卷|闈墨)$', t))
    es = [first(x)[1] for x in m]
    direct = all(es) and len(set(es)) == len(es)
    k0 = ids[0]
    for i in ids[1:]:
        if f(i) == f(k0):
            continue
        a, b = by[k0], by[i]
        (na, ea, da), (nb, eb, db) = first(a), first(b)
        if na in ANON or nb in ANON:
            grade, why = 'D', '一方無責任者／佚名，同題不足以並（4a-B 口徑：需卷數＋版本或總目同源），存疑'
            cat = '含佚名'
        elif zk:
            grade, why = 'C', '同科試卷各為不同考生之卷（%s／%s），同題異書' % (na, nb)
            cat = '試卷'
        elif ea and eb and ea != eb:
            grade, why = 'C', '首位責任者分掛不同人物（%s%s／%s%s），同題異書' % (da, na, db, nb)
            cat = '異人直判' if direct else '異人逐組'
        else:
            grade, why = 'C', '首位責任者異人（%s%s／%s%s），逐組核無誤字、佔位或別名之證，同題異書' % (da, na, db, nb)
            cat = '異人逐組'
        edges.append((k0, i, grade, why)); p[f(i)] = f(k0)
        stat[cat] = stat.get(cat, 0) + 1
    for a, b, grade, why in edges:
        w.write('%s\t%s\t%s\t异人登记-史 %04d《%s》：%s\n' % (a, b, grade, g['n'], t, why))
print(stat)
