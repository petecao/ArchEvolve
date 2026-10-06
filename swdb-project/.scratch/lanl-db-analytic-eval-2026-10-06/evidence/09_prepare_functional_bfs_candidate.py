#!/usr/bin/env python3
"""Prepare a fresh canonical BFS read-offload candidate, without executing it.

Created: 2026-10-06 ET. Parent-owned remote construction recipe for ticket09.
Uses public add/fixture-package/submit command dispatch and current typed-library gates.
Raw source artifacts and command transcripts stay in the external runs directory.
"""
from __future__ import annotations

import argparse
import contextlib
import copy
import io
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = next(p for p in Path(__file__).resolve().parents if (p / 'swdb/cli.py').is_file())
sys.path.insert(0, str(ROOT))
from swdb import artifacts, certification, certification_procedures as procedures, cli, workflow, validate, archevolve
from swdb.library import Library, default_root, proposal_gate
from swdb.profile_package import verify as verify_package
from swdb.store import Store


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records', type=Path, required=True)
    parser.add_argument('--runs-dir', type=Path, required=True)
    parser.add_argument('--prefix', required=True, help='new immutable IDs; use a new prefix on retries')
    parser.add_argument('--pins', type=Path, default=Path(__file__).with_name('09-functional-bfs-source-pins.json'))
    args = parser.parse_args()
    require(re.fullmatch(r'[a-z0-9][a-z0-9._-]*', args.prefix), 'invalid record prefix')
    require(workflow.CREATION_TAGS.get('mode') != 'extensa', 'source-only preparation requires a fresh team process')
    pins = json.loads(args.pins.read_text())
    records = args.records.resolve()
    validation = validate.validate_records(records)
    store = validation.store
    issues = validation.problems
    require(not issues, 'invalid input record store: ' + '; '.join(str(x) for x in issues[:3]))
    source = store.get(pins['canonical_source']['id'], 'source_snapshot')
    require(source is not None, 'canonical scalar source record is missing')
    require(artifacts.digest(source) == pins['canonical_source']['record_sha256'], 'canonical source record pin changed')
    require(source['artifact']['sha256'] == pins['canonical_source']['artifact_sha256'], 'scalar artifact pin changed')
    require(artifacts.digest(source['protections']) == pins['canonical_source']['protections_sha256'], 'protection pin changed')
    require(default_root(records).resolve() == (ROOT / 'library').resolve(),
            'records must use this checkout library (copied stores need a sibling library symlink)')
    library = Library(ROOT / 'library', store)
    require(not library.validate(), 'invalid current typed library')
    require(artifacts.file_hash(ROOT / 'library/dx100/bfs_read_offload.inc') == pins['read_offload_body_sha256'],
            'canonical read-offload body pin changed')
    require(artifacts.file_hash(ROOT / 'library/dx100/dxc_lowering.hpp') == pins['library']['shipped_files'][0]['sha256'],
            'canonical lowering header pin changed')
    proc = procedures.procedure(procedures.CANDIDATE)
    require(proc.version == pins['certification']['version'] == '1.6', 'current strict candidate default must be 1.6')
    require(procedures.manifest(proc, ROOT / 'library')['sources_sha256'] == proc.sources_sha256 ==
            pins['certification']['sources_sha256'], 'strict certification source declaration changed')
    source_id, package_id, proposal_id = (args.prefix + suffix for suffix in ('.source', '.fixture-profile', '.proposal'))
    for rid in (source_id, package_id, proposal_id, proposal_id + '.candidate-1'):
        require(store.get(rid) is None, 'record ID already exists: ' + rid)
    # Gate normative entries before creating any fresh record or raw folder.
    gate = {'message_version': '1.1', 'library': pins['library'],
            'constraints': {'editable_files': [certification.BFS, certification.HEADER]}}
    proposal_gate(gate, store)
    before = artifacts.file_hash(ROOT / 'apps/dx100/benchmarks/gapbs/src/bfs.cc')
    output = artifacts.external_directory(args.runs_dir) / args.prefix
    output.mkdir(exist_ok=False)
    command_receipts = []
    database = output / 'index.sqlite'

    def public(command, *arguments, json_output=False):
        argv = [command, *(str(x) for x in arguments), '--records', str(records), '--db', str(database)]
        if command in archevolve.EVIDENCE_COMMANDS:
            argv += ['--mode', 'archevolve']
        if json_output:
            argv += ['--format', 'json']
        stdout, stderr = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
            try:
                code = cli.main(argv)
            except SystemExit as exc:
                code = int(exc.code or 0)
        index = len(command_receipts) + 1
        out, err = output / f'{index}-{command}.stdout.txt', output / f'{index}-{command}.stderr.txt'
        out.write_text(stdout.getvalue()); err.write_text(stderr.getvalue())
        command_receipts.append({'argv': argv, 'returncode': code,
                                 'stdout_sha256': artifacts.file_hash(out), 'stderr_sha256': artifacts.file_hash(err)})
        require(code == 0, f'public {command} failed: {stderr.getvalue().strip()}; see {output}')
        return json.loads(stdout.getvalue()) if json_output else None

    tree, original = certification.materialize_snapshot(store, source['id'], output / 'reconstructed')
    identity = artifacts.identify(tree)
    require(identity['sha256'] == pins['canonical_source']['artifact_sha256'], 'reconstructed scalar artifact differs')
    require(artifacts.file_hash(tree / certification.BFS) == pins['canonical_source']['bfs_sha256'], 'scalar BFS pin changed')
    artifacts.check_protections(tree, source['protections'])
    producer = {'name': 'swdb-canonical-read-offload-preparation', 'role': 'operator', 'test_client': False}
    context = copy.deepcopy(source['context'])
    # Fresh retained source identity carries no inherited correctness outcomes.
    context['verification'] = {'status': 'unchecked', 'scope': 'Source-only reconstruction; fresh candidate certification pending.'}
    fresh = workflow.record('source_snapshot', source_id, producer=producer,
                            **{key: copy.deepcopy(source[key]) for key in ('implementation', 'application', 'revision', 'regions', 'protections')},
                            artifact=identity, context=context)
    source_file = output / 'source-record.json'
    write_json(source_file, fresh)
    public('add', source_file, '--agent', '--agent-name', producer['name'])
    package = public('fixture-package', source_id, '--id', package_id, json_output=True)
    verify_package(package)
    require(package['completeness'] == 'fixture' and package['evidence']['classification'] == 'contract_fixture',
            'source-only profile must remain a contract fixture')
    patch_file = output / 'read-offload.patch'
    patch_info = certification.create_peter_patch(Store(records), patch_file, library=ROOT / 'library', temporary_root=output)
    require(patch_info['header_sha256'] == pins['library']['shipped_files'][0]['sha256'], 'generated header differs')
    request = {'message_version': '1.1', 'id': proposal_id, 'producer': producer,
               'source_snapshot': source_id, 'profile_package': package_id, 'implementation': fresh['implementation'],
               'source_sha256': identity['sha256'], 'regions': [r['id'] for r in package['regions']],
               'intent': 'Materialize the canonical typed-library BFS read-offload source for fresh strict functional certification; source-only evidence.',
               'constraints': {'editable_files': [certification.BFS, certification.HEADER],
                               'preserve_correctness': True, 'preserve_roi': True},
               'library': copy.deepcopy(pins['library']), 'payload': {'kind': 'patch', 'content': patch_file.read_text()}}
    request_file = output / 'request.json'
    write_json(request_file, request)
    # Explicit profile/protection pins are verified at submission and retained in the receipt;
    # the v1.1 public request schema itself carries source/library pins and profile/source IDs.
    retained = Store(records)
    require(artifacts.digest(retained.get(package_id)) == artifacts.digest(package), 'fixture profile changed before submit')
    require(artifacts.digest(retained.get(source_id)['protections']) == pins['canonical_source']['protections_sha256'],
            'fresh source protections changed before submit')
    proposal_gate(request, retained)
    proposal = public('submit', request_file, '--runs-dir', output / 'candidate-artifacts', json_output=True)
    require(proposal['outcome']['state'] == 'candidate_created', 'submit did not create a candidate')
    retained = Store(records)
    candidate = retained.get(proposal['candidate'], 'candidate')
    require(candidate['state'] == 'unverified', 'source-only submit must not certify a candidate')
    require(candidate['producer'] == producer, 'candidate producer is not the fresh source preparer')
    candidate_tree = artifacts.verify(candidate['artifact'])
    artifacts.check_protections(candidate_tree, source['protections'])
    header = candidate_tree / certification.HEADER
    require(header.read_bytes() == (ROOT / 'library/dx100/dxc_lowering.hpp').read_bytes(), 'shipped header is not byte-identical')
    expected_bfs = certification.peter_source((tree / certification.BFS).read_text())
    require((candidate_tree / certification.BFS).read_text() == expected_bfs, 'candidate differs from canonical read-offload rewrite')
    require(artifacts.file_hash(ROOT / 'apps/dx100/benchmarks/gapbs/src/bfs.cc') == before, 'read-only upstream source changed')
    require(not validate.validate_records(records).problems, 'record validation failed after source-only submit')
    candidate_pin = artifacts.digest(candidate)
    cert_argv = [sys.executable, '-m', 'swdb', 'certify', pins['library']['contract']['id'], '--candidate', candidate['id'],
                 '--records', str(records), '--library', str(ROOT / 'library'), '--runs-dir', str(output / 'strict-certification'),
                 '--command-version', '1.6', '--tile-sizes', '16384,1024', '--threads', '4', '--sources', '0',
                 '--mode', 'archevolve', '--format', 'json']
    receipt = {'date': '2026-10-06 ET', 'state': 'unverified_source_candidate_created', 'execution_performed': False,
               'source_preparation_git_commit': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
               'pins_sha256': artifacts.file_hash(args.pins), 'canonical_source_sha256': identity['sha256'],
               'fresh_source': {'id': source_id, 'record_sha256': artifacts.digest(retained.get(source_id)),
                                'protections_sha256': artifacts.digest(source['protections'])},
               'profile': {'id': package_id, 'record_sha256': artifacts.digest(package), 'evidence_classification': 'contract_fixture'},
               'proposal': {'id': proposal_id, 'request_sha256': artifacts.digest(request), 'patch_sha256': artifacts.file_hash(patch_file)},
               'candidate': {'id': candidate['id'], 'record_sha256': candidate_pin, 'tree_sha256': candidate['artifact']['sha256'],
                             'bfs_sha256': artifacts.file_hash(candidate_tree / certification.BFS),
                             'header_sha256': artifacts.file_hash(header)},
               'library': pins['library'], 'strict_certification': {'state': 'pending_parent_execution',
                                                                  'matrix': pins['certification'], 'argv': cert_argv},
               'public_commands': command_receipts}
    write_json(output / 'source-preparation-receipt.json', receipt)
    print(json.dumps({'receipt': str(output / 'source-preparation-receipt.json'), 'candidate': candidate['id'],
                      'tree_sha256': candidate['artifact']['sha256'], 'execution_performed': False}, indent=2))


if __name__ == '__main__':
    main()
