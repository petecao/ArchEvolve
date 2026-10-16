"""2026-10-16 ET. INERT selected-child test body; observer is prepended by entry.

Only exact frozen 25 test criteria execute. Case diagnostics flush and fsync on
all reports, including setup/call/teardown failures and internal exceptions.
"""
def trace_child_main_v2(arguments):
    import contextlib
    import datetime
    import hashlib
    import json
    import os
    from pathlib import Path
    import sys
    request = arguments['startup_request']
    observed = observe_role_v2(request)
    if {name: observed[name] for name in request} != request:
        raise ValueError('actual test child startup or post-package paths differ before project import')
    project, profile = Path(arguments['project']), Path(arguments['profile'])
    (profile / 'actual-pytest-child-startup.json').write_text(json.dumps(observed, indent=2, sort_keys=True) + '\n')
    policy_bytes = Path(arguments['policy']).read_bytes()
    if hashlib.sha256(policy_bytes).hexdigest() != arguments['policy_sha256']:
        raise ValueError('child root policy bytes differ')
    expected = json.loads(policy_bytes)
    packet = '.scratch/probata-proof-of-concept-2026-10-13/prototype/28-public-memory-trace-resume-20261016'
    sys.path[:0] = [str(project / 'tests'), str(project / packet)]
    from swdb import c_lowering, stdlib_provenance, proof_setup
    import pytest
    tool = c_lowering.locate()
    runtime = stdlib_provenance.runtime_identity(tool)
    # The parent independently validates all selected physical compiler components.
    # Runtime identity records the exact producer binding before tests execute.
    wanted_components = expected['linux_clang_components']
    if (any(name not in runtime for name in wanted_components) or
            {name: runtime[name] for name in wanted_components} != wanted_components):
        raise ValueError('actual Linux compiler parser/driver/wrapper/header components differ')
    identity = c_lowering.identity()
    if identity['naming_rules'] != expected['naming']:
        raise ValueError('selected source-context naming identity differs')
    (profile / 'runtime-provenance.json').write_text(json.dumps({'date': '2026-10-16 ET',
        'source_commit': expected['source_commit'], 'lowering': identity, 'runtime': runtime,
        'proof_setup': proof_setup.identity(), 'startup': observed,
        'scope': 'current Linux source/runtime identity; no proof or hardware acceptance'}, indent=2, sort_keys=True) + '\n')
    packet_policy = json.loads((project / packet / 'actual-policy.json').read_bytes())
    nodes = [packet + '/test_public_actual.py::test_actual_public_abstract_memory_trace[' + row['name'] + ']'
             for row in packet_policy['cases']]
    if nodes != expected['selection']:
        raise ValueError('exact source-bound25-node selection differs')

    class Count:
        selected = None
        @pytest.hookimpl(trylast=True)
        def pytest_collection_finish(self, session):
            self.selected = [row.nodeid for row in session.items]

    count = Count()
    with (profile / 'collection.log').open('x') as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            result = int(pytest.main(['--collect-only', '-q', '--rootdir', str(project), '-p', 'no:cacheprovider', *nodes], plugins=[count]))
    (profile / 'collection.json').write_text(json.dumps({'exit_code': result, 'selected': count.selected, 'expected': nodes}, indent=2) + '\n')
    if result or count.selected != nodes:
        raise ValueError('public trace collection is not exact25')

    class Progress:
        def __init__(self, stream):
            self.stream = stream
        def write(self, value):
            value['at_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
            self.stream.write(json.dumps(value, sort_keys=True, allow_nan=False) + '\n')
            self.stream.flush()
            os.fsync(self.stream.fileno())
        def pytest_runtest_logreport(self, report):
            self.write({'event': 'runtest_report', 'nodeid': report.nodeid, 'when': report.when,
                        'outcome': report.outcome, 'duration': report.duration,
                        'longrepr': str(report.longrepr)[:4096] if report.longrepr else None})
        def pytest_internalerror(self, excrepr, excinfo):
            self.write({'event': 'internal_error', 'error': str(excrepr)[:4096]})
        def pytest_exception_interact(self, node, call, report):
            self.write({'event': 'exception', 'nodeid': node.nodeid, 'when': report.when,
                        'outcome': report.outcome, 'error': str(call.excinfo)[:4096]})

    arguments = ['-q', '--tb=short', '--rootdir', str(project), '-p', 'no:cacheprovider',
                 '--basetemp', str(profile / 'pytest'), '--junitxml', str(profile / 'junit.xml'), *nodes]
    (profile / 'pytest-arguments.json').write_text(json.dumps(arguments, indent=2) + '\n')
    with (profile / 'case-reports.jsonl').open('x') as progress, (profile / 'pytest.log').open('x') as log:
        plugin = Progress(progress)
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            try:
                result = int(pytest.main(arguments, plugins=[plugin]))
            except BaseException as error:
                plugin.write({'event': 'child_exception', 'error': repr(error)[:4096]})
                raise
    (profile / 'exit-code.txt').write_text(str(result) + '\n')
    return result
