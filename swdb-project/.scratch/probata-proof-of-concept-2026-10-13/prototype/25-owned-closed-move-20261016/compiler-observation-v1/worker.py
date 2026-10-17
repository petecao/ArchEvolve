"""2026-10-16 ET. Source observation only; no verifier or native user program."""
import argparse
import dataclasses
import hashlib
import json
import os
from pathlib import Path
import sys


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    raw = (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode()
    if len(raw) > 16*1024**2:
        raise ValueError('bounded complete compiler metadata exceeded')
    with path.open('xb') as stream:
        stream.write(raw); stream.flush(); os.fsync(stream.fileno())
    return {'path': str(path), 'bytes': len(raw), 'sha256': sha(raw)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--source', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--expected', required=True, type=Path)
    args = parser.parse_args()
    expected = json.loads(args.expected.read_bytes())
    if sha(args.source.read_bytes()) != expected['fixture']['sha256']:
        raise ValueError('exact external portable fixture differs')
    if os.environ.get('SWDB_FRAMA_C') != 'none' or os.environ.get('SWDB_CBMC') != 'none':
        raise ValueError('all verifier selectors must remain disabled')
    sys.dont_write_bytecode = True
    sys.path.insert(0, str(args.project))
    os.chdir(args.project)
    from swdb import c_lowering, stdlib_provenance
    runtime = stdlib_provenance.runtime_identity(c_lowering.locate())
    compiler = c_lowering.identity()
    if runtime != expected['linux_project_identity_derivation']['runtime'] or \
            compiler != expected['linux_project_identity_derivation']['predicted_identity']:
        raise ValueError('fresh original compiler/source context differs')
    save(args.output/'compiler-before.json', {'runtime': runtime, 'identity': compiler})
    lowering = c_lowering.lower(args.source, expected['function'])
    data = dataclasses.asdict(lowering)
    text = data.pop('text').encode()
    if lowering.function != expected['function'] or lowering.source_sha256 != expected['fixture']['sha256'] \
            or lowering.summaries or lowering.defines or len(text) > 1024**2:
        raise ValueError('complete original unsubstituted protocol lowering differs')
    with (args.output/'original-lowering.c').open('xb') as stream:
        stream.write(text); stream.flush(); os.fsync(stream.fileno())
    save(args.output/'lowering-metadata.json', data)
    save(args.output/'anchors.json', json.loads(lowering.anchors_json))
    # An additional filtered native parse retains the original function tree.
    # It does not alter the public lowering or install a wrapper around it.
    unit = c_lowering._Unit(c_lowering.locate(), args.source, (), (), None, None)
    node = unit.function_node(expected['function'], None, None, unit=True)
    save(args.output/'original-function-ast.json', node)
    save(args.output/'compiler-after.json', {
        'runtime': stdlib_provenance.runtime_identity(c_lowering.locate()),
        'identity': c_lowering.identity()})
    result = {'classification': 'COMPILER_SOURCE_OBSERVATION_ONLY',
        'function': lowering.function, 'source_sha256': lowering.source_sha256,
        'lowered_sha256': sha(text), 'models': list(lowering.models),
        'anchor_count': len(lowering.anchors),
        'original_source_and_lowering_mutated': False,
        'verifier_or_native_user_program_executed': False,
        'proof_record_created': False, 'source_or_member_or_caller_admitted': False,
        'raw_source_AST_C_stays_remote': True,
        'runtime_scope': 'Observed compiler identity at use; full retained library provenance accompanies the original lowering. Cached frontend identities and OS/loader/source-to-binary/between-check behavior remain explicit TCB.'}
    save(args.output/'observation.json', result)
    print(json.dumps(result, sort_keys=True))


if __name__ == '__main__':
    main()
