#!/usr/bin/env python3
"""Bounded source/count/estimate report with complete setup accounting. 2026-10-06 ET."""
import argparse
import json
import runpy
from pathlib import Path
from swdb import access,artifacts


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--characterization',required=True,type=Path)
    parser.add_argument('--estimate',required=True,type=Path)
    parser.add_argument('--source-commit',required=True)
    parser.add_argument('--validate-log',type=Path)
    args=parser.parse_args()
    shared=runpy.run_path(str(Path(__file__).with_name('05-compact-reports.py')))
    source=access.read_record(args.characterization)
    estimated=access.read_record(args.estimate)
    application=shared['application'](args.characterization,args.estimate)
    if estimated['characterization_sha256']!=artifacts.digest(source):raise ValueError('estimate characterization hash differs')
    observation=source['observation_contract']
    if observation['level']!='functional_semantic_access':raise ValueError('requires functional-semantic execution counts')
    application['characterization']['observation_contract']=observation
    application['characterization']['toolchain']=source['toolchain']
    application['estimate']['parameter_report']=estimated['parameter_report']
    application['estimate']['count_reuse']=estimated.get('count_reuse')
    application['estimate']['verdict']=estimated['verdict']
    application['estimate']['error_band']=estimated['error_band']
    # The shared legacy formatter predates additive setup. Preserve every overhead
    # at both diagnostic-median and exact-trial scopes without dropping zero events.
    def overheads(row,original):
        row['overheads']=[{key:shared['compact'](bound[key]) for key in
            ('model','seconds','state','formula','inputs','missing','notes')} for bound in original['overheads']]
    aggregate={row['id']:row for row in estimated['regions']}
    for row in application['estimate']['regions']:overheads(row,aggregate[row['id']])
    trials={trial['position']:trial for trial in estimated.get('trials',[])}
    for trial in application['estimate']['trials']:
        rows={row['id']:row for row in trials[trial['position']]['regions']}
        for row in trial['regions']:overheads(row,rows[row['id']])
    result={'format':'swdb.functional-application-report.v1','updated':'2026-10-06 ET',
        'source_commit':args.source_commit,'evidence_kind':'functional_counts_plus_analytic_estimate',
        'scope':'Actual functional trial-lambda execution counts and source-only analytic scenarios; no physical DX100 or uninstrumented performance outcome.',
        'application':application}
    if args.validate_log:result['validation']={'file_sha256':access.record_hash(args.validate_log),'output':args.validate_log.read_text()}
    print(json.dumps(result,indent=2,allow_nan=False))


if __name__=='__main__':main()
