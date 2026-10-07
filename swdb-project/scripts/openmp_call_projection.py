"""Read-only exact-source OpenMP call ABI projection. Updated: 2026-10-06 ET.

No application is linked/run. Raw IR remains on its host. This independent static
proof does not rewrite or certify the supplied characterization's runtime counts.
"""
import argparse
import json
from pathlib import Path
import shlex
import subprocess
import sys

from swdb import access, artifacts


class Refusal(ValueError):
    pass


def run(argv, timeout):
    try:
        result = subprocess.run([str(x) for x in argv], capture_output=True, text=True, timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as error:
        raise Refusal(str(error)) from None
    if result.returncode:
        raise Refusal(result.stderr[-4000:] or 'projection subprocess failed')
    return result


def file_hash(path):
    return artifacts.file_hash(path)


def selection(record, mapping):
    source_calls = mapping.get('unmodeled_calls')
    if not isinstance(source_calls, list):
        raise Refusal('source.json has no call-site map')
    selected = {}
    groups = record.get('trials') or [{'position': None, 'unmodeled_calls': record.get('unmodeled_calls')}]
    if not isinstance(groups, list):
        raise Refusal('trial call observations missing or invalid')
    for group in groups:
        if not isinstance(group, dict) or not isinstance(group.get('unmodeled_calls'), list):
            raise Refusal('trial call observations missing or invalid')
        for call in group['unmodeled_calls']:
            if not isinstance(call, dict):
                raise Refusal('trial call observations missing or invalid')
            name = call.get('name')
            if not isinstance(name, str) or not name.startswith('__kmpc_'):
                continue
            count = call.get('execution_count', {}).get('value')
            if type(count) is not int or count < 0:
                raise Refusal('OpenMP execution count is unknown or invalid')
            site = call.get('site')
            if type(site) is not int or not 0 <= site < len(source_calls):
                raise Refusal('OpenMP call site absent from source.json')
            source = source_calls[site]
            if not isinstance(source, dict):
                raise Refusal('source.json call-site map is invalid')
            if any(call.get(key) != source.get(key) for key in ('site', 'name', 'region', 'line')):
                raise Refusal('characterization/source.json OpenMP site mismatch')
            if count:
                positions = selected.setdefault(site, [])
                if group.get('position') is not None:
                    positions.append(group['position'])
    return selected


def project(args):
    record = access.read_record(args.characterization)
    if not isinstance(record, dict) or record.get('kind') != 'workload_characterization' or not record.get('id'):
        raise Refusal('a workload_characterization record is required')
    coverage = record.get('coverage', {})
    counted_function = coverage.get('function')
    if args.function != counted_function or (args.function and coverage.get('scope') != 'function'):
        raise Refusal('function selection differs from characterization coverage.function')
    expected = record.get('static_analysis', {}).get('source_ir_sha256')
    before = {'ir': file_hash(args.source_ir), 'map': file_hash(args.source_map),
              'record': access.record_hash(args.characterization)}
    if expected != before['ir']:
        raise Refusal('source_ir_sha256 mismatch')
    receipt = record.get('binding', {}).get('execution_receipt')
    if record.get('evidence_kind') != 'contract_fixture' and not isinstance(receipt, dict):
        raise Refusal('application characterization needs its execution receipt')
    if isinstance(receipt, dict) and receipt.get('source_ir_sha256') != before['ir']:
        raise Refusal('execution receipt source_ir_sha256 mismatch')
    mapping = access.read_record(args.source_map)
    selected = selection(record, mapping)
    output = args.output_directory.resolve()
    if output.exists():
        raise Refusal('output-directory must be new')
    source = Path(__file__).resolve().parents[1] / 'swdb/llvm/OpenMPCallProjection.cpp'
    llvm = args.llvm_bin.resolve()
    version = run([llvm / 'llvm-config', '--version'], args.timeout_s).stdout.strip()
    if not version.startswith('22.'):
        raise Refusal('LLVM22 is required')
    flags = shlex.split(run([llvm / 'llvm-config', '--cxxflags', '--ldflags', '--system-libs',
                            '--libs', 'core', 'irreader', 'analysis', 'support'], args.timeout_s).stdout)
    output.mkdir(parents=True)
    binary = output / 'openmp-projector'
    compiler = llvm / 'clang++'
    compiler_version = run([compiler, '--version'], args.timeout_s).stdout.strip()
    compile_argv = [compiler, *args.toolchain_flag, source, *flags, '-std=c++17', '-O2', '-o', binary]
    run(compile_argv, args.timeout_s)
    raw_output = output / 'static.json'
    projection_argv = [binary, args.source_ir.resolve(), args.source_map.resolve(), raw_output,
                       ','.join(map(str, sorted(selected))), expected]
    if args.function:
        projection_argv.append(args.function)
    run(projection_argv, args.timeout_s)
    proof = access.read_record(raw_output)
    after = {'ir': file_hash(args.source_ir), 'map': file_hash(args.source_map),
             'record': access.record_hash(args.characterization)}
    if before != after:
        raise Refusal('projection input changed during reading')
    for call in proof['calls']:
        call['execution_trial_positions'] = selected[call['site']]
    proof.update({'format': 'swdb.openmp-call-projection.v1', 'updated': '2026-10-06 ET',
        'basis': 'code_reading',
        'scope': 'Exact-source static ABI facts for the all-trial executed-site union; no addresses, runtime internals, prewarm/residency state, timings or costs.',
        'characterization': {'id': record['id'], 'identity_sha256': record.get('identity_sha256'),
                             'sha256': artifacts.digest(record), 'file_sha256': before['record'],
                             'execution_receipt_source_ir_sha256': receipt.get('source_ir_sha256') if receipt else None},
        'receipt': {'llvm_version': version, 'compiler_version': compiler_version,
            'compiler_sha256': file_hash(compiler), 'wrapper_argv': [sys.executable, *sys.argv],
            'compiler_argv': list(map(str, compile_argv)), 'projection_argv': list(map(str, projection_argv)),
            'projector_source_sha256': file_hash(source), 'projector_binary_sha256': file_hash(binary),
            'wrapper_sha256': file_hash(Path(__file__)),
            'inputs_byte_identical_after_projection': True,
            'application_execution': False, 'raw_ir_exported': False,
            'characterization_runtime_validation': 'Required separately before model admission; this proof adds only static ABI facts.'}})
    if args.function:
        proof['function_selection'] = {'scope': 'function', 'function': args.function,
            'matching': 'Characterize debug owner name or exact LLVM symbol; outlined owner follows its source parent.'}
    proof['identity_sha256'] = artifacts.digest(proof)
    (output / 'projection.json').write_text(json.dumps(proof, indent=2) + '\n')
    return proof


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--characterization', type=Path, required=True, help='immutable YAML/JSON characterization file')
    parser.add_argument('--source-ir', type=Path, required=True, help='host-local normalized.bc; never exported')
    parser.add_argument('--source-map', type=Path, required=True, help='matching host-local source.json')
    parser.add_argument('--function', help='exact debug owner name or LLVM symbol; must equal persisted coverage.function')
    parser.add_argument('--llvm-bin', type=Path, required=True)
    parser.add_argument('--output-directory', type=Path, required=True, help='new host-local helper/projection folder')
    parser.add_argument('--toolchain-flag', action='append', default=[])
    parser.add_argument('--timeout-s', type=float, default=600)
    args = parser.parse_args()
    try:
        if not 0 < args.timeout_s <= 3600:
            raise Refusal('timeout-s must be positive and at most 3600')
        proof = project(args)
    except (Refusal, OSError, ValueError, TypeError, KeyError) as error:
        print('openmp-projection: ' + str(error), file=sys.stderr)
        return 2
    print(json.dumps(proof, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
