"""Checked unbounded heap view for exact original int vector models.

Created 2026-10-15 ET (ticket25). The source/VC translator and uniform allocator
semantics are explicit trusted tools. Every selected positive obligation must be
proved afresh; prototype observations are never promoted into proof records.
"""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import shlex
import shutil
import subprocess
import time

from swdb import heap_model_packets as packets

HERE = Path(__file__).parent
MEMBERS = packets.MEMBERS
COMPONENTS = ('heap_model_view.py', 'heap_model_packets.py', 'heap_model_vcs.py',
              'heap_bridge.mlw', 'heap_model_environment.ml')
DIAGNOSTICS = 'print-generated,why3:compile,why3:import,prover:pp_task'


class Refused(ValueError):
    """The exact source-to-heap correspondence or import binding is absent."""


def _sha(value):
    return hashlib.sha256(value if isinstance(value, bytes) else value.encode()).hexdigest()


def _digest(value):
    return _sha(json.dumps(value, sort_keys=True, separators=(',', ':')))


def identity():
    return {'id': 'heap-model-view-check-1', 'sha256': _digest([
        {'path': name, 'sha256': _sha((HERE / name).read_bytes())} for name in COMPONENTS])}


@dataclass(frozen=True)
class View:
    member: str
    certificate: dict
    pins: dict


def _view(member, manifest):
    if member not in MEMBERS:
        raise Refused('the original heap view supports only the audited int count/value constructor and destructor')
    targets = [row for row in manifest['obligations']
               if row['member'] == member and row['expected'] == 'proven']
    events = [row for row in manifest['source_events'] if row['member'] == member]
    ids = {row['id'] for row in targets}
    if not targets or not events or any(not set(e['obligations']) <= ids for e in events):
        raise Refused('the original source event inventory is not covered by positive proof obligations')
    groups = {g for row in targets for g in row['source_groups']}
    required = {f'C{i}' for i in range(1, 10)} if member == MEMBERS[0] else {f'D{i}' for i in range(1, 8)}
    # The constructor-associated address-reuse control additionally checks D7;
    # retain it as audited lifetime support rather than dropping that target.
    expected_groups = required | ({'D7'} if member == MEMBERS[0] else set())
    if groups != expected_groups:
        raise Refused('the original clause/RTE/init/frame/lifetime inventory is incomplete')
    cert = {'version': 1, 'member': member, 'original_source': manifest['sources'][member],
            'model': manifest['model'], 'source_events': events, 'source_groups': sorted(groups),
            'required_source_groups': sorted(required),
            'obligations': targets, 'semantics': manifest['semantics'],
            'translation_components': manifest['translation_components'],
            'original_caller_premises_added': [], 'generic_caller_composition': 'unsupported',
            'incoming_heap': manifest['semantic_relations']['incoming_heap'],
            'allocation_policy': manifest['semantic_relations']['allocation_policy'],
            'typed_memory': manifest['semantic_relations']['typed_memory'],
            'proof_rule': 'all selected original-source obligations require fresh normal-reader proof; no cached prototype promotion',
            'negative_controls': 'translator regression controls, not desired model-body obligations'}
    return View(member, cert, {'heap_model_view_check': identity(),
        'heap_model_view_certificate': {'id': 'heap-model-view-certificate-1', 'sha256': _digest(cert)}})


def prepare(member, directory):
    try:
        manifest = packets.prepare(Path(directory))
        return _view(member, manifest)
    except (ValueError, KeyError) as exc:
        raise Refused(str(exc)) from None


def check(member, view, directory):
    try:
        fresh = _view(member, packets.check(Path(directory)))
    except (ValueError, KeyError) as exc:
        raise Refused(str(exc)) from None
    if fresh != view:
        raise Refused('the original heap view, target inventory or checker pin changed before launch')
    return fresh


def certificate_text(view):
    return json.dumps(view.certificate, sort_keys=True, indent=2) + '\n'


def flags(tools):
    selected = any(f == '-wp-prover' or f.startswith('-wp-prover=') for f in tools['flags'])
    return [*tools['flags'], '-machdep', 'x86_64',
            *([] if selected else ['-wp-prover', ','.join(tools['provers'])]),
            '-wp-timeout', str(tools['seconds']), '-wp-par', '1', '-wp-smoke-tests',
            '-wp-status-all', '-wp-out', 'prover-files', '-wp-print', '-wp-msg-key', DIAGNOSTICS]


def command(tool, settings_flags, inputs, report_module):
    # One check lemma per input: the default complete property selection is used.
    # No -wp-prop or warning-key exception is added to proof_setup's policy.
    return [*tool, '-machdep', 'x86_64', '-wp-library', str(inputs / 'theory'),
            '-wp-msg-key', DIAGNOSTICS, 'wp_input.c', '-print', '-ocode', 'wp-normalized.c', '-then',
            *settings_flags, '-wp-library', str(inputs / 'theory'), '-wp-report-json', 'wp-goals.json',
            '-then', '-load-module', str(report_module), '-report', '-report-untried',
            '-report-csv', 'wp-properties.csv']


def _remaining(deadline):
    left = deadline - time.monotonic()
    if left <= 0:
        raise TimeoutError('the whole public heap-model budget is spent')
    return left


def _query(argv, deadline, *, cwd=None):
    try:
        done = subprocess.run(argv, cwd=cwd, capture_output=True, timeout=min(120, _remaining(deadline)))
    except subprocess.TimeoutExpired:
        raise TimeoutError('the whole public heap-model setup budget is spent') from None
    if done.returncode:
        raise Refused('heap-model metadata/reader preparation failed: ' + done.stderr.decode(errors='replace')[:800])
    return done.stdout


def foundations(tool, directory, deadline):
    """Bind the actual importer/prover search roots, rather than pinning unused files."""
    find = shlex.split(os.environ.get('SWDB_OCAMLFIND') or 'opam exec --switch=framac-33 -- ocamlfind')
    core = Path(_query([*find, 'query', 'frama-c-wp.core'], deadline).decode().strip()).resolve()
    why3 = Path(_query([*find, 'query', 'why3'], deadline).decode().strip()).resolve()
    prefix = core.parents[2]
    if core != prefix / 'lib/frama-c-wp/core' or why3 != prefix / 'lib/why3':
        raise Refused('WP and Why3 packages must belong to the same selected switch')
    share = Path(_query([*tool, '-print-share-path'], deadline).decode().strip()).resolve()
    if share != prefix / 'share/frama-c/share':
        raise Refused('the selected Frama-C share path is not bound to the reader WP package')
    directory.mkdir(exist_ok=False)
    source = directory / 'heap_model_environment.ml'
    shutil.copyfile(HERE / source.name, source)
    executable = directory / 'heap_model_environment'
    _query([*find, 'ocamlopt', '-linkpkg', '-package', 'why3', '-o', str(executable), str(source)], deadline)
    paths = _query([str(executable)], deadline).decode().split('\0')
    if paths[-1] != '':
        raise Refused('the Why3 load-path metadata response is incomplete')
    stdlib = prefix / 'share/why3/stdlib'
    if [Path(p).resolve() for p in paths[:-1]] != [stdlib]:
        raise Refused('heap import requires the exact selected Why3 standard-library load path')
    roots = {'stdlib': stdlib, 'wp': share / 'wp/why3/frama_c_wp'}
    expected = FOUNDATION_HASHES
    pins = []
    for key, digest in expected.items():
        root, name = key.split('/')
        path = roots[root] / name
        if not path.is_file() or _sha(path.read_bytes()) != digest or path.with_suffix('.why').exists():
            raise Refused('the reviewed standard heap-proof foundation changed or is shadowed: ' + key)
        pins.append({'path': str(path), 'sha256': digest})
    if (stdlib / 'heap_bridge.mlw').exists() or (stdlib / 'heap_bridge.why').exists():
        raise Refused('the selected Why3 load path shadows the canonical heap import')
    return {'frama_share': str(share), 'why3_loadpath': [str(stdlib)], 'sources': pins,
            'ocamlfind_command': find, 'ocaml_package_paths': {'wp_core': str(core), 'why3': str(why3)},
            'metadata_source_sha256': _sha(source.read_bytes()),
            'metadata_executable_sha256': _sha(executable.read_bytes()),
            'metadata_executable': str(executable),
            'scope': 'explicit trusted Why3/Frama-C arithmetic/map/datatype support; no project desired theorem'}


def check_launch(job, adapter, context, command_line, settings_flags, directory):
    """Independent reconstruction at proof_setup's ordinary launch boundary."""
    state = context['heap_model_view']
    view, inputs = state['view'], state['inputs']
    check(job.unit.function, view, inputs)
    if job.unit.tree_sha256 != view.certificate['original_source']['sha256'] or \
            job.unit.contract_sha256 != view.certificate['original_source']['sha256']:
        raise Refused('the public subject does not pin the original model body and contract')
    row = state['row']
    if row not in view.certificate['obligations'] or row['expected'] != 'proven':
        raise Refused('a source obligation was replaced by a control or unrelated target')
    if (Path(directory) / 'wp_input.c').read_text() != (inputs / row['path']).read_text():
        raise Refused('the selected original-source obligation changed before launch')
    if state['certificate_path'].read_text() != certificate_text(view):
        raise Refused('the recorded original-source certificate changed before launch')
    if any(context['pins'].get(key) != pin for key, pin in view.pins.items()):
        raise Refused('the original heap-view checker or certificate pin changed before launch')
    if context['settings'].get('heap_model_view') != view.certificate:
        raise Refused('the recorded heap view differs from the checked original-source certificate')
    expected_flags = flags(context['tools'])
    expected = command(state['tool_command'], expected_flags, inputs, state['report_module'])
    if list(settings_flags) != expected_flags or list(command_line) != expected:
        raise Refused('the complete original-source heap proof command changed before launch')
    foundation = state['foundation']
    if context['settings'].get('heap_model_foundations') != foundation or \
            context['pins'].get('heap_model_foundations') != {
                'id': 'heap-model-standard-foundations-1', 'sha256': _digest(foundation['sources'])}:
        raise Refused('the recorded standard foundation binding changed after planning')
    if any(not Path(pin['path']).is_file() or _sha(Path(pin['path']).read_bytes()) != pin['sha256']
           for pin in foundation['sources']):
        raise Refused('a reviewed heap-proof foundation changed after planning')
    executable = Path(foundation['metadata_executable'])
    if _sha(executable.read_bytes()) != foundation['metadata_executable_sha256']:
        raise Refused('the linked Why3 metadata checker changed after planning')
    observed = _query([str(executable)], state['deadline']).decode().split('\0')
    if observed != [*foundation['why3_loadpath'], '']:
        raise Refused('the actual Why3 import load path changed after planning')
    config = state['why3_config']
    if _sha(Path(config['path']).read_bytes()) != config['sha256']:
        raise Refused('the selected Why3 configuration changed after planning')
    return view.pins['heap_model_view_certificate']['sha256']


def prove(job, adapter, context):
    """Fresh serial positive model obligations through the normal report reader."""
    import dataclasses
    from swdb import framac, proof_setup, rss_watchdog, wp_adapter

    log, root = context['log'], context['wp_dir']
    deadline = context['started_monotonic'] + (job.budget_seconds or wp_adapter.DEFAULT_WALL_SECONDS)
    context['goals'], context['unproven'] = [], []
    context['settings'] = {'tool': 'frama-c-wp', 'session': 'fresh', 'verifier_launched': False,
                           'machdep': 'x86_64', 'flags': flags(context['tools']),
                           'build_constants': list(adapter.defines), 'hint_count': len(adapter.hints),
                           'heap_model_runs': [], 'whole_public_budget_seconds':
                               job.budget_seconds or wp_adapter.DEFAULT_WALL_SECONDS}
    try:
        if adapter.defines or adapter.hints:
            raise Refused('build defines and source hints are unsupported for the exact original heap-model proof')
        inputs = root / 'heap-inputs'
        view = prepare(job.unit.function, inputs)
        cert_path = root / 'heap-model-view.json'
        cert_path.write_text(certificate_text(view))
        context['pins'].update(view.pins)
        context['settings']['heap_model_view'] = view.certificate
        context['reports'] += [('heap_model_original', inputs / (view.member + '.original.c')),
                               ('heap_model_certificate', cert_path),
                               ('heap_model_theory', inputs / 'theory/heap_bridge.mlw'),
                               ('heap_model_manifest', inputs / 'manifest.json')]
        context.setdefault('assumed', []).append({'kind': 'trusted_tool', 'reference': identity(),
            'sentence': 'The checked source-mapped unbounded typed heap VC translation preserves the exact '
                        'original model clauses, accesses, initialization, frame and allocation lifetime. '
                        'No original caller premise is added; generic caller composition remains unsupported.'})
        if view.member == MEMBERS[0]:
            context['assumed'].append({'kind': 'trusted_tool', 'reference': view.certificate['model'],
                'sentence': 'Allocation succeeds under the existing fresh-allocation/available-address/frame policy; '
                            'new typed cells are uninitialized until written.'})
        tool = framac.locate().command
        foundation = foundations(tool, root / 'heap-environment', deadline)
        context['settings']['heap_model_foundations'] = foundation
        context['pins']['heap_model_foundations'] = {'id': 'heap-model-standard-foundations-1',
                                                    'sha256': _digest(foundation['sources'])}
        context['assumed'].append({'kind': 'trusted_tool', 'reference': context['pins']['heap_model_foundations'],
            'sentence': 'The pinned Why3 Boolean/map/ordered-arithmetic/absolute-value/division and Frama-C '
                        'Qed/Cint arithmetic/conversion lemmas are trusted standard proof support; '
                        'no project desired-result lemma is imported as a hypothesis.'})
        reader_dir = root / 'heap-reader'
        reader_dir.mkdir()
        reader = proof_setup.compile_report_module(reader_dir, timeout=min(120, _remaining(deadline)))
        config = {'path': str(wp_adapter.why3_config().resolve()),
                  'sha256': _sha(wp_adapter.why3_config().read_bytes())}
        context['settings']['why3_config'] = config
        state = {'view': view, 'inputs': inputs, 'certificate_path': cert_path,
                 'foundation': foundation, 'report_module': reader, 'tool_command': tool,
                 'why3_config': config, 'deadline': deadline}
        context['heap_model_view'] = state
        cap = int(os.environ.get('SWDB_VERIFIER_RSS_CAP_BYTES') or wp_adapter.DEFAULT_CAP_BYTES)
        for index, row in enumerate(view.certificate['obligations']):
            _remaining(deadline)
            directory = root / ('heap-job-' + row['id'])
            directory.mkdir(exist_ok=False)
            text = (inputs / row['path']).read_text()
            input_path = directory / 'wp_input.c'
            input_path.write_text(text)
            (directory / 'tmp').mkdir()
            state['row'] = row
            invocation = command(tool, context['settings']['flags'], inputs, reader)
            proof_setup.check_generated(job, adapter, context,
                [(input_path, text), (cert_path, certificate_text(view))],
                context['settings']['flags'], command=invocation, scratch=directory)
            context['settings']['verifier_launched'] = True
            timeout = _remaining(deadline)
            log.line('heap command: ' + shlex.join(invocation) + '\ncwd: ' + str(directory) +
                     f'\nremaining whole budget: {timeout:.6f}s; RSS cap: {cap}')
            env = {**os.environ, 'TMPDIR': str(directory / 'tmp'),
                   'SWDB_PROOF_REPORT_OUT': str(directory / 'wp-inventory.json')}
            run = rss_watchdog.run(invocation, log=directory / 'frama-c.log', cwd=directory,
                                  env=env, cap_bytes=cap, timeout=timeout)
            context['settings']['heap_model_verifier_peak_rss_bytes'] = max(
                context['settings'].get('heap_model_verifier_peak_rss_bytes', 0), run.peak_rss_bytes)
            # Leave Verdict.peak_rss_bytes unset: the public worker watchdog
            # measures the entire job, including native metadata/reader builds.
            (directory / 'resources.json').write_text(json.dumps(dataclasses.asdict(run), indent=2) + '\n')
            outcome = wp_adapter.read_outcome(run, (directory / 'frama-c.log').read_text(errors='replace'),
                directory / 'wp-goals.json' if (directory / 'wp-goals.json').exists() else None,
                directory / 'wp-properties.csv' if (directory / 'wp-properties.csv').exists() else None,
                inventory=directory / 'wp-inventory.json')
            context['goals'] += outcome['goals']
            context['unproven'] += outcome['unproven']
            for path in sorted(directory.rglob('*')):
                if path.is_file():
                    name = 'heap_' + str(index) + '_' + str(path.relative_to(directory)).replace('/', '_')
                    context['reports'].append((name, path))
            if index == 0:
                context['reports'].append(('wp_input', input_path))
            receipt = {'id': row['id'], 'resources': dataclasses.asdict(run),
                       'command': invocation, 'cwd': str(directory), 'input_sha256': row['sha256'],
                       'verdict': outcome['verdict'], 'failure_class': outcome['failure_class'],
                       'reading': outcome.get('reading'), 'timeout_seconds': timeout}
            context['settings']['heap_model_runs'].append(receipt)
            log.line(f"heap model {row['id']}: {outcome['verdict']} ({outcome['why']})")
            if outcome['verdict'] != 'proven':
                context['verdict_reading'] = outcome.get('reading')
                return adapter._not_proven(outcome['failure_class'], outcome['why'], context)
            inventory = json.loads((directory / 'wp-inventory.json').read_text())
            ordinary = [g for g in outcome['goals'] if not g.get('smoke')]
            smoke = [g for g in outcome['goals'] if g.get('smoke')]
            if row['kind'] == 'check_lemma':
                lemmas = [p for p in inventory['properties'] if p.get('kind') == 'lemma']
                if len(lemmas) != 1 or lemmas[0].get('dependencies') or lemmas[0].get('extern') or \
                        not lemmas[0]['property'].endswith('_' + row['goal']) or \
                        any(g.get('property') != lemmas[0]['property'] for g in ordinary):
                    raise Refused('the fresh global proof is not owned by the sole source-mapped check lemma')
            elif row['kind'] != 'c_kernel' or not smoke:
                raise Refused('the numeric kernel must retain all ordinary and generated smoke obligations')
            if not ordinary:
                raise Refused('the source-mapped proof generated no ordinary obligation')
        _remaining(deadline)
        check(job.unit.function, view, inputs)
        context['verdict_reading'] = {'check': proof_setup.identity()['verdict_reading'],
                                     'verdict': 'proven'}
        return adapter._verdict('proven', None, context)
    except (TimeoutError, subprocess.TimeoutExpired):
        return adapter._not_proven('timeout', 'the whole public heap-model budget was spent', context)
    except Refused as exc:
        return adapter._not_proven('unsupported_construct', str(exc), context)


# Exact support sources independently inventoried in the full42 e56 capability.
FOUNDATION_HASHES = {'stdlib/algebra.mlw': '39d64b3f351a3a08a391d6d26467e427d9ad61799a0ea93ad9cf85d0acbc4fb4',
 'stdlib/bool.mlw': 'b7072fdd8dd5004d0627b82a66b054518ee54eb4dd66f0883988e363bed251fa',
 'stdlib/int.mlw': 'eb5bc9d4a46e1b6a298d24fd36dcf9dfb8f35cbc75b2f44007cfe1a24550ce8d',
 'stdlib/map.mlw': 'c4cd7b90e39f8407fd714d0e46ce4c6496a98afd32bd69c71237b35a4b7c08a0',
 'stdlib/real.mlw': '50940038bba54f6bd57501e5af6439af8c4f081274eb79a19d888a4cd419b8a2',
 'stdlib/relations.mlw': '0a367aecd2cd627de87d5f4011ddbf930bf49283e0b94b792a338faf921b2cae',
 'wp/cint.mlw': '34165df36963929dc7fc2d06e7609434fddc43924af5a9979e78d89b9c5b989e',
 'wp/qed.mlw': '54d50c3e40ea87b2bb0fd7195341c6c8bfc5ebcf300cb7b18752fae28e622efe'}
