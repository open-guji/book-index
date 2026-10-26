#!/usr/bin/env python3
"""3a 第四轮：由 dossier.jsonl 与逐组人判（MERGE／HOLD）生成 apply_3a.py 批次规格与存疑清单。

    python3 mkbatch.py <dossier.jsonl> <base sha> <批次目录>

逐组人判以 dossier 题名键为键：MERGE 并；HOLD 不并，登存疑与 dedup-judged/3a-第四轮.tsv。
「拆分另立」组（成员 ai_note 记为 3a-2乙「先拆后并」或 部分6 族谱从组内他条拆出）一律不并，判 C。
keeper：优先自有著录（非继承丛书撰者）的 Work，次取 Book 多者，再取 id 小者；跳过已有 merged_into 的成员。"""
import glob, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, '..', '..', '..', '..'))
MERGE = {'漢碑引經考': '考／攷异体，同为六卷，一为師伏堂叢書本、一为光緒三十年刻本',
         '春秋穀梁傳': '同为晉程闡佚书，一条仅存撰人，一条据補晋書藝文志十六卷',
         '紫桃軒雜綴': '襍／雜异体，千頃堂四卷与总目三卷别作四卷相合',
         '經德堂文鈔': '啓／啟异体，同为一卷，涵通樓師友文鈔本与分體叢編本',
         '周易講疏': '同为陳張譏周易講疏三十卷佚书，撰／注只是诸志著录用字不同',
         '國初事跡': '𥘉为初之异体，同为明劉辰一卷',
         '周易象論': '同为晉欒肇三卷（樂为欒之误）',
         '集議孝經': '同为荀昶一卷，補晋志与隋志分著；東晉／南朝宋相邻'}
HOLD = {'仙遊縣志': ('F', '方志，交「合并重复方志 Work」单元'),
        '寧津縣志': ('F', '方志，交「合并重复方志 Work」单元'),
        '異物彙苑': ('D', '千頃堂十卷与总目十八卷相差悬殊，待逐书核'),
        '文溪集': ('D', '兩宋名賢小集一卷选本对二十卷本，选本不并（同第三轮口径）'),
        '文獻公全集': ('D', '十卷本（咸豐黃氏刻）与 3a-2乙 按编次拆出的十一卷本（宋濂王褘輯），编次有别，保持 3a-2乙 拆分')}


def wpath(i):
    return glob.glob(os.path.join(ROOT, 'Work', i[-3], i[-2], i[-1], i + '-*.json'))[0]


def note(i):
    return json.load(open(wpath(i), encoding='utf-8')).get('ai_note') or ''


def split_group(ws):
    ids = [w['id'] for w in ws]
    ns = {i: note(i) for i in ids}
    for i in ids:
        if '拆' in ns[i] and ('先拆后并' in ns[i] or '族谱' in ns[i]):
            return True
    return False


def main():
    src, base, out_dir = sys.argv[1:4]
    L = [json.loads(l) for l in open(src, encoding='utf-8')]
    groups, hold, judged = [], [], []
    for n, x in enumerate(L, 1):
        cid = 'R4-%04d' % n
        ws = [w for w in x['works'] if not json.load(open(wpath(w['id']), encoding='utf-8')).get('merged_into')]
        if len(ws) < 2:
            continue
        k = x['key']
        if k in MERGE:
            kp = sorted(ws, key=lambda w: (w['inherited'], -w['nbooks'], w['id']))[0]
            ev = '同题同首位责任者（同一 Entity、同名）：' + '／'.join('《%s》%s' % (w['title'], w['authors'][0]['name']) for w in ws) + '；逐组复核：' + MERGE[k]
            groups.append({'case_id': cid, 'cluster_id': '3a-' + cid, 'type': 'work', 'keeper': kp['id'],
                           'losers': [w['id'] for w in ws if w['id'] != kp['id']],
                           'keeper_source': '去重方案部分3a第四轮 同 Entity 同题同名普查（book-index %s）' % base[:10],
                           'evidence': ev, 'why': ev,
                           'rule': '去重方案部分3a第四轮：署名异写单元转来的同 Entity 同题同名组（非叢書子目）逐组复核并'})
            continue
        if k in HOLD:
            st, why = HOLD[k]
        elif split_group(ws):
            st, why = 'C', '拆分另立：成员为 3a-2乙「先拆后并」按编次拆出或部分6 族谱按「各修各算」拆出，保持拆分'
        else:
            raise SystemExit('未判：' + k)
        hold.append('\t'.join([cid, st, ' ／ '.join('%s《%s》' % (w['id'], w['title']) for w in ws), why]))
        for a in range(len(ws)):
            for b in range(a + 1, len(ws)):
                judged.append('\t'.join([ws[a]['id'], ws[b]['id'], 'D' if st == 'F' else st, '3a第四轮 %s：%s' % (cid, why)]))
    os.makedirs(out_dir, exist_ok=True)
    json.dump({'groups': groups}, open(os.path.join(out_dir, 'batch.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
    open(os.path.join(HERE, '..', '存疑-第四轮.tsv'), 'w', encoding='utf-8').write('组\t状态\t成员\t依据\n' + '\n'.join(hold) + '\n')
    open(os.path.join(HERE, '..', '..', 'dedup-judged', '3a-第四轮.tsv'), 'w', encoding='utf-8').write(
        '# 部分3a第四轮（同 Entity 同题同名，非叢書子目）不并对；基线 main %s；明细见 .claude/qa/dedup-3a/存疑-第四轮.tsv\n' % base[:10] + '\n'.join(judged) + '\n')
    print('并 %d 组，不并 %d 组，登记 %d 对' % (len(groups), len(hold), len(judged)))


if __name__ == '__main__':
    main()
