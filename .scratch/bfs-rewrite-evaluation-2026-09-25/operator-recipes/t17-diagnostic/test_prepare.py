"""Data-only T17 preparation contracts; created 2026-09-27 ET."""
import importlib.util
import io
import json
from pathlib import Path
import tarfile
import pytest

HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('t17_prepare',HERE/'prepare.py');op=importlib.util.module_from_spec(spec);spec.loader.exec_module(op)


def archive(name,data):
    output=io.BytesIO()
    with tarfile.open(fileobj=output,mode='w') as tar:
        member=tarfile.TarInfo(name);member.size=len(data);tar.addfile(member,io.BytesIO(data))
    return output.getvalue()


def setup(monkeypatch,tmp_path,name='records/base.yaml'):
    dispatch=tmp_path/'dispatch';records=dispatch/'record-view/records'
    monkeypatch.setattr(op,'DISPATCH',dispatch);monkeypatch.setattr(op,'RECORDS',records)
    overlay=b'id: retained\n';monkeypatch.setattr(op,'OVERLAYS',{'records/overlay.yaml':op.digest(overlay)})
    def git(*args):
        if args[0]=='archive':return archive(name,b'id: base\n')
        if args[0]=='show':return overlay
        return b'a'*40
    monkeypatch.setattr(op,'git',git)
    return dispatch,records


def test_data_materialization_keeps_every_base_record_and_exact_overlay(monkeypatch,tmp_path):
    dispatch,records=setup(monkeypatch,tmp_path);op.materialize()
    assert (records/'base.yaml').read_bytes()==b'id: base\n'
    assert (records/'overlay.yaml').read_bytes()==b'id: retained\n'
    manifest=json.loads((dispatch/'record-view-manifest.json').read_text())
    assert [r['path'] for r in manifest['files']]==['base.yaml','overlay.yaml']
    assert manifest['git_provenance'][0]['commit']==op.COMMIT
    assert manifest['git_provenance'][1]['commit']==op.EVIDENCE


def test_existing_dispatch_is_never_modified(monkeypatch,tmp_path):
    dispatch,records=setup(monkeypatch,tmp_path);dispatch.mkdir();(dispatch/'old').write_text('keep')
    with pytest.raises(RuntimeError,match='already exists'):op.materialize()
    assert list(dispatch.iterdir())==[dispatch/'old']


def test_parent_traversal_rejected(monkeypatch,tmp_path):
    dispatch,records=setup(monkeypatch,tmp_path,'records/../escape.yaml')
    with pytest.raises(RuntimeError,match='unsafe archive path'):op.materialize()
    assert not (dispatch/'record-view/escape.yaml').exists()


def test_conflicting_overlay_never_replaces_base(monkeypatch,tmp_path):
    dispatch,records=setup(monkeypatch,tmp_path,'records/overlay.yaml')
    with pytest.raises(RuntimeError,match='conflict'):op.materialize()
    assert (records/'overlay.yaml').read_bytes()==b'id: base\n'


def test_manifest_guard_rejects_added_import_before_runtime_execution(monkeypatch,tmp_path):
    root=tmp_path/'runtime';root.mkdir();(root/'rogue.py').write_text('raise Exception()')
    monkeypatch.setattr(op,'RUNTIME',root);monkeypatch.setattr(op,'git',lambda *args:op.COMMIT.encode())
    manifest=tmp_path/'manifest.json';manifest.write_text(json.dumps({'commit':op.COMMIT,'files':{}}))
    with pytest.raises(RuntimeError,match='runtime bytes differ'):op.guard(manifest,op.digest(manifest.read_bytes()))
