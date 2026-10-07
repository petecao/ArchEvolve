"""Independent bulk service construction public seams, 2026-10-06 ET."""
import json
import subprocess
import sys

from conftest import run_swdb


def run_bulk(records,*args):
    return subprocess.run([sys.executable,'-m','swdb.cpu_bulk_calibration','--records',str(records.path),
        *map(str,args)],capture_output=True,text=True,timeout=150)


def test_portable_bulk_cells_retain_separate_alias_regimes_and_exact_sizes(records,tmp_path):
    output=tmp_path/'bulk'
    result=run_bulk(records,'--output',output,'--fixture','--size',8,'--size',292,
        '--repetitions',3,'--min-trial-s',.002,'--max-wall-s',90)
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((output/'receipt.json').read_text())
    assert raw['evidence_kind']=='fixture' and raw['threads']==1
    scopes=[(s['scope']['event_abi'],s['scope']['size_bytes'],s['scope']['bulk_regime']) for s in raw['services']]
    assert set(scopes)=={('memcpy',8,'constant8_noalias_align8')}|{('memmove',n,r) for n in (8,292)
        for r in ('dynamic_length_disjoint_align4','dynamic_length_overlap_forward4_align4','dynamic_length_overlap_backward4_align4')}
    assert len(scopes)==7
    assert all(s['scope']['transfer_basis']=='inferred' and len(s['trials'])==3 for s in raw['services'])
    assert all(t['events']>0 and t['gross_seconds']>0 and t['driver_seconds']>0 for s in raw['services'] for t in s['trials'])
    imported=run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',output/'receipt.json',
        '--id','fixture.bulk.cost','--fixture','--format','json')
    assert imported.returncode==0,imported.stderr+imported.stdout
    assert all(s['parameter']['basis'] in ('reported','unknown') for s in json.loads(imported.stdout)['services'])
    assert records.validate().returncode==0
    refused=run_bulk(records,'--output',tmp_path/'oversized','--fixture','--size',1048577)
    assert refused.returncode!=0 and not (tmp_path/'oversized').exists()


def test_counted_bulk_matrix_proves_every_exact_bin_and_regime_without_timing(records,tmp_path,llvm22):
    records.copy_repo('applications','kernels','implementations','inputs','machines','profiles','hardware_targets','strategies','operations','intrinsics')
    output=tmp_path/'proof'
    result=run_bulk(records,'--output',output,'--fixture','--count-only','--llvm-bin',llvm22,
        '--size',8,'--size',292,'--max-wall-s',120)
    assert result.returncode==0,result.stderr+result.stdout
    raw=json.loads((output/'count-proof.json').read_text())
    assert raw['timings_collected'] is False and not (output/'receipt.json').exists()
    proof=raw['count_proof'];assert len(proof['points'])==4
    assert proof['pipeline']['version']=='source-normalized-v2'
    for point in proof['points']:
        assert len(point['cells'])==7
        assert all(c['executions']==(point['events'] if point['invoke'] else 0) for c in point['cells'])
        assert all(len(c['source_sites'])==1 for c in point['cells'])
        assert {s['helper_function'] for s in point['source_sites']}=={'bulk_copy8','bulk_move_disjoint','bulk_move_forward','bulk_move_backward'}
    assert raw['context']['optimized_work']['retained']['bulk_copy8']=='constant8_word_load_store'
    assert len(set(p['characterization_sha256'] for p in proof['points']))==4


from testkit.cpu_bulk import native_bulk_receipt


def test_native_bulk_import_requires_full_exact_matrix_and_preserves_unresolved_subtraction(records,tmp_path):
    import copy
    from swdb.cpu_service_calibration import identity
    records.copy_repo('machines')
    def ingest(raw,key):
        raw['identity_sha256']=identity(raw);path=tmp_path/(key+'.json');path.write_text(json.dumps(raw))
        return run_swdb('import-cpu-service-calibration','--records',records.path,'--receipt',path,'--id',key,'--format','json')
    raw=native_bulk_receipt()
    result=ingest(raw,'synthetic.bulk.accepted')
    assert result.returncode==0,result.stderr+result.stdout
    assert records.validate().returncode==0
    missing=copy.deepcopy(raw)
    for s in missing['services']:s['denominator']['proof']['points'][0]['cells'].pop()
    wrong=copy.deepcopy(raw);wrong['services'][1]['scope']['bulk_regime']='application_nonoverlap'
    elided=copy.deepcopy(raw);elided['context']['optimized_work']['retained'].pop('bulk_move_forward')
    unchecked=copy.deepcopy(raw);unchecked['services'][0]['trials'][0]['checked_one_copy']=False
    short=copy.deepcopy(raw);short['services'][0]['trials'][0]['driver_seconds']=.001
    for i,data in enumerate((missing,wrong,elided,unchecked,short)):
        refused=ingest(data,'synthetic.bulk.invalid.'+str(i));assert refused.returncode!=0
    unresolved=copy.deepcopy(raw);unresolved['services'][1]['trials'][0]['driver_seconds']=.2
    kept=ingest(unresolved,'synthetic.bulk.unresolved')
    assert kept.returncode==0,kept.stderr+kept.stdout
    service=json.loads(kept.stdout)['services'][1]
    assert service['parameter']['value'] is None and service['seconds_per_event']['min']<0
