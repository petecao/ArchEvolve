"""Prepare the T20 context5 submission. Created 2026-09-27 ET.

Run from the repository root. Deterministic, data only: no provider call,
submission, transfer or execution.

Context5 keeps context4's strategy, intent, regions, required operations,
constraints, source/package identity and focused worker context. It changes
only (a) the representative HW-producer annotation, which now spells out the
intended DX100 top-down helper and DOBFS dispatch as concrete code blocks with
insertion anchors (test client, labeled per spec D15), and (b) the provider
capture (stream-json, so partial output survives a timeout). The code blocks are
read from producer-check/reference-bfs.cc, which the test client checked on the
pinned DX100 functional model (producer-check/functional-check.sh).
"""
import copy
import difflib
import hashlib
import json
import sys
from pathlib import Path

ROOT = Path.cwd()
sys.path.insert(0, str(ROOT))
from swdb import yamlio  # noqa: E402

HERE = ROOT / '.scratch/bfs-rewrite-evaluation-2026-09-25/operator-recipes/stream-c-20260927'
BASE = 'bfs-campaign-preparation-20260925-a1.upstream-annotated'
PREVIOUS, NEW = BASE + '-context4', BASE + '-context5'
ORIGINAL = ROOT / 'apps/gapbs/src/bfs.cc'
REFERENCE = HERE / 'producer-check/reference-bfs.cc'
AUTHOR = {'path': 'apps/dx100/benchmarks/gapbs/src/bfs.cc', 'function': 'TDStepMAA', 'lines': [66, 225],
          'file_sha256': '6835fc42dfadcb60c1c3fae543f736903977f135fd7c55cd495c0e481b572465',
          'host_copy': 'mbit10:/data1/yanruj/DX100-bfs-e4fc4af/benchmarks/gapbs/src/bfs.cc (same SHA-256)'}
ALLOCATION = {
    'decision': 'resume-plan-20260927.md R8; root allocation for the next attempt after context4, 2026-09-27 10:40 ET',
    'pool_provider_seconds': 1800, 'per_call_seconds': 900, 'per_call_usd': 10, 'maximum_repairs': 2,
    'policy': 'Fresh bounded allocation for context5 defined by root after context4 timed out (900.498 s, '
              'empty stdout). Contexts 1-4 remain failed and charged; nothing is refunded. Unresolved or failed '
              'outcomes are retained. One submission, no retry. No strategy change.'}
PROVIDER = {'kind': 'claude', 'command': ['/data1/yanruj/.npm-global/bin/claude'], 'timeout_s': 900,
            'max_repairs': 2, 'total_seconds': 1800, 'budget_usd': 10, 'output_format': 'stream-json'}

ANCHORS = ['#include "timer.h"', '', '  front.reset();', '  while (!queue.empty()) {']
HEADER = '''SWDB HW ENSEMBLE ANNOTATION (context5) - SELECTED STRATEGY, NOT EXECUTED CODE
Producer: representative HW-producer test client (not a live collaborator agent).

Strategy (unchanged): add a DX100 top-down helper to this upstream direction-optimizing
BFS and prefer it for frontiers larger than four 1,024-vertex blocks
(queue.size() > NUM_CORES*1024); keep the original CPU direction policy (TDStep/BUStep)
for smaller frontiers. Checked 32-bit CSR offset conversion, MAA initialization and slot
allocation happen inside DOBFS, so the complete-call ROI charges them. Build: GCC 13,
-DGEM5 -DMAA -DNUM_CORES=4 -DTILE_SIZE=16384, pinned DX100 API include directory.

The four code blocks below ARE the intended executable edits; all are pure insertions
(no original line is removed or changed). Realize them as a unified diff against the
ORIGINAL src/bfs.cc (which does not contain this comment):
  EDIT 1 inserts after the line  #include "timer.h"
  EDIT 2 inserts between TDStep and QueueToBitmap (after the first blank line that
         follows TDStep's closing brace)
  EDIT 3 inserts in DOBFS after  front.reset();
  EDIT 4 inserts in DOBFS as the first statements inside  while (!queue.empty()) {
Output only those four hunks with at most three lines of context each; do not restate
unchanged code, and keep the interpretation short. Correct only what fails to build
against the supplied headers; do not redesign, rename, reorder MAA calls, or add work.
If an edit cannot be realized against the supplied source and headers, report it in
unresolved with an empty patch.

What each part realizes (adapted from the pinned author TDStepMAA, {author}):
- Headers: <MAA_utility.hpp> includes <MAA_gem5.hpp> and <gem5/m5ops.h> because the build
  defines GEM5; add_mem_region/clear_mem_region, tiles and registers come from MAA_gem5.hpp
  and MAA.hpp (NUM_TILES_PER_CORE = NUM_REGS_PER_CORE = 8). The DX100 code is under MAA.
- Public accessors only: queue.begin()/size(), parent.data(), g.out_neigh(0).begin()
  (the neighbor array base), g.VertexOffsets(). Author queue.shared/start_/out_neighbors_
  are private upstream; indices are relative to the current frontier window.
- Checked conversion: 64-bit SGOffset offsets become int32 only if every count and offset
  fits INT_MAX; otherwise DX100Prepare returns false and DOBFS keeps the CPU policy.
  Offsets are never truncated.
- Slots: eight distinct 32-bit tiles and eight scalar registers per guest thread (exactly
  32 each), allocated serially under omp critical after alloc_MAA()/init_MAA(), inside DOBFS.
  No allocation in a global constructor; the slot tables are plain zero-initialized arrays.
- Tile sequence per thread: stream-load frontier u, gather offsets[u] and offsets[u+1],
  range-loop (i, j), gather v = neighbors[j] and u = frontier[min + i], wait on tile7 and
  use its ACTUAL returned length. Tile length is the largest power of two <= TILE_SIZE with
  remaining > NUM_CORES * length (>= 1024), exactly the author's TILE_SIZE ladder.
- Parent update: gather parent[v], mask parent[v] < 0, masked vector store parent[v] = u
  returning the OLD parent values in tile5, all inside one omp critical, then wait on
  tile5 (the store's old-value destination) before leaving the critical section. The
  author waited on tile3; tile5 is the destination actually consumed. The masked store is
  not a CPU compare-and-swap; the returned old value suppresses duplicate targets.
- Enqueue only lanes with mask true and old parent < 0; scout count sums -old_parent in
  int64_t. Scalar tail (remaining <= NUM_CORES*1024) keeps the compare-and-swap loop and
  the same scout count. Memory regions: the actual frontier window, converted offsets,
  neighbor array and parent array, cleared after the step.
- DOBFS: after an offloaded step, edges_to_check, scout_count and queue.slide_window()
  follow the original top-down bookkeeping. No m5 ROI calls, no verifier change, no PASS
  printing; bottom-up, bitmap handling, parent encoding and final normalization unchanged.
'''


def sha(data):
    return hashlib.sha256(data).hexdigest()


def edits():
    """The reference's insert-only hunks: (anchor line in the original, added text)."""
    original = ORIGINAL.read_text().splitlines(keepends=True)
    reference = REFERENCE.read_text().splitlines(keepends=True)
    blocks = []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, original, reference, autojunk=False).get_opcodes():
        if tag == 'equal':
            continue
        assert tag == 'insert' and i1 == i2 and i1 > 0, (tag, i1, i2)
        blocks.append((original[i1 - 1].rstrip('\n'), ''.join(reference[j1:j2])))
    assert [anchor for anchor, _ in blocks] == ANCHORS, [anchor for anchor, _ in blocks]
    return blocks


def annotation():
    parts = [HEADER.replace('{author}', f"{AUTHOR['path']} lines {AUTHOR['lines'][0]}-{AUTHOR['lines'][1]}, "
                                        f"sha256 {AUTHOR['file_sha256'][:16]}")]
    for number, (anchor, text) in enumerate(edits(), 1):
        where = anchor.strip() or 'the blank line after TDStep'
        parts.append(f'----- EDIT {number} (insert after: {where}) -----\n{text}')
    text = '/*\n' + '\n'.join(parts) + '----- END SWDB HW ANNOTATION -----\n*/\n'
    assert text.count('*/') == 1 and text.count('/*') == 1
    return text


def build():
    prior = json.loads((HERE / 'prepared/context4.proposal.json').read_text())
    retained = yamlio.load(ROOT / 'records/proposals' / (PREVIOUS + '.yaml'))
    assert retained['request'] == prior and retained['outcome']['state'] == 'failed' and not retained.get('candidate')
    request = copy.deepcopy(prior)
    request['id'] = NEW
    request['payload'] = {'kind': 'annotated_source',
                          'content': {'files': {'src/bfs.cc': annotation() + ORIGINAL.read_text()}}}
    parameters = request['parameters']
    parameters['predecessor_proposal'] = PREVIOUS
    parameters['provider_allocation'] = ALLOCATION
    parameters['annotation_revision'] = {
        'from': PREVIOUS, 'change': 'concrete helper and dispatch code blocks with insertion anchors; '
        'author reference cited by identity instead of inlined', 'author_reference': AUTHOR,
        'reference_source_sha256': sha(REFERENCE.read_bytes()),
        'producer_check': 'producer-check/functional-check.sh on the pinned DX100 functional model; '
                          'test-client coherence check only, not candidate or DX100 evidence'}
    for key in ('strategy', 'intent', 'regions', 'required_operations', 'constraints', 'source_snapshot',
                'profile_package', 'source_sha256', 'implementation', 'hardware_target', 'producer'):
        assert request[key] == prior[key], key
    for key in ('supporting_profile_packages', 'selection', 'prompt_projection', 'read_only_context',
                'target_execution_clarification'):
        assert parameters[key] == prior['parameters'][key], key
    return request


def render(request):
    spec = HERE / 'prepare_context4.py'
    import importlib.util
    loader = importlib.util.spec_from_file_location('prepare_context4', spec)
    module = importlib.util.module_from_spec(loader)
    loader.loader.exec_module(module)
    return module.render(request)


def main():
    request = build()
    prompt = render(request)
    out = HERE / 'prepared'
    (out / 'context5.proposal.json').write_text(json.dumps(request, indent=2, ensure_ascii=False) + '\n')
    (out / 'context5.provider.json').write_text(json.dumps(PROVIDER, indent=2) + '\n')
    summary = {'id': NEW, 'predecessor': PREVIOUS, 'prompt_bytes': len(prompt.encode()),
               'prompt_sha256': sha(prompt.encode()), 'context4_prompt_bytes': 115100,
               'annotation_bytes': len(annotation().encode()),
               'proposal_sha256': sha((out / 'context5.proposal.json').read_bytes()),
               'provider_sha256': sha((out / 'context5.provider.json').read_bytes())}
    (out / 'context5.summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
