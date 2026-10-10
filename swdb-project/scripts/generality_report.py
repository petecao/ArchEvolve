#!/usr/bin/env python3
"""Pinned nine-pair per-region analytic reports. Created: 2026-10-06 ET."""
import argparse
import copy
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from swdb import access,artifacts
from swdb.estimate_protocol import estimator_identity

MATRIX={(kernel,target) for kernel in ('bfs','bc','pagerank') for target in ('cpu','dx100','maple')}
THREADS={'cpu':1,'dx100':4,'maple':2}
TARGETS={'cpu':'mbit10','dx100':'dx100-e4fc4af-functional-analytic-v1','maple':'maple-isca2022'}
JACOBI_SHA='ea1e58b6957b0bcc1e76f4fde54131aa52bdefd2014dae604a9b7d9d1a5dae70'


def pinned(records,reference,kind):
    relative=Path(reference['path'])
    path=(records/relative).resolve()
    if relative.is_absolute() or records.resolve() not in path.parents:
        raise ValueError('record reference leaves copied records')
    data=access.read_record(path)
    if data.get('kind')!=kind or data.get('id')!=reference['id'] or artifacts.digest(data)!=reference['sha256']:
        raise ValueError('record kind, identity or content pin changed')
    return data


def regions(rows,aggregate=False):
    result=copy.deepcopy(rows)
    for row in result:
        row['inputs_scope']='diagnostic aggregate; exact inputs are in trials' if aggregate else 'this exact trial'
    return result


def create_report(records,request):
    if request.get('format')!='swdb.generality-report-request.v1' or request.get('identity_sha256')!=artifacts.digest({k:v for k,v in request.items() if k!='identity_sha256'}):
        raise ValueError('request format or seal changed')
    pairs=request['pairs']
    keys=[(row['kernel'],row['target']) for row in pairs]
    if len(keys)!=9 or set(keys)!=MATRIX:
        raise ValueError('requires exactly nine unique kernel-target pairs')
    if request['reference']!={'kernel':'bfs','target':'dx100'}:
        raise ValueError('requires a fresh DX BFS reference')
    bundle=estimator_identity();output=[]
    for pair in pairs:
        kernel=pair['kernel'];target=pair['target'];threads=THREADS[target]
        estimate=pinned(records,pair['estimate'],'estimate')
        char=pinned(records,pair['characterization'],'workload_characterization')
        protocol=pinned(records,pair['protocol'],'protocol')
        subject=pinned(records,pair['subject'],char['subject']['kind'])
        implementation=pinned(records,pair['implementation'],'implementation')
        if estimate.get('basis')!='estimated' or estimate['estimator_sha256']!=bundle or protocol['settings']['estimator_sha256']!=bundle:
            raise ValueError('all estimates and protocols must share the current complete estimator bundle')
        if estimate['characterization']!=char['id'] or estimate['characterization_sha256']!=pair['characterization']['sha256'] or estimate['protocol']!=protocol['id'] or estimate['protocol_sha256']!=protocol['identity_sha256']:
            raise ValueError('estimate characterization or protocol binding changed')
        if char.get('evidence_kind')!='execution' or char['binding']['state']!='verified' or char['coverage']['whole_timed_call'] is not True:
            raise ValueError('requires registered whole-call execution counts')
        if protocol.get('state')!='frozen' or protocol['settings']['mode']!='estimated':
            raise ValueError('requires a frozen estimated protocol')
        if estimate['subject']!=char['subject'] or char['subject']['id']!=subject['id'] or (subject['kind']=='candidate' and subject['implementation']!=implementation['id']) or (subject['kind']=='implementation' and subject['id']!=implementation['id']):
            raise ValueError('subject-source binding changed')
        expected_kernel='gapbs-pr' if kernel=='pagerank' else 'gapbs-'+kernel
        if implementation['kernel']!=expected_kernel:
            raise ValueError('kernel source registration differs')
        if kernel=='pagerank' and (implementation['id']!='gapbs-pr-jacobi-analytic-v1' or char['source']['sha256']!=JACOBI_SHA):
            raise ValueError('requires the registered original Jacobi source')
        settings=protocol['settings'];td=estimate['target_description_snapshot']
        if any(value!=threads for value in [estimate['threads'],char['binding']['threads'],settings['threads'],td['threads']]) or td['target']!=TARGETS[target]:
            raise ValueError('target or thread scope differs')
        if artifacts.digest(settings['target_description']['snapshot'])!=estimate['target_description_sha256'] or artifacts.digest(td)!=estimate['target_description_sha256'] or settings['target_description']['sha256']!=estimate['target_description_sha256']:
            raise ValueError('target snapshot binding changed')
        if estimate['input']!=char['input'] or char['input'] not in settings['inputs'] or settings['roi']!=char['binding']['roi'] or settings['input_run_arguments'][char['input']]!=char['source']['run_arguments']:
            raise ValueError('input, ROI or run-argument scope differs')
        if [(trial['position'],trial['sources']) for trial in estimate['trials']]!=[(trial['position'],trial['sources']) for trial in char['trials']]:
            raise ValueError('trial identities differ')
        ext=td.get('extensions',{})
        if target=='maple' and (ext.get('estimate_only') is not True or ext.get('accuracy_validation') is not False or ext.get('paired_timing') is not None):
            raise ValueError('MAPLE requires estimate-only scope without paired timing')
        if kernel=='pagerank' and target=='cpu' and estimate['error_band'] is not None:
            raise ValueError('Jacobi has no BF/BC CPU error-band admission')
        output.append({'kernel':kernel,'target':target,'threads':threads,'roi':settings['roi'],'input':char['input'],
            'references':{key:pair[key] for key in ('subject','implementation','characterization','protocol','estimate')},
            'source_sha256':char['source']['sha256'],'estimate_only':target=='maple','accuracy_validation':False,
            'paired_timing':None,'seconds':estimate['seconds'],'ratio':estimate['ratio'],'error_band':estimate['error_band'],
            'regions':regions(estimate['regions'],aggregate=True),
            'trials':[{**trial,'regions':regions(trial['regions'])} for trial in estimate['trials']],
            'unmapped_loops':char['unmapped_loops'],'notes':estimate.get('notes',[])})
    modules={p.relative_to(ROOT/'swdb').as_posix():artifacts.file_hash(p) for p in sorted((ROOT/'swdb').rglob('*.py'))}
    report={'format':'swdb.generality-report.v1','updated':request['updated'],'scope':request['scope'],
        'request_sha256':request['identity_sha256'],'reference':request['reference'],
        'code_equality':{'estimator_sha256':bundle,'module_hashes':modules,'estimator_and_mechanism_diff':[]},
        'whole_call_scope':'Median of complete trial totals; aggregate region diagnostics are never summed.',
        'pairs':output}
    report['identity_sha256']=artifacts.digest(report)
    return report


def markdown(report):
    lines=['# Nine-pair generality report','','Updated: '+report['updated'],'',report['scope'],'',
        '| Kernel | Target | T | Whole-call seconds | Ratio | Scope |','|---|---|---:|---:|---:|---|']
    for row in report['pairs']:
        seconds='unknown' if row['seconds'] is None else str(row['seconds'])
        ratio='unknown' if row['ratio'] is None else str(row['ratio'])
        lines.append(f"| {row['kernel']} | {'MAPLE' if row['target']=='maple' else row['target']} | {row['threads']} | {seconds} | {ratio} | {'estimate-only; no paired timing' if row['estimate_only'] else 'counted scope; see exact missing facts'} |")
    lines+=['','All per-region bounds, overheads, unknowns and exact trial inputs are in report.json. Aggregate regions are diagnostic medians.',
            '',f"Complete estimator bundle: `{report['code_equality']['estimator_sha256']}`; estimator/mechanism diff is empty.",
            '', 'Jacobi has no CPU error-envelope transfer from the four admitted BF/BC characterizations. MAPLE has no accuracy-validation or paired-timing claim.']
    return '\n'.join(lines)+'\n'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--records',required=True,type=Path);parser.add_argument('--request',required=True,type=Path)
    parser.add_argument('--output',required=True,type=Path);args=parser.parse_args()
    try:
        report=create_report(args.records,json.loads(args.request.read_text()))
        text=json.dumps(report,indent=2,ensure_ascii=False,allow_nan=False)+'\n';md=markdown(report)
        args.output.mkdir(parents=True,exist_ok=False)
        (args.output/'report.json').write_text(text);(args.output/'report.md').write_text(md)
    except (ValueError,KeyError,OSError,TypeError) as exc:
        print(str(exc),file=sys.stderr);return 2
    return 0


if __name__=='__main__':raise SystemExit(main())
