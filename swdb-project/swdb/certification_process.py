"""Candidate certification with the record-keeping in a separate evaluator process (certify 1.5).

Created: 2026-10-05 ET (ticket 78). Scope decided by Yan-Ru 2026-10-05: an engineering refactor
that moves certification record-keeping out of the candidate's process, plus an overhead
measurement. OS sandboxing or confinement of the candidate process and adversarial tests are out
of scope (ticket 78).

Certify 1.4 (``swdb.certification_blinding``) linked the candidate object, the record writer
(``record.cc``) and the seams (``seams.cc``) into one binary, so the record descriptor, the run plan,
the fault logic, the frontier ledger and the strict model's state all lived in the candidate's
address space. Certify 1.5 splits the run into two processes:

- **evaluator** (trusted; ``library/dx100/certification/v1_5/evaluator.cc`` linked with the
  unchanged 1.4 ``record.cc`` and ``seams.cc`` and the unchanged strict layer). It holds the record
  descriptor and the run plan, the fault logic, the ledger, the strict model's state and the witness
  counters, and writes every record line from its own state.
- **candidate** (the candidate object linked with ``client.cc`` only). Its C++ heap is a shared
  arena mapped at one address in both processes, so the arrays the DX100 model reads and the
  parent array every claim updates are memory the evaluator reads and writes directly. Each seam call
  (the 1.4 prelude's, unchanged) and each strict-layer call is a request on the calling thread's slot.

The record format, the plan, the blinding, the random order, the judge, the attribution rules and
the scan are 1.4's, unchanged (``certification_blinding``): only the build and the run differ.
"""
from __future__ import annotations

import os
import secrets
from pathlib import Path

from swdb import artifacts
from swdb.cli import Failure

VERSION = '1.5'
FOLDER = 'dx100/certification/v1_5'
PRELUDE = FOLDER + '/prelude.hpp'
CLIENT_INCLUDE = FOLDER + '/client'
CONTEXT = FOLDER + '/evaluator_context.hpp'
EVALUATOR_SOURCES = (FOLDER + '/evaluator.cc', 'dx100/certification/v1_4/record.cc', 'dx100/certification/v1_4/seams.cc')
CLIENT_SOURCE = FOLDER + '/client.cc'


def _client_flags(flags, library):
    """The candidate's compile flags with the client interface ahead of the strict layer.

    ``MAA_functional.hpp`` then resolves to the client interface; the strict folder's other
    certification headers (``gem5/m5ops.h``) still resolve as in 1.4."""
    strict = '-I' + str(library / 'dx100/strict')
    if strict not in flags:
        raise Failure('certification flags do not name the strict layer')
    index = flags.index(strict)
    return [*flags[:index], '-I' + str(library / CLIENT_INCLUDE), *flags[index:]]


class Build:
    """Objects and binaries of one candidate tree at one tile size (certify 1.5).

    ``link`` returns the candidate binary (candidate object + client object). ``evaluator`` (one per
    tile size) is linked from trusted sources only. The link record names both binaries' sha256.
    """

    def __init__(self, folder, library, tree, source_path, tile_size, threads):
        from swdb.certification import compiler
        from swdb.certification_isolation import _flags
        self.folder, self.library, self.tree = Path(folder), Path(library), Path(tree)
        self.source_path, self.tile_size, self.threads = Path(source_path), tile_size, threads
        self.folder.mkdir(parents=True, exist_ok=True)
        self.compiler = compiler()
        self.flags = _flags(self.library, self.tree, tile_size, threads)
        self.client_flags = _client_flags(self.flags, self.library)
        self._client = None
        self._evaluator = None

    def _compile(self, source, output, flags, extra=()):
        from swdb.certification import execute
        command = [self.compiler, *flags, *extra, '-c', str(source), '-o', str(output)]
        result = execute(command, Path(str(output) + '.build.json'), timeout=180)
        if result['returncode'] == 0:
            result['object_sha256'] = artifacts.file_hash(output)
        result['object'] = str(output)
        return result

    def candidate_object(self, text, label):
        self.source_path.write_text(text)
        extra = ['-Dmain=swdb_candidate_main', '-iquote', str(self.source_path.parent),
                 '-include', str(self.library / PRELUDE)]
        result = self._compile(self.source_path, self.folder / f'candidate-{label}.o', self.client_flags, extra)
        result['source_sha256'] = artifacts.digest(text)
        return result

    def client_object(self):
        if self._client is None:
            flags = [f for f in self.client_flags if f != '-std=c++11'] + ['-std=c++17']
            result = self._compile(self.library / CLIENT_SOURCE, self.folder / 'client-v15.o', flags,
                                   ['-I' + str(self.library / FOLDER)])
            if result['returncode']:
                raise Failure('trusted certification client failed to build; see ' + result['log'])
            self._client = result
        return self._client

    def evaluator(self):
        """The evaluator binary: evaluator.cc + 1.4 record.cc + 1.4 seams.cc, strict layer."""
        from swdb.certification import execute
        if self._evaluator is None:
            flags = [f for f in self.flags if f != '-std=c++11'] + ['-std=c++17']
            extra = ['-I' + str(self.library / FOLDER), '-include', str(self.library / CONTEXT)]
            objects = []
            for source in EVALUATOR_SOURCES:
                result = self._compile(self.library / source, self.folder / (Path(source).stem + '-evaluator-v15.o'), flags, extra)
                if result['returncode']:
                    raise Failure('trusted certification evaluator failed to build; see ' + result['log'])
                objects.append(result)
            output = self.folder / 'swdb-evaluator'
            link = execute([self.compiler, '-fopenmp', *[o['object'] for o in objects], '-o', str(output)],
                           Path(str(output) + '.link.json'), timeout=180)
            if link['returncode']:
                raise Failure('trusted certification evaluator failed to link; see ' + link['log'])
            self._evaluator = {'binary': str(output), 'sha256': artifacts.file_hash(output),
                               'objects': {Path(s).name: o['object_sha256'] for s, o in zip(EVALUATOR_SOURCES, objects)}}
        return self._evaluator

    def link(self, candidate, output):
        from swdb.certification import execute
        client, evaluator = self.client_object(), self.evaluator()
        command = [self.compiler, '-fopenmp', candidate['object'], client['object'], '-o', str(output)]
        result = execute(command, Path(str(output) + '.link.json'), timeout=180)
        result.update(candidate_object_sha256=candidate.get('object_sha256'),
                      record_object_sha256=evaluator['objects']['record.cc'],
                      seam_object_sha256=evaluator['objects']['seams.cc'],
                      client_object_sha256=client['object_sha256'],
                      evaluator=evaluator['binary'], evaluator_sha256=evaluator['sha256'],
                      process_split=True,
                      binary=str(output), binary_sha256=artifacts.file_hash(output) if result['returncode'] == 0 else None)
        return result


def run(link, graph, source, log, threads, fault=None):
    """One run: the evaluator gets the record descriptor and the plan pipe and starts the candidate
    binary as its child (only the shared arena is passed on); stdout and stderr are only logged."""
    from swdb.certification import execute
    from swdb.certification_blinding import CHANNEL_ENV, PLAN_ENV, plan_line
    record = Path(str(log) + '.record')
    nonce = secrets.token_hex(16)
    descriptor = os.open(record, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    plan_read, plan_write = os.pipe()
    try:
        os.write(plan_write, plan_line(fault, nonce))
        os.close(plan_write)
        plan_write = None
        result = execute([link['evaluator'], link['binary'], '-f', graph, '-r', source, '-n', '1', '-v'], log,
                         threads=threads, extra_env={CHANNEL_ENV: str(descriptor), PLAN_ENV: str(plan_read)},
                         pass_fds=(descriptor, plan_read))
    finally:
        os.close(descriptor)
        os.close(plan_read)
        if plan_write is not None:
            os.close(plan_write)
    result.update(record=str(record.resolve()), record_sha256=artifacts.file_hash(record),
                  plan={'fault': fault, 'nonce': nonce}, evaluator_sha256=link['evaluator_sha256'])
    return result


def run_one(job, log, threads):
    return run(job['link'], job['graph'], job['vertex'], log, threads, fault=job['fault'])


def certify_candidate(tree, library, folder, tile_sizes, threads, sources, *, threshold=64, plugin, contract=None,
                      rng=None):
    """Certify one candidate tree with certify 1.5: 1.4's procedure and judge, the 1.5 process split."""
    from swdb import certification_blinding as blinding
    return blinding.certify_candidate(tree, library, folder, tile_sizes, threads, sources, threshold=threshold,
                                      plugin=plugin, contract=contract, rng=rng, build_class=Build, runner=run_one,
                                      driver_attribute='certification_driver_v15', build_suffix='v15')


# --- native-CPU contracts (ticket 75's path) under 1.5 -------------------------------------------------

NATIVE_FOLDER = 'native/certification/v1_5'
NATIVE_EVALUATOR = NATIVE_FOLDER + '/evaluator.cc'
NATIVE_CLIENT = NATIVE_FOLDER + '/client.cc'
NATIVE_DRIVER = 'dx100/certification/v1_5/bfs_driver.inc'


def _native_build_class(library):
    from swdb.certification_native import NativeBuild

    class NativeProcessBuild(NativeBuild):
        """A native build under 1.5: the candidate object with the unchanged native 1.4 prelude, linked
        with the native client only; the evaluator from native 1.4 record.cc and seams.cc."""

        def _std17(self):
            return [f for f in self.flags if not f.startswith('-std=')] + ['-std=c++17']

        def _trusted_compile(self, source, output, extra):
            from swdb.certification import execute
            command = [self.compiler, *self._std17(), *extra, '-c', str(source), '-o', str(output)]
            result = execute(command, Path(str(output) + '.build.json'), timeout=180)
            if result['returncode']:
                raise Failure('trusted native certification process object failed to build; see ' + result['log'])
            result['object'] = str(output)
            result['object_sha256'] = artifacts.file_hash(output)
            return result

        def process_objects(self):
            from swdb.certification import execute
            if 'process' not in self._trusted:
                context = ['-include', str(library / CONTEXT), '-I' + str(library / FOLDER)]
                objects = {
                    'evaluator.cc': self._trusted_compile(library / NATIVE_EVALUATOR, self.folder / 'evaluator-v15.o', context),
                    'record.cc': self._trusted_compile(self.harness['record'], self.folder / 'record-evaluator-v15.o', context),
                    'seams.cc': self._trusted_compile(self.harness['seams'], self.folder / 'seams-evaluator-v15.o',
                                                      context + [f'-DSWDB_NATIVE_FAULT_BATCH={self.fault_batch}']),
                }
                output = self.folder / 'swdb-evaluator'
                link = execute([self.compiler, '-fopenmp', '-pthread', *[o['object'] for o in objects.values()],
                                '-o', str(output)], Path(str(output) + '.link.json'), timeout=180)
                if link['returncode']:
                    raise Failure('trusted native certification evaluator failed to link; see ' + link['log'])
                client = self._trusted_compile(library / NATIVE_CLIENT, self.folder / 'client-v15.o',
                                               ['-I' + str(library / FOLDER)])
                self._trusted['process'] = {'evaluator': str(output), 'evaluator_sha256': artifacts.file_hash(output),
                                            'objects': {k: v['object_sha256'] for k, v in objects.items()},
                                            'client': client}
            return self._trusted['process']

        def link(self, candidate, fault, output):
            from swdb.certification import execute
            process = self.process_objects()
            command = [self.compiler, '-fopenmp', '-pthread', candidate['object'], process['client']['object'],
                       '-o', str(output)]
            result = execute(command, Path(str(output) + '.link.json'), timeout=180)
            result.update(candidate_object_sha256=candidate.get('object_sha256'),
                          record_object_sha256=process['objects']['record.cc'],
                          seam_object_sha256=process['objects']['seams.cc'],
                          client_object_sha256=process['client']['object_sha256'],
                          evaluator=process['evaluator'], evaluator_sha256=process['evaluator_sha256'],
                          process_split=True, fault_macro=fault, binary=str(output))
            return result

    return NativeProcessBuild


def _native_run(link, output, graph, vertex, log, threads, fault):
    """One native 1.5 run (the native plan line; the evaluator starts the candidate)."""
    from swdb.certification import execute
    from swdb.certification_blinding import CHANNEL_ENV, PLAN_ENV
    from swdb.certification_native import _plan_line
    nonce = secrets.token_hex(16)
    record = Path(log).parent / f'run-{nonce}.record'   # as ticket 75's native 1.4 runs
    descriptor = os.open(record, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    plan_read, plan_write = os.pipe()
    try:
        os.write(plan_write, _plan_line(fault, nonce))
        os.close(plan_write)
        plan_write = None
        result = execute([link['evaluator'], output, '-f', graph, '-r', vertex, '-n', '1', '-v'], log,
                         threads=threads, extra_env={CHANNEL_ENV: str(descriptor), PLAN_ENV: str(plan_read)},
                         pass_fds=(descriptor, plan_read))
    finally:
        os.close(descriptor)
        os.close(plan_read)
        if plan_write is not None:
            os.close(plan_write)
    result.update(record=str(record.resolve()), record_sha256=artifacts.file_hash(record),
                  plan={'fault': fault, 'nonce': nonce}, evaluator_sha256=link['evaluator_sha256'])
    return result


def certify_native(tree, library, folder, profile, plugin, *, rng=None):
    """A native-CPU contract under certify 1.5: the native 1.4 procedure, judge and attribution
    (``certification_native.certify_native_v14``) with the 1.5 process split. The profile's pinned 1.4
    prelude, record writer and seams are used unchanged; the client, the evaluator and the 1.5 driver
    are pinned by the command's sources_sha256 (the profile is not edited)."""
    from swdb import certification_native as native
    return native.certify_native_v14(tree, library, folder, profile, plugin, rng=rng,
                                     build_class=_native_build_class(Path(library)), runner=_native_run,
                                     driver=Path(library) / NATIVE_DRIVER, suffix='v15')
