"""2026-10-16 ET. Prospective real public-test inputs; no execution admission."""
import hashlib
import json
import os
from pathlib import Path
import stat

QUIET={'SWDB_FRAMA_C':'none','SWDB_CLANG':'none','SWDB_CBMC':'none'}
LEGACY_SHA='844da0f557adae447fbafd2617c86aa3f5a7fa475597ca9860c7e33b2f3cc84f'
CALLS=('get_cacheable_tile_pointer','get_noncacheable_tile_pointer','add_mem_region','clear_mem_region','alloc_MAA','init_MAA','wait_ready','get_tile_size','get_reg','set_reg','get_new_reg','get_new_tile','maa_const','print_tile','get_data_type','maa_alu_scalar','maa_alu_vector','maa_alu_reduce','maa_stream_load','maa_stream_store','maa_indirect_load','maa_indirect_store_vector','maa_indirect_store_scalar','maa_indirect_rmw_vector','maa_indirect_rmw_scalar','maa_range_loop')

def strict(raw):
    def pairs(items):
        out={}
        for key,value in items:
            assert key not in out,'duplicate fixture/profile JSON key'
            out[key]=value
        return out
    return json.loads(raw,object_pairs_hook=pairs,parse_constant=lambda _:(_ for _ in ()).throw(AssertionError('nonfinite fixture metadata')))

def physical(row):
    assert type(row) is dict and set(row)=={'path','bytes','sha256'}
    path=Path(row['path']);before=path.lstat()
    assert path.is_absolute() and path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode)
    assert type(row['bytes']) is int and before.st_size==row['bytes'] and 0<row['bytes']<=8*1024*1024
    with path.open('rb') as stream:raw=stream.read(row['bytes']+1)
    stable=lambda value:tuple(getattr(value,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))
    assert len(raw)==row['bytes'] and stable(path.lstat())==stable(before)
    assert hashlib.sha256(raw).hexdigest()==row['sha256']
    return raw

def relative(value):
    assert type(value) is str and value==Path(value).as_posix() and value and not Path(value).is_absolute()
    assert not any(part in ('.','..','__pycache__') for part in value.split('/'))
    return value

def portable_fixture(bundle,tmp_path):
    """Only copy an already materialized, hash-closed real profile export."""
    bundle=Path(bundle).resolve(strict=True);manifest_path=bundle/'manifest.json'
    assert manifest_path.is_file(),'portable checked fixture is not materialized; do not install these tests yet'
    assert manifest_path.resolve(strict=True)==manifest_path and manifest_path.stat().st_size<=8*1024*1024
    manifest=strict(manifest_path.read_bytes())
    assert set(manifest)=={'schema','entry','legacy_entry','files','origin_receipts'} and manifest['schema']=='checked-whole-portable-test-fixture-1'
    assert manifest['legacy_entry']['sha256']==LEGACY_SHA
    assert manifest['origin_receipts'],'a reviewed export of a genuinely prepared profile is required'
    project=(tmp_path/'project').resolve();project.mkdir();library=project/'library';library.mkdir();records=project/'records';records.mkdir()
    seen=set()
    for row in manifest['files']:
        assert set(row)=={'area','path','bytes','sha256'} and row['area'] in ('project','library','records','provenance')
        name=relative(row['path']);key=(row['area'],name);assert key not in seen;seen.add(key)
        assert row['area']!='project' or Path(name).parts[0] not in ('library','records','fixture-provenance')
        source=bundle/row['area']/name
        raw=physical(dict(path=str(source),bytes=row['bytes'],sha256=row['sha256']))
        base={'project':project,'library':library,'records':records,'provenance':project/'fixture-provenance'}[row['area']]
        destination=base/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(raw)
    for row in (manifest['entry'],manifest['legacy_entry']):
        assert set(row)=={'id','path','sha256'}
        path=library/relative(row['path']);assert path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256']
    for name in manifest['origin_receipts']:
        assert ('provenance',relative(name)) in seen
    return dict(project=project,library=library,records=records,manifest=manifest,
        entry=library/manifest['entry']['path'],legacy=library/manifest['legacy_entry']['path'],env={**QUIET,'SWDB_HOME':str(project)})

def actual_selection():
    assert os.environ.get('SWDB_DX100_WHOLE_CHECKED_ACTUAL')=='1','explicit root-selected integration profile required'
    assert not os.environ.get('PYTEST_XDIST_WORKER'),'actual 35-case profile is sequential'
    text=os.environ.get('SWDB_DX100_WHOLE_CHECKED_SELECTION')
    assert text,'root must select the exact physical actual-profile input pin'
    pin=strict(text);selection=strict(physical(pin))
    assert set(selection)=={'schema','profile','command_plan','root_admission','runtime'} and selection['schema']=='checked-whole-actual-selection-1'
    for name in ('root_admission','runtime'):physical(selection[name])
    return pin,selection,strict(physical(selection['profile'])),strict(physical(selection['command_plan']))

def verify_reports(record):
    result={};stable=lambda value:tuple(getattr(value,k) for k in ('st_dev','st_ino','st_mode','st_nlink','st_uid','st_gid','st_size','st_mtime_ns','st_ctime_ns'))
    for row in [record['evidence']['adapter_log'],*record['evidence'].get('reports',[])]:
        path=Path(row['path']);before=path.lstat()
        assert path.resolve(strict=True)==path and stat.S_ISREG(before.st_mode) and 0<=before.st_size<=128*1024*1024
        digest=hashlib.sha256();count=0
        with path.open('rb') as stream:
            for raw in iter(lambda:stream.read(65536),b''):count+=len(raw);assert count<=128*1024*1024;digest.update(raw)
        assert count==before.st_size and digest.hexdigest()==row['sha256'] and stable(path.lstat())==stable(before)
        if 'name' in row:result.setdefault(row['name'],[]).append(row)
    return result

def successful_native_outputs(reports):
    """A positive source proof must also have real successful native samples."""
    for name in ('differential_c_output','differential_cxx_output'):
        assert len(reports[name])==1
        row=reports[name][0];size=Path(row['path']).lstat().st_size
        raw=physical(dict(path=row['path'],bytes=size,sha256=row['sha256']))
        lines=raw.decode('utf-8').splitlines();assert lines
        assert all(line.startswith('run '+str(index)+':') and ' fail=' not in line and line.endswith(' end=done') for index,line in enumerate(lines))

CASES = ({'case_id': 'source-79', 'kind': 'SourceUnit', 'function': 'whole_interface_source_fixture', 'contract_id': 'contract.dx100_whole_source_79', 'expected_verdict': 'refuted'}, {'case_id': 'source-80', 'kind': 'SourceUnit', 'function': 'whole_interface_source_fixture', 'contract_id': 'contract.dx100_whole_source_80', 'expected_verdict': 'proven'}, {'case_id': 'whole_same_thread_read_during_store', 'kind': 'SourceUnit', 'function': 'whole_same_thread_read_during_store', 'contract_id': 'contract.dx100_whole_same_thread_read_during_store', 'expected_verdict': 'refuted'}, {'case_id': 'whole_same_thread_write_during_gather', 'kind': 'SourceUnit', 'function': 'whole_same_thread_write_during_gather', 'contract_id': 'contract.dx100_whole_same_thread_write_during_gather', 'expected_verdict': 'refuted'}, {'case_id': 'whole_same_thread_read_during_gather', 'kind': 'SourceUnit', 'function': 'whole_same_thread_read_during_gather', 'contract_id': 'contract.dx100_whole_same_thread_read_during_gather', 'expected_verdict': 'proven'}, {'case_id': 'finite-history_latest_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_history_latest_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-history_exact_issue_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_history_exact_issue_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-other_thread_cpu_read_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_other_thread_cpu_read_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-pending_store_cpu_read_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_pending_store_cpu_read_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-same_region_write_cover_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_same_region_write_cover_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-same_region_read_read_noncover_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_same_region_read_read_noncover_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-different_region_noncover_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_different_region_noncover_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-owned_tile_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_owned_tile_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-wrong_owner_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_wrong_owner_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-disjoint_owned_tiles_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_disjoint_owned_tiles_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-u64_second_half_conflict_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_u64_second_half_conflict_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-u32_disjoint_half_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_u32_disjoint_half_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-prior_cpu_store_visible_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_prior_cpu_store_visible_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-covered_store_next_thread_load_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_covered_store_next_thread_load_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-critical_end_wait_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_critical_end_wait_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-critical_end_without_wait_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_critical_end_without_wait_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-outside_critical_store_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_outside_critical_store_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-pending_read_lifetime_end_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_pending_read_lifetime_end_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-pair_owned_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_pair_owned_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-pair_wrong_owner_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_pair_wrong_owner_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-command_wrong_owner_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_command_wrong_owner_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-pair_command_half_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_pair_command_half_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-u32_command_half_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_u32_command_half_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-pair_cpu_half_read_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_pair_cpu_half_read_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-u32_cpu_half_read_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_u32_cpu_half_read_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-ready_relation_positive', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_ready_relation_positive', 'expected_verdict': 'proven'}, {'case_id': 'finite-ready_always_one_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_ready_always_one_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-ready_always_zero_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_ready_always_zero_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-ready_cpu_read_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_ready_cpu_read_negative', 'expected_verdict': 'refuted'}, {'case_id': 'finite-prior_cpu_store_old_value_negative', 'kind': 'TraceUnit', 'function': 'dwe_finite_trace', 'contract_id': 'contract.dx100_finite_prior_cpu_store_old_value_negative', 'expected_verdict': 'refuted'})
CASE_IDS = tuple(row["case_id"] for row in CASES)
