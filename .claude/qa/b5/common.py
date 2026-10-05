"""B5 共用：读本仓 Work/Book、读 library_data 各馆、题名/责任者归一化。"""
import json, glob, os, re, unicodedata
from functools import lru_cache
import opencc

ROOT = os.environ.get('BOOK_INDEX', '/home/user/book-index')
LIB = os.environ.get('LIBRARY_DATA', '/home/user/book_index_json/library_data')

_t2s = opencc.OpenCC('t2s')
_jp2s = None
try:
    _jp2s = opencc.OpenCC('jp2t')  # 日文新字体→繁体，再 t2s
except Exception:
    pass

# 常见日文新字体/异体补充（OpenCC 版本差异时兜底）
EXTRA = str.maketrans({'経': '经', '兼': '兼', '尓': '尔', '斎': '斋', '齋': '斋', '辯': '辨', '辨': '辨',
                       '嶋': '岛', '嶌': '岛', '島': '岛', '浄': '净', '淨': '净', '塩': '盐', '鹽': '盐',
                       '㪽': '', '〔': '', '〕': '', '徳': '德', '彜': '彝', '彞': '彝', '峯': '峰', '瑯': '琅', '煕': '熙', '熈': '熙', '巻': '卷', '両': '两', '与': '与', '弁': '辨', '辺': '边', '邉': '边', '邊': '边', '広': '广', '廣': '广', '渋': '涩', '剣': '剑', '釈': '释', '歴': '历', '暦': '历', '蔵': '藏', '芸': '艺', '蘆': '芦', '覚': '觉', '観': '观', '拠': '据', '挙': '举', '倹': '俭', '験': '验', '図': '图', '圖': '图', '総': '总', '縁': '缘', '礼': '礼', '禮': '礼', '寿': '寿', '壽': '寿', '黒': '黑', '帯': '带', '帶': '带', '済': '济', '濟': '济', '氷': '冰', '糸': '丝', '続': '续', '続': '续', '誌': '志', '読': '读', '譯': '译', '訳': '译', '説': '说', '説': '说', '雑': '杂', '難': '难', '黄': '黄', '歓': '欢', '献': '献', '獻': '献', '実': '实', '寶': '宝', '宝': '宝', '写': '写', '寫': '写', '賛': '赞', '讃': '赞', '体': '体', '體': '体', '恵': '惠', '惠': '惠', '遅': '迟', '来': '来', '來': '来', '残': '残', '殘': '残', '帰': '归', '歸': '归', '畳': '叠', '亀': '龟', '龜': '龟', '竜': '龙', '龍': '龙', '麦': '麦', '麥': '麦', '塚': '冢', '冢': '冢', '鉄': '铁', '鐵': '铁', '鎌': '镰', '關': '关', '関': '关', '闕': '阙', '闘': '斗', '當': '当', '当': '当', '徴': '征', '徵': '征', '兎': '兔', '蝉': '蝉', '虫': '虫', '蟲': '虫'})

BRACKET = re.compile(r'[\[\(（［【〔][^\]\)）］】〕]*[\]\)）］】〕]')
PUNCT = re.compile(r'[\s　·・,，.。、;；:：!！?？"\'“”‘’「」『』《》〈〉\-－—_/／\\|*＊]+')
JUAN = re.compile(r'[〇零一二三四五六七八九十百千廿卅\d]+[卷巻]')


def norm_text(s):
    """繁简/日文汉字/异体折叠，去标点与括注。"""
    if not s:
        return ''
    s = unicodedata.normalize('NFKC', str(s))
    s = BRACKET.sub('', s)
    s = _t2s.convert(s).translate(EXTRA)
    if _jp2s is not None:
        pass
    return PUNCT.sub('', s)


def norm_title(s):
    """题名归一：去括注、去尾部卷数/册数，保留实质题名。"""
    s = norm_text(s)
    s = JUAN.sub('', s)
    return s


ROLE = re.compile(r'(?:[撰著編编輯辑注註释釋校纂述譔選选訂订評评補补箋笺疏傳传伝畫画書书等修譯译增刻刊錄录抄鈔钞集者]|奉敕|同撰|共撰|原著)+$')
DYN = re.compile(r'^[\[\(（［【〔]?(周|秦|漢|汉|魏|蜀|吳|吴|晉|晋|宋|齊|齐|梁|陳|陈|隋|唐|五代|十六國|十六国|遼|辽|金|元|明|清|民國|民国|日本|朝鮮|朝鲜|高麗|高丽|南朝[宋齊梁陳]|北魏|北齊|北周|東漢|东汉|西漢|西汉|後漢|后汉|劉宋|刘宋|[前後后]?[漢汉魏晉晋秦趙赵燕涼凉])[\]\)）］】〕]?')


def norm_author(s):
    """责任者归一：去朝代标注与责任方式词，返回主名列表归一串。"""
    if not s:
        return ''
    s = unicodedata.normalize('NFKC', str(s))
    s = re.sub(r'[\[\]［］【】〔〕]', '', s)          # 方括号只表示「推定著者」，去括号留内容
    s = re.sub(r'[\(（][^\)）]*[\)）]', ' ', s)          # 圆括号内是朝代/别称，整体去掉
    s = _t2s.convert(s).translate(EXTRA)
    s = re.sub(r'[\(（）\)]', '', s)
    parts = re.split(r'[;；,，、/／@\s]+|\band\b', s)
    out = []
    for p in parts:
        p = re.sub(r'^[題题]', '', p.strip())
        q = ROLE.sub('', p)
        p = q if len(q) >= 2 else p
        if len(p) > 3 and p[0] in '釋释':
            p = p[1:]
        p = PUNCT.sub('', p)
        if p:
            out.append(p)
    return '|'.join(out)


def iter_works():
    for f in glob.iglob(os.path.join(ROOT, 'Work', '*', '*', '*', '*.json')):
        try:
            yield json.load(open(f, encoding='utf-8'))
        except Exception:
            continue


def iter_books():
    for f in glob.iglob(os.path.join(ROOT, 'Book', '*', '*', '*', '*.json')):
        try:
            yield json.load(open(f, encoding='utf-8'))
        except Exception:
            continue


def load_lib(rel):
    """rel 为 library_data 下的文件或目录名；目录则合并 part-*.json。"""
    p = os.path.join(LIB, rel)
    if os.path.isdir(p):
        out = []
        for f in sorted(glob.glob(os.path.join(p, 'part-*.json'))):
            out += json.load(open(f, encoding='utf-8'))
        return out
    return json.load(open(p, encoding='utf-8'))
