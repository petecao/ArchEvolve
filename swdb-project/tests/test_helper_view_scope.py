"""Independent helper-view entry scope and capture storage; 2026-10-15 ET."""
import pytest

from swdb import helper_windows
from test_helper_windows import UNIT, prepare


def test_a_rehashed_generator_cannot_change_an_unused_unit_parameter_type(tmp_path, monkeypatch):
    original = helper_windows._Plan.__init__
    def faulty(self, *args, **kwargs):
        original(self, *args, **kwargs)
        assert self.output.count('int unused)') == 1
        self.output = self.output.replace('int unused)', 'unsigned unused)', 1)
    monkeypatch.setattr(helper_windows._Plan, '__init__', faulty)
    with pytest.raises(helper_windows.Refused):
        prepare(tmp_path, unit=UNIT.replace('int n)', 'int n,int unused)'))


@pytest.mark.parametrize('storage', ['static ', 'thread_local '])
def test_each_helper_capture_is_fresh_automatic_storage(tmp_path, monkeypatch, storage):
    original = helper_windows._Plan.expand
    def faulty(self, *args, **kwargs):
        text = original(self, *args, **kwargs)
        assert text.count('int swdb_hw_0_arg_1 = n;') == 1
        return text.replace('int swdb_hw_0_arg_1 = n;', storage + 'int swdb_hw_0_arg_1 = n;', 1)
    monkeypatch.setattr(helper_windows._Plan, 'expand', faulty)
    with pytest.raises(helper_windows.Refused):
        prepare(tmp_path)
