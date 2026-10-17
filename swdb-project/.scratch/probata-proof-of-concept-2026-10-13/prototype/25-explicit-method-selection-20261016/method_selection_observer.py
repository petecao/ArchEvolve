"""2026-10-16 ET. Public CLI adapter-boundary observer; no verifier is run.

Only the terminal WP adapter is a test double. The real CLI, method registry,
summary/model job construction, setup check and record writer remain active.
Every result is NOT_PROVEN fixture metadata and cannot support a model proof.
"""
from pathlib import Path
import signal
import sys

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
signal.alarm(45)


def no_tools(event, args):
    if event in {'subprocess.Popen', 'os.system', 'os.posix_spawn', 'os.exec', 'os.fork', 'socket.connect'}:
        raise RuntimeError('method-selection observer forbids native/tool/child execution: '+event)


sys.addaudithook(no_tools)
from swdb import proof
from swdb.cli import main
from swdb.wp_adapter import WpAdapter


def observe_method(self, job):
    job.log.write_text('Method-selection observer only; no compiler or verifier started.\n'+self.method.id+'\n')
    return proof.Verdict('not_proven', {'threads': 1}, failure_class='unknown', record_fields={
        'settings': {'tool': 'test-method-selection-observer', 'flags': [], 'verifier_launched': False,
                     'selected_method': self.method.id, 'scientific_result': False}})


WpAdapter.run = observe_method
WpAdapter.real = False
raise SystemExit(main(sys.argv[1:]))
