"""
Standalone Slither runner — executed inside the venv-slither environment.

Usage:  venv-slither/bin/python _slither_runner_script.py <path/to/contract.sol>

Exits 0 and prints a JSON object to stdout:
    {"success": true,  "detectors": [...]}
    {"success": false, "error": "<message>"}
"""
import inspect
import json
import sys


def _load_detector_classes():
    from slither.detectors import all_detectors
    from slither.detectors.abstract_detector import AbstractDetector

    return [
        cls
        for name in dir(all_detectors)
        if inspect.isclass(cls := getattr(all_detectors, name))
        and issubclass(cls, AbstractDetector)
    ]


def run(sol_file: str) -> dict:
    from slither import Slither

    slither = Slither(sol_file)
    for cls in _load_detector_classes():
        slither.register_detector(cls)

    batches = slither.run_detectors()
    detectors = [item for batch in (batches or []) if batch for item in batch]
    return {"success": True, "detectors": detectors}


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"success": False, "error": "Usage: script.py <sol_file>"}))
        sys.exit(1)

    try:
        result = run(sys.argv[1])
        print(json.dumps(result))
    except Exception as exc:
        print(json.dumps({"success": False, "error": str(exc)}))
        sys.exit(1)
