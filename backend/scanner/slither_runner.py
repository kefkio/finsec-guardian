"""
Slither integration for Solidity static analysis.

Writes source code to a temporary file, runs it through the Slither Python API
with all built-in detectors, and normalises the results into a list of
Finding-compatible dicts ready to be saved to the database.
"""

import inspect
import logging
import os
import tempfile

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Severity mapping
# ---------------------------------------------------------------------------

# Slither DetectorClassification → our severity vocabulary
_CLASSIFICATION_SEVERITY = {
    0: 'high',        # HIGH
    1: 'medium',      # MEDIUM
    2: 'low',         # LOW
    3: 'info',        # INFORMATIONAL
    4: 'info',        # OPTIMIZATION
}


def _classification_to_severity(impact_cls, confidence_cls) -> str:
    """Map Slither classification enums to our severity string.

    High-impact + High-confidence detections are elevated to 'critical'.
    """
    impact_val = getattr(impact_cls, 'value', impact_cls)
    confidence_val = getattr(confidence_cls, 'value', confidence_cls)
    if impact_val == 0 and confidence_val == 0:  # HIGH + HIGH
        return 'critical'
    return _CLASSIFICATION_SEVERITY.get(impact_val, 'info')


# ---------------------------------------------------------------------------
# SWC mapping and recommendations
# ---------------------------------------------------------------------------

DETECTOR_TO_SWC: dict[str, str] = {
    'reentrancy-eth': 'SWC-107',
    'reentrancy-no-eth': 'SWC-107',
    'reentrancy-benign': 'SWC-107',
    'reentrancy-events': 'SWC-107',
    'tx-origin': 'SWC-115',
    'suicidal': 'SWC-106',
    'unprotected-upgrade': 'SWC-118',
    'arbitrary-send-eth': 'SWC-105',
    'arbitrary-send-erc20': 'SWC-105',
    'controlled-delegatecall': 'SWC-112',
    'delegatecall-loop': 'SWC-112',
    'msg-value-loop': 'SWC-113',
    'tautology': 'SWC-116',
    'boolean-equality': 'SWC-116',
    'divide-before-multiply': 'SWC-101',
    'unchecked-lowlevel': 'SWC-104',
    'unchecked-send': 'SWC-104',
    'unused-return': 'SWC-104',
    'locked-ether': 'SWC-132',
    'timestamp': 'SWC-116',
    'assembly': 'SWC-127',
    'low-level-calls': 'SWC-111',
    'missing-zero-check': 'SWC-131',
    'shadowing-local': 'SWC-119',
    'shadowing-state': 'SWC-119',
    'shadowing-abstract': 'SWC-119',
    'uninitialized-local': 'SWC-109',
    'uninitialized-state': 'SWC-109',
    'uninitialized-storage': 'SWC-109',
    'write-after-write': 'SWC-101',
}

RECOMMENDATIONS: dict[str, str] = {
    'SWC-107': (
        'Use the checks-effects-interactions pattern. Update state before '
        'calling external contracts. Consider using ReentrancyGuard.'
    ),
    'SWC-115': 'Replace tx.origin with msg.sender for authorization checks.',
    'SWC-106': 'Add access control to selfdestruct. Consider using Ownable or role-based access.',
    'SWC-118': 'Restrict upgrade functions to authorised roles only.',
    'SWC-105': 'Ensure recipients of ETH transfers are restricted to trusted addresses.',
    'SWC-112': 'Avoid delegatecall to untrusted addresses. Validate callee before delegation.',
    'SWC-113': 'Avoid using msg.value inside loops.',
    'SWC-116': 'Do not rely on block.timestamp for critical logic. Use block numbers or Chainlink VRF.',
    'SWC-101': 'Use SafeMath or Solidity 0.8+ built-in overflow protection.',
    'SWC-104': 'Always check return values of low-level calls.',
    'SWC-132': 'Add a withdraw function or ensure the contract can receive and forward ETH.',
    'SWC-127': 'Minimise inline assembly. Document and test thoroughly.',
    'SWC-111': 'Avoid low-level calls where possible. Validate call success.',
    'SWC-131': 'Add zero-address checks before assigning to address state variables.',
    'SWC-119': 'Rename shadowed variables to avoid unintentional overwrites.',
    'SWC-109': 'Initialise all storage and local variables before use.',
    'SWC-103': 'Ensure the contract compiles cleanly with the target solc version.',
}


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def run_slither(source_code: str) -> list[dict]:
    """Analyse *source_code* with Slither and return a list of finding dicts.

    Each returned dict is compatible with ``scanner.models.Finding`` fields:
        swc_id, title, description, severity, line_number, recommendation

    Errors (compilation failures, missing solc, timeouts) are returned as
    single-item lists with an appropriate informational finding rather than
    raising, so the scan always receives *some* result.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        sol_path = os.path.join(tmpdir, 'contract.sol')
        with open(sol_path, 'w', encoding='utf-8') as fh:
            fh.write(source_code)

        try:
            return _run_python_api(sol_path)
        except Exception as exc:
            return _handle_top_level_error(exc)


# ---------------------------------------------------------------------------
# Slither Python-API runner
# ---------------------------------------------------------------------------

def _run_python_api(sol_path: str) -> list[dict]:
    """Use the Slither Python API to analyse *sol_path*."""
    # Late import so Django startup does not require solc to be present.
    from slither import Slither  # noqa: PLC0415
    import slither.detectors.all_detectors as all_detectors  # noqa: PLC0415

    slither_obj = Slither(sol_path, disable_color=True, solc_disable_warnings=True)

    # Register every built-in detector
    detector_classes = [
        obj for _, obj in inspect.getmembers(all_detectors, inspect.isclass)
    ]
    for cls in detector_classes:
        slither_obj.register_detector(cls)

    results = slither_obj.run_detectors()
    return _parse_detector_results(results)


def _parse_detector_results(results: list) -> list[dict]:
    findings = []
    for detector_result_list in results:
        if not isinstance(detector_result_list, list):
            detector_result_list = [detector_result_list]
        for result in detector_result_list:
            finding = _result_to_finding(result)
            if finding:
                findings.append(finding)
    return findings


def _result_to_finding(result) -> dict | None:
    """Convert a single Slither result Output object to a finding dict."""
    try:
        data = result.data if hasattr(result, 'data') else result
        if not isinstance(data, dict):
            return None

        check = data.get('check', '')
        impact = data.get('impact', 'Informational')
        confidence = data.get('confidence', 'Medium')
        description = data.get('description', '').strip()
        elements = data.get('elements', [])

        line_number = _extract_line(elements)
        swc_id = DETECTOR_TO_SWC.get(check, '')
        severity = _severity_from_strings(impact, confidence)
        title = check.replace('-', ' ').title() if check else data.get('markdown', '')[:80]
        recommendation = RECOMMENDATIONS.get(swc_id, 'Review and fix the identified issue.')

        return {
            'swc_id': swc_id,
            'title': title,
            'description': description,
            'severity': severity,
            'line_number': line_number,
            'recommendation': recommendation,
        }
    except Exception as exc:
        logger.debug('Skipping unparseable result: %s', exc)
        return None


def _severity_from_strings(impact: str, confidence: str) -> str:
    """Convert string impact/confidence (from JSON output) to severity."""
    if impact == 'High' and confidence == 'High':
        return 'critical'
    _map = {'High': 'high', 'Medium': 'medium', 'Low': 'low',
            'Informational': 'info', 'Optimization': 'info'}
    return _map.get(impact, 'info')


def _extract_line(elements: list) -> int | None:
    """Return the first source line number found in the elements list."""
    for el in elements:
        if not isinstance(el, dict):
            continue
        lines = el.get('source_mapping', {}).get('lines', [])
        if lines:
            return lines[0]
    return None


# ---------------------------------------------------------------------------
# Error helpers
# ---------------------------------------------------------------------------

def _handle_top_level_error(exc: Exception) -> list[dict]:
    msg = str(exc)
    logger.warning('Slither analysis failed: %s', msg, exc_info=True)

    # Distinguish compilation errors from infrastructure errors
    compilation_keywords = (
        'solc', 'compilation', 'compile', 'SyntaxError', 'ParserError',
        'TypeError', 'DeclarationError', 'CompilerError', 'crytic',
    )
    if any(kw.lower() in msg.lower() for kw in compilation_keywords):
        return [_compilation_error_finding(msg)]
    return [_error_finding(msg)]


def _compilation_error_finding(detail: str) -> dict:
    return {
        'swc_id': 'SWC-103',
        'title': 'Compilation Error',
        'description': (
            'Slither could not compile the contract.\n\n'
            f'Detail: {detail[:500]}'
        ),
        'severity': 'high',
        'line_number': None,
        'recommendation': RECOMMENDATIONS['SWC-103'],
    }


def _error_finding(detail: str) -> dict:
    return {
        'swc_id': '',
        'title': 'Scanner Error',
        'description': f'An internal error occurred during analysis: {detail[:500]}',
        'severity': 'info',
        'line_number': None,
        'recommendation': (
            'Ensure solc is installed and on your PATH. '
            'Run: solc-select install 0.8.20 && solc-select use 0.8.20'
        ),
    }
