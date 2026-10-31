import os
from flask import Flask, jsonify, render_template, request, abort
from database import (
    init_db, seed_problems, list_problems, get_problem,
    add_submission, get_submissions, get_stats
)
from runner import run_python, evaluate_solution, CodeExecutionError
from seed_data import PROBLEMS

app = Flask(__name__)
app.config["JSON_SORT_KEYS"] = False
app.config["MAX_CONTENT_LENGTH"] = 200_000

init_db()
seed_problems(PROBLEMS)


@app.get("/")
def index():
    return render_template("index.html", stats=get_stats())


@app.get("/problem/<int:problem_id>")
def problem_page(problem_id):
    problem = get_problem(problem_id)
    if not problem:
        abort(404)
    return render_template("problem.html", problem=problem)


@app.get("/api/problems")
def api_problems():
    items = list_problems(
        topic=request.args.get("topic") or None,
        difficulty=request.args.get("difficulty") or None,
        search=request.args.get("search") or None,
    )
    return jsonify(items)


@app.get("/api/problems/<int:problem_id>")
def api_problem(problem_id):
    problem = get_problem(problem_id)
    if not problem:
        return jsonify({"error": "Problem not found"}), 404
    # Test cases are intentionally not returned by the problem detail API.
    safe_problem = {k: v for k, v in problem.items() if k != "tests"}
    return jsonify(safe_problem)


def validate_payload():
    data = request.get_json(silent=True) or {}
    code = data.get("code")
    if not isinstance(code, str):
        return None, None, (jsonify({"error": "A code string is required."}), 400)
    return data, code, None


@app.post("/api/run")
def api_run():
    data, code, error = validate_payload()
    if error:
        return error
    stdin = data.get("stdin", "")
    try:
        result = run_python(code, stdin)
    except CodeExecutionError as exc:
        return jsonify({"error": str(exc)}), 400
    return jsonify(result)


@app.post("/api/submit")
def api_submit():
    data, code, error = validate_payload()
    if error:
        return error
    problem_id = data.get("problem_id")
    if not isinstance(problem_id, int):
        return jsonify({"error": "A valid problem_id is required."}), 400
    problem = get_problem(problem_id)
    if not problem:
        return jsonify({"error": "Problem not found."}), 404
    try:
        report = evaluate_solution(code, problem["tests"])
    except CodeExecutionError as exc:
        return jsonify({"error": str(exc)}), 400
    submission_id = add_submission(
        problem_id, code, report["status"], report["passed"],
        report["total"], report["runtime_ms"]
    )
    report["submission_id"] = submission_id
    return jsonify(report)


@app.get("/api/stats")
def api_stats():
    return jsonify(get_stats())


@app.get("/api/submissions/<int:problem_id>")
def api_problem_submissions(problem_id):
    if not get_problem(problem_id):
        return jsonify({"error": "Problem not found."}), 404
    return jsonify(get_submissions(problem_id))


if __name__ == "__main__":
    # Local-only by design. Do not change to 0.0.0.0 for public hosting.
    app.run(host="127.0.0.1", port=int(os.environ.get("PORT", 5000)), debug=False)
