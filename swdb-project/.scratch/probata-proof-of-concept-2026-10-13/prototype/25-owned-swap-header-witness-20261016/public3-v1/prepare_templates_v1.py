"""2026-10-16 ET. Inert witness3 source templates; no Git/project/tool execution."""
import ast
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
POC = HERE.parents[2]
OLD = POC/'prototype/25-owned-swap-header-cases-20261016/public3-v1'


def pin(path):
    raw = path.read_bytes()
    return {'path': str(path), 'bytes': len(raw), 'sha256': hashlib.sha256(raw).hexdigest()}


def write(path, raw):
    with path.open('xb') as stream:
        stream.write(raw)


def document(path, value):
    write(path, (json.dumps(value, sort_keys=True, indent=2, allow_nan=False)+'\n').encode())


def derive(basis, output, changes):
    before = basis.read_text(); current = before; rows = []
    for old, new in changes:
        count = current.count(old)
        if count < 1:
            raise ValueError('exact predecessor source substitution missing: '+old)
        rows.append({'before': old, 'after': new, 'count': count})
        current = current.replace(old, new)
    inverse = current
    for row in reversed(rows):
        if inverse.count(row['after']) != row['count']:
            raise ValueError('ambiguous full source inverse')
        inverse = inverse.replace(row['after'], row['before'])
    if inverse != before:
        raise ValueError('entire predecessor source inverse differs')
    ast.parse(current)
    write(output, current.encode())
    return {'predecessor': pin(basis), 'output': pin(output),
            'replacements': rows, 'full_inverse_exact': True}


def main():
    entry = derive(OLD/'entry_template.py', HERE/'entry_template.py', [
        ('Inert standalone three-case swap ready-header mathematical normal-WP profile',
         'Inert standalone constructive-witness swap ready-header mathematical normal-WP profile'),
        ('owned-swap-header-cases', 'owned-swap-header-witness'),
        ('reviewed three-case swap header source expectation bytes differ',
         'reviewed constructive-witness swap header source expectation bytes differ'),
        ('vector_owned_swap_header_cases as packets', 'vector_owned_swap_header_witness as packets'),
        ('Standalone conditional swap ready-header three-case native mathematical profile.',
         'Standalone conditional constructive-witness swap ready-header native mathematical profile.'),
        ('wp-owned-swap-header3-v1.yaml', 'wp-owned-swap-header-witness3-v1.yaml'),
        ('Three fresh producer outcomes retained.', 'Three fresh stronger-witness producer outcomes retained.'),
        ("    return manifest\n\n\ndef normal_task_census", "    reconstruction = manifest['reconstruction']\n"
         "    if reconstruction['all_three_stronger_proofs_required'] is not True or \\\n"
         "            reconstruction['reverse_implication_claimed'] or reconstruction['self_swap_excluded'] or \\\n"
         "            reconstruction['added_premises'] or reconstruction['axioms_added']:\n"
         "        raise ValueError('complete stronger-witness sufficient-rule boundary differs')\n"
         "    for row in rows:\n"
         "        recovery = row['existential_introduction']\n"
         "        if recovery['bound_variable_capture'] or not recovery['full_statement_inverse_checked'] or \\\n"
         "                not recovery['witness_sorts_checked_against_bound_source'] or \\\n"
         "                not recovery['instance_to_existential_is_sufficient']:\n"
         "            raise ValueError('typed capture-free existential recovery differs')\n"
         "    return manifest\n\n\ndef normal_task_census")])
    author = derive(OLD/'prepare.py', HERE/'prepare.py', [
        ('Author inert Header3 entry and sparse source using Git/stdlib.',
         'Materialize inert witness3 entry and sparse source from a separately published Git source.'),
        ('SOURCE = sys.argv[1]\nassert len(SOURCE) == 40 and set(SOURCE) <= set(\'0123456789abcdef\')',
         "SOURCE = sys.argv[1] if len(sys.argv) == 2 else None\n"
         "if SOURCE is None or len(SOURCE) != 40 or set(SOURCE) - set('0123456789abcdef'):\n"
         "    raise ValueError('a separately published exact forty-hex source commit is required before materialization')"),
        ("PREVIOUS = POC/'prototype/25-owned-swap-parts-20261016/public13-v1/inert-a102e275-public13-v1'",
         "PREVIOUS = POC/'prototype/25-owned-swap-header-cases-20261016/public3-v1/inert-abb598a4-public3-v1'"),
        ('owned-swap-header3', 'owned-swap-header-witness3'),
        ("source_packet['inputs']", "source_packet['source_inputs']"),
        ('len(physical) == 45', 'len(physical) == 48'),
        ('Three exhaustive owner cases of the unchanged universal ready-header duty under its complete original antecedent.',
         'Three stronger explicit-witness owner cases sufficient for the unchanged universal ready-header duty under its complete original antecedent; all existential recovery and source binding remain separately pending.'),
        ('complete_canonical_files=45', 'complete_canonical_files=48'),
        ("('owned-swap13-public-root-early-preflight.json', 'owned-swap-header-witness3-public-root-early-preflight.json')",
         "('owned-swap-header3-public-root-early-preflight.json', 'owned-swap-header-witness3-public-root-early-preflight.json')"),
        ("('owned-swap13-public-v1', 'owned-swap-header-witness3-public-v1')",
         "('owned-swap-header3-public-v1', 'owned-swap-header-witness3-public-v1')"),
        ('isolated-shared-sparse-header3-v1', 'isolated-shared-sparse-header-witness3-v1'),
        ("'canonical_files': 45", "'canonical_files': 48")])
    def functions(path):
        return {node.name: ast.dump(node, include_attributes=False)
                for node in ast.parse(path.read_bytes()).body if isinstance(node, ast.FunctionDef)}
    old_functions = functions(OLD/'entry_template.py')
    new_functions = functions(HERE/'entry_template.py')
    changed = [name for name in old_functions if old_functions[name] != new_functions[name]]
    if changed != ['canonical_check', 'main'] or len(old_functions)-len(changed) != 18:
        raise ValueError('the complete eighteen inherited normal helpers must stay exact')
    document(HERE/'template-inverses-v1.json', {'date': '2026-10-16 ET',
        'entry': entry, 'author': author, 'changed_entry_function_asts': changed,
        'identical_entry_function_asts': [name for name in old_functions if name not in changed],
        'no_shared_source_theory_or_actual_dispatch_change': True})
    document(HERE/'pending-source-selection-v1.json', {'date': '2026-10-16 ET',
        'status': 'inert templates; source not yet published', 'source_commit': None,
        'remote_project': None, 'source_package_inventory': None, 'source_consumer_oids': None,
        'sparse_projection_files': None, 'sparse_projection_bytes': None,
        'source_mount_floor_bytes': 10*1024**3, 'source_metadata_headroom_bytes': 1024**3,
        'node': None, 'preferred_node_if_freshly_free': 1,
        'resource_policy': json.loads((OLD/'inert-abb598a4-public3-v1/expected.json').read_bytes())['resource_policy'],
        'root_launcher_basis': pin(POC/'prototype/resume-root-20261016/launch_reviewed_main_v10.py'),
        'source_module': 'swdb.vector_owned_swap_header_witness',
        'method_id': 'method.wp-owned-swap-header-witness3-v1',
        'targets': 3, 'canonical_files': 48, 'C_layout_only_units': 0,
        'actual_expected_command_launcher_unmaterialized': True,
        'publication_root_review_and_once_admission_required': True,
        'old_G644_refusals_and_all_existing_clones_and_raw_preserved': True,
        'actual_formal_run': False, 'scientific_source_caller_acceptance': False})
    print(json.dumps({'entry_template': pin(HERE/'entry_template.py'),
        'prospective_author': pin(HERE/'prepare.py'), 'inherited_normal_helpers': 18,
        'published_source': None, 'actual_dispatch': False}))


if __name__ == '__main__':
    main()
