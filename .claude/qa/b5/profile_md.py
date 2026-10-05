"""profile.json → 画像 markdown 表。"""
import json, sys
p = json.load(open(sys.argv[1]))
cols = ['title', 'author', 'version', 'image_url', 'url', 'holding_id']
print('| 馆 | 条数 | 题名 | 责任者 | 版本 | 影像链接 | 详情页 | 题名+责任者去重后 | 题名精确落在 Work 题名集% | 脏度 |')
print('|---|---:|---:|---:|---:|---:|---:|---:|---:|---|')
for l in p['libs']:
    f = l['fill']
    dirty = '；'.join(f'{k}{f[k]}%' for k in ['乱码', '题名含假名', '题名含拉丁', '题名无汉字', '影印标记'] if f.get(k, 0) >= 0.5) or '—'
    print(f"| {l['name']} | {l['n']:,} | {f.get('title',0)}% | {f.get('author',0)}% | {f.get('version',0)}% | {f.get('image_url',0)}% | {f.get('url',0)}% | {l['distinct_title_author']:,} | {l['title_exact_in_work']}% | {dirty} |")
print(f"\n本仓 Work 共 {p['works']:,} 条。")
