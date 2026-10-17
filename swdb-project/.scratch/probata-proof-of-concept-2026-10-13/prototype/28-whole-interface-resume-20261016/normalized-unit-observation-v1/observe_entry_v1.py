"""2026-10-16 ET. Private no-child unit observation; root envelope required.

No compiler/native/verifier runs, model emission, ownership receipt or public
acceptance occurs. The fixed staged namespaces are an observer package, never
represented as the installed public SWDB producer.
"""
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import types

MANIFEST_SHA = 'c03688336db98b8008f557e16fdf6adf589505b5aef2c795bc3c2a63021e3c36'
MAX_CONTROL_BYTES = 1048576
MAX_OUTPUT_BYTES = 4194304
STABLE = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
MODULE_NAMES = ('swdb._dx100_whole.whole_interface_v4', 'swdb._dx100_whole.compiler_unit_adapter_v3',
    'swdb._dx100_whole.receiver_state_draws_v2', 'swdb.dx100_whole_checked', 'swdb.dx100_checked_source',
    'swdb._dx100_whole.lossless_gzip_v2', 'swdb._dx100_whole.role_normalized_gzip_v2',
    'swdb._dx100_whole.closed_python_surface', 'swdb._dx100_whole.normalized_compiler_adapter_v1',
    'swdb._dx100_whole.normalized_capture_ingress_v2', 'swdb._dx100_whole.normalized_unit_observation_v1')


def need(condition, message):
    if not condition: raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()


def parse(raw):
    def pairs(rows):
        result = {}
        for key, value in rows:
            need(key not in result, 'duplicate observation metadata key')
            result[key] = value
        return result
    return json.loads(raw, object_pairs_hook=pairs,
        parse_constant=lambda _: (_ for _ in ()).throw(ValueError('nonfinite observation metadata')))


def fingerprint(value):
    return tuple(getattr(value, name) for name in STABLE)


def read_pin(row, *, limit=MAX_CONTROL_BYTES):
    need(type(row) is dict and set(row) == {'path', 'bytes', 'sha256'}, 'closed physical pin required')
    path = Path(row['path']); before = path.lstat()
    need(path.is_absolute() and path.resolve(strict=True) == path and stat.S_ISREG(before.st_mode)
         and type(row['bytes']) is int and 0 <= row['bytes'] <= limit
         and before.st_size == row['bytes'], 'bounded canonical physical input required')
    with path.open('rb') as handle: raw = handle.read(limit + 1)
    need(fingerprint(path.lstat()) == fingerprint(before) and len(raw) == row['bytes']
         and hashlib.sha256(raw).hexdigest() == row['sha256'], 'physical observation input changed')
    return raw


def no_child(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork', 'socket.')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('no child/native/network operation in private observation')


def controls(policy, control):
    rows = policy['controls']
    need(type(rows) is dict and rows and all(type(name) is str and name == Path(name).name for name in rows),
         'explicit basename control map required')
    total = 0; values = {}
    for name, row in rows.items():
        need(row['path'] == str(control / name), 'control must use its selected physical basename')
        values[name] = read_pin(row); total += len(values[name])
    need(total <= MAX_CONTROL_BYTES, 'bounded complete control packet required')
    need(hashlib.sha256(values['fixed-modules-v1.json']).hexdigest() == MANIFEST_SHA,
         'exact reviewed fixed-module manifest required')
    manifest = parse(values['fixed-modules-v1.json'])
    modules = manifest['modules']
    need(type(modules) is list and tuple(row['module'] for row in modules) == MODULE_NAMES,
         'exact closed staged module order required')
    for row in modules:
        raw = values[row['file']]
        need(len(raw) == row['bytes'] and hashlib.sha256(raw).hexdigest() == row['sha256'],
             'fixed module bytes differ from reviewed manifest')
    return values, modules


def install_fixed(values, modules, control, original_project):
    need(not any(name == 'swdb' or name.startswith('swdb.') for name in sys.modules),
         'observer cannot overlay an imported production package')
    package = types.ModuleType('swdb'); package.__path__ = []; sys.modules['swdb'] = package
    private = types.ModuleType('swdb._dx100_whole'); private.__path__ = []
    sys.modules[private.__name__] = private; package._dx100_whole = private
    paths = types.ModuleType('swdb.paths'); paths.HOME = original_project
    sys.modules[paths.__name__] = paths; package.paths = paths
    for row in modules:
        name = row['module']; path = control / row['file']
        module = types.ModuleType(name); module.__file__ = str(path); module.__package__ = name.rsplit('.', 1)[0]
        sys.modules[name] = module
        exec(compile(values[row['file']], str(path), 'exec'), module.__dict__)
        setattr(sys.modules[module.__package__], name.rsplit('.', 1)[1], module)
    return package, private


class LibraryRoot:
    def __init__(self, root, project): self.root, self.project = root, project

    def resolve(self, row):
        need(type(row) is dict and set(row) == {'root', 'path', 'sha256'}
             and row['root'] in ('library', 'project'), 'closed portable observation input required')
        relative = Path(row['path'])
        need(type(row['path']) is str and row['path'] and not relative.is_absolute()
             and row['path'] == relative.as_posix() and '..' not in relative.parts,
             'canonical relative observation input required')
        return (self.root if row['root'] == 'library' else self.project) / relative


def write_new(path, raw):
    need(len(raw) <= MAX_OUTPUT_BYTES, 'bounded observation output required')
    with path.open('xb') as handle:
        handle.write(raw); handle.flush(); os.fsync(handle.fileno())
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def error_frames(error):
    rows = []; trace = error.__traceback__
    while trace is not None:
        code = trace.tb_frame.f_code
        rows.append({'filename': code.co_filename, 'function': code.co_name, 'line': trace.tb_lineno})
        trace = trace.tb_next
    return {'type': type(error).__name__, 'frames': rows[-12:]}


def main(argv=None):
    argv = list(sys.argv[1:] if argv is None else argv)
    need(len(argv) == 2, 'usage: observe_entry_v1.py POLICY POLICY_SHA256')
    sys.dont_write_bytecode = True; sys.addaudithook(no_child)
    policy_path = Path(argv[0]); control = Path(__file__).parent
    need(policy_path.parent == control and control.resolve(strict=True) == control,
         'policy and entry must share their canonical physical control directory')
    policy_pin = {'path': str(policy_path), 'bytes': policy_path.lstat().st_size, 'sha256': argv[1]}
    policy = parse(read_pin(policy_pin))
    need(type(policy) is dict and set(policy) == {'schema', 'original_project', 'library_root', 'output_root',
         'proof_source', 'capture', 'controls', 'root_admission_receipt'}, 'closed observation selection required')
    need(policy['schema'] == 'root-selected-normalized-unit-observation-1', 'exact observation schema required')
    roots = [Path(policy[name]) for name in ('original_project', 'library_root', 'output_root')]
    need(all(path.is_absolute() and path.resolve(strict=True) == path and path.is_dir() for path in roots),
         'canonical root-created original/library/output directories required')
    project, library_root, output = roots
    need(output == control.parent and not output.is_relative_to(project)
         and not output.is_relative_to(library_root), 'observation outputs must be source/library disjoint')
    need(policy['proof_source'].get('sha256') == '3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd',
         'only the exact first-source observation is supported')
    need(policy['capture'].get('prepared') is None, 'preparation is explicitly unknown before this observation')
    values, modules = controls(policy, control)
    need(Path(__file__).name in policy['controls'], 'entry physical pin is required')
    need({path.name for path in control.iterdir()} == set(policy['controls']) | {policy_path.name},
         'complete exact physical control membership required')
    read_pin(policy['root_admission_receipt'])  # External provenance, never an authority boolean.
    reads = None; status = None
    try:
        package, private = install_fixed(values, modules, control, project)
        source = package.dx100_checked_source; reads = source.Inputs(LibraryRoot(library_root, project))
        original_policy = reads.document(policy['capture']['original']['policy'])
        need(original_policy['source_project'] == str(project), 'captured original project role differs')
        result = private.normalized_unit_observation_v1.observe_capture(policy, reads, project)
        path, original, _tu, declarations, prepared, transport = result
        need(prepared.get('public_admission') is False and prepared.get('schema') ==
             'whole-interface-normalized-original-tu-preparation-1', 'observation must retain its non-admitting schema')
        preparation = canonical(prepared); inputs = canonical([row.row() for row in reads.pins.values()])
        need(len(preparation) <= MAX_OUTPUT_BYTES and len(inputs) <= MAX_OUTPUT_BYTES,
             'complete preparation/read-set metadata must fit bounded outputs')
        reads.recheck(); controls(policy, control); read_pin(policy_pin); read_pin(policy['root_admission_receipt'])
        prepared_pin = write_new(output / 'whole-unit-preparation.json', preparation)
        inputs_pin = write_new(output / 'observed-input-pins.json', inputs)
        status = {'schema': 'private-normalized-unit-observation-result-1', 'observation_complete': True,
            'preparation': prepared_pin, 'input_pins': inputs_pin, 'source_sha256': hashlib.sha256(original).hexdigest(),
            'captured_source_path': str(path), 'declaration_count': len(declarations), 'source_call_count': len(prepared['calls']),
            'normalized_transport': prepared['normalized_transport'], 'transport_binding': transport,
            'observer_package_role': 'fixed private staged namespaces; not installed production',
            'compiler_native_solver_executed': False, 'owned_context_emitted': False, 'public_admission': False}
    except Exception as error:
        status = {'schema': 'private-normalized-unit-observation-result-1', 'observation_complete': False,
                  'error': error_frames(error), 'compiler_native_solver_executed': False,
                  'owned_context_emitted': False, 'public_admission': False}
    finally:
        after = []
        for check in ([reads.recheck] if reads is not None else []) + [lambda: controls(policy, control),
                    lambda: read_pin(policy_pin), lambda: read_pin(policy['root_admission_receipt'])]:
            try: check()
            except Exception as error: after.append(error_frames(error))
        if after:
            status['observation_complete'] = False; status['after_input_errors'] = after
        write_new(output / 'unit-observation-result.json', canonical(status))
    print(json.dumps(status, sort_keys=True, allow_nan=False))
    return 0 if status['observation_complete'] else 1


if __name__ == '__main__': raise SystemExit(main())
