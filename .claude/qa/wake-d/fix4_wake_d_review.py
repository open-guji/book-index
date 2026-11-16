# -*- coding: utf-8 -*-
"""wake-d 第四輪復抽修正（PR #2883）：撤 nw nx ny o4 o5 ns nm，補挂 2u，補 provenance 等。"""
import json, glob, os, subprocess
P = '99jwfmvf'
def f(sfx): return glob.glob('Book/*/*/*/%s%s-*.json' % (P, sfx))[0]
def ld(p): return json.load(open(p, encoding='utf-8'))
def sv(p, d): open(p, 'w', encoding='utf-8').write(json.dumps(d, ensure_ascii=False, indent=2) + '\n')
removed = {}
for s in ['nw', 'nx', 'ny', 'o4', 'o5', 'ns', 'nm']:
    p = f(s); d = ld(p); removed[s] = (d['title'], d['edition'])
    subprocess.run(['git', 'rm', '-q', '-f', p], check=True)
def src(n): return 'CiNii Books https://ci.nii.ac.jp/ncid/' + n
# 2u 補挂
p2 = glob.glob('Book/b/2/u/99jv424b2u-*.json')[0]; d = ld(p2)
d['provenance'] = [{'institution': '東京外國語大學附屬圖書館', 'call_number': '諸岡文庫/IV/40/1', 'source': src('BB00062971')}]
d['sources'].append({'id': 'cinii-bb00062971', 'name': 'CiNii Books', 'type': 'url', 'details': 'https://ci.nii.ac.jp/ncid/BB00062971'})
d['description']['sources'].append(src('BB00062971'))
d['ai_note'] += '\n第四輪（wake-d，2026-11-16）補挂：CiNii BB00062971（九春堂，1983.6- 著錄「明治16」；奥付同載「同十九年十月六日御届再版」，與本條奥付文字相同，視為同本）之東京外國語大學附屬圖書館諸岡文庫藏本（卷之61–125 等零卷）。報告社［1883］BN05908072 之東京大學駒場館藏未確認同本，不挂。出版人名依本條（丸谷新人）。'.replace('1983', '1883')
d['revision'] = '1.0.1'; d['revised_at'] = '2026-11-16'; sv(p2, d)
# nn
p = f('nn'); d = ld(p); d['dating']['certainty'] = 'attested'
d['dating']['basis'] = 'CiNii Books https://ci.nii.ac.jp/ncid/BA75586616 著錄 1891.11；奥付「廿四年十一月七日校正再版」'
d['ai_note'] = d['ai_note'].replace('其中 BB1338488X 注記「出版年は序の日付による」，故刊年僅作推定', '')
sv(p, d)
# nr
p = f('nr'); d = ld(p)
d['provenance'] = [{'institution': '佛教大學附屬圖書館', 'source': src('BA85621746')}, {'institution': '國立民族學博物館', 'call_number': '牧野漢/222.043/チン', 'source': src('BA85621746')}]
sv(p, d)
# o6
p = f('o6'); d = ld(p)
d['provenance'] = [{'institution': '香川大學圖書館（神原文庫）', 'call_number': '399.2/7', 'source': src('BB11796831')},
                   {'institution': '關西大學圖書館', 'call_number': 'L23||||C||7023', 'source': src('BB11796831')}]
sv(p, d)
# o8
p = f('o8'); d = ld(p)
d['provenance'].append({'institution': '島根大學附屬圖書館', 'call_number': 'NDC:124.3/H77', 'source': src('BB1259782X')})
d['publication_info']['publisher'] = '梶田勘助、文光堂書店、吉田久兵衞、林平次郎、鹿田靜七、細川清助'
d['dating']['basis'] += '；刊記「明治36(1903)年8月版権譲受 發行者 愛知縣名古屋市… 梶田勘助」(BB1259782X)'
sv(p, d)
# nu
p = f('nu'); d = ld(p)
d['provenance'].append({'institution': '島根大學附屬圖書館', 'call_number': 'NDC:222.01/Sh15', 'source': src('BB03302754')})
sv(p, d)
# no (1899)
p = f('no'); d = ld(p)
d['provenance'].append({'institution': '立教大學圖書館', 'call_number': '92-74638', 'source': src('BA85250702')})
sv(p, d)
# nv
p = f('nv'); d = ld(p)
d['title'] = '點註戰國策談棷'
d['ai_note'] += '書名用字：Work 題名作「談棷」，CiNii 著錄作「譚棷」，庫內 988g6y2hvk 作「譚諏」，皆為同書異寫，本條依 Work 題名。'
sv(p, d)
# 台賬
L = open('.claude/qa/wake-d/ledger4.tsv', encoding='utf-8').read().split('\n')
out = []
for l in L:
    if any(l.startswith(P + s + '\t') for s in removed): continue
    out.append(l)
open('.claude/qa/wake-d/ledger4.tsv', 'w', encoding='utf-8').write('\n'.join(out))
with open('.claude/qa/wake-d/TODO4.tsv', 'a', encoding='utf-8') as t:
    t.write('標註國語定本 d59ezahlu8sg 1884 溫古書屋（BA78262880 等）\tCiNii\t復抽撤回：高木熊三郎新增明治頭注，屬「近現代學者著作不錄」\n')
    t.write('增評荀子箋釋 d59ezahp9urk 1884 報告堂、1898 博文館（BA32669518 等）\tCiNii\t復抽撤回：邨岡良弼新增頭注本，不錄\n')
    t.write('標註莊子因／標註補義莊子因 d59f2nmmmo00 1885 青木恒三郎、1890 松村九兵衞\tCiNii\t復抽撤回：東條保標註首書本，不錄\n')
    t.write('資治通鑑 d59f2pynclxd 1881 猶興館（BB00906359）\tCiNii\t復抽撤回：著錄僅 18 卷 10 冊，與 294 卷全帙不符，疑為節選本，不能確認全帙\n')
    t.write('補標史記評林 1883 九春堂（BB00062971）\tCiNii\t不新建：與庫內 99jv424b2u 奥付文字相同（御届再版），已補挂其館藏於 99jv424b2u；BN05908072 報告社［1883］駒場館藏未確認同本\n')
ch = ld('.claude/qa/wake-d/changed4.json')
ch = [x for x in ch if not any(x.split('/')[-1].startswith(P + s + '-') for s in removed)]
json.dump(ch, open('.claude/qa/wake-d/changed4.json', 'w'), ensure_ascii=False, indent=0)
print(len(ch), removed.keys())
