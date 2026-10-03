#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J 類 description 之生成（lane-E）。

**法**（v1 N6／J11 之例）：由撰人、卷數、著錄諸志、諸志案語所稱之佚文出處與輯家、存佚
五節綴成，**每節皆據本條 `indexed_by` 之引文，不出其外，亦不臆造；凡著錄所無者一字不書**。
無據之節整節略去，不以「不詳」「未詳」充數。

坑 54：讀 description 先容三型（dict／str／None）。本檔只在其為空時才寫。
坑 66：只讀 indexed_by（志書原文），不讀 ai_note（歷輪作業者之判語）。
"""
import re

CN = {'一':1,'二':2,'三':3,'四':4,'五':5,'六':6,'七':7,'八':8,'九':9,'十':10,
      '百':100,'千':1000,'兩':2,'廿':20,'卅':30}

def desc_text(w):
    """容 dict／str／None 三型（坑 54）。"""
    d = w.get('description')
    if isinstance(d, dict): return (d.get('text') or '').strip()
    if isinstance(d, str): return d.strip()
    return ''

def _cn2int(s):
    if not s: return None
    if s.isdigit(): return int(s)
    tot, cur = 0, 0
    for ch in s:
        if ch not in CN: return None
        v = CN[ch]
        if v >= 10:
            cur = (cur or 1) * v
            if v >= 100: tot += cur; cur = 0
        else:
            cur += v
    return tot + cur or None

JUAN = re.compile(r'([0-9]+|[一二三四五六七八九十百千兩廿卅]+)\s*卷')

def juan_of_node(ib):
    """自一節之 title_info 取其卷數（正卷，不取「録一卷」之附録）。"""
    t = ib.get('title_info') or ''
    t = re.split(r'[　\s]*[録錄]', t)[0]
    m = JUAN.search(t)
    return (m.group(0), _cn2int(m.group(1))) if m else (None, None)

def _sec(ib):
    """自 author_info 取其部類（「見史部·別傳類」→「史部·別傳類」）；無則取 section 欄。"""
    a = (ib.get('author_info') or '').strip()
    if not a:
        a = (ib.get('section') or '').strip().replace('／', '·')
        return a or None
    # author_info 一欄名為「撰人」而其實所載者不一：多數是部類（「見史部·別傳類」），
    # 亦有逕書撰人或「不著撰人名氏」者。**只認確是部類者**，餘一概不取——
    # 否則會生出「《四庫全書總目》列於不著撰人名氏」這種話（坑 54 之同理：先問這欄有幾種型）。
    if not re.match(r'^[見在]', a) and not re.search(r'[部類門屬錄録]', a):
        return None
    a = re.sub(r'^[見在]', '', a).strip()
    a = re.split(r'[。；]|原注', a)[0].strip()
    if not re.search(r'[部類門屬錄録]', a): return None
    return a or None


def _int2cn(n):
    """10 → 十；28 → 二十八；105 → 一百零五。卷數之常用範圍足矣。"""
    d = '零一二三四五六七八九'
    if n < 10: return d[n]
    if n < 20: return '十' + (d[n % 10] if n % 10 else '')
    if n < 100:
        return d[n // 10] + '十' + (d[n % 10] if n % 10 else '')
    if n < 1000:
        r = d[n // 100] + '百'
        rem = n % 100
        if not rem: return r
        if rem < 10: return r + '零' + d[rem]
        return r + _int2cn(rem)
    return str(n)


QUOTE_CAP = 200

def _quote(s):
    """引文入「」之前，把其內之「」降為『』，並免「。」」相疊。
    逾 QUOTE_CAP 者截之並明言其截（全文本在 indexed_by，可覆按）——
    《四庫總目》之提要動輒數百字，全錄則描述失其為描述。"""
    s = s.strip().replace('「', '『').replace('」', '』')
    s = re.sub(r'\s+', ' ', s)          # 《經義考》之節多分行，折為單空格
    s = re.sub(r'[。．]+$', '', s)
    if len(s) > QUOTE_CAP:
        s = s[:QUOTE_CAP] + '……（節錄，全文見本條 indexed_by）'
    return s

def _norm(s):
    return re.sub(r'[《》「」，。、．\s（）()・]', '', s or '')

def informative(ib, title):
    """該節之 summary 是否有題名以外之內容。"""
    s = (ib.get('summary') or '').strip()
    if not s: return None
    if _norm(s) == _norm(title): return None
    if _norm(s) == _norm(ib.get('title_info') or ''): return None
    return s

LOSS_CN = {'lost': '佚', 'partially_extant': '殘存', 'extant': '存'}

# 坑 51 已確認「一 Work 誤植兩書」者（known-issues/undated-20260906-一Work誤植兩書三例.json）。
# 此類條之 description **不得逕作一書之描述**——諸節本非一物，合述即是替一個已知的錯誤背書。
MIXED = {
 'd59f2psgsem9': '**本條之著錄實兼兩書，非一書**（已在案，見 known-issues/undated-20260906-一Work誤植兩書三例.json）：'
                 '《隋書經籍志》《新唐書藝文志》所著者范世英《千金方》三卷，'
                 '《宋史藝文志》《崇文總目》所著者孫思邈《千金方》三十卷——撰人、卷數俱異，斷非一書。'
                 '以下諸節照錄其著錄之文，**不代為合一之判**；拆條須先撞庫（孫思邈書庫中多半另有專條），非本道所辦。',
 'd59f2pwuqha9': '**本條之著錄實兼兩書，非一書**（已在案，見 known-issues/undated-20260906-一Work誤植兩書三例.json）：'
                 '《明史藝文志》《欽定四庫全書總目》所著者明何鏜《名山記》十七卷及其後出增輯本，'
                 '《補晉書藝文志（丁國鈞）》《直齋書錄解題》所著者王子年（王嘉，符秦時人）《名山記》一卷，'
                 '即《拾遺記》第十卷之別行本——二者相去六百餘年，斷非一書。'
                 '以下諸節照錄其著錄之文，**不代為合一之判**；拆條須先撞庫，非本道所辦。',
}


def build(w):
    """回 (text, sources)；無可據者回 (None, None)。"""
    ibs = [x for x in (w.get('indexed_by') or []) if x.get('source')]
    if not ibs: return None, None
    title = w.get('title') or ''
    srcs = []
    for ib in ibs:
        if ib['source'] not in srcs: srcs.append(ib['source'])
    out = []
    if w.get('id') in MIXED:
        out.append(MIXED[w['id']])

    # 一、撰人
    au = [a for a in (w.get('authors') or []) if (a.get('name') or '').strip()]
    if au:
        # 一書數撰人者（庫中有二人同撰而舊分作二條，今併者），代與役若一，
        # 不逐人重書——「荀訥撰、晉曹𨚚撰」讀不成話。
        dys = {(a.get('dynasty') or '').strip() for a in au}
        dys.discard('')
        roles = {(a.get('role') or '撰').strip() for a in au}
        names = '、'.join((a.get('name') or '').strip() for a in au)
        dy = (dys.pop() if len(dys) == 1 else '') or (w.get('dynasty') or '').strip() if len(dys) <= 1 else ''
        role = roles.pop() if len(roles) == 1 else '撰'
        if len(au) > 1 and len(roles) == 0: role = '同撰'
        if len(au) > 1 and role == '撰': role = '同撰'
        out.append((dy + names + role if dy else names + role) + '。')
    else:
        out.append('諸志之著錄不著撰人。')

    # 二、卷數
    jj = [(ib['source'],) + juan_of_node(ib) for ib in ibs]
    jj = [(s, txt, n) for s, txt, n in jj if n]
    if jj:
        ns = {n for _, _, n in jj}
        if len(ns) == 1:
            out.append('諸志皆作%s卷。' % _int2cn(jj[0][2]))
        else:
            by = {}
            for s, txt, n in jj: by.setdefault(n, []).append(s)
            parts = ['、'.join('《%s》' % x for x in v) + '作' + _int2cn(k) + '卷'
                     for k, v in sorted(by.items())]
            out.append('諸志所著卷數不一：' + '；'.join(parts) + '。')

    # 三、著錄諸志
    if len(ibs) != len(srcs):
        multi = [s for s in srcs if sum(1 for x in ibs if x['source'] == s) > 1]
        out.append('本條繫著錄%d節，出於%d家：%s（其中%s%s繫二節以上）。'
                   % (len(ibs), len(srcs), '、'.join('《%s》' % s for s in srcs),
                      '、'.join('《%s》' % s for s in multi),
                      '各' if len(multi) > 1 else ''))
    else:
        out.append('本條見於%d家著錄：%s。' % (len(srcs), '、'.join('《%s》' % s for s in srcs)))
    secs = []
    for ib in ibs:
        s = _sec(ib)
        if s:
            t = '《%s》列於%s' % (ib['source'], s)
            if t not in secs: secs.append(t)      # 併條後同志數節，部類每重複
    if secs: out.append('；'.join(secs) + '。')

    # 四、諸志案語（佚文出處與輯家皆在其中，逐字引之，不代為判斷）
    notes = []
    for ib in ibs:
        s = informative(ib, title)
        if s:
            t = '《%s》：「%s」' % (ib['source'], _quote(s))
            if t not in notes: notes.append(t)
    if notes: out.append('諸志之著錄語：' + '；'.join(notes) + '。')

    # 五、存佚
    ls = w.get('loss_status')
    att = [ib.get('attested_status') for ib in ibs if ib.get('attested_status')]
    if ls in LOSS_CN:
        out.append('本庫判其%s。' % LOSS_CN[ls])
    elif att:
        a0 = att[0]
        if a0 in LOSS_CN:
            out.append('諸志之判作「%s」，本庫之 loss_status 未判。' % LOSS_CN[a0])

    # 尾：來歷與限度
    bu = [s for s in srcs if s.startswith('補晉書')]
    if len(bu) >= 2:
        head = ('上列%d家皆' % len(srcs)) if len(bu) == len(srcs) \
               else ('上列%d家之中，%d家' % (len(srcs), len(bu)))
        out.append('按%s是《補晉書藝文志》諸本（清丁國鈞、文廷式、黃逢元、吳士鑑、秦榮光'
                   '五家各自補撰，晉世本無其志），同為回溯補作而非當代之著錄，其所據又多相沿，'
                   '故「見於%d家」不得逕讀為%d家各自獨立之見證。' % (head, len(srcs), len(srcs)))
    out.append('以上諸節皆據本條所繫著錄之引文撮述，逐字可回 indexed_by 覆按；未覆核原書。')
    return ''.join(out), srcs
