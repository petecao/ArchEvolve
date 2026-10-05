"""Candidate certification the candidate cannot steer (certify 1.3). Created: 2026-10-04 ET (ticket 70).

Agent-decided under Yan-Ru's 2026-10-04 delegation; revisable.

Up to certify 1.2 a candidate artifact ran in the same process and the same translation unit as
the certification harness. The certifier read named checks from stdout and stderr, and a control
build defined ``-DSWDB_DXC_FAULT_<ID>`` where candidate source could test it, so a hostile
candidate could print an expected rejection, or behave differently, only in control builds.

Three layers close that:

* **Record channel, out-of-process verdicts.** The binary's trusted parts
  (``library/dx100/certification/record.cc`` and the strict layer's check) write raw records to a
  file descriptor the harness opened for that run: strict-layer check names, each frontier window
  as vertex IDs, the kernel's returned vector and the execution-witness counters. The kernel's
  result comes from an evaluator-owned ``main`` (``*_driver.inc``) that calls the protected entry
  point. :func:`judge` computes every named check from those records with the evaluator's own
  oracles (the per-level counts and ``bfs_native.verify_parents`` / ``bc_native.verify_scores``).
  Stdout and stderr are kept for people and never parsed for a verdict.
* **Opaque faults.** The candidate translation unit is compiled once per tile size with one
  evaluator prelude (``candidate_prelude.hpp``, forced with ``-include``) whose library seams call
  extern functions. The faults live in a separately compiled object (``seams.cc``), one per
  control, selected by a macro on that object's command line only. Library-fault controls link the
  very same candidate object as the positive matrix; each record carries its sha256.
* **Harness scan (defense in depth).** :func:`scan` refuses candidate-authored text (lines that
  differ from the registered snapshot) that names a harness or fault symbol, the certification-
  build macros, a primitive that reaches file descriptors, the environment or the loader, or a
  string that imitates an evaluator line.

Not closed (recorded in ticket 70): code in the candidate's process can still probe a seam at run
time (for example call ``compare_and_swap`` on scratch data and see whether a failed compare
succeeds) and then misbehave on purpose; the frontier inspection runs at the protected print,
inside the candidate's own function.

Updated: 2026-10-05 ET (ticket 76). Certify 1.4 (``swdb.certification_blinding``) closes those two
holes as far as one process allows and is the default. This module stays the unchanged 1.3 path
(``certify(..., version='1.3')``); its scan also serves 1.4 with the larger primitive set
:data:`PRIMITIVES_1_4`.
"""
from __future__ import annotations

import bisect
import difflib
import os
import re
import struct
from pathlib import Path

from swdb import artifacts
from swdb.cli import Failure, UsageError

CHANNEL_ENV = 'SWDB_CERT_RECORD_FD'
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


class CandidateBuild:
    """The objects of one candidate tree at one tile size.

    ``candidate_object`` compiles the (instrumented) candidate translation unit with the prelude;
    ``trusted_object`` compiles record.cc or seams.cc (one per fault, cached); ``link`` joins them.
    Every command is logged next to its output, as ``certification.compile_cpp`` does.
    """

    def __init__(self, folder, library, tree, source_path, tile_size, threads):
        from swdb.certification import compiler
        self.folder, self.library, self.tree = Path(folder), Path(library), Path(tree)
        self.source_path, self.tile_size, self.threads = Path(source_path), tile_size, threads
        self.folder.mkdir(parents=True, exist_ok=True)
        self.compiler = compiler()
        self.flags = _flags(self.library, self.tree, tile_size, threads)
        self._trusted = {}

    def _compile(self, source, output, extra=()):
        from swdb.certification import execute
        command = [self.compiler, *self.flags, *extra, '-c', str(source), '-o', str(output)]
        result = execute(command, Path(str(output) + '.build.json'), timeout=180)
        if result['returncode'] == 0:
            result['object_sha256'] = artifacts.file_hash(output)
        return result

    def candidate_object(self, text, label):
        """Write the candidate text to its tree path (a private build copy) and compile it."""
        self.source_path.write_text(text)
        extra = ['-Dmain=swdb_candidate_main', '-iquote', str(self.source_path.parent),
                 '-include', str(self.library / PRELUDE)]
        output = self.folder / f'candidate-{label}.o'
        result = self._compile(self.source_path, output, extra)
        result['object'] = str(output)
        result['source_sha256'] = artifacts.digest(text)
        return result

    def trusted_object(self, kind, fault=None):
        """record.cc, or seams.cc with no fault or exactly one fault macro (never the candidate's)."""
        key = (kind, fault)
        if key not in self._trusted:
            source = self.library / (RECORD_SOURCE if kind == 'record' else SEAM_SOURCE)
            name = kind if kind == 'record' else 'seams-' + (fault or 'none').lower()
            output = self.folder / f'{name}.o'
            result = self._compile(source, output, ['-D' + fault] if fault else [])
            result['object'] = str(output)
            if result['returncode']:
                raise Failure(f'trusted certification object failed to build ({name}); see ' + result['log'])
            self._trusted[key] = result
        return self._trusted[key]

    def link(self, candidate, fault, output):
        from swdb.certification import execute
        record, seams = self.trusted_object('record'), self.trusted_object('seams', fault)
        command = [self.compiler, '-fopenmp', candidate['object'], record['object'], seams['object'],
                   '-o', str(output)]
        result = execute(command, Path(str(output) + '.link.json'), timeout=180)
        result.update(candidate_object_sha256=candidate.get('object_sha256'),
                      record_object_sha256=record['object_sha256'], seam_object_sha256=seams['object_sha256'],
                      fault_macro=fault)
        return result


def run(binary, graph, source, log, threads):
    """One run with a fresh record file on a harness-opened descriptor; stdout/stderr only logged."""
    from swdb.certification import execute
    record = Path(str(log) + '.record')
    descriptor = os.open(record, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    try:
        result = execute([binary, '-f', graph, '-r', source, '-n', '1', '-v'], log, threads=threads,
                         extra_env={CHANNEL_ENV: str(descriptor)}, pass_fds=(descriptor,))
    finally:
        os.close(descriptor)
    result['record'] = str(record.resolve())
    result['record_sha256'] = artifacts.file_hash(record)
    return result


# --- records -------------------------------------------------------------------------------------

_STRICT_NAME = re.compile(r'[a-z_]+')


def parse_records(path, strict_names):
    """The evaluator records of one run. Anything malformed or unknown makes the run invalid."""
    parsed = {'begin': False, 'end': False, 'strict': [], 'frontier': [], 'result': None,
              'chunks': None, 'operations': None, 'invalid': []}
    path = Path(path)
    if not path.is_file() or path.stat().st_size > RECORD_LIMIT:
        parsed['invalid'].append('record file missing or too large')
        return parsed
    lines = path.read_bytes().split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    for number, raw in enumerate(lines, 1):
        try:
            line = raw.decode('ascii')
        except UnicodeDecodeError:
            parsed['invalid'].append(f'line {number}: not ASCII')
            continue
        fields = line.split(' ')
        kind = fields[0]
        try:
            if line == 'begin 1' and not parsed['begin'] and number == 1:
                parsed['begin'] = True
            elif kind == 'strict' and len(fields) == 2 and _STRICT_NAME.fullmatch(fields[1]) \
                    and fields[1] in strict_names:
                parsed['strict'].append(fields[1])
            elif kind == 'frontier' and len(fields) >= 2 and int(fields[1]) == len(fields) - 2:
                parsed['frontier'].append([int(v) for v in fields[2:]])
            elif kind == 'result' and len(fields) >= 3 and parsed['result'] is None \
                    and int(fields[2]) == len(fields) - 3 and fields[1] in ('i32', 'f32'):
                if fields[1] == 'i32':
                    values = [int(v) for v in fields[3:]]
                else:
                    values = [struct.unpack('<f', struct.pack('<I', int(v, 16)))[0] for v in fields[3:]]
                parsed['result'] = {'kind': fields[1], 'values': values}
            elif kind == 'witness' and len(fields) == 3 and parsed['chunks'] is None \
                    and fields[1].startswith('chunks=') and fields[2].startswith('operations='):
                parsed['chunks'] = int(fields[1][7:])
                parsed['operations'] = int(fields[2][11:])
            elif line == 'end' and not parsed['end']:
                parsed['end'] = True
            else:
                parsed['invalid'].append(f'line {number}: unexpected record {kind[:20]!r}')
        except (ValueError, struct.error):
            parsed['invalid'].append(f'line {number}: malformed {kind[:20]!r} record')
    return parsed


SEMANTIC_CHECKS = ('verifier', 'frontier_size_equality', 'execution_witness')


def judge(run_result, parsed, counts, *, check_result, result_kind, threshold=64):
    """Every check of one run, computed from its evaluator records and the trusted oracles.

    Returns {passed, reason, observed_checks, named_checks, result_check}. ``reason`` keeps the
    order of certify 1.2's judge (timeout, strict layer, duplicate frontier, process failure,
    verifier, frontier sizes, execution witness), with ``record_invalid`` for a malformed record.
    The semantic checks are evaluated only for a clean run (exit 0, begin and end recorded, no
    strict failure), each independently, so a later check is never hidden behind an earlier one.
    """
    strict = list(dict.fromkeys(parsed['strict']))
    windows = parsed['frontier']
    duplicate = any(len(set(window)) != len(window) for window in windows)
    named = strict + (['duplicate_frontier'] if duplicate else [])
    observed = set(named) | ({'frontier_size_equality'} if duplicate else set())
    clean = (not run_result['timeout'] and run_result['returncode'] == 0 and parsed['begin'] and parsed['end']
             and not strict and not parsed['invalid'])
    result_check = None
    if clean:
        result = parsed['result']
        if result is None or result['kind'] != result_kind:
            result_check = {'passed': False, 'reason': 'no result record of kind ' + result_kind}
        else:
            result_check = check_result(result['values'])
        if not result_check['passed']:
            observed.add('verifier')
        if [len(window) for window in windows] != list(counts):
            observed.add('frontier_size_equality')
        if max(counts) >= threshold and not (parsed['chunks'] and parsed['operations']):
            observed.add('execution_witness')
    if run_result['timeout']:
        reason = 'timeout'
    elif strict:
        reason = 'strict_layer_assertion'
    elif duplicate:
        reason = 'frontier_size_equality'
    elif parsed['invalid']:
        reason = 'record_invalid'
    elif not clean:
        reason = 'process_failure'
    else:
        reason = next((name for name in SEMANTIC_CHECKS if name in observed), 'all_checks_passed')
    return {'passed': reason == 'all_checks_passed', 'reason': reason, 'observed_checks': sorted(observed),
            'named_checks': named, 'result_check': result_check,
            'record_problems': parsed['invalid'][:5]}


# --- harness scan ----------------------------------------------------------------------------------

HARNESS_PREFIXES = ('swdb_strict', 'swdb_fault', 'swdb_seam', 'swdb_hooked', 'swdb_cert', 'swdb_trusted',
                    'swdb_forged', 'swdb_record', 'SWDB_DXC_FAULT', 'SWDB_CERT')
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


def scan(original, candidate, version='1.3'):
    """Findings [(line, token, why)] in candidate-authored lines (those not in the snapshot text).

    ``version`` '1.4' (ticket 76) refuses the larger primitive set :data:`PRIMITIVES_1_4`."""
    primitives = PRIMITIVES_1_4 if version == '1.4' else PRIMITIVES
    from swdb.certification_faults import tokens
    authored = set()
    matcher = difflib.SequenceMatcher(None, original.splitlines(), candidate.splitlines(), autojunk=False)
    for tag, _, _, j1, j2 in matcher.get_opcodes():
        if tag in ('replace', 'insert'):
            authored.update(range(j1 + 1, j2 + 1))
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
        if token.startswith(HARNESS_PREFIXES):
            findings.append((line, token, 'harness or fault symbol'))
        elif token in BUILD_IDENTITY:
            findings.append((line, token, 'certification-build macro'))
        elif token in primitives:
            findings.append((line, token, 'descriptor, environment, loader or process primitive'))
    if literal:
        flush_literal()
    return findings


def refuse_scan_findings(original, candidate, version='1.3'):
    findings = scan(original, candidate, version)
    if findings:
        shown = '; '.join(f'line {line} {token!r} ({why})' for line, token, why in findings[:5])
        more = f' and {len(findings) - 5} more' if len(findings) > 5 else ''
        raise UsageError(f'candidate source refused by the harness scan (certify {version}): ' + shown + more)
