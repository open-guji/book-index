# -*- coding: utf-8 -*-
import re, json, sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import h3lib
N = 'https://ndlsearch.ndl.go.jp/books/'; CI = 'https://ci.nii.ac.jp/ncid/'
CM = {'学':'學','図':'圖','総':'總','属':'屬','経':'經','済':'濟','国':'國','関':'關','広':'廣','会':'會','台':'臺','医':'醫','薬':'藥','歴':'歷','両':'兩','芸':'藝','応':'應','覚':'覺','学':'學','研':'研','蔵':'藏','与':'與','当':'當','営':'營','浜':'濱','岩':'巖','徳':'德','斎':'齋','斉':'齊','辺':'邊','沢':'澤','鉄':'鐵','様':'樣','塩':'鹽','竜':'龍','変':'變','恵':'惠','譲':'讓','禅':'禪','仏':'佛','宝':'寶','済':'濟','体':'體','点':'點','党':'黨','担':'擔','団':'團','圏':'圈','圧':'壓','駅':'驛','験':'驗','観':'觀','険':'險','検':'檢','権':'權','県':'縣','県':'縣','号':'號','仮':'假','価':'價','気':'氣','帰':'歸','旧':'舊','拠':'據','挙':'舉','橋':'橋','実':'實','写':'寫','社':'社','者':'者','収':'收','従':'從','処':'處','暁':'曉','条':'條','状':'狀','乗':'乘','浄':'淨','譜':'譜','晴':'晴','摂':'攝','銭':'錢','双':'雙','蔵':'藏','属':'屬','対':'對','単':'單','脳':'腦','発':'發','払':'拂','変':'變','弁':'辨','没':'沒','万':'萬','訳':'譯','予':'預','来':'來','礼':'禮','霊':'靈','労':'勞','録':'錄','弥':'彌','猟':'獵','専':'專','聴':'聽','隠':'隱','縦':'縱','縄':'繩','剤':'劑','巻':'卷','剣':'劍','歯':'齒','関':'關','宮':'宮','総':'總','継':'繼'}
def inst(name):
    s = re.sub(r'\s+', '', name or '')
    return ''.join(CM.get(c, c) for c in s)
def cih(ncid, with_call=False):
    r = h3lib.nj(ncid)
    return [(inst(o), None, 'CiNii Books ' + CI + ncid) for o in (r['owners'] or [])]
def ndlh(rid, instname, call=None):
    return (instname, call, 'NDL Search ' + N + rid)
def src_ci(ncid): return ('cinii-' + ncid, 'CiNii Books', CI + ncid)
def src_ndl(rid): return ('ndl-' + rid, 'NDL Search', N + rid)

CM.update({'寛':'寬','禄':'祿','暦':'曆','応':'應','広':'廣','衛':'衞','勧':'勸','荘':'莊','悪':'惡','楽':'樂','毎':'每','従':'從','証':'證','説':'說','読':'讀','訳':'譯','伝':'傳','図':'圖','絵':'繪','続':'續','継':'繼','訂':'訂','増':'增','刊':'刊','刻':'刻','譜':'譜','撰':'撰','訓':'訓','点':'點','巻':'卷','註':'註','注':'注','釈':'釋','駅':'驛','観':'觀','聖':'聖','經':'經','蔵':'藏','歳':'歲','実':'實','斎':'齋','弐':'貳','壱':'壹','嶋':'嶋','峰':'峯','旧':'舊'})
def trad(s): return ''.join(CM.get(c, c) for c in (s or ''))
KN = '〇一二三四五六七八九'
def kyear(n):
    if n == 1: return '元'
    s = ''
    if n >= 100: s += KN[n // 100] + '百'; n %= 100; 
    if n >= 10: s += ('' if n // 10 == 1 else KN[n // 10]) + '十'; n %= 10
    if n: s += KN[n]
    return s
def pdparse(pd):
    """'文政9 [1826]' / '[天和2 (1682)]' / '寛政11 [1799] 序' / '嘉永元 [1848]' -> (reign, eranum, year, inferred?)"""
    s = ' '.join(x for x in (pd if isinstance(pd, list) else [pd]) if x)
    m = re.search(r'([^\s\[\]\(\)0-9]{2})\s*(元|\d+|紀元)?\s*[\[\(［]*\s*(?:[^\d\]\)]*?)?(1[0-9]{3})', s)
    reign = None
    m2 = re.search(r'([一-龥]{2})(元|\d+)', s)
    if m2: reign = m2.group(1)
    elif re.search(r'([一-龥]{2})(紀元)', s): reign = re.search(r'([一-龥]{2})紀元', s).group(1)
    y = re.search(r'(1[0-9]{3})', s)
    inferred = bool(re.search(r'序|跋|頃|\?|推定', s)) or bool(re.search(r'^\s*\[[^\]]*\(', s))
    return trad(reign) if reign else None, int(y.group(1)) if y else None, inferred, s
def nvj(n):
    r = h3lib.nj(n); return r
def mk(work, title, hold, edition=None, etype='刻本', note='', desc=None, pubs=None, cert=None, year=None, reign=None, extra_src=(), extra_hold=(), meas=None, key=None):
    """hold: list of ncids (first = representative)"""
    r0 = nvj(hold[0])
    rg, yy, inf, ps = pdparse(r0['pdate'])
    reign = reign or rg; year = year or yy
    pl = pubs if pubs is not None else [trad(p) for p in (r0['pub'] if isinstance(r0['pub'], list) else [r0['pub']]) if p and '不明' not in p and '自筆' not in p]
    pubtxt = '、'.join(pl)
    assert edition, 'edition required'
    cert = cert or ('inferred' if inf else 'attested')
    hl = []
    for n in hold: hl += cih(n)
    hl += list(extra_hold)
    srcs = [src_ci(n) for n in hold] + list(extra_src)
    if meas is None:
        meas = []
        ext = r0['ext'] or ''
        exts = {(nvj(n)['ext'] or '') for n in hold}
        m = re.search(r'(\d+)冊', ext) if len(exts) == 1 else None
        t0 = r0['title'][0] if r0['title'] else ''
        m1 = re.search(r'(\d+)[巻卷]', t0)
        if m1: meas.append((int(m1.group(1)), '卷'))
        if m: meas.append((int(m.group(1)), '冊'))
    creator = trad(r0['creator'] or '')
    dbasis = 'CiNii Books 著錄出版者%s、出版年「%s」' % (pubtxt or '不明', ' '.join(x for x in (r0['pdate'] if isinstance(r0['pdate'], list) else [r0['pdate']]) if x))
    if desc is None:
        desc = '《%s》，%s；%s。據 CiNii Books 著錄（%s），未核原書。' % (title, creator, edition, '／'.join(srcs[i][0].replace('cinii-', 'NCID ') for i in range(min(2, len(srcs)))))
    return dict(work=work, title=title, edition=edition, etype=etype, reign=reign, year=year, cert=cert, dbasis=dbasis, pub=pubtxt or None, meas=meas, hold=hl, src=srcs, desc=desc, note=note)
