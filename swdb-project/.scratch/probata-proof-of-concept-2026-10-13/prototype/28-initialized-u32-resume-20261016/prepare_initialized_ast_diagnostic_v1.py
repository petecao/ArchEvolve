"""2026-10-16 ET. Pure exact V4 diagnostic-leaf authoring, never dispatch."""
import ast
import hashlib
import json
from pathlib import Path


HERE = Path(__file__).resolve().parent
BASE_ENTRY = '9a6246962ed8288829b609711c2fc3d77f436b9411de5bbad58148937895bf6d'
BASE_POLICY = '44b5746071fbbd5db6852e6fd27f14abfdb3216395f73b6c99f047729c8b2b35'
BASE_COMMAND = '39346b58d963edc9cd2a8e33da34b8cabcb10b649f004fc53e8ea79afc1cdfc1'
RAW = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-ast-diagnostic-2baf722f-v1'
FIXTURE = '/data/yanruj/EvolveSWDB_runs/probata-resume-20261016-t28-initialized-pair-2baf722f-v4/initialized-profile/pytest/test_actual_initialized_u32_or0/library'


def read(name, expected=None):
    data = (HERE / name).read_bytes()
    if expected is not None and hashlib.sha256(data).hexdigest() != expected:
        raise ValueError('exact reviewed V4 input changed: ' + name)
    return data


def replace_once(text, old, new):
    if text.count(old) != 1:
        raise ValueError('exact V4 diagnostic leaf anchor differs')
    return text.replace(old, new, 1)


def prepare():
    source = read('linux_pair_entry_v4.py', BASE_ENTRY).decode()
    policy = json.loads(read('linux_pair_policy_2baf722f_v4.json', BASE_POLICY))
    command = json.loads(read('linux_pair_command_2baf722f_v4.json', BASE_COMMAND))
    diagnostic = read('initialized_ast_diagnostic_v1.py')
    ast.parse(diagnostic)
    policy['raw_name'] = Path(RAW).name
    policy['controller_files']['initialized_ast_diagnostic_v1.py'] = {
        'bytes': len(diagnostic), 'sha256': hashlib.sha256(diagnostic).hexdigest()}
    policy['diagnostic_fixture'] = {'library': FIXTURE,
        'origin': 'Passive physical hashes of retained V4 positive fixture on 2026-10-16 ET; original files read-only',
        'files': {
            'proof_units/trust.cc': {'bytes': 309, 'sha256': '6d52feecbef298995433370c79ba01ef0f9d1dcf8727b771823ae94d304af479'},
            'proof_units/gem5/m5ops.h': {'bytes': 133, 'sha256': '4caae6752583fd058e911da16305fe5bebec0fa08d3242242af85494b2b90d7a'},
            'proof_semantics/dx100_bfs_0_1.yaml': {'bytes': 31989, 'sha256': '844da0f557adae447fbafd2617c86aa3f5a7fa475597ca9860c7e33b2f3cc84f'},
            'proof_semantics/dx100_trust_fixture.yaml': {'bytes': 18526, 'sha256': '0cb44dddc062ed63b3b754099902b823c84939348e9eaf32382e90471e421f03'},
            'rewrite_contracts/trust.yaml': {'bytes': 1562, 'sha256': '10fd6b4a86b05b2b180341902a7f45d073c053da306eca091ce66c471f1fa207'}}}
    policy['diagnostic_only'] = True
    policy['diagnostic_retention_cap_bytes'] = 67108864
    original_leaf = "command=['/bin/bash',str(project/'.scratch/probata-proof-of-concept-2026-10-13/prototype/28-initialized-u32-resume-20261016/run_initialized_register_acceptance.sh'),EXPECTED['source_commit'],'pair']"
    diagnostic_leaf = "profile.mkdir();(profile/'tmp').mkdir();(profile/'cache').mkdir()\ncommand=[sys.executable,'-B',str(output/'control/initialized_ast_diagnostic_v1.py'),str(project),str(profile),str(policy_path),sys.argv[4]]"
    source = replace_once(source, original_leaf, diagnostic_leaf)
    source = '"""DIAGNOSTIC ONLY: original source validation retained; no public test/proof/solver.\n"""\n' + source
    ast.parse(source)
    entry_path = HERE / 'linux_initialized_ast_diagnostic_entry_v1.py'
    entry_path.write_text(source)
    policy['linux_launch_binding']['entry_sha256'] = hashlib.sha256(source.encode()).hexdigest()
    policy_path = HERE / 'linux_initialized_ast_diagnostic_policy_v1.json'
    policy_path.write_text(json.dumps(policy, indent=2, sort_keys=True) + '\n')
    command['argv'][7] = RAW + '/control/' + entry_path.name
    command['argv'][9] = RAW
    command['argv'][-2] = RAW + '/control/' + policy_path.name
    command['argv'][-1] = hashlib.sha256(policy_path.read_bytes()).hexdigest()
    command.update(raw_root=RAW, status='INERT exact2baf compiler-observation retention diagnostic; root independent review/admission pending',
                   diagnostic_only=True, actual_pair_launched=False, proof_acceptance=False,
                   diagnostic_retention_cap_bytes=67108864)
    original = command['controller_inputs']
    stages = [entry_path, policy_path, *[Path(row['path']) for row in original[2:]], HERE / 'initialized_ast_diagnostic_v1.py']
    command['controller_inputs'] = [{'path': str(path), 'bytes': path.stat().st_size,
                                     'sha256': hashlib.sha256(path.read_bytes()).hexdigest()} for path in stages]
    if len(stages) != 7 or sum(row['bytes'] for row in command['controller_inputs']) > 1048576:
        raise ValueError('diagnostic seven-file controller exceeds root staging contract')
    command['root_places_exact_controller_metadata'] = {'entry_remote': command['argv'][7], 'policy_remote': command['argv'][-2]}
    command['diagnostic_scope'] = 'Only selected Clang subprocesses; pass-through original validation, no library validate/prove or WP/solver; AST/LLVM/preprocess retained only in new remote raw'
    (HERE / 'linux_initialized_ast_diagnostic_command_v1.json').write_text(json.dumps(command, indent=2, sort_keys=True) + '\n')


if __name__ == '__main__':
    prepare()
