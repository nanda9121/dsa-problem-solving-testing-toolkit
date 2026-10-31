import pytest
import database
from app import app


@pytest.fixture()
def client(tmp_path, monkeypatch):
    db_file = tmp_path / "test.sqlite3"
    monkeypatch.setattr(database, "DB_PATH", db_file)
    database.init_db()
    from seed_data import PROBLEMS
    database.seed_problems(PROBLEMS)
    app.config.update(TESTING=True)
    with app.test_client() as client:
        yield client
