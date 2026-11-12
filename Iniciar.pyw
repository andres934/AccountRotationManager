"""Abre el panel flotante sin ventana de terminal."""

from contextlib import redirect_stderr, redirect_stdout
import ctypes
import traceback

import floating
import rotation


if __name__ == "__main__":
    try:
        rotation.DATA_DIR.mkdir(parents=True, exist_ok=True)
        with (rotation.DATA_DIR / "inicio.log").open("a", encoding="utf-8", buffering=1) as log:
            with redirect_stderr(log), redirect_stdout(log):
                try:
                    floating.main()
                except Exception:
                    traceback.print_exc()
                    raise
    except Exception as exc:
        ctypes.windll.user32.MessageBoxW(None, str(exc), "Rotaci\u00f3n de cuentas", 0x10)
