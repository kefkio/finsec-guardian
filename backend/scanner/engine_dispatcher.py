"""
Engine dispatcher — routes a scan to the correct analysis tool runner.

Each runner is isolated at the subprocess/binary level so that tool-specific
dependencies (e.g. conflicting solc versions, Haskell runtime for Echidna)
do not pollute the shared Django process.

Tool       Binary / module              Isolation strategy
---------  ---------------------------  -----------------------------------------
slither    Slither Python API           Runs in-process via Slither's Python API;
                                        use a separate venv for the whole backend
                                        if you need a different solc version.
mythril    myth CLI (subprocess)        Install in its own venv; set
                                        ANALYSIS_TOOL_VENVS["mythril"] in settings.
echidna    echidna binary (subprocess)  Install the Haskell binary; set
                                        ANALYSIS_TOOL_VENVS["echidna"] in settings.
"""

import logging

logger = logging.getLogger(__name__)

SUPPORTED_TOOLS = ('slither', 'mythril', 'echidna')


def dispatch(tool: str, source_code: str) -> list[dict]:
    """Run *source_code* through *tool* and return a list of finding dicts.

    Args:
        tool:        One of 'slither', 'mythril', 'echidna'.
        source_code: Raw Solidity source text.

    Returns:
        A list of dicts compatible with ``scanner.models.Finding`` fields.
    """
    tool = tool.lower().strip()

    if tool == 'slither':
        from .slither_runner import run_slither
        return run_slither(source_code)

    if tool == 'mythril':
        from .mythril_runner import run_mythril
        return run_mythril(source_code)

    if tool == 'echidna':
        from .echidna_runner import run_echidna
        return run_echidna(source_code)

    logger.warning('Unknown analysis tool requested: %s', tool)
    return [{
        'swc_id': '',
        'title': 'Unknown Analysis Tool',
        'description': (
            f'"{tool}" is not a supported analysis tool. '
            f'Choose one of: {", ".join(SUPPORTED_TOOLS)}.'
        ),
        'severity': 'info',
        'line_number': None,
        'recommendation': f'Set tool to one of: {", ".join(SUPPORTED_TOOLS)}',
    }]
