"""Prospective accepted-pins assembler, prepared 2026-10-07 ET.

Future execution requires a separately parent-reviewed, original-byte-pinned
specification of real receipts/records. This program constructs metadata only;
it never invokes a campaign, provider, collector, selected reader or auditor.
Sealed custody establishes bytes and declared provenance, not study admission.
"""
import argparse
import datetime
import hashlib
import json
import math
import os
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
import time

import yaml

sys.dont_write_bytecode = True
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
AUDITOR = '6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da'
COLLECTOR = 'b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'
PLAN = 'e3420b334ce05f7268699b0079987d1d2afc98fe5cb5503e6069a89038b59170'
CONTRACT = '192eb5d1c2b461f9d42b3532a934c8dc107bb193f29fabbb5ba2dec94acd2978'
EVIDENCE = 'swdb-project/.scratch/lanl-db-analytic-eval-2026-10-06/evidence/'
CIDS = tuple('extensa-gem5-bfs-20261006-p' + str(i) for i in range(1, 5))
MAX_FILE = 32 * 1024 * 1024
MAX_SPEC = 8 * 1024 * 1024
MAX_TOTAL = 512 * 1024 * 1024
MAX_DOCUMENTS = 4096

# Original canonical policies come from pinned writers, not pretty-print output.
KNOWN_WRITERS = {
    'helper28d': ('28d116bede7ab1232a42d24a24565a8ff1db36fca0ce36a2835012db77e2c414', True),
    'supervisorfa703': ('fa703bbd4c71bb4bcf56f47d1e224449f627d5921295e00b9cc105f21e95bde0', False),
    'guard9c5d': ('9c5d9658b524db94805a6b51453dc9edef7096a27312677896d595d39b94f6c6', False),
    'collectorb08': (COLLECTOR, True),
    'cpu_reader8b': ('8b85e34287a4dc67e5ff0c9a535aefd46a6c2ecf6051a934607f853074f90016', True),
    'cpu_export1d1251': ('1d1251baeba12c65c40a7a616060e5ff236197ce73f77335534d4a4d83fe32a6', True),
    'generality_digest_b797': ('b797a19f0d80a1a91b852a360c19e59beba4fa082ce88c38cbec029670e7deda', True),
}
SEALED_ROLES = {
    'manifest_M2', 'freeze_receipt', 'agreement_receipt', 'prepare_supervisor', 'finalize_supervisor',
    'prepare_preregistration', 'finalize_preregistration', 'freeze_publication',
    'ticket11_admission', 'ticket11_export_receipt', 'ticket14_admission', 'ticket14_export_receipt',
    'attempt_before', 'attempt_after', 'attempt_dispatch', 'attempt_stopped', 'attempt_release',
    'dispatch_state_corroboration', 'unclean_resume', 'trajectory_projection', 'outcome_refusal',
    'interrupted_selected_bodies', 'public_candidate_selection',
}
KNOWN_ROLE_FAMILIES = {
    'manifest_M2': 'helper28d', 'freeze_receipt': 'helper28d', 'agreement_receipt': 'helper28d',
    'attempt_dispatch': 'helper28d', 'attempt_stopped': 'helper28d',
    'prepare_supervisor': 'supervisorfa703', 'finalize_supervisor': 'supervisorfa703',
    'prepare_preregistration': 'guard9c5d', 'finalize_preregistration': 'guard9c5d',
    'attempt_before': 'collectorb08', 'attempt_after': 'collectorb08',
    'ticket11_admission': 'cpu_reader8b', 'ticket11_export_receipt': 'cpu_export1d1251',
    'ticket14_admission': 'generality_reader', 'ticket14_export_receipt': 'generality_export',
    'freeze_publication': 'parent_capture', 'dispatch_state_corroboration': 'parent_capture',
    'attempt_release': 'parent_capture', 'unclean_resume': 'parent_capture',
    'trajectory_projection': 'parent_capture', 'outcome_refusal': 'parent_capture',
    'interrupted_selected_bodies': 'parent_capture', 'public_candidate_selection': 'parent_capture',
}
ROOT_FIELDS = {
    'freeze_export', 'report_export', 'manifest_M2', 'policy_id', 'report_id',
    'prepare_supervisor', 'finalize_supervisor', 'prepare_preregistration', 'finalize_preregistration',
    'freeze_publication_custody', 'final_ticket11_acceptance', 'final_ticket14_acceptance',
    'collector_source_pin', 'collector_account', 'selected_records', 'campaigns',
}

class Refused(ValueError):
    pass

def require(condition, code):
    if not condition:
        raise Refused(code)

def hash_bytes(raw):
    return hashlib.sha256(raw).hexdigest()

def canonical(value, ensure_ascii):
    require(type(ensure_ascii) is bool, 'original_canonical_policy_not_boolean')
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False,
                      ensure_ascii=ensure_ascii).encode()

def digest(value, ensure_ascii):
    return hash_bytes(canonical(value, ensure_ascii))

def hex_value(value, length):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value), 'full_hash_required')
    return value

def token(value):
    require(isinstance(value, str) and len(value) <= 256 and re.fullmatch('[A-Za-z0-9_.:-]+', value), 'public_token_required')
    return value

def strict_json(raw):
    def pairs(rows):
        out = {}
        for key, value in rows:
            require(key not in out, 'duplicate_json_key')
            out[key] = value
        return out
    def invalid_constant(_):
        raise Refused('nonfinite_json_constant')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant)

def original_seal(value, identity, policy):
    hex_value(identity, 64)
    require(value.get('identity_sha256') == identity, 'original_compact_identity_differs')
    require(digest({k: v for k, v in value.items() if k != 'identity_sha256'}, policy) == identity,
            'original_compact_seal_differs')

def local_path(text, directory=False):
    p = Path(text)
    require(p.is_absolute() and '..' not in p.parts, 'absolute_original_path_required')
    require(all(not x.is_symlink() for x in (p, *p.parents)), 'symlink_component_refused')
    p = p.resolve(strict=True)
    require(p.is_dir() if directory else stat.S_ISREG(p.stat().st_mode), 'original_regular_path_required')
    return p

def git_path(text):
    p = PurePosixPath(text)
    require(isinstance(text, str) and p.as_posix() == text and not p.is_absolute() and
            '..' not in p.parts and '\\' not in text and text.startswith('swdb-project/'), 'safe_swdb_git_path_required')
    return text

class OriginalLoader(getattr(yaml, 'CSafeLoader', yaml.SafeLoader)):
    pass

OriginalLoader.yaml_implicit_resolvers={first:[(tag,regexp) for tag,regexp in rows if tag!='tag:yaml.org,2002:timestamp'] for first,rows in OriginalLoader.yaml_implicit_resolvers.items()}

def unique_yaml(loader, node, deep=False):
    out = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        require(key not in out, 'duplicate_original_yaml_key')
        out[key] = loader.construct_object(value_node, deep=deep)
    return out

OriginalLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_yaml)

class Originals:
    def __init__(self, repository, refs, documents, deadline_seconds):
        self.repository, self.refs, self.documents = repository, refs, documents
        self.pins, self.values, self.raw_hashes, self.trees = {}, {}, {}, {}
        self.total = 0
        self.deadline = time.monotonic() + deadline_seconds
        require(isinstance(documents, dict) and 0 < len(documents) <= MAX_DOCUMENTS, 'bounded_original_inventory_required')

    def remaining(self):
        value = self.deadline - time.monotonic()
        require(value > 0, 'bounded_metadata_deadline_exceeded')
        return value

    def git(self, *args):
        # Local Git only; do not permit environment redirects, lazy network fetch,
        # pager, filters, text conversion, external diff or a command from input.
        env = {k: v for k, v in os.environ.items() if not k.startswith('GIT_')}
        env.update(GIT_NO_LAZY_FETCH='1', GIT_TERMINAL_PROMPT='0', GIT_OPTIONAL_LOCKS='0', GIT_PAGER='cat')
        return subprocess.check_output(['git', '-c', 'protocol.allow=never', '-c', 'core.fsmonitor=false',
                                        '-C', str(self.repository), *args],
                                       timeout=min(60, self.remaining()), env=env)

    def tree(self, ref):
        require(ref in self.refs, 'unapproved_git_reference')
        if ref not in self.trees:
            self.trees[ref] = {row.split(b'\t', 1)[1].decode(): row.split(b'\t', 1)[0].decode()
                              for row in self.git('ls-tree', '-r', '-z', ref).split(b'\0') if row}
        return self.trees[ref]

    def raw(self, pin):
        self.remaining()
        size = pin['bytes']; hex_value(pin['sha256'], 64)
        require(type(size) is int and 0 <= size <= MAX_FILE, 'bounded_original_file_required')
        if 'commit' in pin:
            require(pin['commit'] in self.refs, 'unapproved_original_git_ref')
            path = git_path(pin['path'])
            mode = self.tree(pin['commit']).get(path, '').split()
            require(len(mode) == 3 and mode[0] in ('100644', '100755') and mode[1] == 'blob', 'original_git_regular_blob_required')
            require(int(self.git('cat-file', '-s', pin['commit'] + ':' + path)) == size, 'original_git_size_differs')
            raw = self.git('cat-file', 'blob', pin['commit'] + ':' + path)
        else:
            p = local_path(pin['path']); require(p.stat().st_size == size, 'original_local_size_differs')
            raw = p.read_bytes()
        require(len(raw) == size and hash_bytes(raw) == pin['sha256'], 'original_file_bytes_differ')
        return raw

    def pin(self, alias):
        token(alias)
        require(alias in self.documents, 'original_document_missing')
        if alias in self.pins:
            return dict(self.pins[alias])
        desc = self.documents[alias]
        require(set(desc) <= {'role', 'origin', 'bytes', 'sha256', 'identity_sha256', 'canonical_ensure_ascii',
                             'expected_format', 'writer', 'id', 'kind', 'record_sha256'}, 'undeclared_original_metadata_refused')
        role = desc['role']
        require(role in SEALED_ROLES | {'control_source', 'selected_record', 'original_unsealed_campaign_export'},
                'raw_state_provider_prompt_auth_log_or_binary_not_an_input_role')
        origin = desc['origin']; require(set(origin) in ({'path'}, {'path', 'commit'}), 'explicit_original_origin_required')
        pin = {**origin, 'bytes': desc['bytes'], 'sha256': desc['sha256']}
        raw = self.raw(pin); self.total += len(raw)
        require(self.total <= MAX_TOTAL, 'selected_input_total_budget_exceeded')
        # Register before checking writer-source references; writer/control source
        # dependency cycles cannot turn a receipt into another source role.
        self.pins[alias] = pin; self.raw_hashes[alias] = hash_bytes(raw)
        if role in SEALED_ROLES:
            require(type(desc['canonical_ensure_ascii']) is bool, 'explicit_original_canonical_policy_required')
            pin.update(identity_sha256=hex_value(desc['identity_sha256'], 64), canonical_ensure_ascii=desc['canonical_ensure_ascii'])
            value = strict_json(raw); original_seal(value, pin['identity_sha256'], pin['canonical_ensure_ascii'])
            expected_format = desc['expected_format']
            if expected_format is None:
                require(role == 'manifest_M2' and 'format' not in value, 'original_format_absence_must_be_explicit_manifest_only')
            else:
                require(isinstance(expected_format, str) and value['format'] == expected_format, 'original_receipt_format_differs')
            self.values[alias] = value
            self.writer(desc['writer'], pin['canonical_ensure_ascii'], KNOWN_ROLE_FAMILIES.get(role))
        elif role == 'original_unsealed_campaign_export':
            require(not {'identity_sha256', 'canonical_ensure_ascii', 'writer'} & set(desc), 'unsealed_original_cannot_gain_a_seal')
            value = strict_json(raw)
            require('identity_sha256' not in value and value['format'] == 'swdb.campaign-export.v1', 'original_unsealed_public_format_required')
            self.values[alias] = value
        elif role == 'selected_record':
            require(not {'identity_sha256', 'canonical_ensure_ascii', 'writer'} & set(desc), 'yaml_record_is_not_compact_seal')
            value = yaml.load(raw, Loader=OriginalLoader)
            require(value['id'] == token(desc['id']) and value['kind'] == token(desc['kind']), 'original_selected_body_identity_differs')
            require(digest(value, True) == hex_value(desc['record_sha256'], 64), 'original_public_record_digest_differs')
            pin.update(id=desc['id'], kind=desc['kind'], record_sha256=desc['record_sha256'])
            self.values[alias] = value
        else:
            require(not {'identity_sha256', 'canonical_ensure_ascii', 'writer', 'id', 'kind', 'record_sha256'} & set(desc),
                    'control_source_must_be_exact_source_bytes')
        self.pins[alias] = pin
        return dict(pin)

    def source(self, alias):
        require(self.documents[alias]['role'] == 'control_source', 'writer_must_be_pinned_source')
        return self.pin(alias)

    def writer(self, writer, policy, required_family=None):
        require(set(writer) == {'family', 'source', 'canonical_policy_sources', 'canonical_ensure_ascii', 'basis', 'parent_reviewed'},
                'explicit_original_writer_policy_contract_required')
        require(writer['basis'] == 'explicit_parent_source_review_of_original_canonical_hashing' and writer['parent_reviewed'] is True,
                'original_writer_review_required')
        require(type(writer['canonical_ensure_ascii']) is bool and writer['canonical_ensure_ascii'] == policy,
                'writer_and_receipt_policy_differ')
        family = writer['family']; source = self.source(writer['source'])
        require(family in set(KNOWN_WRITERS) | {'parent_capture', 'parent_input_specification', 'generality_reader', 'generality_export'},
                'explicit_original_writer_family_required')
        require(required_family is None or family == required_family, 'wrong_original_writer_family')
        sources = writer['canonical_policy_sources']
        require(isinstance(sources, list) and 0 < len(sources) <= 8, 'original_canonical_policy_source_pins_required')
        policies = [self.source(alias)['sha256'] for alias in sources]
        if family in KNOWN_WRITERS:
            expected, canonical_policy = KNOWN_WRITERS[family]
            require(source['sha256'] == expected and policy == canonical_policy, 'pinned_original_writer_policy_differs')
        if family == 'generality_export':
            require(KNOWN_WRITERS['generality_digest_b797'][0] in policies and policy is True,
                    'generality_export_original_delegated_b797_policy_required')
        if family == 'generality_reader':
            require(policy is True, 'generality_reader_original_artifacts_digest_policy_required')

    def materialize(self, value, depth=0):
        require(depth <= 40, 'input_root_depth_exceeded')
        if isinstance(value, dict):
            if '$original_document' in value:
                require(set(value) == {'$original_document'}, 'original_reference_cannot_add_or_override_facts')
                return self.pin(value['$original_document'])
            return {key: self.materialize(child, depth + 1) for key, child in value.items()}
        if isinstance(value, list):
            return [self.materialize(child, depth + 1) for child in value]
        require(value is None or type(value) in (str, int, bool) or type(value) is float and math.isfinite(value),
                'finite_plain_metadata_required')
        return value

    def require_role(self, pin, role):
        require(any(self.documents[alias]['role'] == role and self.pin(alias) == pin for alias in self.documents),
                'original_pin_role_differs')

    def receipt_writer_source(self, pin):
        matches = [alias for alias in self.documents if self.pin(alias) == pin and self.documents[alias]['role'] in SEALED_ROLES]
        require(len(matches) == 1, 'unique_original_receipt_writer_binding_required')
        return self.source(self.documents[matches[0]]['writer']['source'])

    def recheck(self):
        for alias, pin in self.pins.items():
            require(hash_bytes(self.raw(pin)) == self.raw_hashes[alias], 'original_input_changed_before_publication')

def verify_git(originals, args, root):
    require(originals.git('rev-parse', 'HEAD').decode().strip() == args.final_r, 'selected_repository_not_final_R')
    require(originals.git('status', '--porcelain').strip() == b'', 'selected_repository_not_clean')
    originals.git('merge-base', '--is-ancestor', C, args.final_r)
    base = originals.tree(args.final_r); source = originals.tree(C)
    py = lambda tree: {p: meta for p, meta in tree.items() if p.startswith('swdb-project/swdb/') and p.endswith('.py')}
    require(py(base) == py(source) and len(py(base)) == 185, 'final_R_not_exact_C_scientific_source')
    module_hashes = {p[len('swdb-project/swdb/'):]: hash_bytes(originals.git('cat-file', 'blob', args.final_r + ':' + p)) for p in sorted(py(base))}
    require(digest(module_hashes, True) == F6, 'final_R_portable_F6_differs')
    require(originals.git('rev-parse', args.final_r + '^{tree}').decode().strip() == args.final_r_tree, 'final_R_tree_differs')
    for key, commit, tree in (('freeze_export', args.freeze_export, args.freeze_export_tree),
                              ('report_export', args.report_export, args.report_export_tree)):
        item = root[key]; require(item['commit'] == commit and item['tree'] == tree, 'explicit_export_parameters_differ')
        require(originals.git('rev-parse', commit + '^{tree}').decode().strip() == tree, 'original_export_tree_differs')
        require(originals.git('show', '-s', '--format=%P', commit).decode().strip() == args.final_r, 'original_pure_export_sole_parent_differs')
        incoming = originals.tree(commit); require(all(incoming.get(p) == meta for p, meta in base.items()), 'original_export_changes_prior_blob_or_mode')
        require(sorted(set(incoming) - set(base)) == sorted(item['allowed_additions']), 'original_export_exact_additions_differ')
    for key in ('final_ticket11_acceptance', 'final_ticket14_acceptance'):
        originals.git('merge-base', '--is-ancestor', root[key]['actual_export_commit'], args.final_r)

def verify_root(originals, root, args):
    require(set(root) == ROOT_FIELDS, 'existing_auditor_root_fields_required_no_private_extra_fields')
    require(root['collector_account'] == {'host': 'mbit10', 'uid': args.collector_uid, 'user': args.collector_user},
            'collector_account_must_be_explicit_parent_verified_not_path_derived')
    originals.require_role(root['collector_source_pin'], 'control_source')
    require(root['collector_source_pin']['sha256'] == COLLECTOR, 'collector_source_differs')
    for field, role in (('manifest_M2', 'manifest_M2'), ('prepare_supervisor', 'prepare_supervisor'),
                        ('finalize_supervisor', 'finalize_supervisor'), ('prepare_preregistration', 'prepare_preregistration'),
                        ('finalize_preregistration', 'finalize_preregistration'), ('freeze_publication_custody', 'freeze_publication')):
        originals.require_role(root[field], role)
    for field, role in (('freeze_export', 'freeze_receipt'), ('report_export', 'agreement_receipt')):
        item = root[field]
        fields = {'commit', 'tree', 'allowed_additions', 'record_paths', 'receipt'}
        if field == 'freeze_export':
            fields |= {'configuration_paths', 'provider_configuration_path', 'campaign_configuration_paths'}
        require(set(item) == fields, 'export_structure_cannot_carry_raw_or_private_metadata')
        originals.require_role(item['receipt'], role)
        require(item['receipt']['commit'] == item['commit'] and item['receipt']['path'].startswith(EVIDENCE), 'original_export_receipt_origin_differs')
        paths = item['record_paths'] + [item['receipt']['path']] + item.get('configuration_paths', [])
        require(len(paths) == len(set(paths)) and sorted(paths) == sorted(item['allowed_additions']), 'export_additions_not_exact_declared_public_paths')
        for path in paths: git_path(path)
        require(all(p.startswith('swdb-project/records/') and p.endswith('.yaml') for p in item['record_paths']), 'public_export_record_path_required')
    for ticket in (11, 14):
        dep = root['final_ticket' + str(ticket) + '_acceptance']
        fields = {'accepted', 'receipt_identity', 'receipt_pin', 'actual_export_commit', 'actual_export_receipt_pin',
                  'actual_export_receipt_identity', 'selected_reader_source_sha256', 'reader_source_pin'}
        if ticket == 14: fields.add('final_source_commit')
        require(set(dep) == fields and dep['accepted'] is True, 'explicit_original_dependency_boundary_required')
        originals.require_role(dep['receipt_pin'], 'ticket' + str(ticket) + '_admission')
        originals.require_role(dep['actual_export_receipt_pin'], 'ticket' + str(ticket) + '_export_receipt')
        originals.require_role(dep['reader_source_pin'], 'control_source')
        require(dep['receipt_pin']['identity_sha256'] == dep['receipt_identity'] and
                dep['actual_export_receipt_pin']['identity_sha256'] == dep['actual_export_receipt_identity'] and
                dep['reader_source_pin']['sha256'] == dep['selected_reader_source_sha256'], 'dependency_original_pins_differ')
        require(originals.receipt_writer_source(dep['receipt_pin']) == dep['reader_source_pin'],
                'dependency_reader_source_not_its_original_admission_writer')
    token(root['policy_id']); token(root['report_id'])
    require(isinstance(root['selected_records'], list) and root['selected_records'], 'actual_selected_bodies_required_index_not_body')
    require(len({p['id'] for p in root['selected_records']}) == len(root['selected_records']), 'selected_record_id_alias_refused')
    for pin in root['selected_records']: originals.require_role(pin, 'selected_record')
    rows = root['campaigns']; require(len(rows) == 4 and {r['campaign'] for r in rows} == set(CIDS), 'four_explicit_actual_campaign_roots_required')
    for row in rows:
        required = {'campaign', 'projection', 'attempts', 'public_candidate_exports', 'public_candidate_export_selection_custody'}
        require(required <= set(row) <= required | {'interrupted_selected_body_custody'}, 'campaign_root_extra_metadata_refused')
        originals.require_role(row['projection'], 'trajectory_projection')
        originals.require_role(row['public_candidate_export_selection_custody'], 'public_candidate_selection')
        if 'interrupted_selected_body_custody' in row: originals.require_role(row['interrupted_selected_body_custody'], 'interrupted_selected_bodies')
        for pin in row['public_candidate_exports']: originals.require_role(pin, 'original_unsealed_campaign_export')
        require(isinstance(row['attempts'], list) and 0 < len(row['attempts']) <= 256, 'bounded_actual_attempt_history_required')
        for attempt in row['attempts']:
            roles = {'dispatch': 'attempt_dispatch', 'stopped': 'attempt_stopped', 'release_custody': 'attempt_release',
                     'before_custody': 'attempt_before', 'after_custody': 'attempt_after', 'dispatch_state_corroboration': 'dispatch_state_corroboration'}
            require(set(attempt) == set(roles), 'exact_original_attempt_custody_fields_required')
            for field, role in roles.items(): originals.require_role(attempt[field], role)
    # The unchanged auditor also dereferences these two nested receipt-pin seams.
    # Require their source inventory here; never rewrite their containing seals.
    for alias, value in list(originals.values.items()):
        role = originals.documents[alias]['role']
        if role == 'attempt_before' and 'unclean_resume_admission_pin' in value:
            originals.require_role(value['unclean_resume_admission_pin'], 'unclean_resume')
        if role == 'trajectory_projection':
            for event in value.get('outcome_accesses_without_component', []):
                originals.require_role(event['refusal_custody_pin'], 'outcome_refusal')

def fresh_output(text, forbidden):
    p = Path(text); require(p.is_absolute() and '..' not in p.parts and re.fullmatch('[A-Za-z0-9_.-]+', p.name), 'fresh_output_path_required')
    parent = local_path(str(p.parent), directory=True)
    require(parent.stat().st_uid == os.getuid() and not p.exists() and not p.is_symlink(), 'fresh_owned_output_parent_required')
    p = parent / p.name
    for root in forbidden:
        q = Path(root); require(q.is_absolute() and '..' not in q.parts, 'explicit_forbidden_root_required')
        if q.exists(): q = local_path(str(q), directory=True)
        require(p != q and q not in p.parents, 'output_inside_source_or_campaign_refused')
    return p

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('repository', 'final-r', 'final-r-tree', 'freeze-export', 'freeze-export-tree', 'report-export',
                 'report-export-tree', 'spec', 'spec-sha256', 'spec-identity', 'auditor-source', 'collector-source',
                 'plan-source', 'contract-source', 'collector-user', 'output-directory'):
        parser.add_argument('--' + flag, required=True)
    parser.add_argument('--spec-canonical-ensure-ascii', choices=('true', 'false'), required=True)
    parser.add_argument('--collector-uid', type=int, required=True)
    parser.add_argument('--metadata-deadline-seconds', type=int, required=True)
    args = parser.parse_args()
    require(60 <= args.metadata_deadline_seconds <= 3600, 'explicit_bounded_metadata_deadline_required')
    require(args.collector_uid > 0, 'explicit_nonroot_collector_uid_required'); token(args.collector_user)
    for field in ('final_r', 'final_r_tree', 'freeze_export', 'freeze_export_tree', 'report_export', 'report_export_tree'):
        hex_value(getattr(args, field), 40)
    repository = local_path(args.repository, directory=True)
    source_snapshots = {}
    for field, expected in (('auditor_source', AUDITOR), ('collector_source', COLLECTOR), ('plan_source', PLAN), ('contract_source', CONTRACT)):
        p = local_path(getattr(args, field)); require(p.stat().st_size <= MAX_FILE, 'approved_source_size_exceeded')
        raw = p.read_bytes(); require(hash_bytes(raw) == expected, 'approved_preparation_source_differs')
        source_snapshots[field] = {'path': str(p), 'bytes': len(raw), 'sha256': expected}
    spec_path = local_path(args.spec); require(spec_path.stat().st_size <= MAX_SPEC, 'bounded_parent_spec_required')
    spec_raw = spec_path.read_bytes(); require(hash_bytes(spec_raw) == hex_value(args.spec_sha256, 64), 'parent_reviewed_spec_file_sha_differs')
    spec = strict_json(spec_raw); policy = args.spec_canonical_ensure_ascii == 'true'
    original_seal(spec, args.spec_identity, policy)
    require(set(spec) == {'format', 'identity_sha256', 'writer', 'parent_review', 'documents', 'root', 'forbidden_output_roots'}, 'explicit_parent_spec_contract_required')
    require(spec['format'] == 'swdb.lanl17-actual-input-construction-spec.v1', 'parent_spec_format_differs')
    review = spec['parent_review']
    require(review == {'basis': 'explicit_parent_review_of_actual_original_inputs_and_selected_public_body_transfer',
            'source_C': C, 'estimator_sha256': F6, 'final_R': {'commit': args.final_r, 'tree': args.final_r_tree},
            'assembler_sha256': hash_bytes(local_path(__file__).read_bytes()), 'auditor_sha256': AUDITOR, 'collector_sha256': COLLECTOR,
            'parent_approved_actual_inputs': True, 'fixtures_or_replays_allowed': False}, 'actual_parent_review_boundary_missing_or_different')
    deps = spec['root']; require(set(deps) == ROOT_FIELDS, 'explicit_existing_root_template_required')
    refs = {C, args.final_r, args.freeze_export, args.report_export}
    refs.update(hex_value(deps[key]['actual_export_commit'], 40) for key in ('final_ticket11_acceptance', 'final_ticket14_acceptance'))
    originals = Originals(repository, refs, spec['documents'], args.metadata_deadline_seconds)
    originals.writer(spec['writer'], policy, 'parent_input_specification')
    # All declared inputs are checked, including original nested pins and sources;
    # the output contains pins only, never copied raw/private record bodies.
    for alias in spec['documents']: originals.pin(alias)
    root = originals.materialize(deps)
    verify_root(originals, root, args); verify_git(originals, args, root)
    require(originals.git('rev-parse', '--show-toplevel').decode().strip() == str(repository), 'repository_path_not_actual_git_root')
    require(isinstance(spec['forbidden_output_roots'], list) and spec['forbidden_output_roots'], 'actual_campaign_source_forbidden_roots_required')
    forbidden = [str(repository), *spec['forbidden_output_roots']]
    m2 = next(originals.values[a] for a in originals.values if originals.pins[a] == root['manifest_M2'])
    require(m2['source_commit'] == args.final_r and m2['estimator_sha256'] == F6 and
            m2['helper_sha256'] == KNOWN_WRITERS['helper28d'][0], 'selected_original_manifest_source_differs')
    forbidden.append(m2['source'])
    # Exact campaign locations follow the collector's pinned manifest path
    # recipe; no directory is created, enumerated or read at these locations.
    raw_root = Path(m2['raw'])
    require(raw_root.is_absolute() and '..' not in raw_root.parts, 'original_manifest_raw_root_required')
    forbidden.extend(str(raw_root / 'campaign-runs/extensa' / cid) for cid in CIDS)
    destination = fresh_output(args.output_directory, forbidden)
    originals.recheck()
    originals.remaining()
    require(spec_path.read_bytes() == spec_raw, 'original_parent_spec_changed')
    for snap in source_snapshots.values(): require(hash_bytes(local_path(snap['path']).read_bytes()) == snap['sha256'], 'approved_source_changed')
    require(hash_bytes(local_path(__file__).read_bytes()) == review['assembler_sha256'], 'assembler_source_changed_before_publication')
    root.update(format='swdb.lanl17-selected-admission-pins.v2', source_C=C, estimator_sha256=F6,
                final_R={'commit': args.final_r, 'tree': args.final_r_tree}, auditor_sha256=AUDITOR,
                collector_sha256=COLLECTOR, canonical_ensure_ascii=True,
                parent_approved_actual_inputs=review['parent_approved_actual_inputs'],
                fixtures_or_replays_allowed=review['fixtures_or_replays_allowed'])
    root['identity_sha256'] = digest(root, True)
    root_raw = (json.dumps(root, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
    require(len(root_raw) <= MAX_SPEC, 'accepted_pins_root_budget_exceeded')
    custody = {'format': 'swdb.lanl17-input-construction-custody.v1',
        'checked_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'state': 'constructed_for_parent_review_not_auditor_admission', 'actual_campaign_admission': False,
        'source_C': C, 'estimator_sha256': F6, 'final_R': root['final_R'],
        'parent_spec_pin': {'path': str(spec_path), 'bytes': len(spec_raw), 'sha256': hash_bytes(spec_raw),
                            'identity_sha256': spec['identity_sha256'], 'canonical_ensure_ascii': policy},
        'assembler_sha256': review['assembler_sha256'], 'approved_source_snapshots': source_snapshots,
        'accepted_pins_file': {'path': str(destination / 'accepted-pins.json'), 'bytes': len(root_raw),
                               'sha256': hash_bytes(root_raw), 'identity_sha256': root['identity_sha256'], 'canonical_ensure_ascii': True},
        'original_document_pins': originals.pins, 'original_total_bytes_checked': originals.total,
        'original_unsealed_outputs_rewritten': False, 'raw_state_provider_prompts_auth_logs_binaries_transferred': False,
        'collector_auditor_selected_reader_or_main_imports_or_invocations': 0,
        'Store_public_validation_native_provider_campaign_remote_invocations': 0,
        'limits': 'Original receipt/body custody and structural completeness only. Actual full validation, exclusive ownership, semantic trajectories, native dependencies and blind-order/D30 checks remain explicit inherited or unchanged-auditor admission boundaries.'}
    custody['identity_sha256'] = digest(custody, True)
    custody_raw = (json.dumps(custody, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
    require(len(custody_raw) <= MAX_SPEC, 'construction_custody_budget_exceeded')
    destination.mkdir(mode=0o700)
    for name, raw in (('accepted-pins.json', root_raw), ('construction-custody.json', custody_raw)):
        with (destination / name).open('xb') as stream: stream.write(raw)
        (destination / name).chmod(0o600)
    print(json.dumps({'state': custody['state'], 'actual_campaign_admission': False,
        'accepted_pins_file': custody['accepted_pins_file'], 'construction_custody_identity': custody['identity_sha256']}))

if __name__ == '__main__':
    try:
        main()
    except (Refused, KeyError, TypeError, ValueError, RecursionError, OSError, yaml.YAMLError, subprocess.SubprocessError) as exc:
        # Closed codes only: no original body, credential, command or exception
        # text is copied into the control result on a refusal.
        print(json.dumps({'state': 'refused', 'actual_campaign_admission': False,
                          'reason': str(exc) if isinstance(exc, Refused) else type(exc).__name__}), file=sys.stderr)
        sys.exit(3)
