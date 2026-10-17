"""Offline inert templates. Null observations/ownership remain blocking inputs."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
WHOLE = HERE.parent
OUT = HERE / 'profile'


def save(name, value):
    (OUT / name).write_text(json.dumps(value, sort_keys=True, indent=2) + '\n')


request = json.loads((WHOLE / 'public-profile-builder-v1/selection-template-v1.json').read_bytes())
capture = json.loads((WHOLE / 'normalized-unit-envelope-v3/observation-policy-v1.json').read_bytes())['capture']
assert capture['prepared'] is None
request.update(ingress='reviewed-production-route-v4-normalized-complete-capture',
    original_project='/data1/yanruj/probata-resume-20261016-2baf722f/swdb-project',
    capture=capture, compiler_observation=capture['original']['observation'], choice_budget=256,
    proof_source={'root': 'library', 'path': 'proof_units/source.cpp',
                  'sha256': '3148b662b2fbeaa7a8733569d5ea750bce8a598d4e883f9bc64cb1e27dae67cd'})
tree = ast.parse((OUT / 'profile_builder_v3.py').read_bytes())
keys = ast.literal_eval(next(node.value for node in tree.body if isinstance(node, ast.Assign)
    and any(isinstance(t, ast.Name) and t.id == 'REQUEST_KEYS' for t in node.targets)))
assert set(request) == keys
save('selection-template-v4.json', request)
save('pair-selection-template-v4.json', json.loads((WHOLE / 'public-profile-builder-v1/pair-selection-template-v1.json').read_bytes()))
save('root-contract-v4.json', {'schema': 'dx100-public-profile-root-contract-4', 'date': '2026-10-16 ET',
    'state': 'INERT; complete source/ABI/call preparation and owned context have not been supplied',
    'source_base_commit': '1c45737f6cff9b43731d8da530be869a7e5d745e',
    'original_project': request['original_project'], 'producer_project': None,
    'producer_basis': {'path': str(OUT / 'normal-producer-basis-v4.json'),
        'sha256': hashlib.sha256((OUT / 'normal-producer-basis-v4.json').read_bytes()).hexdigest()},
    'request_schema_exact_keys': sorted(keys),
    'preparation': [
        'root independently reviews and publishes the coherent patch with fresh matching producer/method identities',
        'root admits complete first-stream observation and stages its exact preparation and derived ABI observation',
        'root stages a fresh library with the captured first-source buffer and exact 3258-byte memory source as data',
        'root selects the original 2baf project separately from the published producer project/runtime',
        'derive repeats complete capture/source/ABI/statements/model checks and emits a non-owning context request',
        'root owns and stages exact physical runtime/mapping/context/compiler/numeric and owner-rule receipts',
        'globals binds all twelve original source static-global observations after the owned context digest exists',
        'root selects the exact receiver policy and stages all of its bound inputs',
        'assemble repeats derivation and receiver checks, emits the five contracts and closed four-unit registry',
        'root validates and admits both explicit-method public plans sequentially under fresh Linux guards',
        'root cold-audits persisted scientific criteria and finite settled source/runtime/cleanup observations'],
    'owned_receipts_never_emitted': ['mapping_receipt', 'runtime_receipt', 'context_receipt', 'owned_rules_receipt'],
    'memory_rows': {'state': 'explicitly unsupported capture; no prepared or owned receiver data',
        'source': {'path': 'proof_units/same_thread_memory_v1.cpp', 'bytes': 3258,
                   'sha256': '55b9fe4033e80c4c151a743744ccf745082ada5e408aaa782d6ccbb30d88d887'},
        'unready_portable_receiver_field_is_typed_data_not_a_receiver_policy': True},
    'actual_executed': False, 'public_admission': False, 'whole_ticket28_acceptance': False})
print(json.dumps({'templates': 3, 'actual_preparation_or_owned_receipts_created': False}))
