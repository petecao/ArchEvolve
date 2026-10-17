"""2026-10-16 ET. AST-extracted default4 final-gate controls; no actual entry/main."""
import ast
import copy
import json
import os
from pathlib import Path
import sys
import unittest

MEMBERS = ['std_vector_int_ctor', 'std_vector_float_ctor', 'std_vector_double_ctor', 'std_vector_int_ptr_ctor']
ATTEMPTS = []


def audit(event, arguments):
    if event.startswith(('subprocess.', 'socket.')) or event in ('os.system', 'os.fork', 'os.forkpty', 'os.posix_spawn', 'os.exec', 'ctypes.dlopen'):
        ATTEMPTS.append(event)
        raise AssertionError('external boundary prohibited: ' + event)
    if event == 'open':
        path, mode, flags = arguments
        if (isinstance(mode, str) and any(char in mode for char in 'wax+')) or (isinstance(flags, int) and (flags & os.O_ACCMODE != os.O_RDONLY or flags & (os.O_CREAT | os.O_TRUNC | os.O_APPEND))):
            ATTEMPTS.append('writable-open')
            raise AssertionError('writable open prohibited')


def extract(source):
    tree = ast.parse(source)
    chosen = next((node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'completion_gate'), None)
    if chosen is not None:
        selected = ast.Module(body=[chosen], type_ignores=[])
    else:
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        expressions = [node.value for node in main.body if isinstance(node, ast.Assign) and any(isinstance(target, ast.Name) and target.id == 'complete' for target in node.targets)]
        assert len(expressions) == 1
        selected = ast.parse('def completion_gate(results, members, *, wall_seconds, retained_bytes):\n    return False\n')
        selected.body[0].body = [ast.Return(value=expressions[0])]
    namespace = {}
    exec(compile(ast.fix_missing_locations(selected), '<extracted-final-gate>', 'exec'), namespace)
    return namespace['completion_gate'], tree


def rows():
    return [{'member': member, 'verdict': 'proven', 'resources': {'exit_code': 0, 'timed_out': False, 'out_of_memory': False}} for member in MEMBERS]


class FinalGate(unittest.TestCase):
    def accept(self, values=None, members=None, wall=899.0, extent=128 * 1024**2):
        return GATE(rows() if values is None else values, MEMBERS if members is None else members,
                    wall_seconds=wall, retained_bytes=extent)

    def test_safe_exact_four_and_limits(self):
        self.assertTrue(self.accept(wall=900.0))

    def test_final_row_out_of_memory(self):
        values=rows();values[-1]['resources']['out_of_memory']=True
        self.assertFalse(self.accept(values))

    def test_final_row_timeout(self):
        values=rows();values[-1]['resources']['timed_out']=True
        self.assertFalse(self.accept(values))

    def test_final_row_nonzero_exit(self):
        values=rows();values[-1]['resources']['exit_code']=1
        self.assertFalse(self.accept(values))

    def test_incomplete(self):
        self.assertFalse(self.accept(rows()[:-1]))

    def test_duplicate_member(self):
        values=rows();values[-1]=copy.deepcopy(values[0])
        self.assertFalse(self.accept(values))

    def test_wrong_order(self):
        values=rows();values[0],values[1]=values[1],values[0]
        self.assertFalse(self.accept(values))

    def test_unexpected_member(self):
        values=rows();values[-1]['member']='std_vector_int_dtor'
        self.assertFalse(self.accept(values))

    def test_changed_expected_members(self):
        values=rows();values.reverse()
        self.assertFalse(self.accept(values, list(reversed(MEMBERS))))

    def test_not_proven(self):
        values=rows();values[0]['verdict']='not_proven'
        self.assertFalse(self.accept(values))

    def test_settled_deadline(self):
        self.assertFalse(self.accept(wall=900.000001))

    def test_final_metadata_quota(self):
        self.assertFalse(self.accept(extent=128 * 1024**2 + 1))

    def test_missing_resource_flags(self):
        values=rows();del values[-1]['resources']['timed_out']
        self.assertFalse(self.accept(values))

    def test_boolean_exit_not_integer_zero(self):
        values=rows();values[-1]['resources']['exit_code']=False
        self.assertFalse(self.accept(values))

    def test_boolean_extent_not_integer(self):
        self.assertFalse(self.accept(extent=False))

    def test_negative_elapsed(self):
        self.assertFalse(self.accept(wall=-1.0))

    def test_gate_after_archives_source_and_final_metadata(self):
        main=next(node for node in TREE.body if isinstance(node,ast.FunctionDef) and node.name=='main')
        loop=next(node for node in main.body if isinstance(node,ast.For) and isinstance(node.target,ast.Name) and node.target.id=='member')
        source_post=next(node for node in main.body if isinstance(node,ast.For) and isinstance(node.target,ast.Name) and node.target.id=='row')
        final_total=[node for node in main.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='final_total' for target in node.targets)]
        final_elapsed=[node for node in main.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='settled_elapsed' for target in node.targets)]
        final_gate=[node for node in main.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='complete' for target in node.targets)]
        self.assertEqual(len(final_total),1);self.assertEqual(len(final_elapsed),1);self.assertEqual(len(final_gate),1)
        self.assertLess(loop.end_lineno,source_post.lineno)
        self.assertLess(source_post.end_lineno,final_total[0].lineno)
        self.assertLess(final_total[0].lineno,final_elapsed[0].lineno)
        self.assertLess(final_elapsed[0].lineno,final_gate[0].lineno)
        self.assertIn("'incremental.json'",ast.unparse(loop))
        self.assertIn("output.rglob('*')",ast.unparse(final_total[0]))
        self.assertEqual(final_gate[0].value.func.id,'completion_gate')
        self.assertEqual({item.arg:ast.unparse(item.value) for item in final_gate[0].value.keywords}, {'wall_seconds':'settled_elapsed','retained_bytes':'final_total'})

    def test_flushed_publication_settles_before_success(self):
        main=next(node for node in TREE.body if isinstance(node,ast.FunctionDef) and node.name=='main')
        printed=[node for node in main.body if isinstance(node,ast.Expr) and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Name) and node.value.func.id=='print']
        self.assertEqual(len(printed),1)
        self.assertIn(('flush',True),[(item.arg,getattr(item.value,'value',None)) for item in printed[0].value.keywords])
        returned=next(node for node in main.body if isinstance(node,ast.Return))
        self.assertGreater(returned.lineno,printed[0].lineno)
        self.assertIn('time.monotonic() - started <= 900',ast.unparse(returned))


if __name__ == '__main__':
    assert len(sys.argv)==2
    candidate=Path(sys.argv[1]).resolve(strict=True)
    source=candidate.read_text()
    sys.addaudithook(audit)
    GATE,TREE=extract(source)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(FinalGate)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    summary={'date':'2026-10-16 ET','candidate':str(candidate),'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'child_native_network_or_write_attempts':ATTEMPTS,'actual_entry_main':False,'scientific_acceptance':False}
    print(json.dumps(summary,sort_keys=True))
    assert not ATTEMPTS
    raise SystemExit(0 if result.wasSuccessful() else 1)
