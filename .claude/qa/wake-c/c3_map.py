# -*- coding: utf-8 -*-
"""題名＋責任者 → 庫內 Work（只掛已有 Work，不新建）。返回 (work_id, 簡稱) 或 None。"""
import re
N = str.maketrans('経伝学説証図礼誌覚訳辞処点様楽斎広国実斉党歳関圧鉄尽猟徴弁観覧', '經傳學說證圖禮誌覺譯辭處點樣樂齋廣國實齊黨歲關壓鐵盡獵徵辨觀覽')
def norm(s): return (s or '').translate(N).replace('註', '注').replace('註', '注')
def classify(title, cr, alt=''):
    t = norm(title); c = norm(cr); a = norm(' '.join(alt) if isinstance(alt, list) else alt)
    tt = t + ' ' + a
    # 日人著述／特定
    for pat, w, nm in [(r'論語徵集覽', 'd59f2pw12xhc', '論語徵集覽'), (r'論語徵(?!集覽|廣義|正文)|論語徴', 'd59f2q3r7e2p', '論語徵'),
                       (r'論語古義', 'd59gdtwu05qp', '論語古義'), (r'論語古訓(?!外傳)', 'd59gdtwu05qq', '論語古訓'),
                       (r'論語語由', 'd59gdtwu05qe', '論語語由'), (r'論語繹解', 'd59gdtwu05qd', '論語繹解'), (r'論語考文', 'd59gdtwu05qi', '論語考文'),
                       (r'論語義疏|論語集解義疏', 'd59f284r21vn', '論語義疏'), (r'孝經刊誤', 'd59f2hsowvsw', '孝經刊誤'),
                       (r'孝經大義', 'd59f2j564ow1', '孝經大義'), (r'四書或問', 'd59f2ht7ycxu', '四書或問'), (r'大學或問', 'd59f2hjvgjcx', '大學或問'), (r'中庸或問', 'd59f2hm0k5j6', '中庸或問'),
                       (r'論語或問', 'd59f2hk899mp', '論語或問'), (r'孟子或問', 'd59f2hkdvjeq', '孟子或問'), (r'四書集編', 'd59f2htfg1z4', '四書集編'), (r'四書纂疏', 'd59f2gomh9mo', '四書纂疏')]:
        if re.search(pat, tt): return w, nm
    if re.search(r'(標記|標注|考訂|首書|頭書|欄外|標註|補注|音義|考異|攷)', tt) and re.search(r'論語|孟子|孝經', tt): return None  # 日人增注衍生本，歸屬不明
    if re.search(r'古文孝經', tt) and re.search(r'孔|傳', tt+c): return 'd59f21ep59mo', '古文孝經'
    if re.search(r'孝經注疏|孝經註疏', tt): return 'd59fxxkxqrr4', '孝經注疏'
    if re.search(r'御注孝經|御註孝經', tt): return 'd59f28mutk3l', '御注孝經'
    if re.search(r'^(古文)?孝經', t) and re.search(r'玄宗', c): return 'd59f28mutk3l', '御注孝經'
    if re.search(r'爾雅(注疏|疏)|爾雅.*郭璞|爾雅$|爾雅 ', t+' '): return ('d59f2ht89lhc', '爾雅注疏') if re.search(r'注疏|疏|郭', tt+c) else None
    if re.search(r'爾雅翼', tt): return 'd59fy3pll3pc', '爾雅翼'
    multi = len(re.findall(r'大學|中庸|論語|孟子', t)) >= 2 or re.search(r'^四書', t)
    zhu = re.search(r'朱熹|朱子|朱文公', c)
    if re.search(r'^[\W]*(四書)', t) and zhu and not re.search(r'或問|纂疏|集編|大全|蒙引|存疑|講義|俚諺|鈔|抄|解|示蒙|字詁', t): return 'd59f2hry2h34', '四書章句集注'
    if multi and zhu and not re.search(r'或問|纂疏|講義|解|鈔|抄', t): return 'd59f2hry2h34', '四書章句集注'
    if re.fullmatch(r'\W*(論語)(\s*\d*[巻卷]\W*)?', t.split(' ; ')[0].strip()) or re.fullmatch(r'論語\W*(\d+[巻卷]|全|白文|標記)?\W*', t.strip()):
        if re.search(r'何晏|古本|集解', c + t + a): return 'd59f27xfwzya', '論語何晏集解'
        if zhu: return 'd59f2hfxqsqo', '論語集注'
        return None
    if re.search(r'論語集解', t + a) and not re.search(r'集解標記|考異|校勘', t): return 'd59f27xfwzya', '論語何晏集解'
    if re.search(r'論語集注|論語集註', t) and zhu: return 'd59f2hfxqsqo', '論語集注'
    if re.fullmatch(r'\W*(孟子)(\s*\d*[巻卷]\W*)?(存\d+[巻卷])?\W*', t.strip()) or re.search(r'^孟子集注|^孟子集註', t):
        if zhu: return 'd59f2hgl5lhd', '孟子集注'
        if re.search(r'趙', c+t+a): return 'd59f20a3cxs0', '孟子趙岐注'
        return None
    if re.search(r'^孟子趙[註注氏]|孟子趙岐', t+a): return 'd59f20a3cxs0', '孟子趙岐注'
    if re.fullmatch(r'\W*大學(\s*\d*[巻卷]\W*)?', t.strip()) and zhu: return 'd59f2htvoe80', '大學章句'
    if re.search(r'^大學章句', t): return 'd59f2htvoe80', '大學章句'
    if re.fullmatch(r'\W*中庸(\s*\d*[巻卷]\W*)?', t.strip()) and zhu: return 'd59f2hracfsy', '中庸章句'
    if re.search(r'^中庸章句', t): return 'd59f2hracfsy', '中庸章句'
    return None

ALLOW = {
 '孟子集注': {'孟子', '孟子集注'}, '孟子趙岐注': {'孟子', '孟子趙注', '孟子趙氏注'}, '論語集注': {'論語', '論語集注'},
 '論語何晏集解': {'論語', '論語集解', '縮臨古本論語集解', '古本論語集解'}, '大學章句': {'大學', '大學章句'}, '中庸章句': {'中庸', '中庸章句'},
 '四書章句集注': {'四書', '四書集注', '[四書集注]', '大學', '中庸', '論語', '孟子', '四書章句集注'}, '論語徵': {'論語徵'}, '論語徵集覽': {'論語徵集覽'},
 '論語古義': {'論語古義'}, '論語古訓': {'論語古訓'}, '論語繹解': {'論語繹解'}, '論語語由': {'論語語由'}, '論語考文': {'論語考文'},
 '論語義疏': {'論語集解義疏', '論語義疏'}, '大學或問': {'大學或問'}, '中庸或問': {'中庸或問'}, '孟子或問': {'孟子或問'}, '論語或問': {'論語或問'},
 '古文孝經': {'古文孝經', '古文孝經孔傳'}, '孝經注疏': {'孝經注疏'}, '御注孝經': {'孝經', '御注孝經'}, '四書纂疏': {'四書纂疏'}, '四書集編': {'四書集編'}, '四書或問': {'四書或問'}, '孝經大義': {'孝經大義'}, '孝經刊誤': {'孝經刊誤'}, '爾雅注疏': {'爾雅注疏', '爾雅'}, '爾雅翼': {'爾雅翼'},
}
def core_title(title):
    t = norm(title if isinstance(title, str) else title[0])
    t = re.split(r'\s[;.]\s|\s*;\s*|\s\.\s', t)[0]
    t = re.sub(r'[\s,，]*(?:\d+[巻卷]|存\d+[巻卷]|\(存.*?\)|\(.*?\)|附.*)', '', t)
    return t.strip()
def allowed(title, wname): return core_title(title) in ALLOW.get(wname, set())
