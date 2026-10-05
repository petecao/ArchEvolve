"""Code shared by every candidate certification path (certify 1.3-1.6, DX100 and native-CPU).

Created: 2026-10-05 ET (code-review fix F5). Agent-decided under Yan-Ru's delegation; revisable.

Certify 1.3 (``certification_isolation``), 1.4 (``certification_blinding``), 1.5
(``certification_process``) and the native-CPU path (``certification_native``) each carried a copy of
the same compile, link, run, record-reading and evidence code. They now share this module. Nothing
here changes a compile command line, a run's descriptor layout or a verdict: each path passes the
flags, files and names it used before.
"""
from __future__ import annotations

import os
import struct
from pathlib import Path

from swdb import artifacts

CHANNEL_ENV, PLAN_ENV = 'SWDB_CERT_RECORD_FD', 'SWDB_CERT_PLAN_FD'


# --- builds ------------------------------------------------------------------------------------------------

class ObjectBuild:
    """Compile and link one candidate tree's objects; every command is logged next to its output."""

    def __init__(self, folder, flags):
        from swdb.certification import compiler
        self.folder = Path(folder)
        self.folder.mkdir(parents=True, exist_ok=True)
        self.compiler = compiler()
        self.flags = list(flags)

    def compile(self, source, output, flags=None, extra=()):
        from swdb.certification import execute
        command = [self.compiler, *(self.flags if flags is None else flags), *extra, '-c', str(source), '-o', str(output)]
        result = execute(command, Path(str(output) + '.build.json'), timeout=180)
        if result['returncode'] == 0:
            result['object_sha256'] = artifacts.file_hash(output)
        result['object'] = str(output)
        return result

    def compile_candidate(self, source_path, text, label, *, prelude, includes=(), flags=None):
        """Write the candidate text to its tree path (a private build copy) and compile it with the
        evaluator prelude; the candidate's own ``main`` is renamed and never runs."""
        source_path = Path(source_path)
        source_path.write_text(text)
        extra = ['-Dmain=swdb_candidate_main', '-iquote', str(source_path.parent), *includes, '-include', str(prelude)]
        result = self.compile(source_path, self.folder / f'candidate-{label}.o', flags, extra)
        result['source_sha256'] = artifacts.digest(text)
        return result

    def link_objects(self, objects, output, *, pthread=False):
        from swdb.certification import execute
        command = [self.compiler, '-fopenmp', *(['-pthread'] if pthread else []), *[str(o) for o in objects],
                   '-o', str(output)]
        return execute(command, Path(str(output) + '.link.json'), timeout=180)


# --- runs --------------------------------------------------------------------------------------------------

def record_path(log, nonce):
    """A neutral record file name (ticket 78, from ticket 75's review): named by the run's nonce, not by the
    cell or control, so no path the run can see names its fault. ``log`` keeps the mapping."""
    return Path(log).parent / f'run-{nonce}.record'


def run_with_plan(argv, plan_bytes, *, record, log, threads):
    """One run with a fresh record file on ``SWDB_CERT_RECORD_FD`` and, unless ``plan_bytes`` is None
    (certify 1.3), the run plan on a pipe (``SWDB_CERT_PLAN_FD``). Stdout and stderr are only logged."""
    from swdb.certification import execute
    descriptor = os.open(record, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    environment, descriptors = {CHANNEL_ENV: str(descriptor)}, [descriptor]
    plan_read = plan_write = None
    try:
        if plan_bytes is not None:
            plan_read, plan_write = os.pipe()
            os.write(plan_write, plan_bytes)
            os.close(plan_write)
            plan_write = None
            environment[PLAN_ENV] = str(plan_read)
            descriptors.append(plan_read)
        result = execute(argv, log, threads=threads, extra_env=environment, pass_fds=tuple(descriptors))
    finally:
        os.close(descriptor)
        if plan_read is not None:
            os.close(plan_read)
        if plan_write is not None:
            os.close(plan_write)
    result.update(record=str(Path(record).resolve()), record_sha256=artifacts.file_hash(record))
    return result


def run_blinded(argv, plan_bytes, nonce, fault, log, threads):
    """A blinded run (certify 1.4 and later): the nonce-named record file and the plan the run echoes."""
    result = run_with_plan(argv, plan_bytes, record=record_path(log, nonce), log=log, threads=threads)
    result['plan'] = {'fault': fault, 'nonce': nonce}
    return result


def graph_argv(graph, source):
    return ['-f', graph, '-r', source, '-n', '1', '-v']


# --- records -----------------------------------------------------------------------------------------------

def record_lines(path, limit, invalid):
    """(line number, text, fields) of one record file; a missing, oversized or non-ASCII file or line is
    reported in ``invalid``."""
    path = Path(path)
    if not path.is_file() or path.stat().st_size > limit:
        invalid.append('record file missing or too large')
        return
    lines = path.read_bytes().split(b'\n')
    if lines and lines[-1] == b'':
        lines.pop()
    for number, raw in enumerate(lines, 1):
        try:
            line = raw.decode('ascii')
        except UnicodeDecodeError:
            invalid.append(f'line {number}: not ASCII')
            continue
        yield number, line, line.split(' ')


def parse_result(fields, parsed):
    """A `result <i32|f32> <n> <values>` record into ``parsed['result']``; False if the line is not one."""
    if not (len(fields) >= 3 and parsed['result'] is None and int(fields[2]) == len(fields) - 3
            and fields[1] in ('i32', 'f32')):
        return False
    if fields[1] == 'i32':
        values = [int(v) for v in fields[3:]]
    else:
        values = [struct.unpack('<f', struct.pack('<I', int(v, 16)))[0] for v in fields[3:]]
    parsed['result'] = {'kind': fields[1], 'values': values}
    return True


def parse_witness(fields, parsed):
    """The execution-witness record: DX100 `chunks= operations=` or native-CPU `claims= pushes=`, once."""
    if len(fields) != 3 or parsed['chunks'] is not None or parsed['claims'] is not None:
        return False
    if fields[1].startswith('chunks=') and fields[2].startswith('operations='):
        parsed['chunks'] = int(fields[1][7:])
        parsed['operations'] = int(fields[2][11:])
        return True
    if fields[1].startswith('claims=') and fields[2].startswith('pushes='):
        parsed['claims'] = int(fields[1][7:])
        parsed['pushes'] = int(fields[2][7:])
        return True
    return False


def result_check(parsed, result_kind, check_result):
    """The kernel's result check on the recorded result vector (None vector: a failed check)."""
    result = parsed['result']
    if result is None or result['kind'] != result_kind:
        return {'passed': False, 'reason': 'no result record of kind ' + result_kind}
    return check_result(result['values'])


def first_reason(run_result, *, strict, duplicate, invalid, clean, observed, semantic_checks):
    """The reason of a run, in the order every judge since certify 1.2 used."""
    if run_result['timeout']:
        return 'timeout'
    if strict:
        return 'strict_layer_assertion'
    if duplicate:
        return 'frontier_size_equality'
    if invalid:
        return 'record_invalid'
    if not clean:
        return 'process_failure'
    return next((name for name in semantic_checks if name in observed), 'all_checks_passed')


# --- evidence ----------------------------------------------------------------------------------------------

_PROCESS_KEYS = ('client_object_sha256', 'evaluator_sha256', 'process_split')


def evidence(link, verdict, run=None, *, binary_sha256=None):
    """The object identities and checks one matrix cell or control records.

    ``run`` is given for blinded runs (certify 1.4 and later): they also record the binary, the plan,
    the seam witness and, under the process split (1.5 and later), the client and evaluator."""
    out = {'candidate_object_sha256': link['candidate_object_sha256']}
    if run is not None:
        out['binary_sha256'] = link['binary_sha256'] if binary_sha256 is None else binary_sha256
    out.update(seam_object_sha256=link['seam_object_sha256'], record_object_sha256=link['record_object_sha256'])
    if run is not None:
        out['plan'] = run['plan']
    out.update(named_checks=verdict['named_checks'], observed_checks=verdict['observed_checks'],
               result_check=verdict['result_check'], record_problems=verdict['record_problems'])
    if run is not None:
        out['seam_witness'] = verdict['seam_witness']
        out.update({key: link[key] for key in _PROCESS_KEYS if key in link})
    return out
