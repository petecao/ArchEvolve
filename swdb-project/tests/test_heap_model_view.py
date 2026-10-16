"""Public heap-model proof preparation; created 2026-10-15 ET (ticket25).

External stand-ins report deliberate parse errors, sleep, or labeled synthetic
results. These controls exercise public planning, prelaunch and record writing;
they never establish an actual proof.
"""
from pathlib import Path
import os
import shlex
import subprocess
import pytest

from test_standard_range_model import _public_seed


def _heap_public_seed(tmp_path, metadata_action=''):
    library, prove, marker = _public_seed(tmp_path)
    # Metadata-only stand-in response binds the actual native reader packages.
    find = shlex.split(os.environ.get('SWDB_OCAMLFIND') or 'opam exec --switch=framac-33 -- ocamlfind')
    core = Path(subprocess.check_output([*find, 'query', 'frama-c-wp.core'], text=True, timeout=30).strip())
    share = str(core.parents[2] / 'share/frama-c/share')
    frama = tmp_path / 'frama.py'
    action = ''.join(' ' + line + '\n' for line in metadata_action.splitlines())
    frama.write_text(frama.read_text().replace('if "-version"',
        'if "-print-share-path" in sys.argv:\n' + action +
        f' print({share!r});sys.exit(0)\nif "-version"'))
    return library, prove, marker


@pytest.mark.parametrize('member,first', [
    ('std_vector_int_ctor_count_value', 't25_control_ctor_premises_feasible'),
    ('std_vector_int_dtor', 't25_control_dtor_premises_feasible')])
def test_public_original_model_reaches_checked_heap_packet_before_scripted_parse_error(tmp_path, member, first):
    _library, prove, marker = _heap_public_seed(tmp_path)
    record = prove('--model', member)
    assert record['verdict'] == 'not_proven'
    assert record['failure_class'] == 'parse_error', record
    assert marker.exists(), 'the exact heap view must pass setup before the stand-in'
    view = record['settings']['heap_model_view']
    assert view['member'] == member
    assert view['original_caller_premises_added'] == []
    assert view['generic_caller_composition'] == 'unsupported'
    assert view['source_events'] and view['obligations']
    assert len(view['obligations']) == (27 if member.endswith('ctor_count_value') else 11)
    evidence = Path(__file__).parents[1] / '.scratch/probata-proof-of-concept-2026-10-13/evidence'
    import json
    accepted = json.loads((evidence / 't25-full42-cold-summary-v1-e56c62dd-20261015.json').read_text())
    golden = {r['id']: r['canonical_input']['sha256'] for r in accepted['rows']}
    assert all(row['sha256'] == golden[row['id']] for row in view['obligations'])
    assert 'heap_model_view_check' in record['pins']
    assert record['proof_setup_check']['verdict'] == 'passed'
    assert record['proof_setup_check']['runs'][-1]['hashes']['heap_model_view']
    assert '-wp-prop' not in record['settings']['flags']
    reports = {r['name']: r for r in record['evidence']['reports']}
    assert {'heap_model_original', 'heap_model_certificate', 'heap_model_theory'} <= reports.keys()
    text = Path(reports['wp_input']['path']).read_text()
    assert text.count('check lemma ') == 1
    assert first in text
    allocation = [a for a in record['assumptions'] if a['sentence'].startswith('Allocation succeeds')]
    assert bool(allocation) == member.endswith('ctor_count_value')


def test_unmapped_model_build_defines_do_not_silently_enter_the_original_heap_view(tmp_path):
    _library, prove, marker = _heap_public_seed(tmp_path)
    record = prove('--model', 'std_vector_int_ctor_count_value', '--define', 'COUNT=7')
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'unsupported_construct', record
    assert not marker.exists()


def test_public_original_count_constructor_maps_zero_fill_before_standin(tmp_path):
    _library, prove, marker = _heap_public_seed(tmp_path)
    record = prove('--model', 'std_vector_int_ctor_count')
    assert record['failure_class'] == 'parse_error', record
    assert marker.exists()
    view = record['settings']['heap_model_view']
    assert view['member'] == 'std_vector_int_ctor_count'
    assert view['original_caller_premises_added'] == []
    assert view['value_instantiation'] == {'source_expression': '(int)0', 'mathematical_value': 0}
    assert len(view['obligations']) == 27
    assert set(view['required_source_groups']) == {f'C{i}' for i in range(1, 10)}
    events = {e['id']: e for e in view['source_events']}
    assert {'count.fill', 'count.loop.init', 'count.loop.test', 'count.loop.increment',
            'count.final.size'} <= events.keys()
    reports = {r['name']: r for r in record['evidence']['reports']}
    original = Path(reports['heap_model_original']['path']).read_text()
    assert 'this->data[k] = (int)0;' in original
    assert 'this->data[k] == 0;' in original
    assert record['proof_setup_check']['verdict'] == 'passed'
    assert any(a['sentence'].startswith('Allocation succeeds') for a in record['assumptions'])
    targets = {row['id']: row for row in view['obligations']}
    assert 'Heap::put_integer(h,b,4*k,0)' in targets['count.prefix.step']['statement']
    assert 'filled_prefix' in targets['count.final.post']['statement']
    assert targets['count.numeric']['kind'] == 'c_kernel'
    assert not any(row['dependencies'] for row in targets.values())


@pytest.mark.parametrize('attack', ['fill', 'postcondition', 'extra_write', 'prefix'])
def test_public_count_source_and_zero_fill_inventory_cannot_be_laundered(tmp_path, attack):
    actions = {
        'fill': "p.write_text(p.read_text().replace('this->data[k] = (int)0;', 'this->data[k] = (int)1;'))",
        'postcondition': "p.write_text(p.read_text().replace('this->data[k] == 0;', 'this->data[k] == 1;'))",
        'extra_write': "p.write_text(p.read_text().replace('this->size = n;', 'this->size = n; this->capacity = 0;'))",
        'prefix': "m['obligations']=[r for r in m['obligations'] if r['id']!='count.prefix.step']",
    }
    action = 'import json,hashlib\n'
    action += f'stage,=Path({str(tmp_path / "runs")!r}).rglob("heap-inputs")\n'
    action += 'manifest=stage/"manifest.json"\nm=json.loads(manifest.read_text())\n'
    action += 'p=stage/"std_vector_int_ctor_count.original.c"\n' + actions[attack] + '\n'
    action += 'm["sources"]["std_vector_int_ctor_count"]["sha256"]=hashlib.sha256(p.read_bytes()).hexdigest()\n'
    action += 'manifest.write_text(json.dumps(m))'
    _library, prove, marker = _heap_public_seed(tmp_path, action)
    done = prove('--model', 'std_vector_int_ctor_count', ok=False)
    assert done.returncode != 0 and 'heap_model_view' in done.stderr
    assert not marker.exists()


def test_configured_why3_roots_cannot_shadow_the_canonical_heap_or_standard_foundations(tmp_path):
    _library, prove, marker = _heap_public_seed(tmp_path)
    shadow = tmp_path / 'shadow'
    shadow.mkdir()
    (shadow / 'heap_bridge.mlw').write_text('theory Heap\n axiom desired: false\nend\n')
    config = tmp_path / 'why3.conf'
    config.write_text('[main]\nmagic = 14\nloadpath = ' + repr(str(shadow)).replace("'", '"') + '\n' + config.read_text())
    record = prove('--model', 'std_vector_int_ctor_count_value')
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'unsupported_construct', record
    assert not marker.exists()
    handler = next(r for r in record['evidence']['reports'] if r['name'] == 'handler')
    assert 'load path' in Path(handler['path']).read_text()


@pytest.mark.parametrize('attack', ['original', 'obligation', 'theory'])
def test_public_prelaunch_rebuild_rejects_self_consistent_heap_input_tampering(tmp_path, attack):
    actions = {
        'original': "p=stage/'std_vector_int_ctor_count_value.original.c'\n"
                    "p.write_text(p.read_text().replace('this->size = n;', 'this->size = n; this->capacity = 0;'))\n"
                    "m['sources']['std_vector_int_ctor_count_value']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()",
        'obligation': "m['obligations']=[r for r in m['obligations'] if r['id']!='ctor.prefix.step']",
        'theory': "p=stage/'theory/heap_bridge.mlw'\n"
                  "p.write_text(p.read_text().replace('\\nend\\n','\\n axiom forged: false\\nend\\n'))\n"
                  "m['semantics']['sha256']=hashlib.sha256(p.read_bytes()).hexdigest()",
    }
    action = 'import json,hashlib\n'
    action += f'stage,=Path({str(tmp_path / "runs")!r}).rglob("heap-inputs")\n'
    action += 'manifest=stage/"manifest.json"\nm=json.loads(manifest.read_text())\n'
    action += actions[attack] + '\nmanifest.write_text(json.dumps(m))'
    _library, prove, marker = _heap_public_seed(tmp_path, action)
    done = prove('--model', 'std_vector_int_ctor_count_value', ok=False)
    assert done.returncode != 0, done.stdout
    assert 'heap_model_view' in done.stderr, done.stderr
    assert not marker.exists(), 'no formal command may run after the independent source rebuild refuses'


def test_public_serial_heap_targets_share_one_remaining_budget(tmp_path):
    """Synthetic first success followed by a real sleeping stand-in; never an actual proof."""
    _library, prove, marker = _heap_public_seed(tmp_path)
    frama = tmp_path / 'frama.py'
    metadata_prefix = frama.read_text().split('if "-wp" in sys.argv:')[0]
    frama.write_text(metadata_prefix + '''if "-wp" in sys.argv:
 import json,os,re,time
 counter=Path(__file__).with_name("synthetic-first-target")
 if counter.exists():
  time.sleep(30)
  sys.exit(1)
 counter.write_text("SYNTHETIC stand-in only; not actual verifier evidence")
 name=re.search(r"check lemma (\\w+)",Path("wp_input.c").read_text()).group(1)
 prop="check_lemma_"+name
 goal="typed_"+prop
 raw={"goal":goal,"property":prop,"function":None,"line":34,"smoke":False,
      "passed":True,"verdict":"valid","proved":1,
      "provers":[{"prover":"CVC5:1.2.1","time":0,"success":1}]}
 Path("wp-goals.json").write_text(json.dumps([raw]))
 Path("wp-normalized.c").write_text(Path("wp_input.c").read_text())
 Path("wp-properties.csv").write_text("directory\\tfile\\tline\\tfunction\\tproperty kind\\tstatus\\tproperty\\n")
 inv={"version":"1","complete":True,
      "goals":[{"goal":goal,"property":prop,"function":None,"line":34,"smoke":False,
                "passed":True,"targets":[],"results":["valid"]}],
      "properties":[{"property":prop,"function":None,"kind":"lemma","line":34,
                     "extern":False,"dependencies":[],"origin":None,
                     "generated_smoke_failure":False,"description":"synthetic check lemma"}]}
 Path(os.environ["SWDB_PROOF_REPORT_OUT"]).write_text(json.dumps(inv))
 sys.exit(0)
''')
    record = prove('--model', 'std_vector_int_ctor_count_value', '--budget-minutes', '0.1')
    assert record['verdict'] == 'not_proven' and record['failure_class'] == 'timeout', record
    runs = record['settings']['heap_model_runs']
    assert len(runs) == 2 and runs[0]['verdict'] == 'proven', runs
    assert runs[1]['resources']['timed_out'] is True
    assert 0 < runs[1]['timeout_seconds'] < runs[0]['timeout_seconds'] < 6
    assert record['settings']['whole_public_budget_seconds'] == 6


@pytest.mark.parametrize('member,count', [('std_vector_int_dtor', 11), ('std_vector_int_ctor_count', 27)])
def test_complete_synthetic_heap_success_serializes_a_schema_valid_public_record(tmp_path, member, count):
    """Exercise aggregation only; every formal result is a labeled external stand-in."""
    _library, prove, _marker = _heap_public_seed(tmp_path)
    frama = tmp_path / 'frama.py'
    metadata_prefix = frama.read_text().split('if "-wp" in sys.argv:')[0]
    frama.write_text(metadata_prefix + '''if "-wp" in sys.argv:
 import json,os,re
 match=re.search(r"check lemma (\\w+)",Path("wp_input.c").read_text())
 if match:
  specs=[("check_lemma_"+match.group(1),"lemma",False)]
 else:
  assert "size_t t25_ctor_numeric(size_t n, size_t k)" in Path("wp_input.c").read_text()
  specs=[("synthetic_numeric_"+str(i),"assertion",False) for i in range(10)]
  specs.append(("synthetic_numeric_smoke","assertion",True))
 rows=[];generated=[];properties=[]
 for prop,kind,smoke in specs:
  goal="typed_"+prop
  function=None if match else "t25_ctor_numeric"
  rows.append({"goal":goal,"property":prop,"function":function,"line":34,"smoke":smoke,
      "passed":True,"verdict":"valid","proved":1,
      "provers":[{"prover":"CVC5:1.2.1","time":0,"success":1}]})
  generated.append({"goal":goal,"property":prop,"function":function,"line":34,"smoke":smoke,
                    "passed":True,"targets":[],"results":["valid"]})
  properties.append({"property":prop,"function":function,"kind":kind,"line":34,
                     "extern":False,"dependencies":[],"origin":None,
                     "generated_smoke_failure":False,"description":"synthetic control"})
 Path("SYNTHETIC-ONLY.txt").write_text("External stand-in; no actual proof or solver execution")
 Path("wp-goals.json").write_text(json.dumps(rows))
 Path("wp-normalized.c").write_text(Path("wp_input.c").read_text())
 Path("wp-properties.csv").write_text("directory\\tfile\\tline\\tfunction\\tproperty kind\\tstatus\\tproperty\\n")
 inv={"version":"1","complete":True,"goals":generated,"properties":properties}
 Path(os.environ["SWDB_PROOF_REPORT_OUT"]).write_text(json.dumps(inv))
 sys.exit(0)
''')
    # The public command validates the complete record against proof.schema.json.
    record = prove('--model', member)
    assert record['verdict'] == 'proven', record
    assert set(record['verdict_reading']) == {'check', 'verdict'}
    assert record['verdict_reading']['verdict'] == 'proven'
    runs = record['settings']['heap_model_runs']
    assert len(runs) == count and all(r['reading']['verdict'] == 'proven' for r in runs)
    assert len(record['proof_setup_check']['runs']) == count
    assert len(record['goals']) == (11 if count == 11 else 37)
    assert len([g for g in record['goals'] if g.get('smoke')]) == (0 if count == 11 else 1)
    assert all((Path(r['cwd']) / 'SYNTHETIC-ONLY.txt').is_file() for r in runs)


@pytest.mark.skipif(os.environ.get('SWDB_HEAP_MODEL_ACTUAL') != '1',
                    reason='requires separate coordinator admission of exact clean source and formal command')
def test_actual_public_first_pair_heap_models(tmp_path):
    """Actual-only target; ordinary controls never execute this function."""
    _actual_public_models(tmp_path, [('std_vector_int_ctor_count_value', 27), ('std_vector_int_dtor', 11)])


@pytest.mark.skipif(os.environ.get('SWDB_HEAP_MODEL_ACTUAL') != '1',
                    reason='requires separate coordinator admission of exact clean source and formal command')
def test_actual_public_original_count_model(tmp_path):
    """One new original model only; no successful first-pair proofs are repeated."""
    _actual_public_models(tmp_path, [('std_vector_int_ctor_count', 27)])


def _actual_public_models(tmp_path, members):
    import json
    import time
    import yaml
    from conftest import run_swdb
    from test_standard_member_contracts import _member_seed
    from swdb import proof_setup
    seed = _member_seed(tmp_path)
    public = int(os.environ.get('SWDB_HEAP_MODEL_PUBLIC_TIMEOUT_SECONDS', '1800'))
    assert 1 <= public <= 3600
    deadline = float(os.environ.get('SWDB_HEAP_MODEL_PROFILE_DEADLINE_MONOTONIC', time.monotonic() + 4200))
    for member, count in members:
        remaining = min(public, deadline - time.monotonic() - 60)
        assert remaining > 0, 'the admitted whole profile budget is spent'
        argv = ['prove', '--records', str(seed.records), '--adapter', 'wp',
                '--method-version', 'method.wp-tracer-fixture', '--runs-dir', str(seed.runs),
                '--format', 'json', '--model', member, '--budget-minutes', str(remaining / 60)]
        (tmp_path / (member + '.command.json')).write_text(json.dumps(argv, indent=2) + '\n')
        done = run_swdb(*argv, timeout=remaining + 60)
        (tmp_path / (member + '.stdout')).write_text(done.stdout)
        (tmp_path / (member + '.stderr')).write_text(done.stderr)
        assert done.returncode == 0, done.stdout + done.stderr
        record = yaml.safe_load((seed.records / json.loads(done.stdout)['path']).read_text())
        assert record['subject'] == {'kind': 'c_model', 'id': member}
        assert record['verdict'] == 'proven', record
        assert record['evidence_kind'] == 'contract_fixture'
        assert record['bounds'] == {'threads': 1, 'input_size': 'unbounded'}
        assert len(record['settings']['heap_model_runs']) == count
        assert len(record['proof_setup_check']['runs']) == count
        assert record['verdict_reading']['check'] == proof_setup.identity()['verdict_reading']
        assert all(g['status'] == 'valid' for g in record['goals'])
        constructor = member != 'std_vector_int_dtor'
        assert len([g for g in record['goals'] if g.get('smoke')]) == (1 if constructor else 0)
        assert len([g for g in record['goals'] if not g.get('smoke')]) == (36 if constructor else 11)
        numeric = [r for r in record['settings']['heap_model_runs'] if r['id'].endswith('.numeric')]
        assert len(numeric) == (1 if constructor else 0)
        assert record['pins']['code']['sha256'] == record['settings']['heap_model_view']['original_source']['sha256']
