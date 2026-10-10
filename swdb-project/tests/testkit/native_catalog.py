"""Minimal native contract records before source validation. 2026-10-09 ET.

Production history is not a fixture precondition. Every workflow step still
validates these real source/kernel records and the records it creates.
"""
import shutil

from conftest import REPO


def seed_native_contract_records(records, kernel='bfs'):
    implementation={'bfs':'gapbs-bfs-do','bc':'gapbs-bc-brandes'}[kernel]
    # BC's cross-kernel protocol refusal registers a real BFS graph, whose
    # kernel also requires its baseline implementation during validation.
    if kernel == 'bc':seed_native_contract_records(records)
    names=('applications/gapbs.yaml',f'kernels/gapbs-{kernel}.yaml',
           f'implementations/{implementation}.yaml','machines/mbit10.yaml')
    for name in names:
        path=records.path/name;path.parent.mkdir(parents=True,exist_ok=True)
        shutil.copyfile(REPO/'records'/name,path)
    data=records.read(f'implementations/{implementation}.yaml')
    if 'verification' in data:
        data['verification']={'status':'unchecked','evidence':[],'scope':'Isolated contract fixture.'}
        records.write(f'implementations/{implementation}.yaml',data)
