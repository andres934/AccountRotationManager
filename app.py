"""Interfaz web de rotación. Ejecutar con python app.py."""

from contextlib import closing
from html import escape
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from secrets import token_urlsafe
from urllib.parse import parse_qs, urlencode, urlsplit
import sqlite3
import socket

import rotation

ADDRESS = "127.0.0.1"
PORT = 8765
HOST = f"{ADDRESS}:{PORT}"
TOKEN = token_urlsafe(32)
HEALTH = "account-manager-local"
CSS = Path(__file__).with_name("style.css")


def hidden(name, value):
    return f'<input type="hidden" name="{name}" value="{escape(str(value))}">'


def render(message="", error=False):
    day = rotation.today()
    with closing(rotation.connect()) as db:
        accounts = rotation.queue(db, day)
        last = rotation.latest_id(db)
        entries = db.execute("""
            SELECT entries.day, accounts.name, entries.result
            FROM entries JOIN accounts ON accounts.id = entries.account
            ORDER BY entries.id DESC LIMIT 20
        """).fetchall()

    current = next((account for account in accounts if not account["exhausted"]), None)
    token = hidden("token", TOKEN)
    turn = token + hidden("last", last) + hidden("day", day)
    if current:
        headline = escape(current["name"])
        controls = f"""
          <form method="post" action="/" class="outcomes">
            {turn}{hidden("account", current["id"])}
            <button name="action" value="TP" class="tp">TP <small>Take profit</small></button>
            <button name="action" value="SL" class="sl">SL <small>Stop loss</small></button>
            <button name="action" value="BE" class="be">BE <small>Break even</small></button>
          </form>"""
    else:
        headline = "Todas agotadas por hoy" if accounts else "Añade tu primera cuenta"
        controls = ("<p>La cola se reanuda al cambiar el día.</p>" if accounts
                    else "<p>Añade tus cuentas en el orden en que quieres empezar.</p>")

    queue_rows = []
    removal_options = []
    for account in accounts:
        status = "En turno"
        if account["exhausted"]:
            status = f"Agotada · {account['exhausted']}"
        elif account != current:
            status = "En espera"
        css_class = "current" if account == current else ""
        queue_rows.append(f'<li class="{css_class}"><strong>{escape(account["name"])}</strong><span>{status}</span></li>')
        removal_options.append(f'<option value="{account["id"]}">{escape(account["name"])}</option>')
    removal = ""
    if removal_options:
        removal = f"""
          <details class="manage">
            <summary>Eliminar una cuenta</summary>
            <form method="post" action="/">
              {token}
              <label for="remove-account">Cuenta que quieres quitar de la rotación</label>
              <div class="add-row">
                <select id="remove-account" name="account" required>
                  <option value="">Selecciona una cuenta</option>
                  {"".join(removal_options)}
                </select>
                <button class="sl" name="action" value="remove">Eliminar</button>
              </div>
              <p>El historial se conserva.</p>
            </form>
          </details>"""
    queue_content = "".join(queue_rows) or "<li>Aún no hay cuentas.</li>"

    history = "".join(
        f'<li><strong>{escape(entry["name"])}</strong><span>{entry["day"]} · {entry["result"]}</span></li>'
        for entry in entries
    ) or "<li>Aún no hay registros.</li>"
    undo = (f'<form method="post" action="/">{turn}<button class="secondary" name="action" value="undo">'
            'Deshacer último registro</button></form>') if last else ""
    role = "alert" if error else "status"
    notice = f'<p class="notice" role="{role}">{escape(message)}</p>' if message else ""
    available = sum(not account["exhausted"] for account in accounts)
    return f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rotación de cuentas</title>
  <link rel="stylesheet" href="/style.css">
</head>
<body>
  <main>
    <header><h1>Rotación de cuentas</h1><time datetime="{day}">{day}</time></header>
    {notice}
    <section class="hero" aria-label="Turno actual">
      <p class="label">Turno actual</p>
      <h2>{headline}</h2>
      {controls}
    </section>
    <div class="grid">
      <section class="panel">
        <div class="heading"><h2>Cola de cuentas</h2><span>{available} de {len(accounts)} disponibles</span></div>
        <ol>{queue_content}</ol>
        <form method="post" action="/" class="add">
          {token}
          <label for="name">Nombre de la cuenta</label>
          <div class="add-row">
            <input id="name" name="name" required maxlength="80" placeholder="Ej. Fondeo 01">
            <button name="action" value="add">Añadir</button>
          </div>
        </form>
        {removal}
      </section>
      <section class="panel">
        <div class="heading"><h2>Registros recientes</h2></div>
        <ul>{history}</ul>
        {undo}
      </section>
    </div>
  </main>
</body>
</html>"""


class Handler(BaseHTTPRequestHandler):
    def send_content(self, status, content, content_type="text/html; charset=utf-8"):
        body = content.encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Security-Policy", "default-src 'none'; style-src 'self'; form-action 'self'; frame-ancestors 'none'")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        if self.headers.get("Host") != HOST:
            self.send_error(403)
            return
        url = urlsplit(self.path)
        if url.path == "/":
            message = parse_qs(url.query).get("mensaje", [""])[0]
            self.send_content(200, render(message))
        elif url.path == "/health":
            self.send_content(200, HEALTH, "text/plain; charset=utf-8")
        elif url.path == "/style.css":
            self.send_content(200, CSS.read_text(encoding="utf-8-sig"), "text/css; charset=utf-8")
        else:
            self.send_error(404)

    def do_POST(self):
        if self.headers.get("Host") != HOST or self.path != "/":
            self.send_error(403)
            return
        try:
            length = int(self.headers.get("Content-Length", "0"))
            if not 0 < length <= 4096:
                raise ValueError
            fields = parse_qs(self.rfile.read(length).decode("utf-8"), max_num_fields=8)
        except ValueError:
            self.send_error(400)
            return
        form = {name: values[0] for name, values in fields.items()}
        if form.get("token") != TOKEN:
            self.send_content(403, render("Recarga la página y vuelve a intentarlo.", error=True))
            return
        try:
            with closing(rotation.connect()) as db, db:
                message = rotation.update(db, form, rotation.today())
        except ValueError as exc:
            self.send_content(400, render(str(exc), error=True))
            return
        except sqlite3.Error as exc:
            self.log_error("Error de escritura en SQLite: %s", exc)
            self.send_content(503, "<p>No se pudo guardar el cambio. Vuelve a abrir la página e inténtalo de nuevo.</p>")
            return

        self.send_response(303)
        self.send_header("Location", "/?" + urlencode({"mensaje": message}))
        self.send_header("Content-Length", "0")
        self.end_headers()


class LocalServer(HTTPServer):
    allow_reuse_address = False

    def server_bind(self):
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def main(on_ready=None, port=PORT):
    global HOST
    HOST = f'{ADDRESS}:{port}'
    with LocalServer((ADDRESS, port), Handler) as server:
        rotation.initialize()
        if on_ready:
            on_ready()
        print(f"Abre http://{HOST} en el navegador. Ctrl+C para salir.", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
