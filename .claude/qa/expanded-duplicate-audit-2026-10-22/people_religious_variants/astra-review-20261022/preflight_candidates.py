#!/usr/bin/env python3
"""Read-only preflight for exactly PRV-P007 and PRV-H001; never edits native data."""
import argparse
import hashlib
import json
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--repo', type=Path, default=HERE.parents[4])
parser.add_argument('--ref', default='c6dd8356d')
args = parser.parse_args()
snapshot = json.loads((HERE / 'selected-current-snapshots.json').read_text())
plan = json.loads((HERE / 'candidate-plan.json').read_text())
checks = []
for path, item in snapshot['records'].items():
    raw = subprocess.check_output(['git', '-C', str(args.repo), 'show', args.ref + ':' + path])
    digest = hashlib.sha256(raw).hexdigest()
    checks.append({'path': path, 'expected': item['sha256'], 'actual': digest,
                   'ok': digest == item['sha256']})
result = {'ref': args.ref, 'source_checks': checks,
          'source_checks_pass': all(x['ok'] for x in checks),
          'ready_to_apply': False, 'native_mutations': 0,
          'reason': 'Identity confirmation and source hashes do not replace full-reference, cross-repository, losslessness and schema gates.',
          'candidate_mappings': {loser: group['keeper'] for group in plan['groups'] for loser in group['losers']},
          'pending_gates': sorted({gate for group in plan['groups'] for gate in group['pending_gates']})}
print(json.dumps(result, ensure_ascii=False, indent=2))
raise SystemExit(0 if result['source_checks_pass'] else 1)
