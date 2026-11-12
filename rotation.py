"""Gestor local de turnos de cuentas."""

from contextlib import closing
from datetime import date
from pathlib import Path
import os
import sqlite3
import sys

if getattr(sys, "frozen", False):
    DATA_DIR = Path(os.environ["LOCALAPPDATA"]) / "RotacionDeCuentas"
else:
    DATA_DIR = Path(__file__).parent

DATABASE = DATA_DIR / "rotacion.sqlite3"
RESULTS = ("TP", "SL", "BE")


def connect():
    db = sqlite3.connect(DATABASE)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db


def initialize():
    with closing(connect()) as db, db:
        db.executescript("""
            CREATE TABLE IF NOT EXISTS accounts (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL UNIQUE,
                created_after INTEGER NOT NULL,
                active INTEGER NOT NULL DEFAULT 1
            );
            CREATE TABLE IF NOT EXISTS window_settings (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                corner TEXT NOT NULL,
                topmost INTEGER NOT NULL CHECK (topmost IN (0, 1))
            );
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                account INTEGER NOT NULL REFERENCES accounts(id),
                day TEXT NOT NULL,
                result TEXT NOT NULL CHECK (result IN ('TP', 'SL', 'BE'))
            );
        """)
        db.execute("BEGIN IMMEDIATE")
        columns = {column["name"] for column in db.execute("PRAGMA table_info(accounts)")}
        if "active" not in columns:
            db.execute("ALTER TABLE accounts ADD COLUMN active INTEGER NOT NULL DEFAULT 1")


def queue(db, day):
    # Cada cuenta espera desde que se añadió o desde su último TP/SL.
    return db.execute("""
        SELECT accounts.id, accounts.name, MAX(CASE WHEN entries.id > accounts.created_after THEN entries.id END) AS last_turn,
               MAX(CASE WHEN entries.day = ? THEN entries.result END) AS exhausted
        FROM accounts
        LEFT JOIN entries ON accounts.id = entries.account
            AND entries.result IN ('TP', 'SL')
        WHERE accounts.active = 1
        GROUP BY accounts.id
        ORDER BY COALESCE(last_turn, accounts.created_after), last_turn IS NULL, accounts.id
    """, (day,)).fetchall()


def latest_id(db):
    return db.execute("SELECT COALESCE(MAX(id), 0) FROM entries").fetchone()[0]


def update(db, form, day):
    # La transacción mantiene la comprobación del turno y la escritura juntas.
    db.execute("BEGIN IMMEDIATE")
    action = form.get("action")
    if action == "add":
        name = form.get("name", "").strip()
        if not 1 <= len(name) <= 80:
            raise ValueError("Escribe un nombre de entre 1 y 80 caracteres.")
        existing = db.execute("SELECT id, active FROM accounts WHERE name = ?", (name,)).fetchone()
        if existing and existing["active"]:
            raise ValueError("Ya existe una cuenta con ese nombre.")
        if existing:
            db.execute("UPDATE accounts SET active = 1, created_after = ? WHERE id = ?",
                       (latest_id(db), existing["id"]))
            return "Cuenta recuperada al final de la cola."
        db.execute("INSERT INTO accounts (name, created_after) VALUES (?, ?)", (name, latest_id(db)))
        return "Cuenta añadida."

    if action == "remove":
        removed = db.execute("UPDATE accounts SET active = 0 WHERE id = ? AND active = 1",
                             (form.get("account"),))
        if removed.rowcount != 1:
            raise ValueError("La cuenta ya no está en la cola.")
        return "Cuenta eliminada de la rotación."

    if action == "delete_entry":
        removed = db.execute("DELETE FROM entries WHERE id = ?", (form.get("entry"),))
        if removed.rowcount != 1:
            raise ValueError("El registro ya se ha eliminado.")
        return "Registro eliminado."

    last = latest_id(db)
    if form.get("last") != str(last) or form.get("day") != day:
        raise ValueError("La rotación ha cambiado. Comprueba el turno actualizado.")

    if action == "undo" and last:
        db.execute("DELETE FROM entries WHERE id = ?", (last,))
        return "Último registro deshecho."

    if action not in RESULTS:
        raise ValueError("Resultado inválido.")

    current = next((account for account in queue(db, day) if not account["exhausted"]), None)
    if current is None or form.get("account") != str(current["id"]):
        raise ValueError("La cuenta activa ha cambiado. Comprueba el turno actualizado.")

    db.execute("INSERT INTO entries (account, day, result) VALUES (?, ?, ?)",
               (current["id"], day, action))
    return f"{current['name']}: {action} registrado."


def today():
    return date.today().isoformat()


def window_settings(db):
    row = db.execute("SELECT corner, topmost FROM window_settings WHERE id = 1").fetchone()
    return (row["corner"], bool(row["topmost"])) if row else ("bottom-right", True)


def save_window_settings(db, corner, topmost):
    db.execute("""
        INSERT INTO window_settings (id, corner, topmost) VALUES (1, ?, ?)
        ON CONFLICT(id) DO UPDATE SET corner = excluded.corner, topmost = excluded.topmost
    """, (corner, int(topmost)))


def clear_all(db):
    """Clear the local records and preferences in one transaction."""
    db.execute("BEGIN IMMEDIATE")
    db.execute("DELETE FROM entries")
    db.execute("DELETE FROM accounts")
    db.execute("DELETE FROM window_settings")
