"""Library-operation certification 1.1: record verdicts, blinded driver faults, attributed controls.

Created: 2026-10-05 ET (ticket 77). Original SWDB code. Agent-decided under Yan-Ru's delegation
("continue working"); revisable. Command 1.0 (``swdb.library_operations`` with the ported
two-binary harness) stays selectable unchanged.

Command 1.0 judged a library operation inside the candidate's own process: the run template's
``main`` checked the input frame, wrote the output file and printed the frame-violation line, and
the certifier classified a control's abort from that printed line. A candidate could skip those
steps (write its own output file and exit before the frame check), and an agent-authored control
could print the rejection line instead of containing the defect. Command 1.1 closes this:

1. **Verdicts from evaluator-owned records.** A trusted driver (``library_operations/certification/
   v1_1/driver.cc``), compiled separately from the candidate, calls the candidate adapter's
   ``extern "C"`` entry and then, in trusted code, records the frame check and the output buffer on
   a record pipe the evaluator reads (``record.cc``). The record must end with ``end`` and echo the
   run plan's nonce, and the process must exit 0. Python compares the recorded output byte for
   byte with the plain C++ reference's output. Stdout and stderr are logged and never parsed.
2. **Reference out of the candidate's reach.** The reference binary is built and run on every case
   before any candidate or control object is compiled; its outputs are kept in this process and the
   binary and its case folders are deleted before the first candidate build.
3. **Blinded driver faults in the candidate's own binary.** Per build, one candidate binary runs
   the positive cases and two driver-fault controls (``input_write``: the driver flips one input
   bit after the call; ``output_perturb``: it flips one output bit), with the same arguments,
   environment names and descriptor layout. The fault arrives on a 60-byte plan pipe that
   ``record.cc``, linked first, drains before any candidate initializer runs. Every run of a build
   (positive cases, driver faults and mutation controls) takes a fresh ``SystemRandom`` order and a
   fresh, uniformly named case folder. A candidate therefore cannot skip the post-call checks in
   positive runs and keep them in control runs: it cannot tell the two apart.
4. **Attributed rejections.** A driver-fault control is rejected only when its own check fires
   exactly where the fault acted (``input_write``: the only changed input byte is the flipped one;
   ``output_perturb``: the only differing output element is the flipped one) and the positive run
   of the same case passed. An entry's mutation control (a whole-body replacement; its binary holds
   no candidate code) is rejected only when its expected check is computed from its records and
   the positive run of the same case passed, so the check is attributable to the mutation, the
   only code that differs; a control that prints a rejection line instead is ``invalid``.
5. **Evaluator scan (defense in depth).** The body, the entry's candidate template and every control
   mutation are scanned before any build for evaluator symbols, descriptor, environment, loader and
   process primitives, initializer and exit hooks, and printing. A finding fails the certification
   (matrix cell ``scan/harness`` and check ``harness_scan``: legacy names, kept in records).

Residual (in-process, as ticket 76 R1): candidate code shares the address space with the trusted
driver and record object; pointer arithmetic or descriptor scanning can reach the record pipe or
the plan state. The scan refuses the names, not arbitrary pointer arithmetic. Closure: run the
candidate in a process holding no evaluator descriptor, with the driver exchanging buffers over
shared memory, under a syscall filter. The contract-probe cell is unchanged from 1.0: its verdict
file is written by trusted probe code in the candidate's process, and its predicates bind only the
trusted adapter's operands.

Updated: 2026-10-05 ET (code-review fixes F3, F4, F13): the version (1.1 or 1.2), its process split and
its scan primitives come from the version table (``swdb.certification_procedures``); the stale module
default ``VERSION = '1.1'`` and the per-module source rows are gone (the table's manifest replaces them).
"""
from __future__ import annotations

import bisect
import hashlib
import json
import os
import random
import re
import secrets
import shutil
import signal
import subprocess
import threading
from pathlib import Path

from swdb import artifacts
from swdb.cli import Failure

FOLDER = 'library_operations/certification/v1_1'
RECORD_SOURCE = FOLDER + '/record.cc'
DRIVER_SOURCE = FOLDER + '/driver.cc'
# Command 1.2 (ticket 78, 2026-10-05 ET): the same procedure, records and judge with the call in a
# separate candidate process. The trusted evaluator (v1_2/evaluator.cc linked with the unchanged 1.1
# record.cc) reads the case, places the operands in the certify 1.5 shared arena, starts the candidate
# binary (the candidate's unit + v1_2/runner.cc) and checks the frame and records the output from its
# own view after the call. The candidate process holds no record pipe and no plan.
FOLDER_1_2 = 'library_operations/certification/v1_2'
EVALUATOR_SOURCE_1_2 = FOLDER_1_2 + '/evaluator.cc'
RUNNER_SOURCE_1_2 = FOLDER_1_2 + '/runner.cc'
CALL_HEADER_1_2 = FOLDER_1_2 + '/call.hpp'
# The certify 1.5 shared-arena layout, always this checkout's copy (evaluator infrastructure, not a
# library entry; a library folder copied without dx100/ still builds command 1.2).
ARENA_FOLDER = Path(__file__).resolve().parents[1] / 'library/dx100/certification/v1_5'
RECORD_ENV, PLAN_ENV = 'SWDB_LO_RECORD_FD', 'SWDB_LO_PLAN_FD'
RECORD_LIMIT = 64 * 1024 * 1024
RUN_TIMEOUT = 300
FAULT_INDEX = {None: 0, 'input_write': 1, 'output_perturb': 2}
DRIVER_FAULTS = {'input_write': 'frame_violation', 'output_perturb': 'differential_mismatch'}
ATTRIBUTION = {'input_write': 'only_the_flipped_input_byte_changed',
               'output_perturb': 'only_the_flipped_output_element_differs',
               'mutation': 'expected_check_where_the_positive_run_of_the_case_passed'}
FAMILY_MACRO = {'pack': 'PACK', 'gather': 'GATHER', 'regroup': 'REGROUP', 'bin_drain': 'BIN_DRAIN',
                'gather_stream': 'GATHER_STREAM', 'relabel': 'RELABEL'}
CHECK_ORDER = ('frame_violation', 'malformed_output', 'differential_mismatch')

# Scan additions for library-operation sources (ticket 77). A body moves data; it has no reason to
# install initializers or exit hooks, print, end the process, or find its own executable.
LO_EVALUATOR_PREFIXES = ('swdb_lo', 'SWDB_LO')
LO_HARNESS_PREFIXES = LO_EVALUATOR_PREFIXES   # legacy name
LO_PRIMITIVES = {
    'constructor', 'destructor', 'init_priority', 'atexit', 'at_quick_exit', 'quick_exit', '_exit', '_Exit',
    'exit', 'abort', 'raise', 'kill', 'printf', 'fprintf', 'vprintf', 'vfprintf', 'puts', 'fputs', 'putchar',
    'fputc', 'putc', 'fwrite', 'perror', 'cout', 'cerr', 'clog', 'stdout', 'stderr', 'remove', 'rename',
    'unlink', 'chdir', 'getcwd', 'realpath', '_NSGetExecutablePath', '_NSGetArgv', '_NSGetEnviron',
    '__progname', 'program_invocation_name', 'getpid', 'getppid', 'select', 'poll',
}


# --- scan --------------------------------------------------------------------------------------------

def scan_text(text, primitives=None):
    """Findings [(line, token, why)] in one library-operation source (every line is authored).

    ``primitives`` is the procedure's scan set (the version table's; certify 1.4's set when omitted)."""
    from swdb.certification_faults import tokens
    from swdb.certification_isolation import PRIMITIVES_1_4, scan
    findings = list(scan('', text, primitives=PRIMITIVES_1_4 if primitives is None else primitives))
    starts = [0] + [m.end() for m in re.finditer('\n', text)]
    for token, start, _ in tokens(text):
        if not re.fullmatch(r'[A-Za-z_]\w*', token):
            continue
        line = bisect.bisect_right(starts, start)
        if token.startswith(LO_EVALUATOR_PREFIXES):
            findings.append((line, token, 'library-operation evaluator symbol'))
        elif token in LO_PRIMITIVES:
            findings.append((line, token, 'initializer, exit, printing or process primitive'))
    return sorted(set(findings))


def scan_sources(sources, primitives=None):
    """{label: [findings]} for every source with a finding (body, candidate template, controls)."""
    found = {}
    for label, path in sources.items():
        hits = scan_text(Path(path).read_text(errors='ignore'), primitives)
        if hits:
            found[label] = [{'line': line, 'token': token, 'why': why} for line, token, why in hits[:10]]
    return found


# --- builds ------------------------------------------------------------------------------------------

def _execute(command, log):
    result = subprocess.run([str(c) for c in command], capture_output=True, text=True, timeout=600)
    Path(log).write_text(' '.join(map(str, command)) + '\n' + (result.stdout or '') + (result.stderr or ''))
    return result.returncode


class Toolchain:
    """One build of the profile (sanitized or openmp): compiler, flags, run environment."""

    def __init__(self, name, target, folder, library_root, process_split):
        from swdb.extensa.synthesis.targets.cpu_like import _SANITIZE_FLAGS
        self.name, self.target, self.library_root = name, target, Path(library_root)
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.sanitize = name == 'sanitized'
        self.cc = target.spec.cc
        self.flags = [*target.spec.flags, *(_SANITIZE_FLAGS if self.sanitize else [])]
        self._trusted = {}
        self.process_split = process_split
        self.env = {k: v for k, v in os.environ.items() if k not in (RECORD_ENV, PLAN_ENV)}
        threads = getattr(target, 'threads', None)
        if threads is not None:
            self.env.update(OMP_NUM_THREADS=str(threads), OMP_DYNAMIC='FALSE')

    def compile(self, source, output, extra=()):
        code = _execute([self.cc, *self.flags, *extra, '-c', source, '-o', output], str(output) + '.log')
        return {'ok': code == 0, 'object': str(output), 'log': str(output) + '.log',
                'sha256': artifacts.file_hash(output) if code == 0 else None}

    def link(self, objects, output):
        code = _execute([self.cc, *self.flags, *objects, '-o', output], str(output) + '.log')
        return {'ok': code == 0, 'binary': str(output), 'log': str(output) + '.log',
                'sha256': artifacts.file_hash(output) if code == 0 else None}

    def evaluator(self, family, label):
        """Command 1.2: the family's evaluator binary (evaluator.cc + 1.1 record.cc), built without the
        sanitizer flags (it runs no candidate code); a failure is infrastructure."""
        key = ('evaluator', family)
        if key not in self._trusted:
            plain = [f for f in self.target.spec.flags if not f.startswith('-std=')] + ['-std=c++17']
            objects = []
            for source, name in ((RECORD_SOURCE, 'record'), (EVALUATOR_SOURCE_1_2, 'evaluator')):
                output = self.folder / f'{name}-{label}-v12.o'
                extra = ([f'-DSWDB_LO_FAMILY_{FAMILY_MACRO[family]}', '-I' + str(ARENA_FOLDER)]
                         if name == 'evaluator' else [])
                code = _execute([self.cc, *plain, *extra, '-c', self.library_root / source, '-o', output],
                                str(output) + '.log')
                if code:
                    raise Failure('trusted library-operation evaluator failed to build; see ' + str(output) + '.log')
                objects.append(str(output))
            binary = self.folder / f'evaluator-{label}-v12'
            code = _execute([self.cc, *plain, *objects, '-o', binary], str(binary) + '.log')
            if code:
                raise Failure('trusted library-operation evaluator failed to link; see ' + str(binary) + '.log')
            self._trusted[key] = {'binary': str(binary), 'sha256': artifacts.file_hash(binary)}
        return self._trusted[key]

    def trusted(self, family, symbol, label):
        """record.o and the family driver for one entry symbol; a failure is infrastructure.
        Command 1.2 (the process split): the runner object in place of the driver, and no record object."""
        if (family, symbol) in self._trusted:
            return self._trusted[(family, symbol)]
        if self.process_split:
            driver = self.compile(self.library_root / RUNNER_SOURCE_1_2, self.folder / f'runner-{label}.o',
                                  [f'-DSWDB_LO_FAMILY_{FAMILY_MACRO[family]}', f'-DSWDB_LO_RUN_SYMBOL={symbol}',
                                   '-I' + str(ARENA_FOLDER)])
            if not driver['ok']:
                raise Failure('trusted library-operation runner failed to build; see ' + driver['log'])
            self._trusted[(family, symbol)] = (None, driver)
            return None, driver
        record = self.compile(self.library_root / RECORD_SOURCE, self.folder / f'record-{label}.o')
        driver = self.compile(self.library_root / DRIVER_SOURCE, self.folder / f'driver-{label}.o',
                              [f'-DSWDB_LO_FAMILY_{FAMILY_MACRO[family]}', f'-DSWDB_LO_RUN_SYMBOL={symbol}'])
        for part in (record, driver):
            if not part['ok']:
                raise Failure('trusted library-operation certification object failed to build; see ' + part['log'])
        self._trusted[(family, symbol)] = (record, driver)
        return record, driver


def render_unit(folder, template, header, placeholder):
    """A translation unit from a pinned template with a cleanroom copy of ``header``."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    copy = folder / ('synth_candidate.hh' if placeholder == '{{BACKEND_HEADER}}' else 'reference.hh')
    shutil.copy(Path(header), copy)
    unit = folder / 'unit.cpp'
    unit.write_text(Path(template).read_text().replace(placeholder, str(copy.resolve())))
    return unit


def build_binary(toolchain, family, symbol, unit, output, label):
    """record.o first (its initializer runs before the unit's), the trusted driver, then the unit."""
    record, driver = toolchain.trusted(family, symbol, label)
    unit_object = toolchain.compile(unit, Path(output).with_suffix('.o'))
    if not unit_object['ok']:
        return {'ok': False, 'check': 'build_failed', 'log': unit_object['log']}
    if toolchain.process_split:
        # Ticket 78: the candidate binary is the unit and the runner; the evaluator is separate.
        evaluator = toolchain.evaluator(family, label)
        linked = toolchain.link([driver['object'], unit_object['object']], output)
        linked.update(runner_object_sha256=driver['sha256'], unit_object_sha256=unit_object['sha256'],
                      evaluator=evaluator['binary'], evaluator_sha256=evaluator['sha256'], process_split=True)
    else:
        linked = toolchain.link([record['object'], driver['object'], unit_object['object']], output)
        linked.update(record_object_sha256=record['sha256'], driver_object_sha256=driver['sha256'],
                      unit_object_sha256=unit_object['sha256'])
    if not linked['ok']:
        linked['check'] = 'build_failed'
    return linked


# --- runs --------------------------------------------------------------------------------------------

def plan_line(fault, seed, nonce):
    """The fixed-length plan line record.cc reads (60 bytes); the same length for every run."""
    line = f'plan 1 {FAULT_INDEX[fault]:02d} {seed:016x} {nonce}\n'.encode('ascii')
    assert len(line) == 60
    return line


def launch(built, argv):
    """(program, arguments) of one run: the binary itself (1.1), or its evaluator with the candidate
    binary as the first argument (1.2, ticket 78)."""
    if built.get('evaluator'):
        return built['evaluator'], [built['binary'], *argv]
    return built['binary'], list(argv)


def run_binary(binary, argv, env, fault, seed, log, timeout=RUN_TIMEOUT):
    """One run: a record pipe the evaluator drains, a plan pipe, a fresh session; output only logged."""
    nonce = secrets.token_hex(16)
    record_read, record_write = os.pipe()
    plan_read, plan_write = os.pipe()
    try:
        os.write(plan_write, plan_line(fault, seed, nonce))
    finally:
        os.close(plan_write)
    chunks, state = [], {'size': 0, 'overflow': False}

    def drain():
        while True:
            data = os.read(record_read, 1 << 16)
            if not data:
                return
            if state['size'] + len(data) > RECORD_LIMIT:
                state['overflow'] = True
                continue
            chunks.append(data)
            state['size'] += len(data)

    timed_out = False
    with open(log, 'wb') as handle:
        try:
            proc = subprocess.Popen([str(binary), *map(str, argv)], stdin=subprocess.DEVNULL, stdout=handle,
                                    stderr=subprocess.STDOUT, start_new_session=True,
                                    env={**env, RECORD_ENV: str(record_write), PLAN_ENV: str(plan_read)},
                                    pass_fds=(record_write, plan_read))
        finally:
            os.close(record_write)
            os.close(plan_read)
        reader = threading.Thread(target=drain, daemon=True)
        reader.start()
        try:
            code = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            timed_out, code = True, 124
        finally:
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except (ProcessLookupError, PermissionError):
                pass
            proc.wait()
    reader.join(10)
    held = reader.is_alive()
    if not held:
        os.close(record_read)
    data = b''.join(chunks)
    Path(str(log) + '.record').write_bytes(data)
    return {'returncode': code, 'timed_out': timed_out, 'record': data, 'overflow': state['overflow'],
            'channel_held_open': held, 'nonce': nonce, 'fault': fault, 'seed': seed,
            'record_sha256': hashlib.sha256(data).hexdigest()}


_FAULT = re.compile(r'fault (input_write) ([a-z0-9_]+) (\d+)|fault (output_perturb) (\d+)')
_VIOLATION = re.compile(r'frame violation ([a-z0-9_]+) (\d+) (\d+)')
_RESULT = re.compile(r'result (\d+) ([0-9a-f]*)')


def parse_record(data):
    """The 1.1 record of one run, read as a strict sequence. Anything else makes the run invalid."""
    parsed = {'begin': False, 'nonce': None, 'faults': [], 'violations': [], 'frame_ok': False,
              'result': None, 'end': False, 'invalid': []}
    lines = data.split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    elif lines and lines[-1]:
        parsed['invalid'].append('record does not end with a newline')
    stage = 'begin'
    for number, raw in enumerate(lines, 1):
        try:
            line = raw.decode('ascii')
        except UnicodeDecodeError:
            parsed['invalid'].append(f'line {number}: not ASCII')
            break
        if stage == 'begin' and line == 'begin 1':
            parsed['begin'], stage = True, 'plan'
        elif stage == 'plan' and re.fullmatch(r'plan [0-9a-f]{32}', line):
            parsed['nonce'], stage = line[5:], 'fault'
        elif stage == 'fault' and _FAULT.fullmatch(line):
            m = _FAULT.fullmatch(line)
            parsed['faults'].append(('input_write', m.group(2), int(m.group(3))) if m.group(1)
                                    else ('output_perturb', int(m.group(5))))
            stage = 'frame'
        elif stage in ('fault', 'frame') and line == 'frame ok':
            parsed['frame_ok'], stage = True, 'result'
        elif stage in ('fault', 'frame', 'violations') and _VIOLATION.fullmatch(line):
            m = _VIOLATION.fullmatch(line)
            parsed['violations'].append((m.group(1), int(m.group(2)), int(m.group(3))))
            stage = 'violations'
        elif stage in ('result', 'violations') and _RESULT.fullmatch(line):
            m = _RESULT.fullmatch(line)
            if len(m.group(2)) != 2 * int(m.group(1)):
                parsed['invalid'].append(f'line {number}: result length disagrees with its byte count')
                break
            parsed['result'], stage = bytes.fromhex(m.group(2)), 'end'
        elif stage == 'end' and line == 'end':
            parsed['end'], stage = True, 'after'
        else:
            parsed['invalid'].append(f'line {number}: unexpected record at stage {stage}: {line[:60]}')
            break
    return parsed


def judge(run, expected_bytes, reference):
    """Every check of one run from its record and the captured reference output."""
    out = {'check': None, 'checks': [], 'violations': [], 'mismatch_elements': 0, 'first_mismatch': None,
           'fault': None, 'returncode': run['returncode'], 'record_problems': []}
    if run['timed_out']:
        out['check'] = 'timeout'
        return out
    parsed = parse_record(run['record'])
    out['record_problems'] = parsed['invalid'][:3]
    if run['overflow'] or run['channel_held_open']:
        out['check'] = 'record_invalid'
        out['record_problems'].append('record channel overflowed or was held open after the run')
        return out
    if not parsed['end'] and not parsed['invalid']:
        out['check'] = 'runtime_abort' if run['returncode'] else 'record_invalid'
        return out
    if parsed['invalid'] or parsed['nonce'] != run['nonce']:
        out['check'] = 'record_invalid'
        return out
    if run['returncode'] != 0:
        out['check'] = 'runtime_abort'
        return out
    planned = run['fault']
    if (planned is None and parsed['faults']) or (planned is not None and
                                                  [f[0] for f in parsed['faults']] != [planned]):
        out['check'] = 'record_invalid'
        out['record_problems'].append('fault records disagree with the run plan')
        return out
    out['fault'] = parsed['faults'][0] if parsed['faults'] else None
    out['violations'] = parsed['violations']
    checks = []
    if parsed['violations']:
        checks.append('frame_violation')
    result = parsed['result']
    if result is None or len(result) != expected_bytes:
        checks.append('malformed_output')
    else:
        differing = [i for i in range(0, expected_bytes, 8) if result[i:i + 8] != reference[i:i + 8]]
        out['mismatch_elements'] = len(differing)
        out['first_mismatch'] = differing[0] // 8 if differing else None
        out['_differing'] = [i // 8 for i in differing[:4]]
        if differing:
            checks.append('differential_mismatch')
    out['checks'] = checks
    out['check'] = next((c for c in CHECK_ORDER if c in checks), 'passed')
    return out


def fault_attributed(verdict):
    """Ticket 77: the driver fault's own check fired exactly where the fault acted."""
    fault = verdict.get('fault')
    if not fault:
        return False
    if fault[0] == 'input_write':
        return (verdict['check'] == 'frame_violation' and verdict['violations'] == [(fault[1], fault[2], 1)]
                and verdict['mismatch_elements'] == 0)
    return (verdict['check'] == 'differential_mismatch' and not verdict['violations']
            and verdict['mismatch_elements'] == 1 and verdict['first_mismatch'] == fault[1])


# --- certification -----------------------------------------------------------------------------------

def certify(resolved, profile, folder, seed, builds, library_root, *, procedure):
    """Matrix cells, negative controls and the isolation summary of one 1.1 (or, ticket 78, 1.2)
    certification. ``procedure`` is the version table's entry; 1.2 differs only in where the call runs
    (``procedure.process_split``: ``launch``, ``Toolchain.evaluator``)."""
    from swdb.extensa.synthesis.certify import (family_and_shape, resolve_sizes, scan_candidate_header,
                                                scan_candidate_includes)
    folder = Path(folder)
    version, split = procedure.version, procedure.process_split
    family = resolved['family']
    _fam, sc = family_and_shape(family)
    sizes = resolve_sizes(sc, {**resolved['sizes'], **dict(profile.sizes)})
    sources = {'body': resolved['body'], 'candidate_template': resolved['candidate_template'],
               **{f'control:{cid}': c['path'] for cid, c in resolved['controls'].items()}}
    findings = scan_sources(sources, procedure.scan_primitives)
    isolation = {'version': version, 'scan': {'sources': sorted(sources), 'findings': findings}}
    if findings:
        cell = {'cell': 'scan/harness', 'status': 'failed', 'check': 'harness_scan',
                'reason': f'library-operation source refused by the harness scan (command {version}): '
                          + '; '.join(f"{label} line {f[0]['line']} {f[0]['token']!r}" for label, f in findings.items())}
        return [cell], [], isolation
    header_problems = {}
    for label, path in sources.items():
        if label == 'candidate_template':
            continue
        text = Path(path).read_text(errors='ignore')
        problem = scan_candidate_header(text) or scan_candidate_includes(text)
        if problem:
            header_problems[label] = ('forbidden_token' if 'preprocessor' in problem else 'include_policy', problem)
    rng = random.Random(seed)
    n = profile.n_cases
    cases = [sc.gen_case(rng, sizes, case_idx=c, n_cases=n) for c in range(n)]
    expected_bytes = sc.expected_cand_bytes(sizes)
    ref_symbol, cand_symbol = sc.run_symbols
    order = random.SystemRandom()

    # 1. The reference, first and alone: outputs kept here, binary and folders deleted.
    ref_name = 'sanitized' if 'sanitized' in builds else next(iter(builds))
    ref_tool = Toolchain(ref_name, builds[ref_name], folder / 'reference', library_root, split)
    ref_unit = render_unit(folder / 'reference' / 'unit', resolved['reference_template'], resolved['reference'],
                           '{{REFERENCE_HEADER}}')
    ref_binary = build_binary(ref_tool, family, ref_symbol, ref_unit, folder / 'reference' / 'reference_bin', 'ref')
    if not ref_binary['ok']:
        raise Failure('reference build failed; see ' + ref_binary['log'])
    reference = []
    for c, case in enumerate(cases):
        case_dir = folder / 'reference' / 'cases' / secrets.token_hex(8)
        sc.write_case(case_dir, case)
        run = run_binary(*launch(ref_binary, sc.argv(sizes, case, case_dir)), ref_tool.env, None, 0,
                         folder / 'reference' / f'case-{c}.log')
        parsed = parse_record(run['record'])
        if (run['returncode'] or not parsed['end'] or parsed['invalid'] or parsed['violations']
                or parsed['nonce'] != run['nonce'] or parsed['result'] is None
                or len(parsed['result']) != expected_bytes):
            raise Failure(f'reference run failed on case {c}; see {folder / "reference" / f"case-{c}.log"}')
        reference.append(parsed['result'])
    reference_summary = {'binary_sha256': ref_binary['sha256'], 'compiler': ref_tool.cc,
                         'outputs_sha256': artifacts.digest([r.hex() for r in reference]),
                         'deleted_before_candidate_build': True}
    shutil.rmtree(folder / 'reference' / 'cases', ignore_errors=True)
    Path(ref_binary['binary']).unlink()

    # 2. Every binary of every build, before any candidate code runs.
    plans, binaries = {}, {}
    for name, target in builds.items():
        tool = Toolchain(name, target, folder / name, library_root, split)
        bins = {}
        if 'body' in header_problems:
            bins['candidate'] = {'ok': False, 'check': header_problems['body'][0], 'log': header_problems['body'][1]}
        else:
            unit = render_unit(folder / name / 'candidate', resolved['candidate_template'], resolved['body'],
                               '{{BACKEND_HEADER}}')
            bins['candidate'] = build_binary(tool, family, cand_symbol, unit, folder / name / 'candidate_bin', 'cand')
        for cid, control in resolved['controls'].items():
            label = f'control:{cid}'
            if label in header_problems:
                bins[label] = {'ok': False, 'check': header_problems[label][0], 'log': header_problems[label][1]}
                continue
            unit = render_unit(folder / name / 'controls' / cid, resolved['candidate_template'], control['path'],
                               '{{BACKEND_HEADER}}')
            bins[label] = build_binary(tool, family, cand_symbol, unit, folder / name / 'controls' / cid / 'bin',
                                       'cand')
        binaries[name] = bins
        plans[name] = tool

    # 3. Per build: positive cases, driver faults and mutation controls in one random order.
    runs = []
    for name, tool in plans.items():
        bins = binaries[name]
        schedule = []
        for c in range(n):
            schedule.append(('positive', 'candidate', None, c))
            for fault in DRIVER_FAULTS:
                schedule.append(('driver_fault', 'candidate', fault, c))
            for cid in resolved['controls']:
                schedule.append(('control', f'control:{cid}', None, c))
        order.shuffle(schedule)
        for kind, binary_label, fault, c in schedule:
            built = bins[binary_label]
            row = {'build': name, 'kind': kind, 'id': fault if kind == 'driver_fault' else
                   (binary_label.split(':', 1)[1] if kind == 'control' else 'positive'), 'case': c}
            if not built['ok']:
                runs.append({**row, 'check': built.get('check', 'build_failed'), 'binary_sha256': None})
                continue
            case_dir = folder / 'runs' / secrets.token_hex(8)
            sc.write_case(case_dir, cases[c])
            run = run_binary(*launch(built, sc.argv(sizes, cases[c], case_dir)), tool.env, fault,
                             secrets.randbits(63), case_dir / 'run.log')
            verdict = judge(run, expected_bytes, reference[c])
            verdict.pop('_differing', None)
            runs.append({**row, **verdict, 'binary_sha256': built['sha256'], 'nonce': run['nonce'],
                         'record_sha256': run['record_sha256'], 'folder': str(case_dir)})

    # 4. Verdicts.
    def positive_passed(build, case):
        return any(r['kind'] == 'positive' and r['build'] == build and r['case'] == case and r['check'] == 'passed'
                   for r in runs)

    matrix = []
    for name, tool in plans.items():
        mine = [r for r in runs if r['build'] == name and r['kind'] == 'positive']
        failed = [r for r in mine if r['check'] != 'passed']
        matrix.append({'cell': f'{name}/differential', 'build': name, 'compiler': tool.cc,
                       'status': 'passed' if mine and not failed else 'failed',
                       'check': failed[0]['check'] if failed else None,
                       'reason': (f'{len(mine)} cases bitwise-equivalent from trusted records, frame clean'
                                  if mine and not failed else
                                  f"{len(failed)}/{len(mine)} cases failed; first: case {failed[0]['case']} "
                                  f"{failed[0]['check']}"),
                       'seed': seed, 'n_cases': len(mine), 'binary_sha256': binaries[name]['candidate'].get('sha256')})

    controls = []
    for fault, expected in DRIVER_FAULTS.items():
        cells, all_rejected, survived, unattributed = [], True, False, False
        for name in plans:
            mine = [r for r in runs if r['build'] == name and r['kind'] == 'driver_fault' and r['id'] == fault]
            rejected = [r for r in mine if r['check'] == expected and fault_attributed(r)
                        and positive_passed(name, r['case'])]
            survived |= any(r['check'] == 'passed' for r in mine)
            unattributed |= len(rejected) != len(mine)
            all_rejected &= bool(mine) and len(rejected) == len(mine)
            cells.append({'build': name, 'outcome': 'rejected' if mine and len(rejected) == len(mine) else
                          'survived' if any(r['check'] == 'passed' for r in mine) else 'invalid',
                          'check': expected if rejected else (mine[0]['check'] if mine else None),
                          'runs': len(mine), 'attributed_runs': len(rejected)})
        status = 'rejected' if all_rejected else 'survived' if survived else 'invalid'
        controls.append({'id': f'driver.{fault}', 'kind': 'driver_fault', 'clause': 'certifier', 'expected_check': expected,
                         'status': status, 'reason': expected if status == 'rejected' else
                         ('a run of the driver fault passed every check' if survived else 'check_not_attributed_to_fault'),
                         'delivery': 'one_binary_blinded_plan', 'attribution': ATTRIBUTION[fault], 'cells': cells})
    for cid, control in resolved['controls'].items():
        expected = control['check']
        cells, status, reason = [], None, None
        every_build_rejected, any_invalid, any_survived = True, False, False
        for name in plans:
            mine = [r for r in runs if r['build'] == name and r['kind'] == 'control' and r['id'] == cid]
            attributed = [r for r in mine if r['check'] == expected and positive_passed(name, r['case'])]
            invalid = [r for r in mine if r['check'] in ('record_invalid', 'timeout', 'build_failed',
                                                          'forbidden_token', 'include_policy')]
            survived = bool(mine) and all(r['check'] == 'passed' for r in mine)
            any_invalid |= bool(invalid)
            any_survived |= survived
            every_build_rejected &= bool(attributed)
            cells.append({'build': name, 'outcome': 'survived' if survived else 'invalid' if invalid else
                          'rejected' if attributed else 'invalid',
                          'check': expected if attributed else (invalid[0]['check'] if invalid else
                                                                next((r['check'] for r in mine if r['check'] != 'passed'), None)),
                          'runs': len(mine), 'attributed_runs': len(attributed),
                          'checks': sorted({r['check'] for r in mine})})
        if any_survived:
            status, reason = 'survived', 'a matrix build accepted the control on every case'
        elif any_invalid:
            status, reason = 'invalid', 'a control run had no valid record, timed out or did not build'
        elif every_build_rejected:
            status, reason = 'rejected', expected
        else:
            status, reason = 'invalid', 'check_not_recorded: not rejected by ' + str(expected) + ' from trusted records'
        controls.append({'id': cid, 'kind': control['kind'], 'clause': control['clause'], 'expected_check': expected,
                         'status': status, 'reason': reason, 'delivery': 'separate_binary_without_candidate',
                         'attribution': ATTRIBUTION['mutation'], 'cells': cells})

    runs_file = folder / 'runs.json'
    runs_file.write_text(json.dumps(runs, indent=1) + '\n')
    isolation.update({
        'reference': reference_summary,
        'binaries': {name: {label: {k: b.get(k) for k in ('sha256', 'record_object_sha256', 'driver_object_sha256',
                                                           'unit_object_sha256', 'runner_object_sha256',
                                                           'evaluator_sha256') if k in b}
                            for label, b in bins.items()} for name, bins in binaries.items()},
        'delivery': {'positive_and_driver_faults': 'one_binary_blinded_plan',
                     'mutation_controls': 'separate_binary_without_candidate'},
        'order': 'SystemRandom per build over positive cases, driver faults and mutation controls',
        'runs': len(runs), 'runs_file': str(runs_file), 'runs_sha256': artifacts.file_hash(runs_file)})
    if split:
        isolation['process_split'] = {
            'evaluator': 'evaluator.cc + 1.1 record.cc: case inputs, private input copies, driver fault, frame '
                         'check and records; no candidate code',
            'candidate': 'unit + runner.cc: operands copied from the shared arena into its own heap, one call, '
                         'output and inputs copied back; no record pipe, no plan'}
    return matrix, controls, isolation
