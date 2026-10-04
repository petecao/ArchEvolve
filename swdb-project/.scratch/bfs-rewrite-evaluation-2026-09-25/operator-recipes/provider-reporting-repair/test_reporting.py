"""Prospective reporting patch contracts only; no provider call. 2026-09-27 ET."""
import ast
import copy
import json
from pathlib import Path
import pytest

HERE=Path(__file__).resolve().parent
# Extract added helper from the patch itself, leaving the historical packet intact.
patch=(HERE/'optional-provider-reporting.patch').read_text().splitlines()
lines=[line[1:] for line in patch if line.startswith('+') and not line.startswith('+++')]
tree=ast.parse('\n'.join(lines[:lines.index("            receipt.update(provider_reporting(meta, meta_path.parent/'stdout.txt'))")]))
namespace={'json':json}
exec(compile(tree,'prospective reporting patch','exec'),namespace)
report=namespace['provider_reporting']


@pytest.mark.parametrize('state',['interrupted_or_timeout','failed','running',None])
def test_noncompleted_provider_never_parses_stdout_or_changes_failed_outcome(state):
    class Unreadable:
        def open(self,*args):pytest.fail('failed provider output must not be parsed')
    receipt={'proposal_outcome':{'state':'failed','stage':'rewriting','reason':'timed out after 600 seconds'},
             'candidate':None,'budget_debit':{'supplement_used_seconds':600.3155390936881},'provider_calls':1}
    original=copy.deepcopy(receipt)
    receipt.update(report({'state':state},Unreadable()))
    assert all(receipt[key]==value for key,value in original.items())
    assert receipt['provider_output_reporting']['state']=='unavailable'
    assert receipt['reported_cost_usd'] is None and receipt['usage'] is None


@pytest.mark.parametrize('raw',[b'',b'not-json',b'[]',b'null',b'"text"',b'\xff',b' '*(10*1024**2+1)])
def test_optional_empty_invalid_or_oversized_telemetry_is_classified(tmp_path,raw):
    path=tmp_path/'stdout.txt';path.write_bytes(raw)
    before=path.read_bytes()
    result=report({'state':'completed'},path)
    assert result['provider_output_reporting']['state']=='unavailable'
    assert result['reported_cost_usd'] is None
    assert path.read_bytes()==before


def test_missing_optional_output_is_not_a_new_rewrite_failure(tmp_path):
    result=report({'state':'completed'},tmp_path/'missing')
    assert result['provider_output_reporting']['reason']=='FileNotFoundError'


def test_complete_json_preserves_reported_cost_and_usage(tmp_path):
    path=tmp_path/'stdout.txt';path.write_text(json.dumps({'total_cost_usd':1.25,'usage':{'input_tokens':42}}))
    result=report({'state':'completed'},path)
    assert result['reported_cost_usd']==1.25 and result['usage']=={'input_tokens':42}
    assert result['provider_output_reporting']['state']=='available'
