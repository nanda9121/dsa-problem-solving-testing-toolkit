def test_home_page(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Problem library" in response.data


def test_problem_list(client):
    response = client.get("/api/problems")
    assert response.status_code == 200
    assert len(response.get_json()) >= 8


def test_problem_detail_does_not_expose_tests(client):
    response = client.get("/api/problems/1")
    assert response.status_code == 200
    assert "tests" not in response.get_json()


def test_unknown_problem(client):
    assert client.get("/api/problems/99999").status_code == 404


def test_custom_run(client):
    response = client.post("/api/run", json={"code": "print(input().upper())", "stdin": "hello"})
    assert response.status_code == 200
    assert response.get_json()["stdout"].strip() == "HELLO"


def test_submit_and_history(client):
    response = client.post("/api/submit", json={
        "problem_id": 1,
        "code": "nums = list(map(int, input().split()))\ntarget = int(input())\nseen = {}\nfor i, x in enumerate(nums):\n    if target-x in seen:\n        print(seen[target-x], i)\n        break\n    seen[x] = i"
    })
    assert response.status_code == 200
    assert response.get_json()["status"] == "Accepted"
    history = client.get("/api/submissions/1")
    assert len(history.get_json()) == 1


def test_missing_code(client):
    response = client.post("/api/run", json={"stdin": "x"})
    assert response.status_code == 400
