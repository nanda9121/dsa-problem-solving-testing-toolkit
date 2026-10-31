from runner import run_python, evaluate_solution, normalize_output


def test_successful_execution():
    result = run_python("n = int(input())\nprint(n * 2)", "4")
    assert result["status"] == "Completed"
    assert result["stdout"].strip() == "8"


def test_runtime_error():
    result = run_python("print(1 / 0)")
    assert result["status"] == "Runtime Error"


def test_timeout():
    result = run_python("while True:\n    pass", timeout=0.2)
    assert result["status"] == "Time Limit Exceeded"


def test_output_normalization():
    assert normalize_output(" 1 2  \n3 \n") == "1 2\n3"


def test_evaluation():
    code = "a, b = map(int, input().split())\nprint(a + b)"
    report = evaluate_solution(code, [
        {"input": "1 2", "expected": "3", "hidden": False},
        {"input": "4 5", "expected": "9", "hidden": True},
    ])
    assert report["status"] == "Accepted"
    assert report["passed"] == 2
