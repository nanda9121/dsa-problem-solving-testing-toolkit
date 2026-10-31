import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

MAX_CODE_CHARS = 50_000
MAX_INPUT_CHARS = 20_000
MAX_OUTPUT_CHARS = 30_000
DEFAULT_TIMEOUT_SECONDS = 2.0


class CodeExecutionError(Exception):
    pass


def run_python(code, stdin="", timeout=DEFAULT_TIMEOUT_SECONDS):
    """Run trusted local Python code with a wall-clock timeout.

    This is NOT a security sandbox. Do not expose this function to untrusted users.
    """
    if not isinstance(code, str) or not code.strip():
        raise CodeExecutionError("Please enter a Python solution.")
    if len(code) > MAX_CODE_CHARS:
        raise CodeExecutionError("Code is too large.")
    if not isinstance(stdin, str) or len(stdin) > MAX_INPUT_CHARS:
        raise CodeExecutionError("Input is too large.")

    started = time.perf_counter()
    with tempfile.TemporaryDirectory(prefix="algotest_") as temp_dir:
        script_path = Path(temp_dir) / "solution.py"
        script_path.write_text(code, encoding="utf-8")
        env = {
            "PATH": os.environ.get("PATH", ""),
            "PYTHONIOENCODING": "utf-8",
            "PYTHONDONTWRITEBYTECODE": "1",
        }
        try:
            completed = subprocess.run(
                [sys.executable, "-I", str(script_path)],
                input=stdin,
                text=True,
                capture_output=True,
                cwd=temp_dir,
                env=env,
                timeout=timeout,
                check=False,
            )
        except subprocess.TimeoutExpired:
            return {
                "status": "Time Limit Exceeded",
                "stdout": "",
                "stderr": f"Execution exceeded the {timeout:g}-second time limit.",
                "runtime_ms": round((time.perf_counter() - started) * 1000, 2),
            }

    runtime_ms = round((time.perf_counter() - started) * 1000, 2)
    stdout = completed.stdout[:MAX_OUTPUT_CHARS]
    stderr = completed.stderr[:MAX_OUTPUT_CHARS]
    if len(completed.stdout) > MAX_OUTPUT_CHARS or len(completed.stderr) > MAX_OUTPUT_CHARS:
        return {
            "status": "Output Limit Exceeded",
            "stdout": stdout,
            "stderr": "Program output exceeded the configured limit.",
            "runtime_ms": runtime_ms,
        }
    return {
        "status": "Runtime Error" if completed.returncode != 0 else "Completed",
        "stdout": stdout,
        "stderr": stderr,
        "runtime_ms": runtime_ms,
        "returncode": completed.returncode,
    }


def normalize_output(value):
    return "\n".join(line.rstrip() for line in value.strip().splitlines())


def evaluate_solution(code, test_cases):
    results = []
    total_runtime = 0.0
    for index, case in enumerate(test_cases, start=1):
        result = run_python(code, case["input"])
        total_runtime += result["runtime_ms"]
        passed = (
            result["status"] == "Completed"
            and normalize_output(result["stdout"]) == normalize_output(case["expected"])
        )
        item = {
            "case": index,
            "passed": passed,
            "status": "Passed" if passed else result["status"] if result["status"] != "Completed" else "Wrong Answer",
            "runtime_ms": result["runtime_ms"],
        }
        if not case.get("hidden", False):
            item["input"] = case["input"]
            item["expected"] = case["expected"]
            item["actual"] = result["stdout"].strip()
            item["stderr"] = result["stderr"]
        results.append(item)
        if not passed:
            # Continue to show a complete report, while each process remains separately timed.
            continue

    passed_count = sum(1 for item in results if item["passed"])
    return {
        "results": results,
        "passed": passed_count,
        "total": len(results),
        "runtime_ms": round(total_runtime, 2),
        "status": "Accepted" if results and passed_count == len(results) else "Rejected",
    }
