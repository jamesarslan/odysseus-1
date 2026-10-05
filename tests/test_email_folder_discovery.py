"""Folder discovery must preserve real mailbox identities across cache paths."""

import asyncio
from contextlib import contextmanager

import pytest


class FolderConnection:
    def __init__(self):
        self.status = "OK"
        self.calls = []
        self.lines = [
            rb'(\Noselect) "/" "[Gmail]"',
            rb'(\HasNoChildren) "/" "INBOX"',
            rb'(\HasNoChildren \Sent) "/" "[Gmail]/&BB4EQgQ,BEAEMAQyBDsENQQ9BD0ESwQ1-"',
            rb'(\All) "/" "[Gmail]/All Mail"',
            rb'(\Trash) "/" "[Gmail]/Bin"',
            rb'() "/" "Sent invoices"',
        ]

    def list(self):
        self.calls.append(("list",))
        return self.status, self.lines

    def select(self, name, readonly=False):
        self.calls.append(("select", name, readonly))
        return ("NO", []) if name == '"Sent"' else ("OK", [b"0"])

    def uid(self, command, *args):
        self.calls.append((command, *args))
        if command == "SEARCH":
            return "OK", [b""]
        raise AssertionError(command)

    def noop(self):
        return "OK", []

    def logout(self):
        pass


@pytest.fixture
def folder_routes(monkeypatch, tmp_path):
    from routes import email_helpers as helpers, email_routes as routes

    monkeypatch.setattr(helpers, "SCHEDULED_DB", tmp_path / "mail.db")
    monkeypatch.setattr(routes, "SCHEDULED_DB", tmp_path / "mail.db")
    monkeypatch.setattr(helpers, "_POOL_HOOKS", {})
    monkeypatch.setattr(routes, "_POOL_HOOKS", helpers._POOL_HOOKS)
    helpers._init_scheduled_db()
    monkeypatch.setattr(routes, "_start_poller", lambda: None)
    monkeypatch.setattr(routes, "_record_email_received_events", lambda *_args: None)
    conn = FolderConnection()
    scopes = []

    @contextmanager
    def connect(account_id=None, owner=""):
        scopes.append((account_id, owner))
        yield conn

    monkeypatch.setattr(routes, "_imap", connect)
    monkeypatch.setattr(routes, "_imap_connect", lambda *_args, **_kwargs: conn)
    router = routes.setup_email_routes()
    endpoints = {r.path: r.endpoint for r in router.routes if "GET" in r.methods}
    return routes, conn, scopes, endpoints


async def discover(endpoints, *, cached_only=0, account_id="gmail", owner="alice"):
    return await endpoints["/api/email/folders"](
        account_id=account_id, cached_only=cached_only, owner=owner,
    )


@pytest.mark.asyncio
async def test_cold_cached_only_returns_pending_without_fabricated_folders(folder_routes):
    _, conn, _, endpoints = folder_routes
    result = await discover(endpoints, cached_only=1)
    assert result["folders"] == []
    assert result["roles"] == {}
    assert result["sync"]["pending"] is True
    assert conn.calls == []


@pytest.mark.asyncio
async def test_live_discovery_roles_display_names_and_scoped_cache(folder_routes):
    _, conn, scopes, endpoints = folder_routes
    result = await discover(endpoints)
    assert "[Gmail]" not in result["folders"]
    sent = next(name for name, role in result["roles"].items() if role == "sent")
    assert result["display_names"][sent] == "[Gmail]/Отправленные"
    assert result["roles"]["[Gmail]/Bin"] == "trash"
    assert "Sent invoices" not in result["roles"]
    cached = await discover(endpoints, cached_only=1)
    assert cached["folders"] == result["folders"]
    assert cached["roles"] == result["roles"]
    assert cached["sync"]["source"] == "folder_cache"
    assert scopes == [("gmail", "alice")]
    assert conn.calls == [("list",)]
    other_owner = await discover(endpoints, cached_only=1, owner="bob")
    other_account = await discover(endpoints, cached_only=1, account_id="other")
    assert other_owner["folders"] == other_account["folders"] == []


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["timeout", "server_error"])
async def test_expired_discovery_survives_failed_refresh(folder_routes, monkeypatch, failure):
    routes, conn, _, endpoints = folder_routes
    clock = [100.0]
    monkeypatch.setattr(routes.time, "monotonic", lambda: clock[0])
    before = await discover(endpoints)
    clock[0] += 301.0
    stale = await discover(endpoints, cached_only=1)
    assert stale["folders"] == before["folders"]
    assert stale["sync"]["source"] == "folder_cache_stale"
    if failure == "timeout":
        async def timeout(coro, timeout):
            coro.close()
            raise asyncio.TimeoutError
        monkeypatch.setattr(asyncio, "wait_for", timeout)
    else:
        conn.status = "NO"
    after = await discover(endpoints)
    assert after["folders"] == before["folders"]
    assert after["roles"] == before["roles"]
    assert after["sync"]["source"] == "folder_cache_stale"
    assert after["sync"]["warning"]


@pytest.mark.asyncio
@pytest.mark.parametrize("failure", ["timeout", "server_error"])
async def test_failed_cold_discovery_never_invents_destinations(folder_routes, monkeypatch, failure):
    _, conn, _, endpoints = folder_routes
    if failure == "timeout":
        async def timeout(coro, timeout):
            coro.close()
            raise asyncio.TimeoutError
        monkeypatch.setattr(asyncio, "wait_for", timeout)
    else:
        conn.status = "NO"
    result = await discover(endpoints)
    assert result["folders"] == []
    assert result["roles"] == {}
    assert result["error"]
    assert (await discover(endpoints, cached_only=1))["sync"]["pending"]


@pytest.mark.asyncio
async def test_http_sent_alias_selects_discovered_mailbox_and_returns_identity(folder_routes):
    _, conn, _, endpoints = folder_routes
    result = await endpoints["/api/email/list"](
        folder="Sent", limit=1, offset=0, filter="all", from_addr=None,
        account_id="gmail", has_attachments=0, cached_only=0,
        cache_bust=None, owner="alice",
    )
    assert not result.get("error")
    assert result["folder"].startswith("[Gmail]/&")
    assert ("select", f'"{result["folder"]}"', True) in conn.calls
    assert ("select", '"Sent"', True) not in conn.calls


@pytest.mark.asyncio
async def test_http_search_sent_alias_selects_discovered_mailbox(folder_routes):
    _, conn, _, endpoints = folder_routes
    result = endpoints["/api/email/search"](
        q="example", folder="Sent", limit=1, account_id="gmail",
        local_only=False, scope="folder", owner="alice",
    )
    assert not result.get("error")
    assert result["folder"].startswith("[Gmail]/&")
    assert ("select", f'"{result["folder"]}"', True) in conn.calls
