#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""J2 之巡：`description` 之著錄清單過時者。**唯讀為預設；--fix 方寫。**

**所以立此**：`description` 是著錄之**快照**，著錄一動它就過時——而 `scan.py` 之 `J`
只檢「description 全缺」，**不檢其陳舊**，故此類永遠不會自己浮出來。
併條尤其會造：**併條把被併者之 `indexed_by` 併入 keeper**，keeper 之描述遂少算了家數。
實測：2026-09-07 修訖 161 條之後，同日下午五道續併，**數小時內又生 7 條**。

**收窄之由（坑 51）**：寬檢「凡 `description.sources` ≠ `indexed_by` 之源」得 14,258 條
而九成以上是假陽性——`sources` 之義是「**這段描述從何而來**」，非「著錄於哪幾家」，
二者本不必相等（《太一生水》作《郭店楚墓竹簡》、《說苑》作《四庫總目》子部儒家類）。
**故只取「機械撮述體」**（文含「本條見於N家著錄」或「本條繫著錄N節」）——
此體之 `sources` 依其生成之法即 `indexed_by` 之複本，不等即是過時，無解釋餘地。

**修法是無損的**：只換「本條見於N家著錄：…」一句與 `sources` 欄，**餘文一字不動**。
**不逕以生成器重生**——實測重生反而失真：N6 之體於撰人後書本庫之 `juan_count`
（「謝靈運撰，36卷」）而生成器不書；N6 之卷數節採得較全（兼採 title_info 以外之欄），
生成器只讀 title_info，重生會漏掉《新唐書藝文志》三十五卷之屬。**新器未必勝舊文。**
（卷數節因此仍是撮述當時之採錄——**不誤而不全**，各條 ai_note 已記，勿誤以為已補齊。）

用法：
    python3 .claude/qa/inbox/lane-e/j2watch.py          # 巡（唯讀）
    python3 .claude/qa/inbox/lane-e/j2watch.py --fix    # 巡並修，落賬
"""
import glob, json, os, re, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
MECH = re.compile(r'本條見於\d+家著錄|本條繫著錄\d+節')
PAT = re.compile(r'本條見於(\d+)家著錄：([^。]+)。')
NOTE = ('%s qa2/lane-e（著錄清單過時）：本條 description 撮述時著錄為 %d 家，其後增《%s》等節'
        '（併條會把被併者之 indexed_by 併入 keeper），描述未隨改。'
        '今只正「本條見於N家著錄：…」一句與 `sources` 欄，**餘文一字未動**。\n'
        '卷數節仍是撮述當時之採錄，未含新增諸志之卷數——**不誤而不全**。')


def scan():
    """回 [(path, work, 現有之源序)]——皆機械撮述體而清單過時者。"""
    idx = {}
    for f in glob.glob(os.path.join(ROOT, 'index', 'works', '*.json')):
        idx.update(json.load(open(f)))
    out, mech = [], 0
    for wid, e in idx.items():
        p = os.path.join(ROOT, e['path'])
        try: w = json.load(open(p))
        except Exception: continue
        d = w.get('description')
        if not isinstance(d, dict): continue
        s, t = d.get('sources'), d.get('text') or ''
        # 坑 54：sources 有 list[str]／list[空]／list[dict] 三型，只比得了 list[str]
        if not (isinstance(s, list) and s and all(isinstance(x, str) for x in s)): continue
        if not MECH.search(t): continue
        mech += 1
        real = []
        for ib in (w.get('indexed_by') or []):
            src = ib.get('source')
            if src and src not in real: real.append(src)
        if set(s) != set(real): out.append((p, w, real))
    return mech, out


def fix(hits):
    import datetime
    sys.path.insert(0, os.path.join(ROOT, '.claude', 'qa'))
    import verdicts as V
    today = datetime.date.today().isoformat()
    ents, n = [], 0
    for p, w, real in hits:
        d = w['description']; t = d['text']
        m = PAT.search(t)
        if not m: print('  句式不合，跳過：', w['id']); continue
        old = int(m.group(1))
        added = [x for x in real if x not in (d.get('sources') or [])]
        d['text'] = t[:m.start()] + '本條見於%d家著錄：%s。' % (
            len(real), '、'.join('《%s》' % x for x in real)) + t[m.end():]
        d['sources'] = real
        w['ai_note'] = (w.get('ai_note') or '').rstrip() + '\n\n' + (
            NOTE % (today, old, '》《'.join(added[:3]) or '?'))
        json.dump(w, open(p, 'w'), ensure_ascii=False, indent=2); open(p, 'a').write('\n')
        ents.append({'id': w['id'], 'check': 'J', 'verdict': 'fixed',
                     'rule': 'J-著錄清單過時（只正其句不換其體）', 'round': 25, 'by': 'lane-E',
                     'why': '著錄增至 %d 家而描述仍書 %d 家；只正該句與 sources，餘文未動。' % (len(real), old)})
        n += 1
        print('  修 %s %s %d→%d 家' % (w['id'], w.get('title'), old, len(real)))
    if ents: print('落賬', V.add(ents), '筆')
    return n


if __name__ == '__main__':
    mech, hits = scan()
    print('機械撮述體 %d 條，著錄清單過時 %d' % (mech, len(hits)))
    for p, w, real in hits[:20]:
        print('   %-14s %-16s 現 %d 家' % (w['id'], (w.get('title') or '')[:14], len(real)))
    if '--fix' in sys.argv and hits:
        print('\n修：'); fix(hits)
        print('\n**修畢請跑 reindex.py --run --membership 與 verify.py，再 pushmain.sh**')
    elif hits:
        print('\n（唯讀。要修加 --fix）')
