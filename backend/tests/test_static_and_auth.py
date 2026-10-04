import base64

from fastapi.testclient import TestClient

from app.auth import BasicAuthMiddleware
from app.config import Settings
from app.main import app


def _basic(user_pass: str) -> dict[str, str]:
    return {"Authorization": "Basic " + base64.b64encode(user_pass.encode()).decode()}


def test_postgres_scheme_is_rewritten_for_psycopg(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://u:p@host:5432/db")
    monkeypatch.delenv("HUB_DATABASE_URL", raising=False)
    assert Settings(_env_file=None).database_url == "postgresql+psycopg://u:p@host:5432/db"


def test_hub_database_url_wins_over_database_url(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgres://fly/db")
    monkeypatch.setenv("HUB_DATABASE_URL", "postgresql+psycopg://local/db")
    assert Settings(_env_file=None).database_url == "postgresql+psycopg://local/db"


def test_basic_auth_middleware(client):
    gated = BasicAuthMiddleware(app, credentials="me:secret", exempt_paths=("/api/health",))
    c = TestClient(gated)
    assert c.get("/api/health").status_code == 200
    r = c.get("/api/buckets")
    assert r.status_code == 401
    assert r.headers["www-authenticate"].startswith("Basic")
    assert c.get("/api/buckets", headers=_basic("me:wrong")).status_code == 401
    assert c.get("/api/buckets", headers=_basic("me:secret")).status_code == 200


def test_spa_fallback_serves_index_and_files(tmp_path, client):
    (tmp_path / "index.html").write_text("<html>hub</html>")
    (tmp_path / "main.js").write_text("console.log(1)")
    from app import main

    main.mount_static(str(tmp_path))
    try:
        assert client.get("/plan").text == "<html>hub</html>"
        assert client.get("/main.js").text == "console.log(1)"
        assert client.get("/api/nope").status_code == 404
        assert client.get("/api/health").status_code == 200
        # Path traversal falls back to index.html rather than leaving the static root.
        (tmp_path.parent / "outside.txt").write_text("secret")
        r = client.get("/../outside.txt")
        assert r.status_code == 200 and r.text == "<html>hub</html>"
        r = client.get("/%2e%2e/outside.txt")
        assert r.status_code == 200 and r.text == "<html>hub</html>"
    finally:
        # Remove the catch-all so other tests keep their 404s for unknown API paths.
        app.router.routes[:] = [
            r for r in app.router.routes if getattr(r, "name", "") not in ("spa", "assets")
        ]
