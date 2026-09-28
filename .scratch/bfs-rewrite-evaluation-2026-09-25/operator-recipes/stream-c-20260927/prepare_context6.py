"""Prepare the T20 context6 submission. Created 2026-09-27 13:45 ET.

Run from the repository root. Deterministic, data only: no provider call,
submission, transfer or execution.

Context6 keeps context5's strategy, intent, annotated payload (byte-identical
annotation and code blocks), regions, required operations, constraints,
source/package identity, focused worker context and stream-json capture. It
changes only the provider edit format: `edit_format: full_files`. The worker
returns the complete new src/bfs.cc and SWDB computes the unified diff itself.
Context5 failed at application because the provider hand-wrote hunks with wrong
counts and invented context lines ("corrupt patch at line 174"). The prompt's
format instruction states that it overrides the annotation's request for a
unified diff; the annotation text itself is not changed.
"""
import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
from swdb import artifacts, rewrite, yamlio  # noqa: E402

HERE = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/stream-c-20260927'
BASE = 'bfs-campaign-preparation-20260925-a1.upstream-annotated'
PREVIOUS, NEW = BASE + '-context5', BASE + '-context6'
ALLOCATION = {
    'decision': 'root allocation for the attempt after context5, 2026-09-27 13:20 ET (Stream C3 brief)',
    'pool_provider_seconds': 1800, 'per_call_seconds': 900, 'per_call_usd': 10, 'maximum_repairs': 2,
    'policy': 'Fresh bounded allocation for context6 defined by root after context5 completed (505.39 s, '
              'USD 1.15) but its hand-written diff failed application (corrupt patch at line 174). Contexts '
              '1-5 remain failed and charged; nothing is refunded. Unresolved or failed outcomes are retained. '
              'One submission, no retry. No strategy change.'}
PROVIDER = {'kind': 'claude', 'command': ['/data1/yanruj/.npm-global/bin/claude'], 'timeout_s': 900,
            'max_repairs': 2, 'total_seconds': 1800, 'budget_usd': 10, 'output_format': 'stream-json',
            'edit_format': 'full_files'}
EDIT_FORMAT = {
    'from': PREVIOUS, 'change': 'provider edit_format full_files: the worker returns complete changed files; '
    'SWDB computes the unified diff (git diff --no-index) and applies the unchanged patch and protection checks',
    'reason': 'context5 provider output failed git apply: wrong hunk counts and context lines absent from the '
              'source (corrupt patch at line 174)',
    'annotation': 'byte-identical to context5; the full_files prompt states that its output format overrides '
                  'the annotation request for a unified diff'}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    prior = json.loads((HERE / 'prepared/context5.proposal.json').read_text())
    retained = yamlio.load(ROOT / 'records/proposals' / (PREVIOUS + '.yaml'))
    assert retained['request'] == prior and retained['outcome']['state'] == 'failed' and not retained.get('candidate')
    assert 'patch application failed' in retained['outcome']['reason']
    request = copy.deepcopy(prior)
    request['id'] = NEW
    parameters = request['parameters']
    parameters['predecessor_proposal'] = PREVIOUS
    parameters['provider_allocation'] = ALLOCATION
    parameters['edit_format_revision'] = EDIT_FORMAT
    return request


def render(request):
    package = yamlio.load(next((ROOT / 'records/profile_packages').glob(request['profile_package'] + '.yaml')))
    snapshot = yamlio.load(ROOT / 'records/source_snapshots' / (request['source_snapshot'] + '.yaml'))
    source = {'artifact': artifacts.identify(ROOT / 'apps/gapbs'), 'context': snapshot['context'],
              'protections': snapshot['protections']}
    assert source['artifact']['sha256'] == request['source_sha256']
    return rewrite.prompt_for(request, source, package, edit_format=PROVIDER['edit_format'])


def main():
    request = build()
    prompt = render(request)
    out = HERE / 'prepared'
    (out / 'context6.proposal.json').write_text(json.dumps(request, indent=2, ensure_ascii=False) + '\n')
    (out / 'context6.provider.json').write_text(json.dumps(PROVIDER, indent=2) + '\n')
    summary = {'id': NEW, 'predecessor': PREVIOUS, 'prompt_bytes': len(prompt.encode()),
               'prompt_sha256': sha(prompt.encode()), 'context5_prompt_bytes': 115453,
               'proposal_sha256': sha((out / 'context6.proposal.json').read_bytes()),
               'provider_sha256': sha((out / 'context6.provider.json').read_bytes())}
    (out / 'context6.summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
