"""
Standalone Mythril runner — executed inside the venv-mythril environment.

Usage:  venv-mythril/bin/python _mythril_runner_script.py <path/to/contract.sol> [timeout_seconds]

Exits 0 and prints a JSON object to stdout:
    {"success": true,  "issues": [...]}
    {"success": false, "error": "<message>"}
"""
import json
import sys


def run(sol_file: str, timeout: int = 60) -> dict:
    from mythril.mythril import MythrilAnalyzer, MythrilDisassembler

    disassembler = MythrilDisassembler(eth=None, solc_version=None)
    disassembler.load_from_solidity([sol_file])

    analyzer = MythrilAnalyzer(
        strategy="dfs",
        disassembler=disassembler,
        execution_timeout=timeout,
        max_depth=22,
        loop_bound=3,
    )
    report = analyzer.fire_lasers(modules=None, transaction_count=2)

    issues = []
    for issue in report.issues:
        issues.append(
            {
                "swc_id": issue.swc_id,
                "title": issue.title,
                "severity": getattr(issue, "severity", "Medium"),
                "description_long": issue.description_long or "",
                "description_short": issue.description_short or "",
                "lineno": getattr(issue, "lineno", None),
                "code": getattr(issue, "code", ""),
                "function": getattr(issue, "function", ""),
                "address": getattr(issue, "address", None),
            }
        )

    return {"success": True, "issues": issues}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Usage: script.py <sol_file> [timeout]"}))
        sys.exit(1)

    sol_file = sys.argv[1]
    timeout = int(sys.argv[2]) if len(sys.argv) > 2 else 60

    try:
        result = run(sol_file, timeout)
        print(json.dumps(result))
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}))
        sys.exit(1)
