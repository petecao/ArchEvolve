"""Candidate certification with the record-keeping in a separate evaluator process (certify 1.5, 1.6).

Created: 2026-10-05 ET (ticket 78). Scope decided by Yan-Ru 2026-10-05: an engineering refactor
that moves certification record-keeping out of the candidate's process, plus an overhead
measurement. OS sandboxing or confinement of the candidate process and adversarial tests are out
of scope (ticket 78).

Certify 1.4 (``swdb.certification_blinding``) linked the candidate object, the record writer
(``record.cc``) and the seams (``seams.cc``) into one binary, so the record descriptor, the run plan,
the fault logic, the seam-witness events and the strict model's state all lived in the candidate's
address space. Certify 1.5 splits the run into two processes:

- **evaluator** (trusted; ``library/dx100/certification/v1_5/evaluator.cc`` linked with the
  unchanged 1.4 ``record.cc`` and ``seams.cc`` and the unchanged strict layer). It holds the record
  descriptor and the run plan, the fault logic, the seam-witness events, the strict model's state and
  the witness counters, and writes every record line from its own state.
- **candidate** (the candidate object linked with ``client.cc`` only). Its C++ heap is a shared
  arena mapped at one address in both processes, so the arrays the DX100 model reads and the
  parent array every claim updates are memory the evaluator reads and writes directly. Each seam call
  (the 1.4 prelude's, unchanged) and each strict-layer call is a request on the calling thread's slot.

The record format, the plan, the blinding, the random order, the judge, the attribution rules and
the scan are 1.4's, unchanged (``certification_blinding``): only the build and the run differ.

Updated: 2026-10-05 ET (code-review fixes C4, C24, F3, F5): certify 1.6 is this module with the
version table's legality rules v2 (``swdb.certification_legality``); builds and runs share
``swdb.certification_common``. The 1.5 behavior is unchanged.
"""
from __future__ import annotations

import re
import secrets
from pathlib import Path

from swdb import artifacts
from swdb import certification_common as common
from swdb.cli import Failure

FOLDER = 'dx100/certification/v1_5'
PRELUDE = FOLDER + '/prelude.hpp'
CLIENT_INCLUDE = FOLDER + '/client'
CONTEXT = FOLDER + '/evaluator_context.hpp'
EVALUATOR_SOURCES = (FOLDER + '/evaluator.cc', 'dx100/certification/v1_4/record.cc', 'dx100/certification/v1_4/seams.cc')
CLIENT_SOURCE = FOLDER + '/client.cc'
record_path = common.record_path


def _client_flags(flags, library):
    """The candidate's compile flags with the client interface ahead of the strict layer.

    ``MAA_functional.hpp`` then resolves to the client interface; the strict folder's other
    certification headers (``gem5/m5ops.h``) still resolve as in 1.4."""
    strict = '-I' + str(library / 'dx100/strict')
    if strict not in flags:
        raise Failure('certification flags do not name the strict layer')
    index = flags.index(strict)
    return [*flags[:index], '-I' + str(library / CLIENT_INCLUDE), *flags[index:]]


def _std17(flags):
    return [f for f in flags if f != '-std=c++11'] + ['-std=c++17']


class Build(common.ObjectBuild):
    """Objects and binaries of one candidate tree at one tile size (certify 1.5 and later).

    ``link`` returns the candidate binary (candidate object + client object). ``evaluator`` (one per
    tile size) is linked from trusted sources only. The link record names both binaries' sha256.
    """

    def __init__(self, folder, library, tree, source_path, tile_size, threads):
        from swdb.certification_isolation import _flags
        self.library, self.tree = Path(library), Path(tree)
        self.source_path, self.tile_size, self.threads = Path(source_path), tile_size, threads
        super().__init__(folder, _flags(self.library, self.tree, tile_size, threads))
        self.client_flags = _client_flags(self.flags, self.library)
        self._client = None
        self._evaluator = None

    def candidate_object(self, text, label):
        return self.compile_candidate(self.source_path, text, label, prelude=self.library / PRELUDE,
                                      flags=self.client_flags)

    def client_object(self):
        if self._client is None:
            result = self.compile(self.library / CLIENT_SOURCE, self.folder / 'client-v15.o',
                                  _std17(self.client_flags), ['-I' + str(self.library / FOLDER)])
            if result['returncode']:
                raise Failure('trusted certification client failed to build; see ' + result['log'])
            self._client = result
        return self._client

    def evaluator(self):
        """The evaluator binary: evaluator.cc + 1.4 record.cc + 1.4 seams.cc, strict layer."""
        if self._evaluator is None:
            extra = ['-I' + str(self.library / FOLDER), '-include', str(self.library / CONTEXT)]
            objects = []
            for source in EVALUATOR_SOURCES:
                result = self.compile(self.library / source, self.folder / (Path(source).stem + '-evaluator-v15.o'),
                                      _std17(self.flags), extra)
                if result['returncode']:
                    raise Failure('trusted certification evaluator failed to build; see ' + result['log'])
                objects.append(result)
            output = self.folder / 'swdb-evaluator'
            link = self.link_objects([o['object'] for o in objects], output)
            if link['returncode']:
                raise Failure('trusted certification evaluator failed to link; see ' + link['log'])
            self._evaluator = {'binary': str(output), 'sha256': artifacts.file_hash(output),
                               'objects': {Path(s).name: o['object_sha256'] for s, o in zip(EVALUATOR_SOURCES, objects)}}
        return self._evaluator

    def link(self, candidate, output):
        client, evaluator = self.client_object(), self.evaluator()
        result = self.link_objects([candidate['object'], client['object']], output)
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
    from swdb.certification_blinding import plan_line
    nonce = secrets.token_hex(16)
    result = common.run_blinded([link['evaluator'], link['binary'], *common.graph_argv(graph, source)],
                                plan_line(fault, nonce), nonce, fault, log, threads)
    result['evaluator_sha256'] = link['evaluator_sha256']
    return result


def run_one(job, log, threads):
    return run(job['link'], job['graph'], job['vertex'], log, threads, fault=job['fault'])


def certify_candidate(tree, library, folder, tile_sizes, threads, sources, *, threshold=64, plugin, contract=None,
                      rng=None, procedure=None):
    """Certify one candidate tree with certify 1.5 or 1.6: 1.4's procedure and judge, the process split.

    ``procedure`` is the version table's entry (candidate 1.5 when omitted); it names the driver and
    the legality rules (1.6: legality v2)."""
    from swdb import certification_blinding as blinding
    from swdb import certification_procedures as procedures
    procedure = procedure or procedures.procedure(procedures.CANDIDATE, '1.5')
    return blinding.certify_candidate(tree, library, folder, tile_sizes, threads, sources, threshold=threshold,
                                      plugin=plugin, contract=contract, rng=rng, procedure=procedure,
                                      build_class=Build, runner=run_one, build_suffix='v15')


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
            result = self.compile(source, output, self._std17(), extra)
            if result['returncode']:
                raise Failure('trusted native certification process object failed to build; see ' + result['log'])
            return result

        def process_objects(self):
            if 'process' not in self._trusted:
                context = ['-include', str(library / CONTEXT), '-I' + str(library / FOLDER)]
                objects = {
                    'evaluator.cc': self._trusted_compile(library / NATIVE_EVALUATOR, self.folder / 'evaluator-v15.o', context),
                    'record.cc': self._trusted_compile(self.harness['record'], self.folder / 'record-evaluator-v15.o', context),
                    'seams.cc': self._trusted_compile(self.harness['seams'], self.folder / 'seams-evaluator-v15.o',
                                                      context + [f'-DSWDB_NATIVE_FAULT_BATCH={self.fault_batch}']),
                }
                output = self.folder / 'swdb-evaluator'
                link = self.link_objects([o['object'] for o in objects.values()], output, pthread=True)
                if link['returncode']:
                    raise Failure('trusted native certification evaluator failed to link; see ' + link['log'])
                client = self._trusted_compile(library / NATIVE_CLIENT, self.folder / 'client-v15.o',
                                               ['-I' + str(library / FOLDER)])
                self._trusted['process'] = {'evaluator': str(output), 'evaluator_sha256': artifacts.file_hash(output),
                                            'objects': {k: v['object_sha256'] for k, v in objects.items()},
                                            'client': client}
            return self._trusted['process']

        def link(self, candidate, fault, output):
            process = self.process_objects()
            result = self.link_objects([candidate['object'], process['client']['object']], output, pthread=True)
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
    from swdb.certification_native import _plan_line
    nonce = secrets.token_hex(16)
    result = common.run_blinded([link['evaluator'], output, *common.graph_argv(graph, vertex)],
                                _plan_line(fault, nonce), nonce, fault, log, threads)
    result['evaluator_sha256'] = link['evaluator_sha256']
    return result


def certify_native(tree, library, folder, profile, plugin, *, rng=None, procedure=None):
    """A native-CPU contract under certify 1.5: the native 1.4 procedure, judge and attribution
    (``certification_native.certify_native_v14``) with the 1.5 process split. The profile's pinned 1.4
    prelude, record writer and seams are used unchanged; the client, the evaluator and the 1.5 driver
    are named by the command's source manifest (the profile is not edited)."""
    from swdb import certification_native as native
    from swdb import certification_procedures as procedures
    procedure = procedure or procedures.procedure(procedures.NATIVE, '1.5')
    return native.certify_native_v14(tree, library, folder, profile, plugin, rng=rng, procedure=procedure,
                                     build_class=_native_build_class(Path(library)), runner=_native_run,
                                     suffix='v15')


# --- DX100 authored-directive rule (1.5 and later; ticket 78, from ticket 75's review) ---------------------

_CONDITIONAL = re.compile(r'#\s*(if|ifdef|ifndef|elif|elifdef|elifndef)\b(.*)$')
_DEFINITION = re.compile(r'#\s*(define|undef)\s+([A-Za-z_]\w*)')
# Names whose definition differs between a certification build and a target build: the 1.4/1.5
# prelude's seam macros and the hooked intrinsics.
SEAM_MACROS = ('compare_and_swap', 'QueueBuffer', 'SlidingQueue', '__dxc_session_begin', '__dxc_thread_context',
               '__dxc_wait', '__dxc_gather', '__dxc_stream_load', '__dxc_range_loop', '__dxc_alu_scalar',
               '__dxc_accelerated_chunk', 'main', 'DOBFS', 'Brandes')


def knob_default_macros(contract):
    """The macros a DX100 rewrite may give a default with ``#ifndef M`` / ``#define M`` / ``#endif``:
    each contract knob's declared spellings (``SWDB_KNOB_<NAME>`` and ``SWDB_<NAME>``)."""
    from swdb.certification_legality import knob_spellings
    names = set()
    for knob in (contract or {}).get('knobs') or []:
        names |= set(knob_spellings(knob['name']))
    return names


def directive_findings(original, candidate, contract):
    """Findings [(line, token, why)] of the DX100 directive rule (1.5 and later) on candidate-authored lines.

    Ticket 75's native rule (only ``#pragma omp`` may be authored) would refuse ticket 20, ticket 42
    and both a7 bests, which author knob defaults and a diagnostic block. The DX100 form keeps its
    intent: no authored code may depend on whether it is a certification build. An authored
    conditional directive is allowed only as
      - ``#ifndef M`` directly followed by ``#define M ...`` and ``#endif``, M a contract knob macro;
      - ``#ifdef SWDB_DXC_DIAGNOSTIC`` (defined in neither certification nor target builds).
    Any other ``#if``/``#ifdef``/``#ifndef``/``#elif``, the token ``defined``, and ``#define`` or
    ``#undef`` of a seam macro are refused."""
    from swdb.certification_isolation import authored_lines
    authored = authored_lines(original, candidate)
    lines = candidate.splitlines()
    knobs = knob_default_macros(contract)
    findings = []
    for number in sorted(authored):
        text = lines[number - 1].strip()
        if not text.startswith('#'):
            continue
        conditional = _CONDITIONAL.match(text)
        definition = _DEFINITION.match(text)
        if conditional:
            kind, condition = conditional.group(1), conditional.group(2).split('//')[0].strip()
            following = [lines[i].strip() for i in range(number, min(number + 2, len(lines)))]
            knob_default = (kind == 'ifndef' and condition in knobs and len(following) == 2
                            and re.match(r'#\s*define\s+' + re.escape(condition) + r'\b', following[0])
                            and re.match(r'#\s*endif\b', following[1]))
            diagnostic = kind == 'ifdef' and condition == 'SWDB_DXC_DIAGNOSTIC'
            if not (knob_default or diagnostic):
                findings.append((number, '#' + kind, 'conditional directive (only knob defaults and the '
                                 'SWDB_DXC_DIAGNOSTIC block may be authored)'))
        elif definition and definition.group(2) in SEAM_MACROS:
            findings.append((number, definition.group(2), 'definition of a certification seam macro'))
        elif re.search(r'\bdefined\b', text):
            findings.append((number, 'defined', 'conditional on the build'))
    return findings


def refuse_directives(original, candidate, contract, version='1.5'):
    from swdb.cli import UsageError
    findings = directive_findings(original, candidate, contract)
    if findings:
        shown = '; '.join(f'line {line} {token!r} ({why})' for line, token, why in findings[:5])
        more = f' and {len(findings) - 5} more' if len(findings) > 5 else ''
        # "harness scan": the legacy words campaign code classifies aborted certifications by.
        raise UsageError(f'candidate source refused by the harness scan (certify {version} directives): '
                         + shown + more)
