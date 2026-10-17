"""2026-10-16 ET. Namespace-only successor; no tools or dispatch."""
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RAW = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-memory-trace-04af74c1-v4'


def read(name, wanted=None):
    path = HERE / name
    if path.is_symlink() or not path.is_file(): raise ValueError('regular frozen controller required')
    data = path.read_bytes()
    if wanted is not None and hashlib.sha256(data).hexdigest() != wanted: raise ValueError('frozen namespace basis differs')
    return data


def prepare():
    old = read('linux_trace_entry_v2.py', 'd319185131bd708c57229fe16e269da6e6298d1afba3c057a8fcc0f89aa43c93').decode()
    anchor = "'probata-resume-20261016-t28-memory-trace-' + commit[:8] + '-v2'"
    if old.count(anchor) != 1: raise ValueError('one exact raw namespace comparison required')
    entry = old.replace(anchor, anchor.removesuffix("-v2'") + "-v4'", 1).replace(
        "raise ValueError('fresh V2 memory-trace raw namespace differs')", "raise ValueError('fresh V4 memory-trace raw namespace differs')", 1)
    entry_name = 'linux_trace_entry_v4.py'
    (HERE / entry_name).write_text(entry)
    policy = json.loads(read('linux_trace_policy_04af74c1_v3.json', '47629d9c974d9352f208764a2c93186da119b810b8750980461ac6de1600e214'))
    policy.update(raw_name=Path(RAW).name, status='INERT namespace V4; exact V3 source/runtime/25 criteria retained; root admission pending')
    policy['linux_launch_binding']['entry_sha256'] = hashlib.sha256(entry.encode()).hexdigest()
    policy_name = 'linux_trace_policy_04af74c1_v4.json'
    (HERE / policy_name).write_text(json.dumps(policy, sort_keys=True, indent=2) + '\n')
    command = json.loads(read('linux_trace_command_04af74c1_v3.json', 'c97559d11049d2a534332e5bfb8d1a877dbb8163597735cb0e3010b32c8c1d80'))
    command.update(raw_root=RAW, status='INERT namespace V4; original pretool V3 refusal preserved; independent review/root admission pending')
    command['argv'][7:] = [RAW + '/control/' + entry_name, command['source'], RAW,
                           RAW + '/control/' + policy_name, hashlib.sha256(read(policy_name)).hexdigest()]
    controls = copy.deepcopy(command['controller_inputs'])
    for row, name in zip(controls[:2], (entry_name, policy_name)):
        data = read(name)
        row.update(name=name, path=str(HERE / name), bytes=len(data), sha256=hashlib.sha256(data).hexdigest())
    command['controller_inputs'] = controls
    command['control_total_bytes'] = sum(row['bytes'] for row in controls)
    if len(controls) != 9 or command['control_total_bytes'] > 1048576: raise ValueError('closed staging cap differs')
    command['root_places_exact_controller_metadata'] = {'entry_remote': command['argv'][7], 'policy_remote': command['argv'][-2]}
    command_name = 'linux_trace_command_04af74c1_v4.json'
    (HERE / command_name).write_text(json.dumps(command, sort_keys=True, indent=2) + '\n')
    return {name: {'bytes': len(read(name)), 'sha256': hashlib.sha256(read(name)).hexdigest()}
            for name in (entry_name, policy_name, command_name)}


if __name__ == '__main__': print(json.dumps(prepare(), sort_keys=True, indent=2))
