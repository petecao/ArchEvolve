"""Prospective schema cannot turn planning into dispatch. 2026-09-27 ET."""
import importlib.util
import json
from pathlib import Path
import pytest
import jsonschema

HERE=Path(__file__).resolve().parent
s=importlib.util.spec_from_file_location('t17_prospective_plan',HERE/'validate_plan.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)


def test_actual_prospective_manifest_has_expected_cells_and_no_authority():
    value=json.loads((HERE/'manifest-template.json').read_text());result=m.validate(value)
    assert result['dispatch_allowed'] is False and result['expected_primary_executions']==24


@pytest.mark.parametrize('fault',['dispatch','renewed-window','budget','duplicate-series','wrong-role','invented-workload','primary-rebuild'])
def test_incomplete_plan_cannot_create_a_budget_or_scientific_substitution(fault):
    value=json.loads((HERE/'manifest-template.json').read_text())
    if fault=='dispatch':value['dispatch_allowed']=True
    elif fault=='renewed-window':value['historical_diagnostic']['original_deadline']='2026-09-27T01:57:10.605637-04:00'
    elif fault=='budget':value['budget_derivation']['aggregate_seconds']=600
    elif fault=='duplicate-series':value['series'][1]=value['series'][0]
    elif fault=='wrong-role':value['series'][0]['accelerated']=True
    elif fault=='invented-workload':value['series'][0]['workload']='arbitrarily-selected'
    else:value['remaining_diagnostic_prerequisite']['primary_recompile']=True
    with pytest.raises((AssertionError,jsonschema.ValidationError)):m.validate(value)
