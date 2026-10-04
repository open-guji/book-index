#!/usr/bin/env python3
"""Check every proposed Commons page against the live API before writing metadata.

Only --finalize removes inaccessible/changed files from the proposed additions.
All API outcomes are retained. A renamed file is linked by its current title.
"""
import argparse
import concurrent.futures
import json
import time
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timezone
from pathlib import Path

API = 'https://commons.wikimedia.org/w/api.php'


def sha_integer(value):
    # Snapshot sha1 uses MediaWiki base36; API imageinfo returns hex.
    return int(value, 16 if len(value) == 40 else 36)


def fetch(ids):
    query = {'action': 'query', 'format': 'json', 'formatversion': '2', 'pageids': '|'.join(map(str, ids)),
             'prop': 'imageinfo', 'iiprop': 'sha1|mime', 'maxlag': '5'}
    url = API + '?' + urllib.parse.urlencode(query)
    error = ''
    for attempt in range(3):
        try:
            request = urllib.request.Request(url, headers={'User-Agent': 'BookIndexCommonsRematch/1.0 (bibliographic reconciliation)'})
            with urllib.request.urlopen(request, timeout=30) as response:
                data = json.load(response)
            if 'error' in data:
                raise RuntimeError(data['error'])
            time.sleep(5)
            return ids, data['query']['pages'], ''
        except Exception as exc:
            error = str(exc)
            if attempt < 2:
                delay = 2 + attempt * 2
                if isinstance(exc, urllib.error.HTTPError) and exc.code == 429:
                    delay = max(30, int(exc.headers.get('Retry-After') or 30))
                    print(f'Commons rate limit: waiting {delay}s before retry', flush=True)
                time.sleep(delay)
    return ids, [], error


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('report', type=Path)
    parser.add_argument('--finalize', action='store_true')
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    path = args.report / 'plan.json'
    plan = json.loads(path.read_text(encoding='utf-8'))
    rows = {r['file']['pageid']: r for r in plan['additions']}
    assert len(rows) == len(plan['additions']) and rows
    previous_path = args.report / 'live-check.json'
    previous = json.loads(previous_path.read_text(encoding='utf-8'))['files'] if args.resume and previous_path.exists() else []
    outcomes = {r['pageid']: r for r in previous if r['pageid'] in rows and r['status'] == 'verified'
                and sha_integer(r['sha1']) == sha_integer(rows[r['pageid']]['file']['sha1'])}
    ids = sorted(pid for pid in rows if pid not in outcomes)
    batches = [ids[i:i + 50] for i in range(0, len(ids), 50)]
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
        futures = [pool.submit(fetch, batch) for batch in batches]
        for number, future in enumerate(concurrent.futures.as_completed(futures), 1):
            pageids, pages, error = future.result()
            for pid in pageids:
                outcomes[pid] = {'pageid': pid, 'status': 'request_failed' if error else 'missing', 'error': error}
            for page in pages:
                pid = page.get('pageid')
                if pid not in rows:
                    continue
                image = (page.get('imageinfo') or [{}])[0]
                result = {'pageid': pid, 'current_title': page.get('title'), 'sha1': image.get('sha1'), 'mime': image.get('mime')}
                if not image.get('sha1'):
                    result['status'] = 'missing_image'
                elif sha_integer(image['sha1']) != sha_integer(rows[pid]['file']['sha1']):
                    result['status'] = 'scan_changed'
                elif image.get('mime') != rows[pid]['file'].get('mime'):
                    result['status'] = 'mime_changed'
                elif not page.get('title', '').startswith('File:'):
                    result['status'] = 'not_file_page'
                else:
                    result['status'] = 'verified'
                outcomes[pid] = result
            if number % 10 == 0 or number == len(batches):
                print(f'Live API: {number}/{len(batches)} batches, {sum(v["status"] == "verified" for v in outcomes.values())} verified files', flush=True)
            previous_path.write_text(json.dumps({'files': [outcomes[pid] for pid in sorted(outcomes)]}, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    counts = {}
    for item in outcomes.values():
        counts[item['status']] = counts.get(item['status'], 0) + 1
    report = {'checked_at_utc': datetime.now(timezone.utc).isoformat(), 'counts': counts,
              'files': [outcomes[pid] for pid in sorted(outcomes)]}
    (args.report / 'live-check.json').write_text(json.dumps(report, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if args.finalize:
        assert not counts.get('request_failed'), 'API connectivity failures must not be treated as invalid scans'
        accepted, deferred, renamed = [], [], 0
        for row in plan['additions']:
            outcome = outcomes[row['file']['pageid']]
            if outcome['status'] == 'verified':
                file = outcome['current_title'][5:]
                url = 'https://commons.wikimedia.org/wiki/File:' + urllib.parse.quote(file.replace(' ', '_'), safe='')
                if url != row['resource']['url']:
                    row['previous_url'] = row['resource']['url']
                    row['resource']['url'] = url
                    renamed += 1
                accepted.append(row)
            else:
                deferred.append({**row, 'live_outcome': outcome})
        plan['additions'] = accepted
        plan['counts']['live_deferred'] = len(deferred)
        plan['counts']['live_renamed'] = renamed
        plan['counts']['new_resources_planned'] = len(accepted)
        plan['live_check_at_utc'] = report['checked_at_utc']
        path.write_text(json.dumps(plan, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        (args.report / 'live-deferred.json').write_text(json.dumps(deferred, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(counts), flush=True)


if __name__ == '__main__':
    main()
