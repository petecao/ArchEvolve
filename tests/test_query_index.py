"""Public queries use one freshness-checked SQLite snapshot, 2026-09-27 ET."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest
from conftest import load_fixture,run_swdb
from swdb import db,workflow,yamlio
from swdb.cli import Failure


def application(records,name='before'):
    value=load_fixture('application.yaml');value['name']=name
    records.write('applications/fixture-app.yaml',value)
    return yamlio.load(records.path/'applications/fixture-app.yaml')


def test_custom_index_refreshes_and_never_uses_default(records,tmp_path):
    first=application(records);selected=tmp_path/'selected.sqlite'
    args=SimpleNamespace(records=records.path,db=selected,id=first['id'],chain=False)
    assert workflow.get_record(args)==first
    assert selected.is_file() and not db.default_path(records.path).exists()
    second=application(records,'after')
    assert workflow.get_record(args)==second
    assert json.loads(db.sql(selected,'SELECT json FROM records')[0]['json'])==second
    records.write_text('applications/fixture-app.yaml','not: [valid')
    with pytest.raises(Failure,match='validation error'):workflow.get_record(args)
    assert json.loads(db.sql(selected,'SELECT json FROM records')[0]['json'])==second


def test_index_for_different_records_root_is_rebuilt(records,tmp_path):
    from swdb import yamlio
    first=application(records);selected=tmp_path/'selected.sqlite'
    db.query_store(records.path,selected)
    other=tmp_path/'other-records';(other/'applications').mkdir(parents=True)
    changed=copy.deepcopy(first);changed['name']='other-root'
    (other/'applications/fixture-app.yaml').write_text(yamlio.dumps(changed))
    assert db.query_store(other,selected).get(first['id'])==changed
    assert not db.is_stale(other,selected) and db.is_stale(records.path,selected)


@pytest.mark.parametrize('command,args',[
    ('capabilities',['missing-target']),('bfs-hotspots',['missing-profile','--kind','loop']),
    ('profile-strategies',['missing-package']),('strategy-regions',['missing-strategy']),
    ('get',['fixture-app','--chain'])])
def test_all_query_entrypoints_honor_selected_index(records,tmp_path,command,args):
    application(records);selected=tmp_path/'custom'/f'{command}.sqlite'
    result=run_swdb(command,*args,'--records',records.path,'--db',selected,'--format','json')
    assert result.returncode==(0 if command=='get' else 1),result.stderr
    assert selected.is_file() and not db.default_path(records.path).exists()
    assert db.sql(selected,'SELECT id FROM records')==[{'id':'fixture-app'}]


def test_chain_root_and_ancestors_share_one_sqlite_snapshot(records,tmp_path,monkeypatch):
    records.add_stub();selected=tmp_path/'chain.sqlite'
    old_impl=yamlio.load(records.path/'implementations/stub-impl.yaml');old_app=yamlio.load(records.path/'applications/gapbs.yaml')
    original=db.sql;reads=[]
    def mutate_after_select(path,query):
        rows=original(path,query);reads.append(query)
        new_impl=copy.deepcopy(old_impl);new_impl['name']='changed after snapshot'
        new_app=copy.deepcopy(old_app);new_app['name']='changed after snapshot'
        records.write('implementations/stub-impl.yaml',new_impl)
        records.write('applications/gapbs.yaml',new_app)
        return rows
    monkeypatch.setattr(db,'sql',mutate_after_select)
    args=SimpleNamespace(records=records.path,db=selected,id='stub-impl',chain=True)
    result=workflow.get_record(args)
    assert result['records']['stub-impl']==old_impl and result['records']['gapbs']==old_app
    assert len(reads)==1
    monkeypatch.setattr(db,'sql',original)
    later=workflow.get_record(args)
    assert later['records']['stub-impl']['name']=='changed after snapshot'
    assert later['records']['gapbs']['name']=='changed after snapshot'


def test_coverage_query_uses_selected_index(records,tmp_path):
    application(records);selected=tmp_path/'coverage.sqlite';request=tmp_path/'request.json'
    request.write_text(json.dumps({'message_version':'1.0','id':'query-fixture','candidate_protocols':[],
        'artifact_reference_comparisons':[],'controlled_reference_comparisons':[]}))
    result=run_swdb('bfs-coverage',request,'--records',records.path,'--db',selected,'--format','json')
    assert result.returncode==0,result.stderr
    assert json.loads(result.stdout)['acceptance']=='incomplete'
    assert selected.is_file() and not db.default_path(records.path).exists()
