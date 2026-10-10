"""Prospective ticket 17 parent_input_specification writer; not executed.

Future input is a separately reviewed, original-SHA-bound unsealed metadata
template. This writer adds only its new specification seal, not observed facts
or study admission. It imports no SWDB module and reads no selected receipt,
campaign state or record body. All such originals remain the assembler's input.
"""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import sys
import time

sys.dont_write_bytecode = True
C = 'f893fed400347ed23d92e917d8bde21b75e5375d'
F6 = 'f6f07110941ecdeeba12212897f3ecfc8a7a74749264c1d3371e73db22c8e1c3'
AUDITOR = '6a91ed1015bcc1caa771348e8bd1f591254ba130e55570ed18bc8121d67a06da'
COLLECTOR = 'b08db809b80cbebc6ce98dd8df8fdd4f327b170cdd7a545af0876ad68a832a5c'
FORMAT = 'swdb.lanl17-actual-input-construction-spec.v1'
MAX_METADATA = 8 * 1024 * 1024
ROOT_FIELDS = {'freeze_export', 'report_export', 'manifest_M2', 'policy_id', 'report_id',
    'prepare_supervisor', 'finalize_supervisor', 'prepare_preregistration', 'finalize_preregistration',
    'freeze_publication_custody', 'final_ticket11_acceptance', 'final_ticket14_acceptance',
    'collector_source_pin', 'collector_account', 'selected_records', 'campaigns'}
CIDS = {'extensa-gem5-bfs-20261006-p' + str(i) for i in range(1, 5)}

class Refused(ValueError):
    pass

def require(condition, code):
    if not condition:
        raise Refused(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def digest(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'),
                          ensure_ascii=True, allow_nan=False).encode())

def full_hash(value, length=64):
    require(isinstance(value, str) and re.fullmatch('[0-9a-f]{' + str(length) + '}', value), 'full_original_hash_required')
    return value

def strict_json(raw):
    def pairs(items):
        out = {}
        for key, value in items:
            require(key not in out, 'duplicate_template_key')
            out[key] = value
        return out
    def nonfinite(_):
        raise Refused('nonfinite_template_constant')
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=nonfinite)

def absolute_path(text, *, existing=False, directory=False):
    p = Path(text)
    require(p.is_absolute() and '..' not in p.parts and all(not x.is_symlink() for x in (p, *p.parents)),
            'absolute_nonsymlink_original_path_required')
    p = p.resolve(strict=existing)
    if existing:
        require(p.is_dir() if directory else stat.S_ISREG(p.stat().st_mode), 'original_regular_path_required')
    return p

def original_file(text, expected, maximum):
    p = absolute_path(text, existing=True)
    require(p.stat().st_size <= maximum, 'bounded_original_source_or_template_required')
    raw = p.read_bytes()
    require(sha(raw) == full_hash(expected), 'original_source_or_template_file_sha_differs')
    return p, raw

def bounded_structure(value, depth=0):
    require(depth <= 40, 'bounded_template_depth_required')
    if isinstance(value, dict):
        for key, child in value.items():
            require(isinstance(key, str), 'plain_template_key_required')
            bounded_structure(child, depth + 1)
    elif isinstance(value, list):
        for child in value: bounded_structure(child, depth + 1)
    else:
        require(value is None or type(value) in (str, int, float, bool), 'plain_template_metadata_required')

def fresh_output(text, forbidden):
    p = absolute_path(text)
    require(re.fullmatch('[A-Za-z0-9_.-]+', p.name) is not None and not p.exists() and not p.is_symlink(), 'fresh_output_required')
    parent = absolute_path(str(p.parent), existing=True, directory=True)
    require(parent.stat().st_uid == os.getuid(), 'owned_existing_output_parent_required')
    for root in forbidden:
        require(p != root and root not in p.parents, 'output_inside_source_or_campaign_refused')
    return parent / p.name

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for flag in ('template', 'template-sha256', 'template-author-source', 'template-author-source-sha256',
                 'parent-review-sha256', 'assembler-source', 'assembler-sha256', 'writer-source-alias',
                 'source-root', 'output-directory'):
        parser.add_argument('--' + flag, required=True)
    parser.add_argument('--campaign-root', action='append', required=True)
    parser.add_argument('--metadata-deadline-seconds', type=int, required=True)
    args = parser.parse_args()
    require(60 <= args.metadata_deadline_seconds <= 120, 'explicit_finite_metadata_deadline_required')
    deadline = time.monotonic() + args.metadata_deadline_seconds
    template_path, template_raw = original_file(args.template, args.template_sha256, MAX_METADATA)
    author_path, author_raw = original_file(args.template_author_source, args.template_author_source_sha256, MAX_METADATA)
    assembler_path, assembler_raw = original_file(args.assembler_source, args.assembler_sha256, MAX_METADATA)
    own_path = absolute_path(__file__, existing=True)
    require(own_path.stat().st_size <= MAX_METADATA, 'bounded_writer_source_required')
    own_raw = own_path.read_bytes()
    value = strict_json(template_raw)
    require(set(value) == {'format', 'writer', 'parent_review', 'documents', 'root', 'forbidden_output_roots'} and
            value['format'] == FORMAT, 'exact_unsealed_parent_reviewed_template_format_required')
    bounded_structure(value)
    require(digest(value['parent_review']) == full_hash(args.parent_review_sha256), 'exact_original_parent_review_digest_required')
    review = value['parent_review']
    require(set(review) == {'basis', 'source_C', 'estimator_sha256', 'final_R', 'assembler_sha256',
                          'auditor_sha256', 'collector_sha256', 'parent_approved_actual_inputs', 'fixtures_or_replays_allowed'},
            'exact_parent_review_fields_required')
    require(review['basis'] == 'explicit_parent_review_of_actual_original_inputs_and_selected_public_body_transfer' and
            review['source_C'] == C and review['estimator_sha256'] == F6 and
            review['assembler_sha256'] == sha(assembler_raw) and review['auditor_sha256'] == AUDITOR and
            review['collector_sha256'] == COLLECTOR and review['parent_approved_actual_inputs'] is True and
            review['fixtures_or_replays_allowed'] is False, 'explicit_reviewed_actual_input_boundary_required')
    require(set(review['final_R']) == {'commit', 'tree'}, 'explicit_reviewed_final_R_required')
    for key in ('commit', 'tree'): full_hash(review['final_R'][key], 40)
    require(set(value['root']) == ROOT_FIELDS, 'existing_auditor_root_template_required')
    require(isinstance(value['documents'], dict) and 0 < len(value['documents']) <= 4096, 'bounded_original_descriptor_inventory_required')
    alias = args.writer_source_alias
    require(re.fullmatch('[A-Za-z0-9_.:-]{1,256}', alias) is not None and alias in value['documents'], 'explicit_original_writer_source_alias_required')
    own_pin = {'path': str(own_path), 'bytes': len(own_raw), 'sha256': sha(own_raw)}
    require(value['documents'][alias] == {'role': 'control_source', 'origin': {'path': str(own_path)},
                                       'bytes': len(own_raw), 'sha256': sha(own_raw)}, 'writer_alias_not_exact_original_writer_bytes')
    require(value['writer'] == {'family': 'parent_input_specification', 'source': alias,
            'canonical_policy_sources': [alias], 'canonical_ensure_ascii': True,
            'basis': 'explicit_parent_source_review_of_original_canonical_hashing', 'parent_reviewed': True},
            'exact_original_spec_writer_canonical_true_contract_required')
    source = absolute_path(args.source_root, existing=True, directory=True)
    require(len(args.campaign_root) == 4, 'four_explicit_actual_campaign_roots_required')
    campaigns = [absolute_path(p) for p in args.campaign_root]
    require({p.name for p in campaigns} == CIDS and len({p.parent for p in campaigns}) == 1 and
            campaigns[0].parent.name == 'extensa' and campaigns[0].parent.parent.name == 'campaign-runs',
            'exact_named_campaign_path_boundaries_required')
    require(isinstance(value['forbidden_output_roots'], list) and value['forbidden_output_roots'], 'explicit_parent_forbidden_roots_required')
    forbidden = [absolute_path(p) for p in value['forbidden_output_roots']]
    require({source, *campaigns} <= set(forbidden), 'parent_reviewed_template_omits_source_or_campaign_boundary')
    destination = fresh_output(args.output_directory, forbidden)
    # Preserve the original template and all of its facts. Only the new
    # specification's canonical-true whole-object identity is added.
    output = dict(value)
    output['identity_sha256'] = digest(value)
    output_raw = (json.dumps(output, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
    require(len(output_raw) <= MAX_METADATA, 'sealed_specification_budget_exceeded')
    custody = {'format': 'swdb.lanl17-parent-input-specification-writer-custody.v1',
        'written_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'canonical_ensure_ascii': True,
        'state': 'parent_reviewed_metadata_only_not_actual_campaign_admission', 'actual_campaign_admission': False,
        'writer_source_pin': own_pin,
        'original_unsealed_template_pin': {'path': str(template_path), 'bytes': len(template_raw), 'sha256': sha(template_raw)},
        'template_author_source_pin': {'path': str(author_path), 'bytes': len(author_raw), 'sha256': sha(author_raw)},
        'template_parent_review_sha256': digest(review), 'assembler_source_pin': {'path': str(assembler_path), 'bytes': len(assembler_raw), 'sha256': sha(assembler_raw)},
        'new_specification_pin': {'path': str(destination / 'input-specification.json'), 'bytes': len(output_raw),
                                  'sha256': sha(output_raw), 'identity_sha256': output['identity_sha256'], 'canonical_ensure_ascii': True},
        'facts_generated_or_template_original_rewritten': False,
        'original_receipt_record_or_campaign_state_files_read': 0,
        'SWDB_Store_collector_auditor_reader_native_provider_campaign_remote_actions': 0,
        'admission_boundary': 'Exact parent-reviewed metadata bytes and original source pins only; no live observations, original document checks, scientific or trajectory admission is performed.'}
    custody['identity_sha256'] = digest(custody)
    custody_raw = (json.dumps(custody, indent=2, ensure_ascii=True, allow_nan=False) + '\n').encode()
    require(len(custody_raw) <= MAX_METADATA and time.monotonic() < deadline, 'bounded_metadata_publication_required')
    for path, raw in ((template_path, template_raw), (author_path, author_raw), (assembler_path, assembler_raw), (own_path, own_raw)):
        require(absolute_path(str(path), existing=True).read_bytes() == raw, 'original_template_or_source_changed_before_publication')
    destination.mkdir(mode=0o700)
    for name, raw in (('input-specification.json', output_raw), ('writer-custody.json', custody_raw)):
        with (destination / name).open('xb') as stream: stream.write(raw)
        (destination / name).chmod(0o600)
    print(json.dumps({'state': custody['state'], 'actual_campaign_admission': False,
                      'new_specification_pin': custody['new_specification_pin'], 'writer_custody_identity': custody['identity_sha256']}))

if __name__ == '__main__':
    try:
        main()
    except (Refused, KeyError, TypeError, ValueError, RecursionError, OSError) as exc:
        print(json.dumps({'state': 'refused', 'actual_campaign_admission': False,
                          'reason': str(exc) if isinstance(exc, Refused) else type(exc).__name__}), file=sys.stderr)
        sys.exit(3)
