"""Safe record parsing is independent of optional LibYAML. Updated: 2026-10-05 ET (shared tests/testkit); 2026-09-25."""
from pathlib import Path

import pytest
import yaml

from swdb import yamlio
from swdb.store import record_files
from testkit.toolchain import load_script


def pure_python_module(monkeypatch):
    # Reload the public loader with the optional extension absent, as on a
    # dependency-only installation. Do not change the active store's loader.
    with monkeypatch.context() as patch:
        patch.delattr(yaml, 'CSafeLoader', raising=False)
        module = load_script(yamlio.__file__, 'yamlio_python_fixture')
    return module


def test_all_retained_records_have_identical_safe_parser_meaning(monkeypatch):
    fallback = pure_python_module(monkeypatch)
    records = Path(__file__).resolve().parents[1] / 'records'
    files = list(record_files(records))
    assert files
    for path, _ in files:
        assert yamlio.load(path) == fallback.load(path)


@pytest.mark.parametrize('use_fallback', [False, True])
def test_record_dates_and_safe_yaml_types_are_preserved(tmp_path, monkeypatch, use_fallback):
    parser = pure_python_module(monkeypatch) if use_fallback else yamlio
    record = tmp_path / 'record.yaml'
    record.write_text('created: 2026-09-25\nfinished: 2026-09-25T21:00:00Z\n'
                      'values: [null, true, false, 17, -2, 1.25]\n'
                      'shared: &values [1, 2]\ncopy: *values\ntext: |\n  alpha\n  beta\n')
    assert parser.load(record) == {
        'created': '2026-09-25', 'finished': '2026-09-25T21:00:00Z',
        'values': [None, True, False, 17, -2, 1.25], 'shared': [1, 2],
        'copy': [1, 2], 'text': 'alpha\nbeta\n'}
    # Neither loader may modify PyYAML's process-wide timestamp policy.
    assert str(yaml.safe_load('2026-09-25')) == '2026-09-25'
    assert not isinstance(yaml.safe_load('2026-09-25'), str)


@pytest.mark.parametrize('use_fallback', [False, True])
@pytest.mark.parametrize('content', [
    'context:\n  evidence: first\n  evidence: second\n',
    'kind: !!python/object/apply:builtins.str [unsafe]\n',
    'unterminated: [\n',
])
def test_both_record_parsers_reject_invalid_or_unsafe_yaml(tmp_path, monkeypatch, use_fallback, content):
    parser = pure_python_module(monkeypatch) if use_fallback else yamlio
    record = tmp_path / 'invalid.yaml'
    record.write_text(content)
    with pytest.raises(yaml.YAMLError):
        parser.load(record)
