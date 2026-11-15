"""sjj-members 公用：题名异体归一、责任者解析、库内索引（流式读 git 对象，免检出）。"""
import csv, os, pickle, re, subprocess, sys, json, threading
import opencc
HERE = os.path.dirname(os.path.abspath(__file__)); BI = os.path.abspath(os.path.join(HERE, '../../..'))
sys.path.insert(0, os.path.join(BI, '.claude/qa'))
from scan import VARIANTS
cc = opencc.OpenCC('t2s')
EX = str.maketrans({'経':'經','註':'注','徴':'徵','辨':'辯','従':'從','与':'與','対':'對','関':'關','両':'兩','徳':'德','説':'說','呉':'吳','録':'錄','懐':'懷','倶':'俱','絶':'絕','内':'內','戸':'戶','静':'靜','釣':'鈞','顔':'顏','増':'增','寳':'寶','兪':'俞','啓':'啟','峯':'峰','煕':'熙','栄':'榮','稲':'稻','島':'島','邉':'邊','俟':'竢','琅':'瑯','祕':'秘','徑':'徑','爲':'為','說':'說','裏':'裡','藝':'藝'})
PUNCT = re.compile(r'[\s·・、，,。．.：:；;「」『』《》〈〉()（）〔〕【】\[\]]')
BR = re.compile(r'（[^（）]*）|\([^()]*\)|〔[^〔〕]*〕|【[^【】]*】|\[[^\[\]]*\]')
def norm(s): return cc.convert(PUNCT.sub('', BR.sub('', s or '')).translate(VARIANTS).translate(EX))
def nname(s): return cc.convert((s or '').translate(VARIANTS).translate(EX))
def clean_title(t):
    t = re.sub(r'\s*[,，]\s*\d+卷.*$', '', t)
    t = re.sub(r'\s+:\s+.*$', '', t)
    t = t.replace('　', '').strip()
    return t
ROLES = [('輯校', '輯校'), ('纂修', '纂'), ('校刊', '校刊'), ('校閲', '校'), ('校正', '校'), ('檢校', '校'), ('考訂', '校'), ('參訂', '校'), ('批點', '評'), ('評次', '評次'), ('評註', '評注'), ('評選', '評選'), ('補注', '補注'), ('述註', '述注'), ('句解', '句解'),
         ('蒐輯', '輯'), ('編輯', '編'), ('撰', '撰'), ('輯', '輯'), ('編', '編'), ('著', '撰'), ('述', '述'), ('註', '注'), ('注', '注'), ('校', '校'), ('訂', '校'), ('評', '評'), ('集', '輯'), ('譯', '譯'), ('書', '書'), ('箋', '箋')]
def parse_au(s):
    """返回 (authors[(name,role,dyn_hint)], composite)"""
    s = (s or '').strip()
    if re.search(r'\s\.\s|^\.', s) or s.count('撰') > 1 and ' . ' in s: return None, True
    out = []
    for part in re.split(r'\s*;\s*|\s*,\s*|，', s):
        part = part.strip()
        if not part: continue
        m = re.match(r'^[\(（](.*?)[\)）]\s*(.*)$', part); hint = None
        if m: hint, part = m.group(1), m.group(2)
        part = part.replace('[', '').replace(']', '').replace('(釋)', '釋').strip()
        role = None
        for k, v in ROLES:
            if part.endswith(k) and len(part) > len(k):
                role = v; part = part[:-len(k)].strip(); break
        part = re.sub(r'[\s\[\]]+$', '', part)
        if part: out.append((part, role or '撰', hint))
    # 后续无角色者继承：「A, B撰」→ 都是撰
    return out, False
G = '/home/user/book-index'
def load_idx(path):
    return pickle.load(open(path, 'rb'))

DISP = str.maketrans({'黄':'黃','径':'徑','歳':'歲','弐':'貳','覚':'覺','写':'寫','浄':'淨','属':'屬','当':'當','栄':'榮','荘':'莊','尭':'堯','恵':'惠','満':'滿','済':'濟','営':'營','数':'數','専':'專','剣':'劍','厳':'嚴','払':'拂','団':'團','応':'應','塩':'鹽','壱':'壹','弁':'辨','拠':'據','担':'擔','畳':'疊','礼':'禮','称':'稱','縄':'繩','険':'險','験':'驗','駅':'驛','鉄':'鐵','険':'險','徳':'德','経':'經','説':'說','呉':'吳','録':'錄','懐':'懷','倶':'俱','徴':'徵','絶':'絕','内':'內','戸':'戶','静':'靜','釣':'鈞','顔':'顏','増':'增','寳':'寶','兪':'俞','啓':'啟','煕':'熙','覧':'覽','観':'觀','両':'兩','関':'關','対':'對','従':'從','辺':'邊','実':'實','来':'來','眞':'真','総':'總','巻':'卷','経':'經','歴':'曆','暦':'曆','盧':'盧','従':'從','廣':'廣','齋':'齋','澤':'澤','獨':'獨','濵':'濱','圖':'圖','寛':'寬','応':'應','隠':'隱','斎':'齋','択':'擇','様':'樣','変':'變','継':'繼','縁':'緣','賛':'贊','訳':'譯','読':'讀','訓':'訓','遺':'遺','国':'國','学':'學','舘':'館','蔵':'藏','輯':'輯','挙':'舉','昇':'升','訂':'訂','広':'廣','鈔':'鈔'})
GENERIC_SEG = re.compile(r'^(影印|出版年は|版心|巻頭|扉の|序の|付[:：]|附[:：]|各冊|前半|後半|訓点|訓點|目録|収録|収録内容|丁付|本文|標題紙|跋|序跋|「.*」,序|附録|藏書印|落丁|巻末|題簽|題签)')
YR = re.compile(r'(\d+)年')
CN = '〇一二三四五六七八九'
def cn_num(n):
    n = int(n)
    if n < 10: return CN[n]
    if n < 20: return '十' + (CN[n % 10] if n % 10 else '')
    if n < 100: return CN[n // 10] + '十' + (CN[n % 10] if n % 10 else '')
    return str(n)
def disp(s):
    s = s.translate(DISP).replace('径', '徑').replace('歳', '歲')
    s = re.sub(r'(\d+)〜(\d+)\((\d{4})〜(\d+)\)年', lambda m: cn_num(m.group(1)) + '至' + cn_num(m.group(2)) + '年（' + m.group(3) + '—19' + m.group(4) + '）', s)
    s = re.sub(r'(\d+)\((\d{3,4})\)\s*年', lambda m: cn_num(m.group(1)) + '年（' + m.group(2) + '）', s)
    s = re.sub(r'(\d+)年', lambda m: cn_num(m.group(1)) + '年', s)
    s = re.sub(r'\((\d{3,4})(?:-\d{3,4})?\)', lambda m: '（' + m.group(0)[1:-1] + '）', s)
    s = re.sub(r',\s*([^,]{1,6})の項$', r'，\1部分', s)
    s = s.replace('元年', '元年')
    s = s.replace('民国', '民國').replace('清・', '清').replace('明・', '明').replace('日本・', '日本').replace('朝鮮・', '朝鮮')
    s = re.sub(r'(?<=[\u4e00-\u9fff）]),(?=[\u4e00-\u9fff「])', '', s)
    return s.strip()
def bases_of(note, is_hoben=False):
    """返回候选底本字符串列表（按注记次序）。"""
    out = []
    segs = [s.strip() for s in re.split(r'\s/\s|\s\|\s', note) if s.strip()]
    for s in segs:
        m = re.match(r'^底本[:：]\s*(.+)$', s)
        if m:
            out += [x.strip() for x in re.split(r'[;；]', m.group(1)) if x.strip()]; continue
        m = re.search(r'本書は(.+?)(?:に|の)影印', s)
        if m: out.append(m.group(1).strip()); continue
        if GENERIC_SEG.match(s): continue
        if re.search(r'(刊本|刻本|排印本|鈔本|抄本|活字本|寫本|写本|石印本|景印本|影印本|套印本|重刊本|覆刊|叢書本|全書本|遺書本|經解本|解本|刊|版|稿本)(\(.*\))?(の影印)?$', s):
            out.append(re.sub(r'の影印$', '', s).strip())
    return out

STOP = re.compile(r'(正統|排印本|刊本|刻本|鈔本|抄本|活字本|寫本|影印本|景印本|石印本|套印本|重刊本|重刻本|覆刻本|影印|排印|刊|刻|鈔|抄|本|版|日本|中國|清|明|宋|元|唐|民國|昭和|大正|明治|天保|文政|文化|享和|寬政|安永|天明|延享|寶曆|元祿|正德|享保|萬曆|崇禎|嘉靖|康熙|雍正|乾隆|嘉慶|道光|咸豐|同治|光緒|宣統|年間|間|[0-9０-９（）()，,、「」『』〈〉:：;；\s。·\-]|[〇一二三四五六七八九十元]+年)')
def core(s):
    t = (s or '').translate(VARIANTS).translate(EX)
    return cc.convert(STOP.sub('', t))
def norm_keep(s):
    return cc.convert((s or '').translate(VARIANTS).translate(EX))
def lcs(a, b):
    import difflib
    m = difflib.SequenceMatcher(None, a, b).find_longest_match(0, len(a), 0, len(b))
    return m.size
def ed_match(base, ed):
    cb, ce = core(disp(base)), core(ed or '')
    if len(cb) < 2 or len(ce) < 2: return 0.0
    if cb == ce: return 1.0
    if cb in ce or ce in cb: return 1.0 if min(len(cb), len(ce)) >= 4 else 0.3
    l = lcs(cb, ce)
    if l >= 4 and l / min(len(cb), len(ce)) >= 0.8: return 0.5
    return 0.4 if l >= 3 else 0.0

def usable(base):
    """底本注記是否足以認定一個版本：多版本混記→否；排印本須有出版者/叢書名；刊鈔本須有堂號/叢書名，或明記年份。"""
    if len(re.findall(r'(刊|刻|鈔|抄|排印|石印|活字|套印|影印|景印)本', base)) >= 2 or re.search(r'[:：]', base): return False
    c = core(base)
    typ = re.search(r'排印|鉛印', base)
    if typ: return len(c) >= 2
    if len(c) >= 2: return True
    return bool(re.search(r'[一二三四五六七八九十元]+年|（\d{4}', base)) and len(c) >= 0 and bool(re.search(r'(刊|刻|鈔|抄)本', base))
