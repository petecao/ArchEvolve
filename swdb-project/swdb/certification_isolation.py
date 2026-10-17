"""Candidate certification the candidate cannot steer (certify 1.3). Created: 2026-10-04 ET (ticket 70).

Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

Up to certify 1.2 a candidate artifact ran in the same process and the same translation unit as the
certification evaluator code. The certifier read named checks from stdout and stderr, and a control
build defined ``-DSWDB_DXC_FAULT_<ID>`` where candidate source could test it, so a hostile
candidate could print an expected rejection, or behave differently, only in control builds.

Three layers close that:

* **Record channel, out-of-process verdicts.** The binary's trusted parts
  (``library/dx100/certification/record.cc`` and the strict layer's check) write raw records to a
  file descriptor the evaluator opened for that run: strict-layer check names, each frontier window
  as vertex IDs, the kernel's returned vector and the execution-witness counters. The kernel's
  result comes from an evaluator-owned ``main`` (``*_driver.inc``) that calls the protected entry
  point. :func:`judge` computes every named check from those records with the evaluator's own
  reference computations (the per-level counts and ``bfs_native.verify_parents`` /
  ``bc_native.verify_scores``). Stdout and stderr are kept for people and never parsed for a verdict.
* **Opaque faults.** The candidate translation unit is compiled once per tile size with one
  evaluator prelude (``candidate_prelude.hpp``, forced with ``-include``) whose library seams call
  extern functions. The faults live in a separately compiled object (``seams.cc``), one per
  control, selected by a macro on that object's command line only. Library-fault controls link the
  very same candidate object as the positive matrix; each record carries its sha256.
* **Evaluator scan (defense in depth).** :func:`scan` refuses candidate-authored text (lines that
  differ from the registered snapshot) that names an evaluator or fault symbol, the certification-
  build macros, a primitive that reaches file descriptors, the environment or the loader, or a
  string that imitates an evaluator line. Its refusal text and campaign check keep the legacy name
  "harness scan" (``harness_scan``).

Not closed (recorded in ticket 70): code in the candidate's process can still probe a seam at run
time (for example call ``compare_and_swap`` on scratch data and see whether a failed compare
succeeds) and then misbehave on purpose; the frontier inspection runs at the protected print,
inside the candidate's own function.

Updated: 2026-10-05 ET (ticket 76). Certify 1.4 (``swdb.certification_blinding``) closes those two
holes as far as one process allows. This module stays the unchanged 1.3 path; its scan also serves
1.4 and later with the larger primitive set :data:`PRIMITIVES_1_4`.
Updated: 2026-10-05 ET (code-review fixes F3, F5): the scan's primitive set comes from the version
table (``swdb.certification_procedures``); builds, runs and record reading share
``swdb.certification_common``. Compile commands, descriptor layout and verdicts are unchanged.
"""
from __future__ import annotations

import bisect
import difflib
import re
import struct
from pathlib import Path

from swdb import certification_common as common
from swdb.cli import Failure, UsageError

CHANNEL_ENV = common.CHANNEL_ENV
FOLDER = 'dx100/certification'            # relative to the library root
PRELUDE = FOLDER + '/candidate_prelude.hpp'
RECORD_SOURCE = FOLDER + '/record.cc'
SEAM_SOURCE = FOLDER + '/seams.cc'
RECORD_LIMIT = 256 * 1024 * 1024
STRICT_EXIT, DUPLICATE_EXIT = 86, 88


# --- builds ------------------------------------------------------------------------------------

def _flags(library, model, tile_size, threads):
    return ['-std=c++11', '-O1', '-g', '-fopenmp', '-DFUNC', '-DGEM5', f'-DTILE_SIZE={tile_size}',
            f'-DNUM_CORES={threads}', '-DSWDB_CERT_RECORD',
            '-I' + str(library / 'dx100/strict'), '-I' + str(library / 'dx100'),
            '-I' + str(model / 'benchmarks/API'), '-I' + str(model / 'include')]


class CandidateBuild(common.ObjectBuild):
    """The objects of one candidate tree at one tile size.

    ``candidate_object`` compiles the (instrumented) candidate translation unit with the prelude;
    ``trusted_object`` compiles record.cc or seams.cc (one per fault, cached); ``link`` joins them.
    Every command is logged next to its output, as ``certification.compile_cpp`` does.
    """

    def __init__(self, folder, library, tree, source_path, tile_size, threads):
        self.library, self.tree = Path(library), Path(tree)
        self.source_path, self.tile_size, self.threads = Path(source_path), tile_size, threads
        super().__init__(folder, _flags(self.library, self.tree, tile_size, threads))
        self._trusted = {}

    def candidate_object(self, text, label):
        """Write the candidate text to its tree path (a private build copy) and compile it."""
        return self.compile_candidate(self.source_path, text, label, prelude=self.library / PRELUDE)

    def trusted_object(self, kind, fault=None):
        """record.cc, or seams.cc with no fault or exactly one fault macro (never the candidate's)."""
        key = (kind, fault)
        if key not in self._trusted:
            source = self.library / (RECORD_SOURCE if kind == 'record' else SEAM_SOURCE)
            name = kind if kind == 'record' else 'seams-' + (fault or 'none').lower()
            result = self.compile(source, self.folder / f'{name}.o', extra=['-D' + fault] if fault else [])
            if result['returncode']:
                raise Failure(f'trusted certification object failed to build ({name}); see ' + result['log'])
            self._trusted[key] = result
        return self._trusted[key]

    def link(self, candidate, fault, output):
        record, seams = self.trusted_object('record'), self.trusted_object('seams', fault)
        result = self.link_objects([candidate['object'], record['object'], seams['object']], output)
        result.update(candidate_object_sha256=candidate.get('object_sha256'),
                      record_object_sha256=record['object_sha256'], seam_object_sha256=seams['object_sha256'],
                      fault_macro=fault)
        return result


def run(binary, graph, source, log, threads):
    """One run with a fresh record file on an evaluator-opened descriptor; stdout/stderr only logged."""
    return common.run_with_plan([binary, *common.graph_argv(graph, source)], None,
                                record=Path(str(log) + '.record'), log=log, threads=threads)


# --- records -------------------------------------------------------------------------------------

_STRICT_NAME = re.compile(r'[a-z_]+')


def parse_records(path, strict_names):
    """The evaluator records of one run. Anything malformed or unknown makes the run invalid."""
    parsed = {'begin': False, 'end': False, 'strict': [], 'frontier': [], 'result': None,
              'chunks': None, 'operations': None, 'claims': None, 'pushes': None, 'invalid': []}
    for number, line, fields in common.record_lines(path, RECORD_LIMIT, parsed['invalid']):
        kind = fields[0]
        try:
            if line == 'begin 1' and not parsed['begin'] and number == 1:
                parsed['begin'] = True
            elif kind == 'strict' and len(fields) == 2 and _STRICT_NAME.fullmatch(fields[1]) \
                    and fields[1] in strict_names:
                parsed['strict'].append(fields[1])
            elif kind == 'frontier' and len(fields) >= 2 and int(fields[1]) == len(fields) - 2:
                parsed['frontier'].append([int(v) for v in fields[2:]])
            elif kind == 'result' and common.parse_result(fields, parsed):
                pass
            elif kind == 'witness' and common.parse_witness(fields, parsed):
                pass   # DX100 chunks/operations, or (ticket 75) the native-CPU claims/pushes
            elif line == 'end' and not parsed['end']:
                parsed['end'] = True
            else:
                parsed['invalid'].append(f'line {number}: unexpected record {kind[:20]!r}')
        except (ValueError, struct.error):
            parsed['invalid'].append(f'line {number}: malformed {kind[:20]!r} record')
    return parsed


SEMANTIC_CHECKS = ('verifier', 'frontier_size_equality', 'execution_witness')


def judge(run_result, parsed, counts, *, check_result, result_kind, threshold=64, witness=None):
    """Every check of one run, computed from its evaluator records and the trusted reference counts.

    Returns {passed, reason, observed_checks, named_checks, result_check}. ``reason`` keeps the
    order of certify 1.2's judge (timeout, strict layer, duplicate frontier, process failure,
    verifier, frontier sizes, execution witness), with ``record_invalid`` for a malformed record.
    The semantic checks are evaluated only for a clean run (exit 0, begin and end recorded, no
    strict failure), each independently, so a later check is never hidden behind an earlier one.
    ``witness`` (ticket 75) replaces the DX100 execution-witness rule with a predicate
    ``witness(parsed, counts) -> bool`` (the native rule counts seam claims and pushes).
    """
    # Ticket 75 review: the witness line must be the form of the judged target (DX100 chunks and
    # operations, or the native claims and pushes); the other form makes the record invalid.
    other_form = parsed.get('claims') is not None if witness is None else parsed.get('chunks') is not None
    if other_form:
        parsed = {**parsed, 'invalid': list(parsed['invalid']) + ['witness record of another target']}
    strict = list(dict.fromkeys(parsed['strict']))
    windows = parsed['frontier']
    duplicate = any(len(set(window)) != len(window) for window in windows)
    named = strict + (['duplicate_frontier'] if duplicate else [])
    observed = set(named) | ({'frontier_size_equality'} if duplicate else set())
    clean = (not run_result['timeout'] and run_result['returncode'] == 0 and parsed['begin'] and parsed['end']
             and not strict and not parsed['invalid'])
    result_check = None
    if clean:
        result_check = common.result_check(parsed, result_kind, check_result)
        if not result_check['passed']:
            observed.add('verifier')
        if [len(window) for window in windows] != list(counts):
            observed.add('frontier_size_equality')
        if witness is not None:
            if not witness(parsed, counts):
                observed.add('execution_witness')
        elif max(counts) >= threshold and not (parsed['chunks'] and parsed['operations']):
            observed.add('execution_witness')
    reason = common.first_reason(run_result, strict=strict, duplicate=duplicate, invalid=parsed['invalid'],
                                 clean=clean, observed=observed, semantic_checks=SEMANTIC_CHECKS)
    return {'passed': reason == 'all_checks_passed', 'reason': reason, 'observed_checks': sorted(observed),
            'named_checks': named, 'result_check': result_check,
            'record_problems': parsed['invalid'][:5]}


# --- evaluator scan (legacy name: harness scan) -------------------------------------------------------

EVALUATOR_PREFIXES = ('swdb_strict', 'swdb_fault', 'swdb_seam', 'swdb_hooked', 'swdb_cert', 'swdb_trusted',
                      'swdb_forged', 'swdb_record', 'SWDB_DXC_FAULT', 'SWDB_CERT', 'SWDB_NATIVE')
HARNESS_PREFIXES = EVALUATOR_PREFIXES   # legacy name
# Macros that tell a certification build from the target build.
BUILD_IDENTITY = {'SWDB_STRICT', 'FUNC'}
# Primitives that reach file descriptors, the environment, the loader or other processes.
PRIMITIVES = {
    'write', 'pwrite', 'writev', 'dprintf', 'vdprintf', 'syscall', 'fdopen', 'freopen', 'dup', 'dup2', 'dup3',
    'fcntl', 'ioctl', 'open', 'openat', 'creat', 'close', 'fopen', 'ofstream', 'fstream', 'filebuf',
    'basic_ofstream', 'basic_fstream', 'basic_filebuf',
    'getenv', 'secure_getenv', 'setenv', 'unsetenv', 'putenv', 'environ', '__environ',
    'dlopen', 'dlsym', 'dladdr', 'dl_iterate_phdr', 'asm', '__asm', '__asm__',
    'system', 'popen', 'fork', 'vfork', 'execl', 'execlp', 'execle', 'execv', 'execve', 'execvp',
    'posix_spawn', 'posix_spawnp', 'ptrace', 'mmap', 'mprotect',
}
# Certify 1.4 (ticket 76, 2026-10-05 ET) also refuses reading descriptors (the run plan arrives on
# one), files that could carry state from one run to the next, and frame or symbol introspection.
# Defense in depth only: 1.4's guarantees do not rest on the scan (ticket 76, residual threats).
PRIMITIVES_1_4 = PRIMITIVES | {
    'read', 'pread', 'readv', 'preadv', 'recv', 'recvfrom', 'recvmsg', 'socket', 'socketpair', 'pipe', 'pipe2',
    'ifstream', 'basic_ifstream', 'tmpfile', 'tmpnam', 'mkstemp', 'mkostemp', 'mkdtemp', 'shm_open', 'sem_open',
    'msgget', 'shmget', 'filesystem', 'opendir', 'readdir', 'scandir', 'stat', 'fstat', 'lstat', 'access',
    'sysctl', 'proc_pidinfo', 'task_for_pid', 'backtrace', 'backtrace_symbols', '__builtin_frame_address',
    '__builtin_return_address', '__builtin_extract_return_addr', 'dl_iterate_phdr', '_dyld_get_image_header',
    '_dyld_image_count', 'getauxval', 'process_vm_readv', 'prctl', 'signal', 'sigaction', 'setjmp', 'longjmp',
}
# Text that imitates an evaluator line (verdicts no longer come from output; refused anyway).
IMITATIONS = ('SWDB_STRICT_ASSERT', 'SWDB_PRESERVATION_FAIL', 'SWDB_DIFFERENTIAL', 'SWDB_CERT',
              'trusted_frontier', 'accelerated_chunks', 'strict_operations', 'Verification', '/proc/', '/dev/fd')


def _literal_text(token):
    body = token[1:-1] if token[:1] == '"' else ''
    return re.sub(r'\\(.)', r'\1', body)


def authored_lines(original, candidate):
    """1-based numbers of the candidate lines that are not lines of the snapshot text."""
    authored = set()
    matcher = difflib.SequenceMatcher(None, original.splitlines(), candidate.splitlines(), autojunk=False)
    for tag, _, _, j1, j2 in matcher.get_opcodes():
        if tag in ('replace', 'insert'):
            authored.update(range(j1 + 1, j2 + 1))
    return authored


def scan(original, candidate, version='1.3', *, directives=False, primitives=None):
    """Findings [(line, token, why)] in candidate-authored lines (those not in the snapshot text).

    ``primitives`` is the refused primitive set of the running procedure
    (``CertifyProcedure.scan_primitives``); without it, the candidate procedure of ``version`` names it
    (1.3: :data:`PRIMITIVES`; 1.4 and later: :data:`PRIMITIVES_1_4`, ticket 76).

    ``directives`` (ticket 75 review; native-CPU contracts): an authored preprocessor directive other
    than ``#pragma omp`` is refused, and so is the token ``defined``. The seam macros
    (``compare_and_swap``, ``QueueBuffer``, ``SlidingQueue``) exist only in certification builds, so
    ``#ifndef QueueBuffer`` would let a candidate run other code on the target. The DX100 rewrites
    author ``#ifdef`` blocks of their own and keep the scan without it (certify 1.5 and later add the
    DX100 directive rule of ``swdb.certification_process``).
    """
    if primitives is None:
        from swdb import certification_procedures as procedures
        primitives = procedures.procedure(procedures.CANDIDATE, version).scan_primitives
    from swdb.certification_faults import tokens
    authored = authored_lines(original, candidate)
    starts = [0]
    for match in re.finditer('\n', candidate):
        starts.append(match.end())
    line_of = lambda offset: bisect.bisect_right(starts, offset)
    findings, literal, literal_line = [], [], None

    def flush_literal():
        text = ''.join(literal)
        for marker in IMITATIONS:
            if marker in text:
                findings.append((literal_line, marker, 'string imitates an evaluator line or path'))
        literal.clear()

    if directives:
        for number, text in enumerate(candidate.splitlines(), 1):
            stripped = text.strip()
            if number in authored and stripped.startswith('#') and not re.match(r'#\s*pragma\s+omp\b', stripped):
                findings.append((number, stripped.split()[0] if stripped.split() else '#',
                                 'preprocessor directive (only #pragma omp may be authored)'))
    for token, start, _ in tokens(candidate):
        line = line_of(start)
        if line not in authored:
            if literal:
                flush_literal()
            continue
        if token[:1] == '"':
            if not literal:
                literal_line = line
            literal.append(_literal_text(token))
            continue
        if literal:
            flush_literal()
        if not re.fullmatch(r'[A-Za-z_]\w*', token):
            continue
        if token.startswith(EVALUATOR_PREFIXES):
            findings.append((line, token, 'evaluator or fault symbol'))
        elif directives and token == 'defined':
            findings.append((line, token, 'preprocessor directive (only #pragma omp may be authored)'))
        elif token in BUILD_IDENTITY:
            findings.append((line, token, 'certification-build macro'))
        elif token in primitives:
            findings.append((line, token, 'descriptor, environment, loader or process primitive'))
    if literal:
        flush_literal()
    return findings


def refuse_scan_findings(original, candidate, version='1.3', *, directives=False, primitives=None):
    # 2026-10-08 ET: retain the public text and mark this authored-source refusal explicitly.
    findings = scan(original, candidate, version, directives=directives, primitives=primitives)
    if findings:
        shown = '; '.join(f'line {line} {token!r} ({why})' for line, token, why in findings[:5])
        more = f' and {len(findings) - 5} more' if len(findings) > 5 else ''
        raise common.CandidateUsageError(f'candidate source refused by the harness scan (certify {version}): '
                                         + shown + more, check='harness_scan')
