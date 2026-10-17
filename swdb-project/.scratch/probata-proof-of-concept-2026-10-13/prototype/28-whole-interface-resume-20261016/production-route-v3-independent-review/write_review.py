"""Independent physical pins/inverses and source-review receipt; no project imports."""
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;WHOLE=HERE.parent;ROUTE=WHOLE/'production-route-v3';V2=WHOLE/'production-route-v2'
def pin(path):
    raw=path.read_bytes();return {'path':str(path),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
def doc(path):return json.loads(path.read_bytes())
packet=ROUTE/'source-packet-v3.json';assert pin(packet)['sha256']=='333d3aeecd251a0fd7ce3a489f958ba0faf9951c6fc8f03ab78d27cb2f550379'
new=doc(packet);old=doc(V2/'source-packet-v2.json')
for row in new['files']+old['files']:
    actual=pin(Path(row['path']));assert (actual['bytes'],actual['sha256'])==(row['bytes'],row['sha256'])
scope=doc(ROUTE/'v3-inverse-scope.json');changed=[]
for relative,meta in scope['inverse'].items():
    path=ROUTE/'proposed'/relative;lines=path.read_text().splitlines(keepends=True)
    for change in sorted(meta['exact_line_inverse'],key=lambda row:row['new_begin'],reverse=True):
        begin,end=change['new_begin'],change['new_end'];assert lines[begin:end]==change['after'],relative
        lines[begin:end]=change['before']
    restored=''.join(lines).encode();assert restored==(V2/'proposed'/relative).read_bytes(),relative
    changed.append(relative)
for relative in scope['byte_identical_production_files']:
    assert (ROUTE/'proposed'/relative).read_bytes()==(V2/'proposed'/relative).read_bytes(),relative
bases=[]
for name,changes in doc(ROUTE/'hook-inverse-v1.json').items():
    source=(ROUTE/'proposed/swdb'/name).read_text()
    for change in reversed(changes):
        assert source.count(change['new'])==change['count'],(name,change)
        source=source.replace(change['new'],change['old'])
    assert source.encode()==(ROUTE/'base-source'/name).read_bytes(),name
    bases.append(name)
controls=json.loads((HERE/'independent-controls.log').read_text().splitlines()[-1]);assert controls['tests']==6 and controls['failures']==controls['errors']==controls['skips']==0 and controls['child_events']==[]
review={'date':'2026-10-16 ET','verdict':'PASS: independent static standards/native-boundary preparation review only',
    'packet':pin(packet),'full_patch':pin(ROUTE/'production-full-v3.patch'),'V2_packet':pin(V2/'source-packet-v2.json'),
    'physical_pin_rows_rehashed':len(new['files'])+len(old['files']),'V3_changed_production_inverse':sorted(changed),
    'V3_unchanged_production_files':len(scope['byte_identical_production_files']),'six_hook_exact_base_inverse':sorted(bases),
    'independent_controls':controls,'review_files':[pin(HERE/'review_controls.py'),pin(HERE/'independent-controls.log'),pin(HERE/'write_review.py')],
    'findings':[],
    'reviewed_behavior':[
        'Exact new checked-body/source kind and fresh method select the isolated full-TU/source/receiver route. Generic call summaries and pointer exemptions are not granted by this entry.',
        'The exact 79/80 pair changes only the postcondition. All source/model/receiver/Plan/view inputs are freshly regenerated and physically rechecked before and after actual launch seams.',
        'Generated C and original-source C++ have fixed separate roles. Replay can only consume freshly regenerated C++ bytes; CBMC and loop inventory can only consume C bytes. Canonical physical hash/size checks refuse aliases and substitutions.',
        'Checked-only native failure overrides both recovery macros before oracle/model/source definitions. It prints and flushes exact failure/end metadata and calls _Exit; it never longjmps through proxy lifetimes and does not imply destructor execution on fatal paths.',
        'Each sampled oracle row starts a fresh process. Successful source return evaluates its result before array destruction/lifetime exit; receiver preparation and independent draw-table initialization occur once.',
        'Source-preserving projection V2 remains byte-identical. Lowered C is not used as the independent original-source C++ counterpart; agreement still uses the same explicit owned concrete model on both sides.',
        'All six receiver context premises bind exact owned, recorded library rules. The unchanged entry#rule producer carries physical entry SHA references and owners; no free assumed_clause is manufactured.',
        'Whole-state assigns everything is admitted only for the physically selected checked scalar pair. Unsupported source/effects/contracts/frames and malformed metadata preserve refusal or existing generic diagnostics.',
        'Existing optional defaults and legacy prelude/harness behavior remain intact under the exact reviewed inverses. No WP summary fallback exists for checked concrete bodies.'
    ],
    'remaining_actual_gates':[
        'No complete accepted original-TU capture exists for this fixture. The route currently supports its exact V8 complete transport/schema and refuses V10/raw duplicate streams; any normalized role transport requires a separately reviewed successor.',
        'Actual full-TU/source/ABI/call/global/CPU/lifetime/receiver/view exercise and fresh method/runtime/environment publication/admission remain required.',
        'Real positive proof, negative replay/refutation, source/public record and reachability controls remain root-owned; source review and synthetic controls provide none of those outcomes.',
        'First fixed scalar trace is not whole-interface readiness, two-thread, region/ownership/pair or full ticket28 acceptance. Source/compiler projection, numeric runtime and MMIO-implements-semantics remain explicit owned TCB premises.'
    ],
    'actual_capture_reader_or_scientific_execution':False,'shared_production_edited':False,'compiler_native_solver_SSH_executed':False,'public_or_full28_acceptance':False}
(HERE/'independent-review-v3.json').write_text(json.dumps(review,sort_keys=True,indent=2)+'\n')
print(json.dumps(pin(HERE/'independent-review-v3.json')))
