#!/usr/bin/env python3
"""Prepare bounded representative BFS proposals from real public packages.

Created: 2026-09-25 (Eastern Time). These are operator-selected strategies, not
an autonomous strategy search. This client does not submit or evaluate code.
"""
import argparse
import difflib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from swdb import artifacts, bfs_protocol, profile_package
from swdb.store import Store


def native_patch(original):
    """Selected CPU strategy: balance frontier work and remove redundant work."""
    start = original.index('\nvoid TDStep(')
    end = original.index('\nint64_t TDStep2(', start)
    body = original[start:end]
    old = '#pragma omp for nowait\n'
    if body.count(old) != 1:
        raise ValueError('selected scalar TDStep worksharing loop does not match')
    body = body.replace(old, '#pragma omp for schedule(dynamic, 64) nowait\n')
    old = 'if (compare_and_swap(parent[v], curr_val, u)) {\n                        parent[v] = u;'
    if body.count(old) != 1:
        raise ValueError('selected scalar post-CAS store does not match')
    body = body.replace(old, 'if (compare_and_swap(parent[v], curr_val, u)) {')
    changed = original[:start] + body + original[end:]
    old = '        std::cout << "Starting TDStep: " << queue.size() << " elements" << std::endl;'
    if changed.count(old) != 1:
        raise ValueError('selected scalar diagnostic print does not match')
    changed = changed.replace(old, '        if (logging_enabled)\n    ' + old)
    return changed


def upstream_annotation(original, reference):
    """Keep the unchanged upstream source and supply explicit HW instructions."""
    instruction = r'''
SWDB HW ENSEMBLE ANNOTATION — SELECTED STRATEGY, NOT EXECUTED CODE
Introduce a DX100-backed top-down step in this upstream direction-optimizing BFS.
Preserve upstream application provenance, graph storage, BFSVerifier, and all
evaluator-owned ROI inputs. The evaluator times the entire DOBFS call, including
conversion, allocation, accelerator initialization, and normalization.

Use only the queried pinned DX100 API, with NUM_CORES=4 and TILE_SIZE=16384.
Include <omp.h>, <climits>, <stdexcept>, <MAA_gem5.hpp>, and <MAA_utility.hpp>
as needed. Define the new helper and setup in this translation unit. Do not edit
any header or invent an operation. The reference helper below is source context
from the pinned artifact; adapt it, do not compile this comment as-is.

Adaptation requirements:
1. Use queue.begin()/end()/size(), parent.data(), and g.out_neigh(0).begin().
   Upstream queue members, pvector storage, and graph neighbors are private.
   Graph::VertexOffsets() returns 64-bit offsets. Within the timed DOBFS call,
   create a checked int32 offset vector only when all counts and offsets fit
   INT_MAX. Otherwise retain the existing CPU algorithm. Never truncate offsets.
2. Allocate eight distinct 32-bit tiles and eight scalar registers per guest
   thread, exactly 32 of each in total. Follow the pinned API's serialized slot
   allocation and initialization, inside DOBFS. No allocation in a global
   constructor or outside the complete-call timing boundary.
3. Preserve the pinned stream-load / offset gathers / range-loop / neighbor and
   source gathers / masked parent update sequence. Use the actual returned tile
   length. Preserve barriers and scalar frontier-tail handling. Wait for tile5,
   the destination containing old parent values, before consuming those values
   or leaving the parent-update critical section; waiting only on tile3 does
   not establish that the store's result tile is ready.
4. Keep competing parent reads, mask generation, and masked stores serialized
   by the same OpenMP critical section. Enqueue only entries with a true mask
   and returned old parent < 0. Duplicate parent targets need the returned old
   value; this operation is not a CPU compare-and-swap instruction. Sum -old_parent
   in int64_t for newly discovered vertices and return that scout count. Preserve
   the scalar fallback's compare-and-swap and scout-count behavior as well.
5. When queue.size() > NUM_CORES*1024, select this offloaded top-down helper
   rather than switching to bottom-up, so the intended accelerator phase is
   actually eligible. For smaller frontiers preserve the original direction
   policy and original CPU TDStep. Keep edges_to_check, queue transitions,
   bottom-up bitmap handling, parent encoding, and final normalization correct.
6. Memory-region registration must describe valid actual queue, converted CSR,
   neighbor, and parent ranges. Keep initialization and any cleanup charged to
   DOBFS. Do not add m5 ROI controls, disable verification, or print PASS yourself.

If these exact APIs or preconditions cannot be resolved, return unresolved
requirements. Do not substitute another strategy. Apply these annotations as
actual executable edits against the original source supplied separately.

PINNED DX100 REFERENCE HELPER (unmodified source context, not a ready upstream patch):
'''
    # Block-comment escaping retains the reference visibly without terminating it.
    comment = (instruction + reference).replace('*/', '* /')
    return '/*\n' + comment + '\nEND SWDB HW ANNOTATION\n*/\n' + original


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--case', choices=['dx100-instructions', 'dx100-patch',
                                         'upstream-instructions', 'upstream-annotated'], required=True)
    parser.add_argument('--id', required=True)
    parser.add_argument('--package', required=True)
    parser.add_argument('--support-package', required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--records', type=Path, default=ROOT / 'records')
    args = parser.parse_args()
    args.records = args.records.resolve()
    if not re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.id):
        parser.error('id must use record identifier syntax')

    def query(command, *rest):
        result = subprocess.run([sys.executable, '-m', 'swdb', command, *rest,
            '--records', str(args.records), '--format', 'json'], cwd=ROOT,
            capture_output=True, text=True, timeout=180)
        if result.returncode:
            raise RuntimeError(f'public {command} failed: {result.stderr}')
        return json.loads(result.stdout)

    packages = [query('get', value) for value in (args.package, args.support_package)]
    if packages[0]['id'] == packages[1]['id']:
        raise ValueError('proposal support requires two distinct graph-family packages')
    implementation = 'dx100-bfs-scalar' if args.case.startswith('dx100-') else 'gapbs-bfs-do'
    identified_implementation = query('get', implementation)
    expected_artifact = artifacts.identify(artifacts.source_root(Store(args.records), identified_implementation))
    if any(p.get('kind') != 'profile_package' or p.get('implementation') != implementation
           or p.get('completeness') != 'complete' or p.get('evidence', {}).get('classification') != 'execution'
           or p.get('evidence', {}).get('primary_correctness', {}).get('state') != 'passed' for p in packages):
        raise ValueError('both packages must contain complete, real, checked baseline evidence for this implementation')
    sources = [query('get', p['source_snapshot']) for p in packages]
    for package, source in zip(packages, sources):
        profile_package.verify(package)
        artifacts.verify(source['artifact'])
        if source['implementation'] != implementation or source['artifact']['sha256'] != package['context']['source_sha256']:
            raise ValueError('package source artifact or implementation identity is inconsistent')
    if sources[0]['artifact']['sha256'] != sources[1]['artifact']['sha256']:
        raise ValueError('the two packages describe different source artifacts')
    evaluations = [query('get', p['evaluation']) for p in packages]
    workloads = [query('get', e['context']['workload']['id']) for e in evaluations]
    if {w['definition']['family'] for w in workloads} != {'kronecker', 'uniform_random'}:
        raise ValueError('the package pair must cover both required graph families')
    for package, source, evaluation, workload in zip(packages, sources, evaluations, workloads):
        bfs_protocol.verify_immutable(workload)
        expected_context = profile_package._context(evaluation)
        if (evaluation.get('evidence_kind') != 'execution' or evaluation.get('request', {}).get('fixture') is True
                or evaluation['outcome']['state'] != 'complete' or evaluation['correctness']['state'] != 'passed'
                or package['evidence']['evaluation_sha256'] != artifacts.digest(evaluation)
                or any(artifacts.digest(package['context'].get(key)) != artifacts.digest(value) for key, value in expected_context.items())
                or package['context'].get('primary_binary_sha256') != evaluation.get('build', {}).get('binary_sha256')
                or artifacts.digest(package['context'].get('build')) != artifacts.digest(evaluation.get('build'))
                or evaluation['context']['workload']['canonical_sha256'] != workload['definition']['canonical_sha256']):
            raise ValueError('baseline package evaluation or canonical workload identity changed')
        baseline = query('get', evaluation['candidate'])
        ancestor = query('get', baseline['source_snapshot'])
        if (baseline.get('artifact_role') != 'source_baseline' or baseline.get('proposal')
                or any(item['implementation'] != implementation for item in (baseline, ancestor, evaluation))
                or baseline['artifact']['sha256'] != source['artifact']['sha256']
                or baseline['artifact']['sha256'] != ancestor['artifact']['sha256']
                or baseline['artifact']['sha256'] != expected_artifact['sha256']
                or identified_implementation['function'] != 'DOBFS'
                or any(item['context'].get('function') != identified_implementation['function']
                       for item in (baseline, ancestor, source))
                or package['candidate'] != baseline['id']):
            raise ValueError('representative proposals require unchanged pinned application source and entry point')
    package, source = packages[0], sources[0]
    path = 'benchmarks/gapbs/src/bfs.cc' if implementation == 'dx100-bfs-scalar' else 'src/bfs.cc'
    original = (Path(source['artifact']['path']) / path).read_text()
    functions = {'DOBFS'} if args.case == 'upstream-instructions' else {'DOBFS', 'TDStep'}
    regions = [r['id'] for r in package['regions'] if r.get('kind') == 'function' and r.get('name') in functions]
    if not regions or not any(r.get('name') == 'DOBFS' for r in package['regions'] if r['id'] in regions):
        raise ValueError('the selected functions are absent from automatic source discovery')
    envelope = {'message_version': '1.0', 'id': args.id,
        'producer': {'name': 'swdb-representative-' + args.case,
                     'role': 'hw' if args.case == 'upstream-annotated' else 'sw', 'test_client': True},
        'profile_package': package['id'], 'source_snapshot': source['id'],
        'implementation': implementation, 'source_sha256': source['artifact']['sha256'], 'regions': regions,
        'constraints': {'editable_files': [path], 'preserve_correctness': True, 'preserve_roi': True},
        'parameters': {'supporting_profile_packages': [p['id'] for p in packages],
                       'selection': 'operator_selected_before_candidate_assessment'}, 'required_operations': []}
    if args.case == 'dx100-patch':
        changed = native_patch(original)
        envelope.update(strategy='cpu-frontier-load-balancing-and-redundant-work-elimination',
            intent='Use dynamic 64-vertex scheduling for scalar TDStep; remove the redundant parent store after successful CAS; emit the per-level diagnostic only when logging is enabled. Preserve the BFS algorithm, parent updates, level barriers, and complete-call ROI.',
            payload={'kind': 'patch', 'content': ''.join(difflib.unified_diff(
                original.splitlines(keepends=True), changed.splitlines(keepends=True), fromfile='a/' + path, tofile='b/' + path))})
        envelope['parameters']['frontier_schedule'] = {'kind': 'dynamic', 'chunk_vertices': 64}
    elif args.case == 'upstream-instructions':
        envelope.update(strategy='remove-dead-initial-bitmap-clear',
            intent='Eliminate only the initial curr.reset() in DOBFS: BUStep resets its next destination before every read/use. Preserve front.reset(), every BUStep reset, direction switching, and structural BFS semantics.',
            payload={'kind': 'structured_instructions', 'content': {
                'operation': 'remove_dead_initialization', 'function': 'DOBFS', 'statement': 'curr.reset();',
                'preconditions': ['BUStep executes next.reset() before destination bitmap writes',
                                  'curr is not read before serving as the BUStep destination'],
                'preserve': ['front.reset()', 'BUStep next.reset()', 'all traversal and direction-switch logic',
                             'BFSVerifier', 'complete-call ROI'],
                'on_unsatisfied_precondition': 'return unresolved; do not choose another strategy'}})
    else:
        capabilities = query('capabilities', 'dx100-e4fc4af-4c')
        target = capabilities['target']
        envelope.update(hardware_target=target['id'], require_executable_backend=True)
        envelope['required_operations'] = [{'operation': operation['id'],
            'interface': target['interface']['id'], 'interface_version': target['interface']['version'],
            'model_revision': target['model']['revision']} for operation in capabilities['operations']]
        if args.case == 'dx100-instructions':
            intent = ('Within the original scalar DOBFS, initialize the same per-thread MAA tiles and registers used by DOBFSMAA, '
                'inside the complete-call ROI, and route its frontier expansion through the existing TDStepMAA. '
                'Preserve the original DOBFS signature, BFSVerifier, m5 event locations, graph representation, parent initialization, '
                'level transitions, and normalization. Preserve existing adaptive full/tail handling and serialized parent updates. '
                'In TDStepMAA, wait for tile5, the destination holding returned old parent values, after the masked indirect store '
                'before CPU consumption or leaving the critical section. Do not merely select the existing DOBFSMAA entry point '
                'or add a comment: the evaluated DOBFS body must actually change. Use only the pinned supported operations. '
                'This is a representative selected offload strategy; no tuning or alternative strategy search is authorized.')
            envelope.update(strategy='existing-dx100-top-down-offload', intent=intent,
                            payload={'kind': 'natural_language', 'content': intent})
        else:
            pinned = (ROOT / 'apps/dx100/benchmarks/gapbs/src/bfs.cc').read_text()
            begin = pinned.index('void TDStepMAA(')
            reference = pinned[begin:pinned.index('\nvoid TDStep(', begin)]
            envelope.update(strategy='upstream-hybrid-dx100-top-down-offload',
                intent='Implement the annotated DX100 top-down helper and explicit frontier-size dispatch within upstream direction-optimizing BFS, preserving checked representation conversion, scout counts, parent-update synchronization, and complete-call ROI.',
                payload={'kind': 'annotated_source', 'content': {'files': {path: upstream_annotation(original, reference)}}})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as output:
        json.dump(envelope, output, indent=2)
        output.write('\n')
    print(json.dumps({'proposal': args.id, 'path': str(args.output.resolve()),
                      'payload': envelope['payload']['kind'], 'submitted': False, 'gain_claim': False}, indent=2))


if __name__ == '__main__':
    main()
