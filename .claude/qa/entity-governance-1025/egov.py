"""作者 Entity 治理（去重方案第 2 部分）共用函数：载入人物、反查作者位引用、朝代关系。
全库扫描约 1.5 分钟；各脚本自己调用，不依赖外部缓存。"""
import glob, json, os, re, sys, collections

HERE = os.path.dirname(os.path.abspath(__file__))
QA = os.path.dirname(HERE)
ROOT = os.path.abspath(os.path.join(QA, '..', '..'))
sys.path[:0] = [QA]
import jio, entity_merge  # noqa: E402

URI_RE = re.compile(r'data\.library\.sh\.cn/entity/person/(\w+)')


def load_people():
    """{id: (相对路径, 记录)}，含墓碑。"""
    out = {}
    for f in glob.glob(os.path.join(ROOT, 'Entity', '*', '*', '*', '*.json')):
        d = json.load(open(f, encoding='utf-8'))
        if d.get('subtype') == 'people':
            out[d['id']] = (os.path.relpath(f, ROOT), d)
    print('载入人物 Entity %d 条（live %d）' % (len(out), sum(1 for v in out.values() if not v[1].get('merged_into'))))
    assert out, '载入 0 条人物'
    return out


def scan_authored(types=('Work', 'Book', 'Collection')):
    """[(类型, 相对路径, 记录)]，只含非墓碑记录。"""
    out = []
    for t in types:
        for f in glob.glob(os.path.join(ROOT, t, '*', '*', '*', '*.json')):
            d = json.load(open(f, encoding='utf-8'))
            if d.get('merged_into'):
                continue
            out.append((t, os.path.relpath(f, ROOT), d))
    print('载入 %s 记录 %d 条' % ('/'.join(types), len(out)))
    assert out, '载入 0 条记录'
    return out


def build_ref_map(recs):
    """entity_id -> [相对路径]（authors[].entity_id）。"""
    m = collections.defaultdict(set)
    for t, rel, d in recs:
        for a in d.get('authors') or []:
            if isinstance(a, dict) and a.get('entity_id'):
                m[a['entity_id']].add(rel)
    return m


def patch_entity_merge(refmap):
    """把 entity_merge 的 grep 反查换成预建索引（每个 loser 省约半分钟），语义不变。"""
    def fast(eid):
        hits = []
        for rel in sorted(refmap.get(eid, ())):
            d, fmt = jio.load(rel)
            if any(isinstance(a, dict) and a.get('entity_id') == eid for a in d.get('authors') or []):
                hits.append((rel, d, fmt))
        return hits
    entity_merge.scan_referencing_works = fast


def uris_of(d):
    return set(URI_RE.findall(json.dumps(d.get('description'), ensure_ascii=False)))


def resolve(people, eid):
    n = 0
    while eid in people and people[eid][1].get('merged_into'):
        eid = people[eid][1]['merged_into']; n += 1
        assert n < 6, '墓碑环'
    return eid
