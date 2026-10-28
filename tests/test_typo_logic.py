import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from bot.github_client import SubmissionRefused, check_submission_guards
from bot.typo_logic import (
    apply_fixes,
    find_typos,
    is_doc_file,
    is_safe_change,
    load_dictionary,
    validate_dictionary,
)

DICT = {"teh": "the", "recieve": "receive", "documenation": "documentation"}


class DocFileTests(unittest.TestCase):
    def test_doc_extensions(self):
        self.assertTrue(is_doc_file("README.md"))
        self.assertTrue(is_doc_file("docs/guide.rst"))
        self.assertTrue(is_doc_file("notes.txt"))

    def test_code_files_rejected(self):
        self.assertFalse(is_doc_file("src/main.py"))
        self.assertFalse(is_doc_file("app.js"))
        self.assertFalse(is_doc_file("noextension"))

    def test_excluded_dirs_rejected(self):
        self.assertFalse(is_doc_file("node_modules/pkg/README.md"))
        self.assertFalse(is_doc_file("vendor/lib/notes.md"))


class FindTyposTests(unittest.TestCase):
    def test_finds_simple_typo(self):
        ms = find_typos("This is teh guide.\n", DICT)
        self.assertEqual(len(ms), 1)
        self.assertEqual(ms[0].correction, "the")
        self.assertEqual(ms[0].line, 1)

    def test_capitalized_typo_keeps_case(self):
        ms = find_typos("Teh guide.\n", DICT)
        self.assertEqual(len(ms), 1)
        self.assertEqual(ms[0].correction, "The")

    def test_code_fence_is_skipped(self):
        text = "teh intro\n```\nteh code sample\n```\n"
        ms = find_typos(text, DICT)
        self.assertEqual(len(ms), 1)
        self.assertEqual(ms[0].line, 1)

    def test_inline_code_and_url_are_skipped(self):
        text = "Use `teh` literally, see https://example.com/teh and teh word.\n"
        ms = find_typos(text, DICT)
        self.assertEqual(len(ms), 1)

    def test_word_boundary(self):
        ms = find_typos("tehs and stehl\n", DICT)
        self.assertEqual(ms, [])


class ApplyFixesTests(unittest.TestCase):
    def test_apply_round_trip(self):
        fixed, ms = apply_fixes("I recieve teh documenation.\n", DICT)
        self.assertEqual(fixed, "I receive the documentation.\n")
        self.assertEqual(len(ms), 3)

    def test_apply_preserves_code_fence(self):
        text = "teh\n```\nteh\n```\n"
        fixed, _ = apply_fixes(text, DICT)
        self.assertEqual(fixed, "the\n```\nteh\n```\n")


class DictionaryAndSafetyTests(unittest.TestCase):
    def test_bundled_dictionary_is_valid(self):
        path = os.path.join(os.path.dirname(__file__), "..", "config", "typos.json")
        d = load_dictionary(path)
        self.assertGreaterEqual(len(d), 30)
        self.assertEqual(validate_dictionary(d), [])

    def test_invalid_dictionary_detected(self):
        problems = validate_dictionary({"teh": "teh", "": "x", "foo": "teh", "Teh": "the"})
        self.assertTrue(problems)

    def test_safe_change_limits(self):
        self.assertTrue(is_safe_change(1, 1))
        self.assertTrue(is_safe_change(3, 20))
        self.assertFalse(is_safe_change(4, 5))
        self.assertFalse(is_safe_change(1, 21))
        self.assertFalse(is_safe_change(0, 0))


class SubmissionGuardTests(unittest.TestCase):
    def test_submission_refused_by_default(self):
        os.environ.pop("SUBMIT_ENABLED", None)
        with self.assertRaises(SubmissionRefused):
            check_submission_guards(confirm="SUBMIT")


if __name__ == "__main__":
    unittest.main()
