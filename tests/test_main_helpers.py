"""Tests for generator __main__ helper functions (CLI parsing)."""
import sys
import unittest
from unittest.mock import patch

# Import after potential path setup; run tests from project root
import generator.__main__ as main


class TestManageTemporalityArgs(unittest.TestCase):
    """Tests for manage_temporality_args."""

    def test_valid_returns_tuple(self):
        slice_d, scope_d, num = main.manage_temporality_args("3600,86400,7")
        self.assertEqual(slice_d, 3600)
        self.assertEqual(scope_d, 86400)
        self.assertEqual(num, 7)

    def test_scope_must_be_greater_than_slice(self):
        with self.assertRaises(ValueError) as ctx:
            main.manage_temporality_args("86400,3600,7")
        self.assertIn("scope", str(ctx.exception).lower())

    def test_scope_must_be_multiple_of_slice(self):
        with self.assertRaises(ValueError) as ctx:
            main.manage_temporality_args("3600,10000,7")
        self.assertIn("multiple", str(ctx.exception).lower())

    def test_invalid_length_calls_print_usage(self):
        with patch.object(main, 'print_usage', side_effect=RuntimeError("exit")) as mock_print_usage:
            with self.assertRaises(RuntimeError):
                main.manage_temporality_args("3600,86400")
            mock_print_usage.assert_called_once()


class TestManageOutputArgs(unittest.TestCase):
    """Tests for manage_output_args."""

    def test_single_format(self):
        out = main.manage_output_args("bash")
        self.assertEqual(out, ["bash"])

    def test_multiple_formats(self):
        out = main.manage_output_args("bash,cloudsimplus,cbtool")
        self.assertEqual(out, ["bash", "cloudsimplus", "cbtool"])

    def test_invalid_format_raises(self):
        with self.assertRaises(ValueError):
            main.manage_output_args("invalid")
        with self.assertRaises(ValueError):
            main.manage_output_args("bash,invalid")
