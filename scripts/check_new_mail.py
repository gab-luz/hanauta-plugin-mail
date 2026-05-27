#!/usr/bin/env python3
from __future__ import annotations

import json
import imaplib
import os
import subprocess
from pathlib import Path

STATE_DIR = Path.home() / ".local" / "state" / "hanauta" / "email-client"
STORAGE_PATH = STATE_DIR / "storage.json"
SERVICE_STATE_PATH = STATE_DIR / "mail_notify_state.json"
DEFAULT_DB_PATH = STATE_DIR / "mail.sqlite3"


def load_storage_config() -> dict[str, str]:
    try:
        payload = json.loads(STORAGE_PATH.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("invalid storage config")
    except Exception:
        payload = {}
    return {
        "db_path": str(payload.get("db_path", DEFAULT_DB_PATH)).strip() or str(DEFAULT_DB_PATH),
    }


def load_accounts(db_path: Path) -> list[dict]:
    import sqlite3

    if not db_path.exists():
        return []
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            """
            SELECT id, label, email_address, username, password, imap_host, imap_port, imap_ssl,
                   notify_enabled, poll_interval_seconds
            FROM accounts
            """
        ).fetchall()
        return [dict(row) for row in rows]
    except Exception:
        return []
    finally:
        conn.close()


def load_state() -> dict[str, int]:
    try:
        payload = json.loads(SERVICE_STATE_PATH.read_text(encoding="utf-8"))
        if isinstance(payload, dict):
            return {str(k): int(v) for k, v in payload.items()}
    except Exception:
        pass
    return {}


def save_state(state: dict[str, int]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    SERVICE_STATE_PATH.write_text(json.dumps(state, ensure_ascii=True, indent=2), encoding="utf-8")


def notify(summary: str, body: str) -> None:
    cmd = ["notify-send", "-a", "Hanauta Mail", "-u", "normal", summary, body]
    try:
        subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True)
    except Exception:
        pass


def account_label(account: dict) -> str:
    label = str(account.get("label", "")).strip()
    if label:
        return label
    return str(account.get("email_address", "Mail account")).strip() or "Mail account"


def unread_count(account: dict) -> int | None:
    host = str(account.get("imap_host", "")).strip()
    user = str(account.get("username", "")).strip() or str(account.get("email_address", "")).strip()
    password = str(account.get("password", ""))
    port = int(account.get("imap_port", 993) or 993)
    use_ssl = bool(int(account.get("imap_ssl", 1) or 0))
    if not host or not user or not password:
        return None

    client = None
    try:
        if use_ssl:
            client = imaplib.IMAP4_SSL(host, port)
        else:
            client = imaplib.IMAP4(host, port)
        client.login(user, password)
        status, _ = client.select("INBOX", readonly=True)
        if status != "OK":
            return None
        status, data = client.search(None, "UNSEEN")
        if status != "OK":
            return None
        raw = data[0] if data else b""
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8", "ignore")
        raw = str(raw).strip()
        if not raw:
            return 0
        return len([x for x in raw.split() if x])
    except Exception:
        return None
    finally:
        if client is not None:
            try:
                client.logout()
            except Exception:
                pass


def main() -> int:
    db_path = Path(load_storage_config()["db_path"]).expanduser()
    accounts = load_accounts(db_path)
    if not accounts:
        return 0

    state = load_state()
    changed = False

    for account in accounts:
        if not bool(int(account.get("notify_enabled", 1) or 0)):
            continue
        account_id = int(account.get("id", 0) or 0)
        if account_id <= 0:
            continue
        key = str(account_id)
        count = unread_count(account)
        if count is None:
            continue
        prev = int(state.get(key, count))
        if count > prev:
            delta = count - prev
            label = account_label(account)
            if delta == 1:
                notify("Novo e-mail", f"{label}: 1 nova mensagem não lida")
            else:
                notify("Novos e-mails", f"{label}: {delta} novas mensagens não lidas")
        state[key] = count
        changed = True

    if changed:
        save_state(state)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
