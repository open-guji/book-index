#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""生成 curation/read-home.json（阅读首页策展数据，overview#321／#308 B 块）。

人工策展的部分（选目、导语、分组、名著版本系统与短名）写在本文件顶部的常量里；
凡是能由数据算出的（可读与否、text_count、edition_count、书名）一律现算，不手抄。
可读集 ＝ book-text 里有 `<Work|Book>/<c1>/<c2>/<c3>/<id>/manifest.json` 的条目。

  python3 curation/build_read_home.py --text-root ../book-text            # 写 curation/read-home.json
  python3 curation/build_read_home.py --text-root ../book-text --check    # 只校验，不写（与现有文件比对）

格式说明见同目录 README.md。
"""
import argparse, collections, glob, json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUT = os.path.join(ROOT, 'curation', 'read-home.json')

# ── 一、推荐阅读：6 部（稿 README §一，#308）。导语核过库内 description／manifest 的事实 ──
PICKS = [
    ('96kzii6z28', '小说', '石頭記',
     '现存《红楼梦》最早的抄本系统，仅存十六回，脂批最密。想读脂批，从这一本起。'),
    ('d59f2mpwwagw', '文章选本', '古文觀止',
     '清吴楚材、吴调侯叔侄合编，选先秦至明代文章二百二十二篇，分十二卷，流传最广的古文读本之一。'),
    ('d59f2mpwl1xf', '诗选', '唐詩三百首',
     '蘅塘退士孙洙编选，收唐代七十七位诗人约三百一十首，按体裁分类，是流传最广的唐诗选本。'),
    ('d59f2870u874', '诗文总集', '昭明文選',
     '现存最早的诗文总集，萧统编，分体编次，收先秦至梁诗文七百余篇，唐宋人读书必备。'),
    ('d59f23o7ygw2', '史志目录', '漢書藝文志',
     '据刘歆《七略》删订的现存最早史志目录，六略三十八种，每条可跳到作品页。'),
    ('d59dh3vo9af4', '书目提要', '四庫總目',
     '二百卷，著录书三千四百余部、存目六千七百余部，一书一篇提要，是查考古书的总门径。'),
]

# ── 二、专题：按作品类型分组（稿 README「10-01 修订」）。条目写稿里的 id；
#    若该 id 是 Book 且其 Work 可读（文本已并到 Work 名下），自动改用 Work id，并记 via_book ──
SHELF = [  # (所志朝代, [(id, 是否正史原志)])
    ('漢', [('d59f23o7ygw2', 1)]),
    ('後漢', [('d59f2o2lm0ht', 0), ('d59f2mp12329', 0)]),
    ('三國', [('d59f2mp1dblt', 0)]),
    ('晉', [('d59f2o2larya', 0), ('d59f2mp2xibm', 0), ('d59f2o2lx91d', 0), ('d59f2o2m8hky', 0), ('d59f5ilweo6h', 0)]),
    ('劉宋', [('d59f2o2muyo2', 0), ('d59f2ofz9b0h', 0)]),
    ('南齊', [('d59f2ofu9i4i', 0), ('d59f2ofr54ht', 0)]),
    ('梁', [('d59f2o2koav5', 0)]),
    ('陳', [('d59f2ofrgdfm', 0)]),
    ('魏', [('d59f2og3xv5t', 0)]),
    ('北齊', [('d59f2og3xv5s', 0)]),
    ('周', [('d59f2og98w75', 0)]),
    ('南北朝', [('d59f2ofyy29s', 0)]),
    ('隋', [('d59f28nmafwh', 1)]),
    ('唐', [('d59f2gcburcx', 1), ('d59f2hl0cmio', 1)]),
    ('宋', [('d59f2gdp696q', 1), ('d59f2mp38qv4', 0)]),
    ('遼金元', [('d59f2mp1zsox', 0)]),
    ('元', [('d59f2mp1zsoz', 0)]),
    ('明', [('d59f2mox0000', 1)]),
    ('清', [('d59f2mp0flz4', 1)]),
]
TOPICS = [  # (key, 组名, [id…])
    ('shumu', '书目与考证', ['d59f2hqc0c1t', 'az9irz0xim', 'd59f2htm01du', 'd59f2nl40936', 'd59f2mel8d1c', 'd59f2mel8d1d',
                          'd59dh3vo9af4', '4j2miiaic2', 'c359vh0hyr', '9q9og758p7', 'd59f2ofwg64g', 'd59f2hr9pypt',
                          'd59f2mp0quip', 'd59f2o2lx91e', 'd59f2mp0flz6']),
    ('congshu', '丛书', ['d59f2og4vke9', 'd59f2og4vksh']),
    ('dangan', '档案', ['d59f2nfhf8cg', 'd59f2ng9il8j', 'd59f2nh7uozl', 'd59f2nfdoe0z', 'd59f2neu0fsx', 'd59f2nf16w3o',
                      'd59f2ndl29s2', 'd59f2ng20wlc', 'd59f2neqw26a', 'd59f2s1hhg5c', 'd59f2s1j1mv4', 'd59f2rzrzp4w',
                      'd59f2rxyfv28', 'd59f2ofmgkch', 'd59f2og0708x', 'd59f2rujgd1c']),
    ('shishu', '史书与史料', ['988lpnv75x', 'kpbt9o3xd3', 'd59f2ncf8cn5', 'd59f2mcdblz4']),
    ('shiwenji', '诗文集', ['98ji05um82', 'd59f2870u874', 'd59f2mpwl1xf', 'd59f2mpwwagw', 'd59f2mpwwagx', 'd59f2og5taf4']),
    ('zishu', '子书与辑佚', ['98ji05um80', 'd59f2mua7w8y', 'h6nlgrnoc6', 'u04zro04s0', 'zdiwtiilsg', 'ui6x6usoho', '98ji05um84']),
]

# ── 三、名著与版本：版本系统名与短名照稿（book-index 的 Book.lineage 只有各本的承袭关系，没有「系统」名，
#    故系统名在此手工维护；短名对过 Book.edition／lineage.alias，见 README） ──
FAMOUS = [  # (Work id, 显示名, [(系统名, [(Book id, 版本短名)…])…])
    ('d59df01avcw0', '紅樓夢', [('脂本', [('96kzii6z28', '甲戌本'), ('96kzirvbwg', '庚辰本'), ('96kzjb81kw', '戚正本')]),
                              ('程本', [('96kzkdm8e8', '程甲本'), ('96kzkmzcow', '程乙本')])]),
    ('d59f2nksrpj4', '水滸傳', [('百回本', [('988g9bwr9g', '容與堂本')]), ('簡本', [('988g9bwr9n', '插增本')]),
                              ('七十回本', [('988g9blipt', '貫華堂本')])]),
    ('d59f2nk1atq9', '三國演義', [('嘉靖本', [('988g31lpfr', '嘉靖壬午本')]),
                                ('毛評本', [('988g9ant3e', '醉耕堂本'), ('988g9ant3i', '第一才子書')])]),
    ('d59dh3vo9af4', '欽定四庫全書總目', [('刻本', [('96mid1ogzk', '武英殿本'), ('96mmy9nfuo', '浙江本')]),
                                      ('排印', [('96mmyltp1c', '萬有文庫本')])]),
    ('d59f23o7ygw2', '漢書·藝文志', [('刻本', [('988g239lop', '百衲本（景祐）'), ('988g7ywhzl', '文淵閣四庫本')])]),
    ('d59f2evs8ni8', '司馬法', [('', [('98ji05um80', '四部叢刊本'), ('98ji05um81', '四庫全書本')])]),
]


def load(p):
    return json.load(open(p, encoding='utf-8'))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--text-root', required=True)
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()

    man = {}
    for p in glob.glob(os.path.join(a.text_root, '*', '*', '*', '*', '*', 'manifest.json')):
        parts = p.split(os.sep)
        if parts[-6] in ('Work', 'Book'):
            man[parts[-2]] = load(p)
    ent = {}
    for t in ('Work', 'Book'):
        for p in glob.glob(os.path.join(ROOT, t, '*', '*', '*', '*.json')):
            d = load(p)
            ent[d['id']] = d
    books_of = collections.defaultdict(list)
    for i, d in ent.items():
        if d.get('type') == 'book' and d.get('work_id'):
            books_of[d['work_id']].append(i)

    def own_texts(i):
        return len(man[i]['versions']) if i in man else 0

    def text_count(work_or_book):
        """作品自身的文本数（manifest 里的版本数）＋同 work_id 且可读的 Book 的文本数。"""
        n = own_texts(work_or_book)
        if ent[work_or_book]['type'] == 'work':
            n += sum(own_texts(b) for b in books_of[work_or_book] if b in man)
        return n

    skipped = []

    def resolve(i, what):
        """稿里的 id → 进组用的 id：自身可读用自身；Book 不可读而其 Work 可读，改用 Work（记 via_book）；否则丢，记入 skipped。"""
        if i in man:
            return i, None
        d = ent.get(i)
        if d and d['type'] == 'book' and d.get('work_id') in man:
            return d['work_id'], i
        skipped.append({'id': i, 'title': d['title'] if d else None, 'where': what,
                        'why': 'id 不存在' if not d else '本身与所属 Work 均无 manifest（不可读）'})
        return None, None

    def item(i, via, **extra):
        d = ent[i]
        r = {'id': i, 'kind': 'Work' if d['type'] == 'work' else 'Book', 'title': d['title']}
        if via:
            r['via_book'] = via
        r.update(extra)
        r['text_count'] = text_count(i)
        return r

    # picks
    picks = []
    for n, (i, label, slip, blurb) in enumerate(PICKS, 1):
        assert i in man, f'推荐 {i} 不可读'
        d = ent[i]
        r = {'order': n, 'id': i, 'kind': 'Work' if d['type'] == 'work' else 'Book', 'title': d['title'],
             'type_label': label, 'slip': slip, 'blurb': blurb}
        if d['type'] == 'book':
            r['edition'] = d.get('edition') or ''
            r['work_id'] = d.get('work_id')
        picks.append(r)

    # topics
    topics = []
    shelf_items = []
    for per, lst in SHELF:
        for i, orig in lst:
            rid, via = resolve(i, '史志目录')
            if rid:
                shelf_items.append(item(rid, via, period_of=per, orig=bool(orig)))
    topics.append({'key': 'shizhi', 'label': '史志目录', 'layout': 'shelf', 'items': shelf_items})
    for key, label, ids in TOPICS:
        items = []
        for i in ids:
            rid, via = resolve(i, label)
            if rid:
                items.append(item(rid, via))
        topics.append({'key': key, 'label': label, 'layout': 'list', 'items': items})

    # famous
    famous = []
    for wid, name, systems in FAMOUS:
        w = ent[wid]
        entry = {'work_id': wid, 'title': name, 'record_title': w['title'],
                 'work_readable': wid in man,
                 'own_texts': [{'key': v['key'], 'kind': v['kind'], 'label': v['label'], 'source_name': v.get('source_name') or v['label']}
                               for v in man[wid]['versions']] if wid in man else [],
                 'text_count': text_count(wid), 'edition_count': w.get('_edition_count', 0), 'systems': []}
        for sysname, eds in systems:
            lst = []
            for bid, short in eds:
                b = ent[bid]
                assert b['type'] == 'book' and b.get('work_id') == wid, f'{bid} 不是 {wid} 的 Book'
                lst.append({'book_id': bid, 'short': short, 'readable': bid in man, 'edition': b.get('edition') or ''})
            entry['systems'].append({'name': sysname, 'editions': lst})
        famous.append(entry)

    readable = {'total': len(man), 'work': sum(1 for i in man if ent[i]['type'] == 'work'),
                'book': sum(1 for i in man if ent[i]['type'] == 'book')}
    out = {'schema': 'read-home/1', 'readable': readable, 'picks': picks, 'topics': topics, 'famous': famous,
           'not_readable_dropped': skipped}
    text = json.dumps(out, ensure_ascii=False, indent=2) + '\n'
    if a.check:
        cur = open(OUT, encoding='utf-8').read() if os.path.exists(OUT) else ''
        print('一致' if cur == text else '与现有文件不一致（重新生成会改动）')
        sys.exit(0 if cur == text else 1)
    open(OUT, 'w', encoding='utf-8').write(text)
    print(f"可读 {readable}；picks {len(picks)}；" + '；'.join(f"{t['label']} {len(t['items'])}" for t in topics) +
          f"；famous {len(famous)}；丢弃（不可读）{len(skipped)}")
    for s in skipped:
        print('  丢弃', s)


if __name__ == '__main__':
    main()
