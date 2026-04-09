"""Unit tests for scanner.slither_runner (no solc required)."""
from unittest.mock import patch, MagicMock

import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.test import TestCase
from scanner.slither_runner import (
    _severity_from_strings,
    _extract_line,
    _compilation_error_finding,
    _error_finding,
    run_slither,
)


class SeverityMappingTests(TestCase):
    def test_high_high_is_critical(self):
        self.assertEqual(_severity_from_strings('High', 'High'), 'critical')

    def test_high_medium_is_high(self):
        self.assertEqual(_severity_from_strings('High', 'Medium'), 'high')

    def test_medium_is_medium(self):
        self.assertEqual(_severity_from_strings('Medium', 'High'), 'medium')

    def test_low_is_low(self):
        self.assertEqual(_severity_from_strings('Low', 'Low'), 'low')

    def test_informational_is_info(self):
        self.assertEqual(_severity_from_strings('Informational', 'High'), 'info')

    def test_optimization_is_info(self):
        self.assertEqual(_severity_from_strings('Optimization', 'High'), 'info')


class ExtractLineTests(TestCase):
    def test_returns_first_line(self):
        elements = [{'source_mapping': {'lines': [42, 43]}}]
        self.assertEqual(_extract_line(elements), 42)

    def test_returns_none_when_empty(self):
        self.assertIsNone(_extract_line([]))

    def test_skips_missing_source_mapping(self):
        elements = [{'type': 'function'}, {'source_mapping': {'lines': [10]}}]
        self.assertEqual(_extract_line(elements), 10)


class FindingHelperTests(TestCase):
    def test_compilation_error_finding_structure(self):
        f = _compilation_error_finding('solc not found')
        self.assertEqual(f['swc_id'], 'SWC-103')
        self.assertEqual(f['severity'], 'high')
        self.assertIn('solc not found', f['description'])

    def test_error_finding_structure(self):
        f = _error_finding('unexpected error')
        self.assertEqual(f['severity'], 'info')
        self.assertIn('unexpected error', f['description'])


class RunSlitherFallbackTests(TestCase):
    """Verify run_slither returns a graceful finding when Slither cannot compile."""

    def test_slither_error_returns_finding_list(self):
        with patch('scanner.slither_runner._run_python_api', side_effect=Exception('solc not found')):
            results = run_slither('pragma solidity ^0.8.0;')
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
        self.assertEqual(results[0]['swc_id'], 'SWC-103')

    def test_slither_generic_error_returns_info_finding(self):
        with patch('scanner.slither_runner._run_python_api', side_effect=RuntimeError('boom')):
            results = run_slither('pragma solidity ^0.8.0;')
        self.assertIsInstance(results, list)
        self.assertGreater(len(results), 0)
