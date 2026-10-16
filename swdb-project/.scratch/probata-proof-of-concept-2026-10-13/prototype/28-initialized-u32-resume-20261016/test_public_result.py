"""2026-10-16 ET. Pure public-entry result census; no project/compiler imports."""
import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


def no_children(event, args):
    if event.startswith(('subprocess.', 'os.exec', 'os.spawn', 'os.posix_spawn', 'os.fork')) or event in {'os.system', 'ctypes.dlopen'}:
        raise RuntimeError('pure census test refuses ' + event)


sys.addaudithook(no_children)
ENTRY = Path(__file__).with_name('public_entry_v3.py')
spec = importlib.util.spec_from_file_location('initialized_public_entry', ENTRY)
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)
NAME = 'test_public_initialized_u32_has_ordinary_prewrite_capacity_and_original_partial_frame'
CASE = '<testcase classname="tests.test_dx100_initialized_register" name="' + NAME + '">{}</testcase>'


class PublicResultTests(unittest.TestCase):
    def census(self, text):
        with tempfile.TemporaryDirectory(prefix='probata-resume-20261016-t28-census-') as directory:
            path = Path(directory) / 'junit.xml'
            if text is not None:
                path.write_text(text)
            return entry.read_public_junit(path)

    def suite(self, cases=CASE.format(''), *, tests='1', failures='0', errors='0', skipped='0'):
        return ('<testsuites><testsuite tests="' + tests + '" failures="' + failures +
                '" errors="' + errors + '" skipped="' + skipped + '">' + cases + '</testsuite></testsuites>')

    def test_one_selected_execution_is_accepted(self):
        result = self.census(self.suite())
        self.assertTrue(result['accepted'], result)
        self.assertEqual(result['cases'], 1)

    def test_no_execution_is_refused(self):
        self.assertFalse(self.census(self.suite('', tests='0'))['accepted'])

    def test_skip_with_zero_process_exit_is_refused(self):
        self.assertFalse(self.census(self.suite(CASE.format('<skipped/>'), skipped='1'))['accepted'])

    def test_failure_with_zero_process_exit_is_refused(self):
        self.assertFalse(self.census(self.suite(CASE.format('<failure/>'), failures='1'))['accepted'])

    def test_error_with_zero_process_exit_is_refused(self):
        self.assertFalse(self.census(self.suite(CASE.format('<error/>'), errors='1'))['accepted'])

    def test_changed_test_identity_is_refused(self):
        self.assertFalse(self.census(self.suite().replace(NAME, 'test_unrelated'))['accepted'])

    def test_changed_module_identity_is_refused(self):
        self.assertFalse(self.census(self.suite().replace('tests.test_dx100_initialized_register', 'test_unrelated'))['accepted'])

    def test_duplicate_case_is_refused_even_with_one_count(self):
        self.assertFalse(self.census(self.suite(CASE.format('') * 2))['accepted'])

    def test_reported_count_mismatch_is_refused(self):
        self.assertFalse(self.census(self.suite(tests='2'))['accepted'])

    def test_unreported_failure_child_is_refused(self):
        self.assertFalse(self.census(self.suite(CASE.format('<failure/>')))['accepted'])

    def test_missing_report_is_refused(self):
        self.assertFalse(self.census(None)['accepted'])

    def test_invalid_xml_is_refused(self):
        self.assertFalse(self.census('<testsuites>')['accepted'])

    def test_missing_census_fields_is_refused(self):
        self.assertFalse(self.census(self.suite().replace(' skipped="0"', ''))['accepted'])

    def test_extra_suite_is_refused(self):
        self.assertFalse(self.census(self.suite().replace('</testsuites>', '<testsuite tests="0"/></testsuites>'))['accepted'])

    def test_nested_suite_is_refused(self):
        self.assertFalse(self.census(self.suite().replace('</testsuite>', '<testsuite tests="99" skipped="99"/></testsuite>'))['accepted'])

    def test_doctype_is_refused(self):
        self.assertFalse(self.census('<!DOCTYPE testsuites>' + self.suite())['accepted'])


if __name__ == '__main__':
    unittest.main()
