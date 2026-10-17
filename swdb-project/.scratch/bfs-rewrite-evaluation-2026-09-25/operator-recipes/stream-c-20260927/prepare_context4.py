"""Prepare the T20 R8 focused-context submission (context4). Created 2026-09-27 ET.

Run from the repository root. Deterministic, data only: it derives the new
envelope from the retained context3 envelope (same strategy, intent, annotated
payload, source/package identity, regions and required operations), replaces
the worker context with the R8 focused set and writes the provider allocation.
It performs no provider call, submission, transfer or execution.
"""
import copy
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
from swdb import artifacts, rewrite, yamlio  # noqa: E402

HERE = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/stream-c-20260927'
OLD = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/provider-context3/prepared'
BASE = 'bfs-campaign-preparation-20260925-a1.upstream-annotated'
PREVIOUS, NEW = BASE + '-context3', BASE + '-context4'
# R8 focused set: DX100 MAA API headers used by the gem5 build and the upstream
# queue/vector/graph headers whose public accessors the helper must use. The
# author TDStepMAA reference is already inside the annotated payload.
FOCUSED_HEADERS = ['benchmarks/API/MAA_gem5.hpp', 'benchmarks/API/MAA.hpp', 'benchmarks/API/MAA_utility.hpp',
                   'src/sliding_queue.h', 'src/pvector.h', 'src/graph.h']
ALLOCATION = {
    'decision': 'resume-plan-20260927.md R8',
    'pool_provider_seconds': 1800, 'per_call_seconds': 900, 'per_call_usd': 10, 'maximum_repairs': 2,
    'policy': 'Fresh bounded recovery allocation under the standing approval. Contexts 1-3 remain failed and '
              'charged under the original pool (1367.6099595148116 s); nothing is refunded or reset. Unresolved '
              'or failed outcomes are retained. No strategy change.'}
PROVIDER = {'kind': 'claude', 'command': ['/data1/yanruj/.npm-global/bin/claude'], 'timeout_s': 900,
            'max_repairs': 2, 'total_seconds': 1800, 'budget_usd': 10}


def sha(data):
    return hashlib.sha256(data).hexdigest()


def build():
    prior = json.loads((OLD / 'upstream-annotated-context3.proposal.json').read_text())
    retained = yamlio.load(ROOT / 'records/proposals' / (PREVIOUS + '.yaml'))
    assert retained['request'] == prior and retained['outcome']['state'] == 'failed' and not retained.get('candidate')
    request = copy.deepcopy(prior)
    request['id'] = NEW
    old = prior['parameters']
    context = old['read_only_context']
    headers = {h['path']: h for h in context['headers']}
    assert set(FOCUSED_HEADERS) <= set(headers)
    request['parameters'] = {
        'supporting_profile_packages': old['supporting_profile_packages'],
        'selection': old['selection'],
        'predecessor_proposal': PREVIOUS,
        'prompt_projection': rewrite.FOCUSED,
        'provider_allocation': ALLOCATION,
        'read_only_context': {
            'scope': context['scope'], 'evidence_limit': context['evidence_limit'], 'target': context['target'],
            'headers': [headers[p] for p in FOCUSED_HEADERS],
            'omitted_from_worker': {
                'operations': artifacts.digest(context['operations']),
                'headers': {p: headers[p]['sha256'] for p in headers if p not in FOCUSED_HEADERS}},
            'required_operations_note': 'The proposal required_operations list names the supported operations.'},
        'target_execution_clarification': old['target_execution_clarification'],
    }
    for key in ('strategy', 'intent', 'payload', 'regions', 'required_operations', 'constraints',
                'source_snapshot', 'profile_package', 'source_sha256', 'implementation', 'hardware_target'):
        assert request[key] == prior[key], key
    return request


def render(request):
    package = yamlio.load(next((ROOT / 'records/profile_packages').glob(request['profile_package'] + '.yaml')))
    snapshot = yamlio.load(ROOT / 'records/source_snapshots' / (request['source_snapshot'] + '.yaml'))
    source = {'artifact': artifacts.identify(ROOT / 'apps/gapbs'), 'context': snapshot['context'],
              'protections': snapshot['protections']}
    assert source['artifact']['sha256'] == request['source_sha256']
    return rewrite.prompt_for(request, source, package)


def main():
    request = build()
    prompt = render(request)
    out = HERE / 'prepared'
    out.mkdir(parents=True, exist_ok=True)
    (out / 'context4.proposal.json').write_text(json.dumps(request, indent=2, ensure_ascii=False) + '\n')
    (out / 'context4.provider.json').write_text(json.dumps(PROVIDER, indent=2) + '\n')
    summary = {'id': NEW, 'predecessor': PREVIOUS, 'prompt_bytes': len(prompt.encode()),
               'prompt_sha256': sha(prompt.encode()), 'context3_prompt_bytes': 275533,
               'proposal_sha256': sha((out / 'context4.proposal.json').read_bytes()),
               'provider_sha256': sha((out / 'context4.provider.json').read_bytes())}
    (out / 'context4.summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
