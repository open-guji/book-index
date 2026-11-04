#!/usr/bin/env python3
"""schema 审查第 12 组：people 的 external_ids.cbdb_match／cbdb_source 挪到顶层 external_ids_meta。

external_ids 只留真标识（cbdb_id、cbdb_id_alt、wikidata_id、viaf_id）；匹配过程元数据放
`external_ids_meta: {cbdb_match, cbdb_source}`，紧跟在 external_ids 之后。external_ids 搬空则删键。
幂等；先干跑：python3 move_cbdb_meta.py [--apply]
"""
import glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
META = ('cbdb_match', 'cbdb_source')


def fmt(d):
    return json.dumps(d, ensure_ascii=False, indent=2) + '\n'


def main(apply):
    n = bad = 0
    for p in glob.iglob(os.path.join(ROOT, 'Entity', '*', '*', '*', '*.json')):
        t = open(p, encoding='utf-8').read()
        if 'cbdb_match' not in t and 'cbdb_source' not in t:
            continue
        d = json.loads(t)
        ext = d.get('external_ids')
        if not isinstance(ext, dict) or not any(k in ext for k in META):
            continue
        if fmt(d) != t:
            bad += 1
            print('格式非标准，跳过：', p)
            continue
        meta = {k: ext.pop(k) for k in META if k in ext}
        out = {}
        for k, v in d.items():
            if k == 'external_ids':
                if ext:
                    out[k] = ext
                out['external_ids_meta'] = dict(d.get('external_ids_meta', {}), **meta)
            elif k != 'external_ids_meta':
                out[k] = v
        n += 1
        if apply:
            open(p, 'w', encoding='utf-8').write(fmt(out))
    print('改 %d 个文件；格式非标准跳过 %d' % (n, bad))


if __name__ == '__main__':
    main('--apply' in sys.argv)
