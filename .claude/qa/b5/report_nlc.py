"""B5-4 把抽检 JSON 渲染为 markdown 明细，并统计「无」档构成。用法：python3 report_nlc.py 目录"""
import sys, os, json, collections
sys.path.insert(0, os.path.dirname(__file__))
from common import *
D = sys.argv[1]


def render(f, title, verdicts):
    xs = json.load(open(os.path.join(D, f + '.json')))
    L = [f'# {title}', '', '| # | 馆方详情页（点开核对） | 页面题名 / 责任者 / 版本项 | 本仓 Work（id）| 判定 |', '|---|---|---|---|---|']
    for x in xs:
        p = x['page']
        wa = '、'.join(f"{a[0]}({a[1] or '—'})" for a in x['work_authors'])
        L.append(f"| {x['n']} | [{x['url'].split('fid=')[-1]}]({x['url']}) | {p.get('题名','')} / {p.get('责任者','')} / {p.get('版本项','')} | {x['work_title']}（{x['work_id']}）{wa}，{x['work_dynasty'] or '—'}，{x['work_juan'] if x['work_juan'] is not None else '—'}卷 | {verdicts.get(x['n'], '对')} |")
    return '\n'.join(L) + '\n'


if __name__ == '__main__':
    v1 = json.loads(sys.argv[2]) if len(sys.argv) > 2 else {}
    v2 = json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}
    v1 = {int(k): v for k, v in v1.items()}; v2 = {int(k): v for k, v in v2.items()}
    open(os.path.join(D, '抽检-50.md'), 'w').write(render('抽检50', '抽检 50 条（确定档，seed 20261005）', v1))
    open(os.path.join(D, '抽检-追加50.md'), 'w').write(render('抽检50b', '追加抽检 50 条（确定档，seed 7777）', v2))
