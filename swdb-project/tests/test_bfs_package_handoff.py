"""Existing-source delta handoff, using actual Git patch application. Date: 2026-09-25."""
import runpy

import pytest

from conftest import REPO
from swdb import artifacts, workflow


def test_rebased_demo_patch_preserves_prior_edit_and_exact_changed_source(tmp_path):
    before, after = tmp_path / 'before', tmp_path / 'after'
    before.mkdir(); after.mkdir()
    # Earlier measurement already removed redundant work. The new patch must
    # add only the retained helper, rather than applying that removal again.
    (before / 'bfs.cc').write_text('int DOBFS(){return 1;}\n')
    (after / 'bfs.cc').write_text('int helper(){return 1;}\nint DOBFS(){return helper();}\n')
    for root in (before, after):
        (root / 'graph.h').write_text('// fixed supporting header\n')
    snapshots = [{'artifact': artifacts.identify(root)} for root in (before, after)]
    driver = runpy.run_path(str(REPO / 'scripts/bfs_package_handoff.py'))
    path, patch = driver['demonstrated_patch'](*snapshots)
    output = tmp_path / 'materialized'
    workflow.apply_patch(before, output, patch, [path], [])
    assert artifacts.identify(output)['sha256'] == snapshots[1]['artifact']['sha256']
    (after / 'graph.h').write_text('// unrelated header change\n')
    snapshots[1]['artifact'] = artifacts.identify(after)
    with pytest.raises(ValueError, match='single BFS translation-unit'):
        driver['demonstrated_patch'](*snapshots)
