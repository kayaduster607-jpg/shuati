"""Smoke-test the real Flask routes using disposable data, without a server.

Run from the repository root: python scripts/verify_api.py
Requires the same Flask and Flask-Cors dependencies as app.py.
"""

from contextlib import redirect_stdout
from importlib import util
import io
import json
import os
from pathlib import Path
import sys
from tempfile import TemporaryDirectory


ROOT = Path(__file__).resolve().parents[1]
CHECKS = 0


def check(condition, description):
    """Fail with a specific behavior while keeping credentials out of output."""
    global CHECKS
    CHECKS += 1
    if not condition:
        raise AssertionError(description)


def load_app(data_directory):
    """Import app.py after redirecting all account and content storage."""
    os.environ["DATA_DIR"] = str(data_directory)
    spec = util.spec_from_file_location("shuati_release_app", ROOT / "app.py")
    module = util.module_from_spec(spec)
    sys.modules[spec.name] = module
    # The application logs its default demo accounts on first initialization.
    with redirect_stdout(io.StringIO()):
        spec.loader.exec_module(module)
    module.app.config["TESTING"] = True
    return module


def login(client, username, password):
    """Return a test-only authorization header; never print the token."""
    response = client.post("/api/auth/login", json={"username": username, "password": password})
    check(response.status_code == 200, "demo account login")
    return {"Authorization": "Bearer " + response.json["token"]}


def verify_auth(client):
    """Check static serving, failed login, identity and administrator access."""
    check(client.get("/").status_code == 200, "serve deployment frontend")
    check(client.get("/api/banks").status_code == 401, "deny anonymous data access")
    check(client.post("/api/auth/login", json={"username": "admin", "password": "invalid"}).status_code == 401, "deny wrong password")
    admin = login(client, "admin", "admin123")
    user = login(client, "user", "123456")
    other = login(client, "user2", "123456")
    check(client.get("/api/auth/me", headers=user).json["username"] == "user", "read authenticated identity")
    check(client.get("/api/admin/users", headers=user).status_code == 403, "deny non-admin user management")
    check(len(client.get("/api/admin/users", headers=admin).json) == 4, "initialize four demo accounts")
    return admin, user, other


def verify_question_flow(client, user, other):
    """Exercise bank creation, batch deduplication, editing and account isolation."""
    bank = client.post("/api/banks", headers=user, json={"name": "Release smoke bank"}).json
    bank_id = bank["id"]
    check(len(client.get("/api/banks", headers=user).json) == 1, "persist a bank")
    check(client.get("/api/banks", headers=other).json == [], "isolate banks by account")
    question = {"type": "single_choice", "content": "Which language powers Flask?", "options": ["Python", "SQL"], "answer": "A"}
    response = client.post("/api/questions", headers=user, json={"bank_id": bank_id, "questions": [question, question]})
    check(response.json == {"added": 1, "skipped": 1}, "deduplicate the same batch")
    questions = client.get("/api/questions", headers=user, query_string={"bank_id": bank_id}).json
    check(len(questions) == 1, "filter questions by bank")
    check(client.get("/api/questions", headers=other).json == [], "isolate questions by account")
    question_id = questions[0]["id"]
    client.put(f"/api/questions/{question_id}", headers=user, json={"explanation": "Flask is a Python framework."})
    check(client.get("/api/questions", headers=user).json[0]["explanation"].startswith("Flask"), "persist question edits")
    return bank_id, question_id


def verify_records_and_progress(client, user, question_id):
    """Check answer persistence and resumable practice lifecycle."""
    response = client.post("/api/records", headers=user, json={"records": [{"question_id": question_id, "is_correct": True, "user_answer": "A"}]})
    check(response.json["count"] == 1, "append answer records")
    check(client.get("/api/records", headers=user).json[0]["is_correct"] is True, "load answer records")
    progress = {"mode": "normal", "index": 1, "answers": {"0": "A"}}
    client.put("/api/saved-practice", headers=user, json=progress)
    check(client.get("/api/saved-practice", headers=user).json == progress, "restore saved practice")
    client.delete("/api/saved-practice", headers=user)
    check(not client.get("/api/saved-practice", headers=user).json, "clear saved practice")


def verify_admin_and_cleanup(client, admin, user, bank_id):
    """Verify account administration and clean up only disposable test content."""
    response = client.post("/api/admin/users", headers=admin, json={"username": "release-smoke-user", "password": "smoke-password", "role": "user"})
    check(response.status_code == 200, "create user as administrator")
    user_id = response.json["user"]["id"]
    client.post(f"/api/admin/users/{user_id}/reset-password", headers=admin, json={"password": "smoke-new-password"})
    temporary_user = login(client, "release-smoke-user", "smoke-new-password")
    check(client.delete("/api/admin/users/admin1", headers=admin).status_code == 400, "prevent deleting the current administrator")
    check(len(client.get("/api/admin/stats", headers=admin).json) == 5, "read account data statistics")
    client.delete(f"/api/admin/users/{user_id}", headers=admin)
    check(client.get("/api/auth/me", headers=temporary_user).status_code == 401, "deny a deleted account")
    client.delete(f"/api/banks/{bank_id}", headers=user)
    check(client.get("/api/questions", headers=user).json == [], "delete a bank's questions")
    client.post("/api/auth/logout", headers=user)
    check(client.get("/api/auth/me", headers=user).status_code == 401, "invalidate a logged-out token")


def main():
    """Run all checks in one isolated directory and leave no real user changes."""
    with TemporaryDirectory(prefix="shuati-smoke-") as directory:
        module = load_app(Path(directory))
        client = module.app.test_client()
        admin, user, other = verify_auth(client)
        bank_id, question_id = verify_question_flow(client, user, other)
        verify_records_and_progress(client, user, question_id)
        verify_admin_and_cleanup(client, admin, user, bank_id)
        check((Path(directory) / "users.json").exists(), "write to the isolated data directory")
    print(json.dumps({"checks_passed": CHECKS, "real_user_data_touched": False}))


if __name__ == "__main__":
    main()
