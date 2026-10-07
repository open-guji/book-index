#!/usr/bin/env python3
"""Rematch the Commons metadata snapshot, using file-local evidence only.

uv run --with opencc python -X utf8 .claude/qa/rematch_commons.py \
  --source ../book-index-crawler-cache/wiki-commons-book-data --cache <outside-repo>

Default: a review plan, no metadata writes. --apply writes the reviewed plan.
Existing Commons resources are preserved; this pass fills missing Commons links.
The complete file snapshot is scanned, rather than the aggregate books metadata.
"""
from __future__ import annotations

import argparse
import collections
import csv
import functools
import gzip
import hashlib
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import quote, unquote, urlsplit

import opencc

ROOT = Path(__file__).resolve().parents[2]
JP = opencc.OpenCC('jp2t')
SIMP = opencc.OpenCC('t2s')
RULE_VERSION = 2
NUMBER = r'[零〇一二三四五六七八九十百千萬万兩两壹貳贰叁肆伍陆陸柒捌玖拾佰仟\d]+'
DYNASTY = r'(?:南朝宋|南朝梁|南朝陳|南朝齐|南朝|後漢|后汉|東漢|东汉|西漢|西汉|東晉|东晋|西晉|西晋|北宋|南宋|北魏|後魏|后魏|北齊|北齐|北周|五代|民國|民国|元代|明代|清代|宋代|唐代|漢|汉|魏|蜀|吳|吴|晉|晋|齊|齐|梁|陳|陈|隋|唐|宋|遼|辽|金|元|明|清|周|日|日本|朝鮮|朝鲜)'
ROLES = r'(?:編纂|编纂|編輯|编辑|輯錄|辑录|編著|编著|纂修|重修|補注|补注|集解|註疏|注疏|義疏|义疏|箋注|笺注|校訂|校订|校勘|校刊|撰|著|編|编|輯|辑|纂|修|注|註|疏|校|訂|订|譯|译|述|集|評|评|繪|绘|錄|录|傳|传|等)'
GENERIC_NAMES = {'佚名', '失名', '无名氏', '不详', '阙名', '敕撰', '奉敕撰', '御撰', '御制', '纂修官', '史官', '官方'}


@functools.lru_cache(maxsize=500000)
def norm(value: str) -> str:
    value = SIMP.convert(JP.convert(value or ''))
    return re.sub(r'[\s\u3000（）()【】《》〈〉「」『』\[\]·•_\-，,。:：;；]', '', value)


def plain(value: str) -> str:
    value = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', value or '')
    value = re.sub(r'<[^>]*>', ' ', value)
    return value.strip()


@functools.lru_cache(maxsize=200000)
def file_title(value: str) -> str:
    """Remove explicit volume/count suffixes only; never strip arbitrary subtitles."""
    zh = re.search(r'\{\{zh\s*\|([^{}]+)\}\}', value or '', re.I)
    value = plain(zh.group(1) if zh else value)
    value = re.sub(r'\s*[（(](?:四庫全書本|四库全书本|四部叢刊本|四部丛刊本)[）)]\s*$', '', value)
    value = re.sub(r'[\[【（(]?第' + NUMBER + r'[冊册卷部集][\]】）)]?\s*$', '', value)
    value = re.sub(r'(?:[\s\[【（(]*' + NUMBER + r'[卷冊册][\]】）)]*|不分卷|卷[上下中]|[上下中]冊|[上下中]册)\s*$', '', value)
    return norm(value)


@functools.lru_cache(maxsize=100000)
def clean_author(raw: str) -> str:
    raw = plain(raw)
    raw = re.sub(r'\{\{(?:[Cc]reator|[Aa]uthor):([^{}|]+)(?:\|[^{}]*)?\}\}', r'\1', raw)
    raw = re.sub(r'\{\{(?:zh|[Ll]ang\|zh)\|([^{}]+)\}\}', r'\1', raw)
    # Unparsed templates, placeholders or Latin descriptions are not exact evidence.
    if '{{' in raw or re.search(r'[〓?？]', raw):
        return ''
    return SIMP.convert(JP.convert(raw))


@functools.lru_cache(maxsize=100000)
def dynasty_group(value: str) -> str:
    value = norm(value)
    return {'东汉': '汉', '西汉': '汉', '后汉': '汉', '东晋': '晋', '西晋': '晋',
            '北宋': '宋', '南宋': '宋', '宋代': '宋', '清代': '清', '明代': '明',
            '唐代': '唐', '元代': '元', '日本': '日', '朝鲜': '朝鲜'}.get(value, value)


def dynasty_compatible(left: str, right: str) -> bool:
    groups = {'汉': {'西汉', '东汉'}, '后汉': {'东汉'}, '晋': {'西晋', '东晋'},
              '宋': {'北宋', '南宋'}, '刘宋': {'刘宋'}, '南朝宋': {'刘宋'},
              '南朝梁': {'梁'}, '南朝齐': {'齐'}, '南朝陈': {'陈'},
              '南北朝': {'刘宋', '齐', '梁', '陈', '北魏', '北齐', '北周'},
              '三国魏': {'魏'}, '后魏': {'北魏'}}
    def values(value):
        value = norm(value)
        value = {'宋代': '宋', '唐代': '唐', '明代': '明', '清代': '清', '元代': '元', '日本': '日'}.get(value, value)
        return groups.get(value, {value})
    return bool(values(left) & values(right))


@functools.lru_cache(maxsize=200000)
def author_supported(name: str, dynasty: str, raw: str) -> bool:
    """Match a complete name at author-field boundaries, retaining surname characters.

    Dynasty prefixes are optional and checked when present. Thus 宋敏求 and
    吴敬梓 are not shortened to 敏求/敬梓, and 王修 is not split on the role 修.
    """
    raw = clean_author(raw)
    if not raw:
        return False
    dynasty_re = SIMP.convert(JP.convert(DYNASTY))
    roles_re = SIMP.convert(JP.convert(ROLES))
    sep = r'[\s,，、;/；／|]'
    pattern = (r'(?:^|' + sep + '|' + roles_re + r')\s*'
               r'(?:(?:[（(〔\[【]\s*)?(?P<dyn>' + dynasty_re + r')(?:\s*[）)〕\]】])?\s*)?'
               + re.escape(name) + r'\s*(?:[（(]\s*)?(?=$|' + sep + '|' + roles_re + ')')
    for match in re.finditer(pattern, raw):
        found = match.group('dyn')
        if found and dynasty and not dynasty_compatible(found, dynasty):
            continue
        return True
    return False


def names_of_work(work: dict) -> set[str]:
    result = set()
    for author in work.get('authors') or []:
        name = norm(plain(author.get('name', '')))
        if name and len(name) >= 2 and name not in GENERIC_NAMES:
            result.add(name)
    return result


def unexplained_author_text(raw: str, names: set[str]) -> str:
    """Detect contributors/other book titles hidden inside an aggregated Author field.

    A matching category and first author are insufficient if the same catalog field
    also names unrelated books or contributors. These files need manual disambiguation.
    """
    raw = clean_author(raw)
    for name in sorted(names, key=len, reverse=True):
        raw = raw.replace(name, '')
    raw = re.sub(SIMP.convert(JP.convert(DYNASTY)), '', raw)
    raw = re.sub(SIMP.convert(JP.convert(ROLES)), '', raw)
    return ''.join(re.findall(r'[\u3400-\u9fff\U00020000-\U0003134f]', raw))


def has_commons(work: dict) -> bool:
    return any(urlsplit(r.get('url') or '').hostname == 'commons.wikimedia.org' or
               (r.get('id') or '').lower().startswith('commons')
               for r in work.get('resources') or [])


def canon_url(url: str) -> str:
    return unquote(url).replace(' ', '_').split('#')[0]


def dump(path: Path, value, preserve_format=False):
    path.parent.mkdir(parents=True, exist_ok=True)
    indent = 2
    if preserve_format and path.exists():
        match = re.search(r'(?m)^([ \t]+)"', path.read_text(encoding='utf-8'))
        if match:
            indent = match.group(1)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=indent) + '\n', encoding='utf-8', newline='\n')


def load_index():
    result, locations = {}, {}
    for path in sorted((ROOT / 'index/works').glob('*.json')):
        data = json.loads(path.read_text(encoding='utf-8'))
        for wid, entry in data.items():
            assert wid not in result, wid
            result[wid] = entry
            locations[wid] = path
    assert result, 'Empty Work scan'
    return result, locations


def git_sha(path: Path) -> str:
    return subprocess.check_output(['git', '-C', str(path), 'rev-parse', 'HEAD'], text=True).strip()


def build_cache(source: Path, cache: Path, index: dict):
    signature = {'source_commit': git_sha(source), 'index_commit': git_sha(ROOT), 'rule_version': RULE_VERSION}
    signature_path = cache.with_suffix('.signature.json')
    if cache.exists() and signature_path.exists() and json.loads(signature_path.read_text()) == signature:
        print('Reusing checked snapshot candidate cache', flush=True)
        return signature
    titles = set()
    for entry in index.values():
        titles.update(norm(t) for t in [entry['title'], *(entry.get('additional_titles') or [])] if isinstance(t, str) and t)
    counts = collections.Counter()
    cache.parent.mkdir(parents=True, exist_ok=True)
    with cache.open('w', encoding='utf-8', newline='\n') as output:
        for shard in sorted((source / 'data/files').glob('*.gz')):
            with gzip.open(shard, 'rt', encoding='utf-8') as stream:
                for line in stream:
                    rec = json.loads(line)
                    counts['source_files_scanned'] += 1
                    categories = rec.get('book_categories') or [rec.get('book', '')]
                    keys = {norm(t) for t in categories if t}
                    if keys & titles:
                        output.write(line.rstrip('\n') + '\n')
                        counts['candidate_files'] += 1
            print(f"Scanned {shard.name}: {counts['source_files_scanned']:,} files / {counts['candidate_files']:,} candidates", flush=True)
    manifest = json.loads((source / 'data/manifest.json').read_text())
    assert counts['source_files_scanned'] == manifest['counts']['files']
    dump(signature_path, signature)
    dump(cache.with_suffix('.counts.json'), counts)
    return signature


def rank(rec: dict):
    # Prefer a declared single-volume file, then numbered first volume, then stable page ID.
    volume = str(rec.get('volume') or '')
    first = norm(volume) in {'1', '01', '001', '0001', '第1册', '第一册', '第一卷', '第1卷', '卷一', '卷1', '卷01', '卷001'}
    return (str(rec.get('volumes') or '') == '1', first, -len(rec['file']), -rec['pageid'])


def classify(work: dict, rec: dict) -> tuple[str, list[str]]:
    title_keys = {norm(t) for t in [work['title'], *(work.get('additional_titles') or [])] if isinstance(t, str)}
    categories = {norm(t) for t in rec.get('book_categories') or [rec.get('book', '')] if t}
    if len(categories) != 1:
        return 'multi_book_file', []
    if not title_keys & categories:
        return 'title_mismatch', []
    if rec.get('mime') not in {'application/pdf', 'image/vnd.djvu'}:
        return 'not_document_scan', []
    if re.fullmatch(r'[\s\[（(]*(?:卷首|序|序言|目錄|目录|跋|牌記|牌记|索引)[\s\]）)]*', str(rec.get('volume') or '')) or re.search(r'\s(?:卷首|目錄|目录)\.(?:pdf|djvu)$', rec['file'], re.I):
        return 'front_matter_only', []
    if rec.get('title') and file_title(rec['title']) not in title_keys:
        return 'file_title_conflict', []
    if work.get('subtype', 'book') != 'book':
        return 'not_book_work', []
    if work.get('loss_status') == 'lost':
        return 'lost_work_conflict', []
    mine = names_of_work(work)
    if not mine:
        return 'work_author_missing', []
    if not clean_author(rec.get('author') or ''):
        return 'file_author_unusable', []
    # Exact person names; no substring overlap or arbitrary shared-character score.
    supported = set()
    for author in work.get('authors') or []:
        name = norm(plain(author.get('name', '')))
        if name in mine and author_supported(name, author.get('dynasty') or work.get('dynasty') or '', rec.get('author') or ''):
            supported.add(name)
    if not supported:
        return 'author_mismatch', []
    # Every named Work contributor must be supported by this very file.
    if not mine <= supported:
        return 'work_contributors_not_all_supported', sorted(supported)
    if unexplained_author_text(rec.get('author') or '', mine):
        return 'source_contributors_not_all_supported', sorted(supported)
    return 'confirmed', sorted(supported)


def plan(source: Path, cache: Path, report: Path):
    index, _ = load_index()
    signature = build_cache(source, cache, index)
    by_title = collections.defaultdict(set)
    for wid, entry in index.items():
        for t in [entry['title'], *(entry.get('additional_titles') or [])]:
            if isinstance(t, str) and t:
                by_title[norm(t)].add(wid)
    works, best, existing = {}, {}, set()
    sha_owners = collections.defaultdict(set)
    counts = collections.Counter()
    pair_counts = collections.Counter()
    findings = []
    work_verdicts = collections.defaultdict(collections.Counter)
    work_examples = {}
    def load_work(wid):
        if wid not in works:
            work = json.loads((ROOT / index[wid]['path']).read_text(encoding='utf-8'))
            assert work['id'] == wid and work['type'] == 'work'
            works[wid] = work
        return works[wid]
    seen_pageids = set()
    with cache.open(encoding='utf-8') as stream:
        for number, line in enumerate(stream, 1):
            rec = json.loads(line)
            if number % 50000 == 0:
                print(f'Matched {number:,} candidate files / {len(works):,} Works / {len(best):,} possible additions', flush=True)
            assert rec['pageid'] not in seen_pageids
            seen_pageids.add(rec['pageid'])
            candidates = set().union(*(by_title[norm(t)] for t in rec.get('book_categories') or [rec.get('book', '')] if t))
            valid = []
            for wid in sorted(candidates):
                work = load_work(wid)
                verdict, names = classify(work, rec)
                pair_counts[verdict] += 1
                work_verdicts[wid][verdict] += 1
                if has_commons(work):
                    existing.add(wid)
                if verdict == 'confirmed':
                    valid.append((wid, names))
                elif (wid, verdict) not in work_examples:
                    work_examples[(wid, verdict)] = {'work_id': wid, 'work_title': work['title'], 'file': rec['file'],
                                                    'pageid': rec['pageid'], 'file_author': rec.get('author', ''), 'verdict': verdict}
            for wid, names in valid:
                sha_owners[rec['sha1']].add(wid)
            if len(valid) > 1:
                pair_counts['ambiguous_work_same_author'] += len(valid)
                for wid, names in valid:
                    findings.append({'work_id': wid, 'work_title': works[wid]['title'], 'file': rec['file'],
                                     'pageid': rec['pageid'], 'file_author': rec.get('author', ''), 'verdict': 'ambiguous_work_same_author'})
                continue
            for wid, names in valid:
                if wid in existing:
                    continue
                if wid not in best or rank(rec) > rank(best[wid]['file']):
                    best[wid] = {'work_id': wid, 'work_title': works[wid]['title'], 'path': index[wid]['path'],
                                 'matched_names': names, 'file': rec}
    # Also forbid a byte-identical scan being assigned to distinct Works.
    rows = []
    for wid in sorted(best):
        row = best[wid]
        if len(sha_owners[row['file']['sha1']]) != 1:
            pair_counts['shared_scan_sha1'] += 1
            continue
        rec = row['file']
        row['before_sha256'] = hashlib.sha256((ROOT / row['path']).read_bytes()).hexdigest()
        metadata = {'format': 'PDF' if rec['mime'] == 'application/pdf' else 'DjVu'}
        for k in ['edition', 'publisher']:
            if rec.get(k):
                metadata[k] = plain(rec[k])
        if rec.get('date'):
            metadata['year'] = plain(str(rec['date']))
        volume = str(rec.get('volume') or '')
        if volume:
            metadata['note'] = f'本链接为扫描册 {volume}；不代表全书齐备。'
        else:
            metadata['note'] = '链接指向单个扫描文件；全书齐备情况未核。'
        row['resource'] = {'id': 'commons', 'name': '维基共享资源',
                           'url': 'https://commons.wikimedia.org/wiki/File:' + quote(rec['file'].replace(' ', '_'), safe=''),
                           'types': ['image'], 'root_type': 'catalog', 'metadata': metadata}
        rows.append(row)
    counts.update(json.loads(cache.with_suffix('.counts.json').read_text()))
    counts['works_in_index'] = len(index)
    counts['works_with_title_candidates'] = len(works)
    counts['candidate_works_already_have_commons'] = len(existing)
    counts['new_resources_planned'] = len(rows)
    payload = {**signature, 'matcher_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
               'counts': dict(counts), 'pair_verdicts': dict(pair_counts), 'additions': rows}
    dump(report / 'plan.json', payload)
    dump(report / 'deferred-examples.json', [*work_examples.values(), *findings])
    dump(report / 'work-verdicts.json', {wid: {'title': works[wid]['title'], 'existing_commons': wid in existing,
                                            'file_verdict_counts': dict(work_verdicts[wid])}
                                      for wid in sorted(works)})
    print(json.dumps({k: v for k, v in payload.items() if k != 'additions'}, ensure_ascii=False, indent=2), flush=True)
    return payload


def apply(report: Path):
    payload = json.loads((report / 'plan.json').read_text(encoding='utf-8'))
    assert git_sha(ROOT) == payload['index_commit'], 'Baseline commit changed'
    assert hashlib.sha256(Path(__file__).read_bytes()).hexdigest() == payload['matcher_sha256'], 'Matching code changed; regenerate the plan'
    assert payload.get('live_check_at_utc'), 'Check and finalize the live Commons API results first'
    live = {r['pageid']: r for r in json.loads((report / 'live-check.json').read_text(encoding='utf-8'))['files']}
    assert payload['additions']
    index, locations = load_index()
    indexes = {}
    for row in payload['additions']:
        path = ROOT / row['path']
        raw = path.read_bytes()
        assert hashlib.sha256(raw).hexdigest() == row['before_sha256'], row['work_id']
        work = json.loads(raw)
        assert not has_commons(work), row['work_id']
        assert classify(work, row['file'])[0] == 'confirmed'
        assert live[row['file']['pageid']]['status'] == 'verified', row['work_id']
    # Validate every row before the first write.
    for row in payload['additions']:
        path = ROOT / row['path']
        work = json.loads(path.read_text(encoding='utf-8'))
        work.setdefault('resources', []).append(row['resource'])
        # schema-v2（overview#459 F6-3）：不寫 `_has_image`、不手改 index/——
        # 二者由 build/build_derived.py 據 resources 生成（--write-index 寫回 index/）
        dump(path, work, preserve_format=True)
    print(f"Applied {len(payload['additions'])} new image resources; "
          "now run: python3 build/build_derived.py --write-index", flush=True)


def audit(report: Path):
    payload = json.loads((report / 'plan.json').read_text(encoding='utf-8'))
    index, _ = load_index()
    shas, urls, checked = set(), set(), 0
    specs = [payload['index_commit'] + ':' + r['path'] for r in payload['additions']]
    blobs = subprocess.check_output(['git', 'cat-file', '--batch'], input=('\n'.join(specs) + '\n').encode('utf-8'))
    offset = 0
    for row in payload['additions']:
        current = json.loads((ROOT / row['path']).read_text(encoding='utf-8'))
        header_end = blobs.index(b'\n', offset)
        header = blobs[offset:header_end].split()
        assert header[1] == b'blob'
        size = int(header[2])
        raw = blobs[header_end + 1:header_end + 1 + size]
        offset = header_end + 1 + size + 1
        assert hashlib.sha256(raw).hexdigest() == row['before_sha256']
        before = json.loads(raw)
        expected = dict(before)
        expected['resources'] = [*(before.get('resources') or []), row['resource']]
        assert current == expected, f"Unexpected field changes: {row['path']}"
        assert classify(before, row['file'])[0] == 'confirmed'
        assert row['resource']['types'] == ['image']
        assert row['file']['sha1'] not in shas
        assert canon_url(row['resource']['url']) not in urls
        shas.add(row['file']['sha1']); urls.add(canon_url(row['resource']['url']))
        checked += 1
    assert checked > 0
    for path in sorted((ROOT / 'index/works').glob('*.json')):
        rel = path.relative_to(ROOT).as_posix()
        before = json.loads(subprocess.check_output(['git', 'show', payload['index_commit'] + ':' + rel]))
        for row in payload['additions']:
            if row['work_id'] in before:
                before[row['work_id']]['has_image'] = True
        assert json.loads(path.read_text(encoding='utf-8')) == before, f'Unexpected index edits: {rel}'
    changed = subprocess.check_output(['git', '-c', 'core.quotepath=false', 'diff', payload['index_commit'], '--name-only'], encoding='utf-8').splitlines()
    changed_works = {p for p in changed if p.startswith('Work/')}
    assert changed_works == {r['path'] for r in payload['additions']}
    allowed_tools = {'.claude/qa/rematch_commons.py', '.claude/qa/check_commons_live.py', 'tests/test_rematch_commons.py'}
    report_rel = report.relative_to(ROOT).as_posix() + '/'
    assert all(p.startswith(('Work/', 'index/works/', report_rel)) or p in allowed_tools for p in changed), 'Unexpected tracked metadata modifications'
    with (report / 'additions.csv').open('w', encoding='utf-8-sig', newline='') as stream:
        columns = ['work_id', 'work_title', 'matched_names', 'file_author', 'pageid', 'file', 'volume', 'edition', 'date', 'source', 'url']
        writer = csv.DictWriter(stream, fieldnames=columns)
        writer.writeheader()
        for row in payload['additions']:
            rec = row['file']
            writer.writerow({'work_id': row['work_id'], 'work_title': row['work_title'], 'matched_names': ';'.join(row['matched_names']),
                             'file_author': rec.get('author', ''), 'pageid': rec['pageid'], 'file': rec['file'], 'volume': rec.get('volume', ''),
                             'edition': rec.get('edition', ''), 'date': rec.get('date', ''), 'source': rec['source'], 'url': row['resource']['url']})
    print(f'Audit passed: {checked} records, original fields/resources preserved, unique scan SHA1/URLs, image indexes consistent', flush=True)


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--source', type=Path)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--report', type=Path, default=ROOT / '.claude/qa/reports/commons-rematch-20261003')
    parser.add_argument('--apply', action='store_true')
    parser.add_argument('--audit', action='store_true')
    args = parser.parse_args()
    if args.apply:
        apply(args.report)
    elif args.audit:
        audit(args.report)
    else:
        assert args.source and args.cache, '--source and --cache required for planning'
        plan(args.source.resolve(), args.cache.resolve(), args.report)


if __name__ == '__main__':
    main()
