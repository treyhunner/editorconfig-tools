#!/usr/bin/python
from unittest import TestCase
from os.path import abspath

from editorconfig import get_properties
from editorconfig_tools.editorconfig_tools import EditorConfigChecker


def get_filename(test_file):
    return abspath('tests/{0}'.format(test_file))


class EditorConfigCheckerTest(TestCase):

    """Tests for EditorConfigChecker"""

    def assertFileErrors(self, filename, expected_errors):
        full_filename = get_filename(filename)
        props = get_properties(full_filename)
        checker = EditorConfigChecker()
        errors = checker.check(full_filename, props)
        self.assertEquals((filename, errors), (filename, expected_errors))

    def test_check_crlf(self):
        self.assertFileErrors('crlf_valid.txt', [])
        self.assertFileErrors('crlf_invalid_cr.txt', [
            "Final newline found",
            "Incorrect line ending found: cr",
        ])
        self.assertFileErrors('crlf_invalid_lf.txt', [
            "Final newline found",
            "Incorrect line ending found: lf",
        ])

    def test_check_cr(self):
        self.assertFileErrors('cr_valid.txt', [])
        self.assertFileErrors('cr_invalid_lf.txt', [
            "Incorrect line ending found: lf",
        ])
        self.assertFileErrors('cr_invalid_crlf.txt', [
            "Incorrect line ending found: crlf",
        ])

    def test_check_lf(self):
        self.assertFileErrors('lf_valid.txt', [])
        self.assertFileErrors('lf_invalid_cr.txt', [
            "Incorrect line ending found: cr",
        ])
        self.assertFileErrors('lf_invalid_crlf.txt', [
            "Incorrect line ending found: crlf",
            "No final newline found",
        ])
