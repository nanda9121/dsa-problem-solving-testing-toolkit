# AlgoTest — DSA Problem-Solving & Testing Toolkit

A local-first DSA practice platform built with Python, Flask, SQLite, HTML, CSS and JavaScript.

## Features

- Browse curated DSA problems by topic and difficulty.
- Read problem statements, examples and constraints.
- Write Python solutions in a browser-based editor.
- Run a custom input or submit against visible + hidden test cases.
- See per-test-case pass/fail results and execution time.
- Store submission history and track solved problems.
- View dashboard statistics.
- Seeded starter problem set.

## Requirements

- Python 3.11 or newer
- pip
- A modern browser

## Setup (Windows PowerShell)

```powershell
cd AlgoTest
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python app.py
```

Open http://127.0.0.1:5000

If PowerShell blocks activation, run the app without activating:
```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

## Setup (macOS / Linux)

```bash
cd AlgoTest
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python app.py
```

## Run automated tests

```bash
pytest -q
```

## How to use

1. Open the dashboard.
2. Choose a problem.
3. Write a complete Python program that reads from standard input and prints the answer to standard output.
4. Click **Run custom input** to test your own input.
5. Click **Submit solution** to run all test cases and save the result.
6. Review your submission history and dashboard statistics.

### Input/output contract

Each problem provides an input format and expected output format. Your submitted program is executed as a separate Python process. It must read `sys.stdin` and write its answer to `sys.stdout`.

Example for Two Sum:
```python
nums = list(map(int, input().split()))
target = int(input())

seen = {}
for i, value in enumerate(nums):
    need = target - value
    if need in seen:
        print(seen[need], i)
        break
    seen[value] = i
```

## Project structure

```text
AlgoTest/
├── app.py
├── database.py
├── runner.py
├── seed_data.py
├── requirements.txt
├── pytest.ini
├── README.md
├── instance/                 # SQLite database created at runtime
├── templates/
│   ├── base.html
│   ├── index.html
│   └── problem.html
├── static/
│   ├── css/style.css
│   └── js/app.js
└── tests/
    ├── conftest.py
    ├── test_runner.py
    └── test_routes.py
```

## API overview

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/api/problems` | List problems |
| GET | `/api/problems/<id>` | Problem details |
| POST | `/api/run` | Run one custom input |
| POST | `/api/submit` | Evaluate all test cases and save submission |
| GET | `/api/stats` | Dashboard statistics |
| GET | `/api/submissions/<problem_id>` | Submission history |

## Safety and deployment notes

**This starter is intended for local use by one trusted user.** It executes Python code supplied through the UI. A subprocess timeout is not a security sandbox: untrusted code may still access files, environment data, or the network.

- Keep the Flask server bound to `127.0.0.1`.
- Do not expose this app directly to the public internet.
- Do not deploy the code execution endpoint to a public hosting service.
- For a public version, move execution into disposable containers or a dedicated sandbox service with CPU, memory, process, filesystem and network restrictions; add authentication, CSRF protection, rate limiting and queue limits.
- The included GitHub workflow tests the project; GitHub Pages can host documentation, not this dynamic Flask application.

## GitHub

```bash
git init
git add .
git commit -m "Initial AlgoTest implementation"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/AlgoTest.git
git push -u origin main
```

Enable GitHub Actions under **Settings → Actions** if workflows are restricted. The included workflow runs pytest on pushes and pull requests.

## Next improvements

- Add user accounts and per-user progress.
- Add more DSA questions and curated tags.
- Add language adapters for Java and C++.
- Add a hardened container-based execution service.
- Add complexity analysis guidance and editorial solutions.
