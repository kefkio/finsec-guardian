"""
Echidna runner for property-based fuzz testing of Solidity contracts.

Echidna is a fuzzer — it does not produce static analysis findings in the same
way as Slither/Mythril. This runner:
  1. Writes the source to a temp file.
  2. Invokes Echidna via subprocess with JSON output mode.
  3. Normalises property-failure results into Finding-compatible dicts.

Because Echidna has its own dependency tree (Haskell runtime, specific solc
version), it should be installed as a standalone binary. Configure its path:

    ANALYSIS_TOOL_VENVS = {
        'echidna': '/path/to/echidna',   # path to the echidna binary
    }

If not configured the runner looks for 'echidna' on PATH.
"""

import json
import logging
import os
import subprocess
import tempfile

from django.conf import settings

logger = logging.getLogger(__name__)


def _echidna_binary() -> str:
    venvs = getattr(settings, 'ANALYSIS_TOOL_VENVS', {})
    return venvs.get('echidna', 'echidna')


def run_echidna(source_code: str) -> list[dict]:
    """
    Run Echidna on *source_code* and return normalised finding dicts.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        sol_path = os.path.join(tmpdir, 'contract.sol')
        with open(sol_path, 'w', encoding='utf-8') as fh:
            fh.write(source_code)

        binary = _echidna_binary()
        cmd = [binary, sol_path, '--format', 'json', '--timeout', '60']

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=tmpdir,
            )
        except FileNotFoundError:
            return [_not_installed_finding()]
        except subprocess.TimeoutExpired:
            return [_timeout_finding()]
        except Exception as exc:
            return [_error_finding(str(exc))]

        output = result.stdout.strip()
        if not output:
            if result.returncode == 0:
                return [_info_finding('Echidna completed with no property failures.')]
            return [_error_finding(result.stderr[-500:])]

        try:
            report = json.loads(output)
        except json.JSONDecodeError:
            # Echidna may output line-delimited JSON or plain text
            return _parse_text_output(output)

        return _parse_echidna_report(report)


def _parse_echidna_report(report) -> list[dict]:
    findings = []
    # Echidna JSON: {"campaign": {...}, "tests": [...]}
    tests = report.get('tests', []) if isinstance(report, dict) else []
    for test in tests:
        status = test.get('status', '')
        if status == 'failed':
            findings.append({
                'swc_id': '',
                'title': f'Property Failure: {test.get("name", "unknown")}',
                'description': (
                    f'Echidna falsified the property `{test.get("name", "")}`. '
                    f'Reproducer: {json.dumps(test.get("reproducer", []))}'
                ),
                'severity': 'high',
                'line_number': None,
                'recommendation': (
                    'Review the failing property. Ensure invariants hold for all '
                    'reachable states and input sequences.'
                ),
            })
    if not findings:
        findings.append(_info_finding('All Echidna properties passed (no failures found).'))
    return findings


def _parse_text_output(output: str) -> list[dict]:
    """Fallback: turn each output line into an info finding."""
    lines = [l.strip() for l in output.splitlines() if l.strip()]
    findings = []
    for line in lines[:20]:
        failed = 'failed' in line.lower() or 'falsified' in line.lower()
        findings.append({
            'swc_id': '',
            'title': 'Echidna: ' + line[:80],
            'description': line,
            'severity': 'high' if failed else 'info',
            'line_number': None,
            'recommendation': 'Review and fix the reported property failure.' if failed else '',
        })
    return findings or [_info_finding('Echidna produced no structured output.')]


def _info_finding(msg: str) -> dict:
    return {
        'swc_id': '',
        'title': 'Echidna Result',
        'description': msg,
        'severity': 'info',
        'line_number': None,
        'recommendation': '',
    }


def _not_installed_finding() -> dict:
    return {
        'swc_id': '',
        'title': 'Echidna Not Installed',
        'description': (
            'The `echidna` binary was not found. '
            'Install Echidna and configure ANALYSIS_TOOL_VENVS["echidna"] in Django settings.'
        ),
        'severity': 'info',
        'line_number': None,
        'recommendation': (
            'Download the Echidna binary from https://github.com/crytic/echidna/releases\n'
            'Then set ANALYSIS_TOOL_VENVS = {"echidna": "/path/to/echidna"} in settings.py'
        ),
    }


def _timeout_finding() -> dict:
    return {
        'swc_id': '',
        'title': 'Echidna Analysis Timeout',
        'description': 'Echidna exceeded the time limit.',
        'severity': 'info',
        'line_number': None,
        'recommendation': 'Increase the timeout or reduce the complexity of properties under test.',
    }


def _error_finding(detail: str) -> dict:
    return {
        'swc_id': '',
        'title': 'Echidna Scanner Error',
        'description': f'An error occurred during Echidna analysis: {detail}',
        'severity': 'info',
        'line_number': None,
        'recommendation': 'Ensure Echidna is correctly installed and the contract is valid.',
    }
