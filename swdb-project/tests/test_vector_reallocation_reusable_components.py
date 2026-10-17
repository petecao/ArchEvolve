"""2026-10-16 ET. Public reuse of exact conditional mathematical components."""
from pathlib import Path
import hashlib
import shutil

import pytest


ARCHIVE = Path(__file__).parent/'fixtures/proof/vector_closed_scientific_bundle'


def test_reusable_components_bind_only_the_complete_unchanged_55_targets():
    from swdb import vector_reallocation_closed_binding as packets

    result, files = packets.reusable_components(ARCHIVE)
    assert result['complete_source_target_count'] == 55
    assert [(row['id'], len(row['targets'])) for row in result['components']] == [
        ('constructor', 35), ('destructor', 11), ('private_frame', 9)]
    assert result['scientific_dependencies_bound'] is True
    assert result['scientific_catalog_sha256'] == packets.REVIEWED_CATALOG_SHA256
    assert result['original_archive_target_count'] == 82
    assert result['unrelated_components_required'] == []
    for component in result['components']:
        assert component['historical_identity_preserved'] is True
        assert component['historical_source_commit'] == packets.HISTORICAL_SOURCES[component['id']]
        assert component['cold_evidence'] and component['complete_cold_context']
        for target in component['targets']:
            assert target['kind'] in {'check_lemma', 'c_kernel'}
            assert target['input_sha256']
            if target['kind'] == 'c_kernel':
                assert component['id'] == 'constructor' and target['id'] == 'ctor.numeric'
                assert target['statement'] is None
            else:
                assert target['statement']
            assert target['observation']
            assert any(name.startswith('components/'+component['id']+'/') and
                       hashlib.sha256(raw).hexdigest() == target['input_sha256']
                       for name, raw in files.items())
        prefix = 'components/'+component['id']+'/'
        assert any(name.startswith(prefix) for name in files)
    assert result['source_admission'] is False
    assert result['source_typed_bridge_established'] is False
    assert result['caller_acceptance'] is False
    assert result['current_model_records_created'] == []


def test_reusable_components_refuse_modified_missing_or_unbound_evidence(tmp_path):
    from swdb import vector_reallocation_closed_binding as packets

    for mutation in ('catalog', 'object', 'missing', 'extra', 'link'):
        directory = tmp_path/mutation
        shutil.copytree(ARCHIVE, directory)
        selected = sorted((directory/'objects').glob('*.json'))[0]
        if mutation == 'catalog':
            path = directory/'catalog.json'
            path.write_bytes(path.read_bytes().replace(b'82', b'55', 1))
        elif mutation == 'object':
            selected.write_bytes(selected.read_bytes()+b'\n')
        elif mutation == 'missing':
            selected.unlink()
        elif mutation == 'extra':
            (directory/'accepted.json').write_text('{}')
        else:
            selected.unlink()
            selected.symlink_to(directory/'catalog.json')
        with pytest.raises(packets.Refused):
            packets.reusable_components(directory)
