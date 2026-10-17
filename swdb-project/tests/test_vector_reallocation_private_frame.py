"""2026-10-16 ET. Pending private lifetime frame artifact controls."""
import json

import pytest


def test_private_frame_packet_retains_release_and_the_complete_incoming_observation(tmp_path):
    from swdb import vector_reallocation_private_frame as frames
    directory = tmp_path / 'private-frame'
    plan = frames.prepare(directory)
    assert frames.check(directory) == plan
    assert plan['proof_admission'].startswith('unsupported:')
    assert plan['caller_premises_added'] == []
    assert plan['current_proof_records_admitted'] == []
    assert plan['source_typed_bridge_established'] is False
    assert {row['id'] for row in plan['obligations']} == {
        'entry.reflexive', 'automatic.frame', 'allocation.frame',
        'integer_store.frame', 'pointer_store.frame', 'release.frame',
        'automatic_end.frame', 'cleanup.observation', 'cleanup.exists_scalar'}
    prelude = (directory / 'prelude.acsl').read_text()
    for name in ['Heap::same_object', 'Heap::contents', 'Heap::initialized_at',
                 'Heap::live(entry,b)', 'Heap::end_automatic(Heap::release(now,b),r)']:
        assert name in prelude
    # Allocation history and private dead cells are hidden by observation. The
    # actual terminal transition is retained, not replaced by heap equality.
    assert 'entry == now' not in prelude
    assert 'next ==' not in prelude
    for row in plan['obligations']:
        text = (directory / row['path']).read_text()
        assert 'check lemma ' + row['goal'] in text
        assert 'axiom ' not in text and 'assume ' not in text
    cleanup = next(row for row in plan['obligations'] if row['id'] == 'cleanup.exists_scalar')
    text = (directory / cleanup['path']).read_text()
    assert r'\exists Heap::heap final; \exists integer scalar;' in text
    assert 'Heap::load_int(now,b,0)' in text
    assert 'Heap::load_int(final' not in text
    assert 't25_private_cleanup(now,r,b)' in text
    assert 'Heap::freeable(now,b,0)' in text


@pytest.mark.parametrize('change', ['release', 'observation', 'metadata', 'extra'])
def test_private_frame_packet_refuses_transition_or_frame_tampering(tmp_path, change):
    from swdb import vector_reallocation_private_frame as frames
    directory = tmp_path / 'private-frame'
    plan = frames.prepare(directory)
    if change == 'release':
        row = next(row for row in plan['obligations'] if row['id'] == 'cleanup.exists_scalar')
        path = directory / row['path']
        path.write_text(path.read_text().replace('t25_private_cleanup(now,r,b)', 'now'))
    elif change == 'observation':
        path = directory / 'prelude.acsl'
        path.write_text(path.read_text().replace('Heap::initialized_at', 'unused_initialization'))
    elif change == 'metadata':
        path = directory / 'manifest.json'
        changed = json.loads(path.read_text())
        changed['source_typed_bridge_established'] = True
        path.write_text(json.dumps(changed))
    else:
        (directory / 'accepted-proof.json').write_text('{}')
    with pytest.raises(ValueError):
        frames.check(directory)
