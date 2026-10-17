"""2026-10-16 ET. Local ancillary authoring only; performs no dispatch or SSH."""
import ast
import copy
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
POC = WHOLE.parent.parent
OLD = WHOLE / 'normalized-unit-envelope-v3-dispatch'
PACKET = WHOLE / 'normalized-unit-envelope-v5'
LAUNCHER = WHOLE / 'root-launcher-loader-v11/launch_observer_loader_v11.py'


def pin(path):
    raw = path.read_bytes()
    return dict(path=str(path), bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())


def save(path, value):
    raw = value if isinstance(value, bytes) else (json.dumps(value, indent=2, sort_keys=True) + '\n').encode()
    with path.open('xb') as stream:
        stream.write(raw)
    return pin(path)


def build(standards):
    evidence = pin(standards)
    command = json.loads((PACKET / 'command-v5.json').read_bytes())
    baseline = json.loads((OLD / 'root-source-review-v3.json').read_bytes())
    selected = copy.deepcopy(baseline)
    controls = [dict(name=name, **row) for name, row in sorted(command['stage_sources'].items())]
    controls.append(dict(name='envelope-policy-v5.json', **pin(PACKET / 'envelope-policy-v5.json')))
    assert len(controls) == 31 and sum(row['bytes'] for row in controls) == 479538
    assert len({row['name'] for row in controls}) == 31
    for row in controls:
        assert pin(Path(row['path'])) == {key: row[key] for key in ('path', 'bytes', 'sha256')}
    selected.update(control_files=controls, raw_root=command['raw'], review_evidence=evidence)
    changed = [name for name in baseline if baseline[name] != selected[name]]
    assert set(changed) == {'control_files', 'raw_root', 'review_evidence'}
    review_path = HERE / 'root-source-review-v5.json'
    source_review = save(review_path, selected)
    old_preflight = (OLD / 'root-derived-scoped-preflight-v3.py').read_text()
    old_output = "OUTPUT=Path('/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v3')"
    new_output = old_output.replace('-v3', '-v5')
    old_needle = "'/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v3')\n"
    new_needle = "'/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v3','/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-unit-observation-2baf722f-v5')\n"
    assert old_preflight.count(old_output) == 1 and old_preflight.count(old_needle) == 2
    # Limit the reader-set addition to the needles assignment; keep all old
    # reader roots and change only the separately checked fresh output path.
    new_preflight = old_preflight.replace(old_output, new_output)
    assert new_preflight.count(old_needle) == 1
    new_preflight = new_preflight.replace(old_needle, new_needle)
    reconstructed = new_preflight.replace(new_needle, old_needle).replace(new_output, old_output)
    assert reconstructed == old_preflight
    old_defs = {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(old_preflight).body if isinstance(node, ast.FunctionDef)}
    new_defs = {node.name: ast.dump(node, include_attributes=False) for node in ast.parse(new_preflight).body if isinstance(node, ast.FunctionDef)}
    assert old_defs == new_defs
    preflight = save(HERE / 'root-derived-scoped-preflight-v5.py', new_preflight.encode())
    inverse = save(HERE / 'preflight-inverse-v5.json', dict(date='2026-10-16 Eastern', predecessor=pin(OLD / 'root-derived-scoped-preflight-v3.py'), successor=preflight, replacements=[dict(old=old_output,new=new_output,count=1),dict(old=old_needle,new=new_needle,count=1,after_first_replacement=True)], complete_inverse=True, all_function_ASTs_exact=True, original_readers_preserved=True, source_runtime_known_pins_and_guards_unchanged=True))
    argv = ['/Users/yanrujhou/.pyenv/versions/3.12.6/bin/python3', '-I', '-B', str(LAUNCHER), selected['source_commit'], 't28-unit-observation-v5', '1200', '0', str(PACKET / 'root-argv-v5.json'), str(review_path)]
    payload = dict(schema='semantic-observer-v5-root-ancillary-packet-1', date='2026-10-16 Eastern', actual_executed=False, root_once_admission_pending=True,
        launcher=pin(LAUNCHER), source_review=source_review, source_packet=pin(PACKET / 'source-packet-v5.json'), envelope_command=pin(PACKET / 'command-v5.json'), bare_argv=pin(PACKET / 'root-argv-v5.json'), root_standards=evidence,
        independent_spec=pin(WHOLE / 'normalized-unit-envelope-v5-independent-review/independent-semantic-observer-v5-spec-review-20261016.json'), predecessor_source_review=pin(OLD / 'root-source-review-v3.json'), preflight=preflight, preflight_inverse=inverse,
        exact_local_launcher_argv=argv, source_project='/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project', node=0, no_new_checkout_required=True,
        flat_control_payloads=30, separate_envelope_policy=1, flat_control_count=31, flat_control_bytes=479538,
        guard=dict(rss_bytes=4294967296,whole_seconds=1200,workers=1,retained_bytes=268435456),run_environment_unset=['LIBRARY_PATH','LD_LIBRARY_PATH'],
        inverse=dict(changed_fields=changed,all_other_source_review_fields_exact=True,production_diff_two_paths_exact=True,baseline_and_original2baf_source_exact=True),
        preflight_wrapper_note='Inherited scoped preflight does not pin a MemAcc HEAD. The unchanged V11 launcher freshly fetches and requires exact physical socket_lane and hostlock bytes against FETCH_HEAD; no stale HEAD rebind was needed.',
        authority_boundary='Existing completed source reviews are evidence only. Root must separately admit this exact prospective invocation after fresh scoped source/raw/process/lease/runtime/disk checks; no new admission receipt is fabricated or put in observer controls.',
        source_ABI_call_or_public_admission=False)
    return save(HERE / 'root-ancillary-packet-v5.json', payload)


if __name__ == '__main__':
    assert len(sys.argv) == 2, 'pass the existing actual root Standards receipt; no placeholder'
    print(json.dumps(build(Path(sys.argv[1]).resolve()), sort_keys=True))
