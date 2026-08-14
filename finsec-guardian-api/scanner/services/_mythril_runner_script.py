from __future__ import annotations

import argparse
import json
import sys


def _build_cmd_args(
    timeout: int,
) -> argparse.Namespace:
    """
    Build the argparse namespace expected by Mythril 0.24.8.
    """
    return argparse.Namespace(
        no_onchain_data=True,
        max_depth=22,
        execution_timeout=timeout,
        loop_bound=3,
        create_timeout=None,
        disable_dependency_pruning=False,
        custom_modules_directory="",
        pruning_factor=None,
        solver_timeout=10_000,
        parallel_solving=False,
        unconstrained_storage=False,
        call_depth_limit=3,
        disable_iprof=False,
        solver_log=None,
        transaction_sequences=None,
        disable_coverage_strategy=False,
        disable_mutation_pruner=False,
        enable_summaries=False,
        enable_state_merging=False,
    )


def run(
    sol_file: str,
    timeout: int = 60,
) -> dict:
    """
    Execute Mythril against a Solidity source file.

    Returns a JSON-serializable dictionary containing the raw,
    normalized Mythril issue dictionaries.
    """
    from mythril.mythril import (
        MythrilAnalyzer,
        MythrilDisassembler,
    )

    disassembler = MythrilDisassembler(
        eth=None,
        solc_version=None,
    )

    disassembler.load_from_solidity(
        [sol_file],
    )

    analyzer = MythrilAnalyzer(
        disassembler=disassembler,
        cmd_args=_build_cmd_args(timeout),
        strategy="dfs",
    )

    report = analyzer.fire_lasers(
        modules=None,
        transaction_count=2,
    )

    # Mythril can capture internal failures in Report.exceptions
    # instead of raising them.
    if report.exceptions:
        return {
            "success": False,
            "issues": [],
            "error": (
                "Mythril analysis failed: "
                + "\n".join(report.exceptions)
            ),
        }

    # Mythril 0.24.8 stores issues as Dict[bytes, Issue].
    # Issue.as_dict is the stable normalized representation.
    issues = [
        issue.as_dict
        for issue in report.issues.values()
    ]

    return {
        "success": True,
        "issues": issues,
    }


def main() -> int:
    if len(sys.argv) < 2:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": (
                        "Usage: script.py "
                        "<sol_file> [timeout]"
                    ),
                }
            )
        )
        return 1

    sol_file = sys.argv[1]

    try:
        timeout = (
            int(sys.argv[2])
            if len(sys.argv) > 2
            else 60
        )
    except ValueError:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "Timeout must be an integer.",
                }
            )
        )
        return 1

    try:
        result = run(
            sol_file,
            timeout,
        )

        print(
            json.dumps(result),
        )

        return 0

    except Exception as exc:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": str(exc),
                }
            )
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())