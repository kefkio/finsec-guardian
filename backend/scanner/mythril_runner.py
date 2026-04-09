"""
Mythril runner for EVM bytecode / Solidity symbolic execution analysis.

Mythril is run as a subprocess so it can be installed in an isolated
virtualenv that does not conflict with Slither's dependencies.
The path to the mythril executable (or its venv python) is configurable
via Django settings:

    ANALYSIS_TOOL_VENVS = {
        'mythril': '/path/to/mythril-venv/bin/python',   # optional
    }

If not configured, the runner falls back to the 'myth' binary on PATH.
"""

import json
import logging
import os
import subprocess
import sys
import tempfile

from django.conf import settings

logger = logging.getLogger(__name__)


def _myth_executable() -> list[str]:
    """Return the command prefix for invoking Mythril."""
    venvs = getattr(settings, 'ANALYSIS_TOOL_VENVS', {})
    python = venvs.get('mythril')
    if python:
        return [python, '-m', 'mythril.interfaces.cli']
    # fall back to 'myth' on PATH
    return ['myth']


def run_mythril(source_code: str) -> list[dict]:
    """
    Analyse *source_code* with Mythril and return normalised finding dicts.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        sol_path = os.path.join(tmpdir, 'contract.sol')
        with open(sol_path, 'w', encoding='utf-8') as fh:
            fh.write(source_code)

        cmd = _myth_executable() + [
            'analyze',
            sol_path,
            '-o', 'jsonv2',
            '--execution-timeout', '60',
        ]

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=120,
                cwd=tmpdir,
            )
        except FileNotFoundError:
            return [_not_installed_finding('mythril', 'myth')]
        except subprocess.TimeoutExpired:
            return [_timeout_finding('Mythril')]
        except Exception as exc:
            return [_error_finding('Mythril', str(exc))]

        output = result.stdout.strip()
        if not output:
            # Mythril prints nothing when there are no issues (exit 0)
            if result.returncode == 0:
                return []
            return [_error_finding('Mythril', result.stderr[-500:])]

        try:
            report = json.loads(output)
        except json.JSONDecodeError:
            logger.warning('Mythril non-JSON output: %s', output[:500])
            return [_error_finding('Mythril', output[:300])]

        return _parse_mythril_report(report)


def _parse_mythril_report(report) -> list[dict]:
    findings = []
    # jsonv2 format: list of issue objects at top level or under 'issues'
    issues = report if isinstance(report, list) else report.get('issues', [])
    for issue in issues:
        findings.append(_issue_to_finding(issue))
    return findings


def _issue_to_finding(issue: dict) -> dict:
    swc_id = issue.get('swc-id', '')
    if swc_id and not swc_id.startswith('SWC-'):
        swc_id = f'SWC-{swc_id}'

    severity_raw = issue.get('severity', 'Informational').lower()
    severity_map = {'high': 'high', 'medium': 'medium', 'low': 'low',
                    'informational': 'info', 'optimization': 'info'}
    severity = severity_map.get(severity_raw, 'info')

    locations = issue.get('locations', [{}])
    line_number = None
    if locations:
        line_text = locations[0].get('sourceMap', '')
        # sourceMap may be "line:col" or "offset:length:fileIdx"
        try:
            line_number = int(line_text.split(':')[0])
        except (ValueError, IndexError):
            pass

    return {
        'swc_id': swc_id,
        'title': issue.get('title', 'Unknown Issue'),
        'description': issue.get('description', '').strip(),
        'severity': severity,
        'line_number': line_number,
        'recommendation': issue.get('extra', {}).get('description', 'Review and remediate the identified issue.'),
    }


def _not_installed_finding(tool: str, binary: str) -> dict:
    return {
        'swc_id': '',
        'title': f'{tool.title()} Not Installed',
        'description': (
            f'The `{binary}` binary was not found. '
            f'Install {tool} in its own virtualenv and configure '
            f'ANALYSIS_TOOL_VENVS["{tool}"] in Django settings.'
        ),
        'severity': 'info',
        'line_number': None,
        'recommendation': (
            f'python -m venv venvs/{tool}\n'
            f'venvs/{tool}/bin/pip install {tool}\n'
            f'# Then set ANALYSIS_TOOL_VENVS = {{"{tool}": "venvs/{tool}/bin/python"}} in settings.py'
        ),
    }


def _timeout_finding(tool: str) -> dict:
    return {
        'swc_id': '',
        'title': f'{tool} Analysis Timeout',
        'description': f'{tool} exceeded the time limit. The contract may be too complex.',
        'severity': 'info',
        'line_number': None,
        'recommendation': 'Simplify the contract or increase the execution timeout.',
    }


def _error_finding(tool: str, detail: str) -> dict:
    return {
        'swc_id': '',
        'title': f'{tool} Scanner Error',
        'description': f'An error occurred during {tool} analysis: {detail}',
        'severity': 'info',
        'line_number': None,
        'recommendation': f'Ensure {tool} is correctly installed and configured.',
    }
