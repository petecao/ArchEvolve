"""2026-10-16 ET. Root-admitted exact compiler-trace replay; no formal tools."""
import json
import copy
from pathlib import Path
import pytest
from swdb import dx100_allocation_source as allocation

TRACE=json.loads((Path(__file__).parent/'fixtures/dx100_allocator_linux_assertions.json').read_text())['assertions']

@pytest.mark.parametrize('row',TRACE,ids=lambda r:r['family']+'/'+r['type']+'/'+r['assertion'])
def test_original_linux_source_assertions_retain_exact_guards(row):
 variable=('num_tiles_needed'if row['family']=='get_new_tile'else'num_regs_needed')if row['assertion']=='width'else('SPD_count'if row['family']=='get_new_tile'else'REG_count')
 allocation._assertion(row['ast'],row['assertion'],variable)


@pytest.mark.parametrize('change',['increment','call','condition','wrong-argument','wrong-signature','wrong-name','extra-leaf','nested-wrapper','literal-wrapper','changed-predicate'])
def test_captured_assertion_mutations_preserve_fail_closed_operator_and_guard_checks(change):
 node=copy.deepcopy(TRACE[0]['ast'])
 call=next(n for n in allocation._walk(node)if n.get('kind')=='CallExpr')
 argument=allocation._children(call)[4];wrapper=allocation._children(argument)[0]
 predefined=allocation._children(wrapper)[0]
 if change=='increment':wrapper['inner']=[{'kind':'UnaryOperator','opcode':'++','inner':[predefined]}]
 elif change=='call':wrapper['inner']=[{'kind':'CallExpr','inner':[{'kind':'DeclRefExpr','referencedDecl':{'kind':'FunctionDecl','name':'mutate'}}]}]
 elif change=='condition':
  conditional=next(n for n in allocation._walk(node)if n.get('kind')=='ConditionalOperator')
  conditional['inner'][0]={'kind':'UnaryOperator','opcode':'__extension__','inner':[conditional['inner'][0]]}
 elif change=='wrong-argument':
  call['inner'][1]={'kind':'UnaryOperator','opcode':'__extension__','inner':[call['inner'][1]]}
 elif change=='wrong-signature':
  reference=allocation._strip_expr(call['inner'][0]);reference['referencedDecl']['type']['qualType']='int (const char *, const char *, unsigned int, const char *)'
 elif change=='wrong-name':predefined['name']='__FUNCTION__'
 elif change=='extra-leaf':predefined['inner'].append(copy.deepcopy(predefined['inner'][0]))
 elif change=='nested-wrapper':wrapper['inner']=[copy.deepcopy(wrapper)]
 elif change=='literal-wrapper':wrapper['inner']=[predefined['inner'][0]]
 elif change=='changed-predicate':
  literal=next(n for n in allocation._walk(node)if n.get('kind')=='IntegerLiteral'and n.get('value')=='2');literal['value']='3'
 with pytest.raises(allocation.Refused):allocation._assertion(node,'width','num_tiles_needed')
