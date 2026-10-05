"""Statik fayl uzatish testi — ``resolve_static`` + ``serve_path`` (traversal-xavfsiz)."""

from __future__ import annotations

import json
from pathlib import Path

from doda.container import build_container
from doda.interfaces.api.server import resolve_static, serve_path


def _make_site(tmp_path: Path) -> Path:
    (tmp_path / "index.html").write_text("<h1>DODA</h1>", "utf-8")
    (tmp_path / "app.js").write_text("console.log(1)", "utf-8")
    (tmp_path / "secret.txt").write_text("maxfiy", "utf-8")
    return tmp_path


def test_resolve_root_serves_index(tmp_path: Path) -> None:
    _make_site(tmp_path)
    f = resolve_static(tmp_path, "/")
    assert f is not None
    assert b"DODA" in f.body
    assert f.content_type.startswith("text/html")
    assert "charset=utf-8" in f.content_type


def test_resolve_named_file_with_query(tmp_path: Path) -> None:
    _make_site(tmp_path)
    f = resolve_static(tmp_path, "/app.js?v=3")
    assert f is not None
    assert b"console.log" in f.body


def test_resolve_missing_returns_none(tmp_path: Path) -> None:
    _make_site(tmp_path)
    assert resolve_static(tmp_path, "/yoq.html") is None


def test_resolve_traversal_rejected(tmp_path: Path) -> None:
    site = tmp_path / "site"
    site.mkdir()
    (site / "index.html").write_text("ok", "utf-8")
    (tmp_path / "outside.txt").write_text("sir", "utf-8")
    assert resolve_static(site, "/../outside.txt") is None


def test_serve_path_health(tmp_path: Path) -> None:
    _make_site(tmp_path)
    code, ctype, body = serve_path(build_container(), tmp_path, "/health")
    assert code == 200
    assert "application/json" in ctype
    assert json.loads(body)["status"] == "ok"


def test_serve_path_status(tmp_path: Path) -> None:
    _make_site(tmp_path)
    code, _ctype, body = serve_path(build_container(), tmp_path, "/status")
    assert code == 200
    assert json.loads(body)["service"] == "doda"


def test_serve_path_static_and_404(tmp_path: Path) -> None:
    _make_site(tmp_path)
    container = build_container()
    code, _ctype, body = serve_path(container, tmp_path, "/")
    assert code == 200
    assert b"DODA" in body
    code2, _, body2 = serve_path(container, tmp_path, "/nope")
    assert code2 == 404
    assert b"404" in body2
