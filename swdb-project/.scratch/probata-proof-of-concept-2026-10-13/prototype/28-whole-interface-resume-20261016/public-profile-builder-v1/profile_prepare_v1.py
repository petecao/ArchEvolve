"""2026-10-16 ET. Inert no-child preparation entry; root admission required.

No verifier/compiler/version/network child can run inside this entry. Actual
public prove commands are emitted separately, never executed here.
"""
import argparse
import hashlib
import json
from pathlib import Path
import stat
import sys
import types

BUILDER_SHA = 'f594d5c23bef2bcda7a97c6a214601913425d7a24f2575985102eefe0b0391c2'


def deny_child(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'socket.connect', 'socket.bind'}:
        raise RuntimeError('compiler-free preparation forbids child/network event: ' + event)


def checked_builder():
    path = Path(__file__).resolve().with_name('profile_builder_v1.py')
    before = path.lstat()
    if not stat.S_ISREG(before.st_mode) or path.resolve(strict=True) != path:
        raise ValueError('canonical physical builder required')
    raw = path.read_bytes()
    fields = ('st_dev', 'st_ino', 'st_mode', 'st_nlink', 'st_uid', 'st_gid', 'st_size', 'st_mtime_ns', 'st_ctime_ns')
    if hashlib.sha256(raw).hexdigest() != BUILDER_SHA or any(getattr(before, name) != getattr(path.lstat(), name) for name in fields):
        raise ValueError('frozen builder changed')
    module = types.ModuleType('selected_profile_builder_v1'); module.__file__ = str(path)
    sys.modules[module.__name__] = module
    exec(compile(raw, str(path), 'exec'), module.__dict__)
    return module


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('phase', choices=('derive', 'globals', 'assemble'))
    parser.add_argument('--selection-pin', required=True, help='exact JSON physical pin, selected by root')
    parser.add_argument('--derived-pin')
    parser.add_argument('--context-pin')
    parser.add_argument('--receiver-pin')
    parser.add_argument('--output', required=True)
    args = parser.parse_args(argv)
    sys.dont_write_bytecode = True; sys.addaudithook(deny_child)
    builder = checked_builder()
    selection_pin = builder.parse(args.selection_pin)
    request = builder.parse(builder.read(selection_pin))
    if args.phase == 'derive':
        derived = builder.derive(request)
        files = {'profile-derivation.json': builder.canonical(derived),
            'source-atlas.json': builder.canonical(derived['atlas']), 'model-assembly.json': builder.canonical(derived['assembly']),
            'statement-preparation.json': builder.canonical(derived['statements']),
            'derived-abi-summary.json': builder.canonical(derived['abi']),
            'context-request.json': builder.canonical(derived['context_request'])}
    else:
        if not args.derived_pin or not args.context_pin:
            raise ValueError('exact derived/context pins are required')
        derived = builder.parse(builder.read(builder.parse(args.derived_pin)))
        context = builder.parse(args.context_pin)
        if args.phase == 'globals':
            files = {'source-globals.json': builder.canonical(builder.bind_globals(request, derived, context))}
        else:
            if not args.receiver_pin:
                raise ValueError('root-selected exact receiver policy pin required')
            prepared = builder.assemble(request, derived, context_receipt=context,
                receiver_policy=builder.parse(args.receiver_pin))
            files = prepared.pop('files')
            files['profile-preparation-receipt.json'] = builder.canonical(prepared)
    rows = builder.write_new_files(Path(args.output), files)
    builder.read(selection_pin)
    print(json.dumps({'schema': 'dx100-profile-preparation-output-1', 'phase': args.phase,
        'files': rows, 'scientific_tools_executed': False, 'proof_result': 'pending'}, sort_keys=True))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
