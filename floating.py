"""Panel flotante de Windows. La rotación se comparte con la web."""

from contextlib import closing
import ctypes
from ctypes import wintypes
from pathlib import Path
import sqlite3
import struct
import zlib
from math import hypot
import tkinter as tk
from tkinter import font, messagebox, ttk

import rotation

CORNERS = {
    "Arriba a la izquierda": "top-left",
    "Arriba a la derecha": "top-right",
    "Abajo a la izquierda": "bottom-left",
    "Abajo a la derecha": "bottom-right",
}
WIDTH = 384
MARGIN = 12


BACKGROUND = "#10141b"
TEXT = "#eaf0f9"
MUTED = "#a9b6ca"
BORDER = "#303a49"
ACCENT = "#a8f0cf"
HERO = "#1a2428"
CARD = "#191f2a"
FIELD = "#121822"
FONT = "Segoe UI"


def rounded_surface(root, fill, edge, radius, shadow, underlay, center):
    """Blend rounded edges and shadows into the surrounding panel color."""
    inset = radius + 7
    size = inset * 2 + center

    def color(value):
        return bytes.fromhex(value[1:])

    def distance(x, y):
        dx = max(radius + 3 - x, x - (size - radius - 4), 0)
        dy = max(radius + 2 - y, y - (size - radius - 7), 0)
        return hypot(dx, dy) - radius

    def coverage(value):
        return max(0.0, min(1.0, value))

    def chunk(kind, data):
        return (struct.pack(">I", len(data)) + kind + data
                + struct.pack(">I", zlib.crc32(kind + data)))

    fill, edge, underlay = color(fill), color(edge), color(underlay)
    rows = bytearray()
    for y in range(size):
        rows.append(0)
        for x in range(size):
            outline = distance(x + 0.5, y + 0.5)
            opacity = coverage(0.5 - outline)
            interior = coverage(-0.5 - outline)
            shading = shadow * coverage(1 - max(0, distance(x + 0.5, y - 2.5)) / 5) ** 2
            alpha = opacity + shading * (1 - opacity)
            for inside, border, backdrop in zip(fill, edge, underlay):
                rows.append(round(inside * interior + border * (opacity - interior) + backdrop * (1 - alpha)))
            rows.append(255)
    png = b"\x89PNG\r\n\x1a\n"
    png += chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
    png += chunk(b"IDAT", zlib.compress(rows))
    png += chunk(b"IEND", b"")
    return tk.PhotoImage(master=root, data=png), inset


def rounded_style(root, style, name, fill, edge, radius, shadow, states=(), underlay=BACKGROUND):
    element = f"{name}.surface"
    is_button = name.endswith("TButton")
    center = 8 if is_button or name.endswith("TCombobox") else 24
    normal, inset = rounded_surface(root, fill, edge, radius, shadow, underlay, center)
    images = [normal]
    variants = []
    for state, color, stroke, depth in states:
        image, _ = rounded_surface(root, color, stroke, radius, depth, underlay, center)
        images.append(image)
        variants.append((state, image))
    # Tk keeps image names in the theme, so retain the Python image objects.
    root.surface_images.extend(images)
    style.element_create(element, "image", normal, *variants, border=inset, padding=0, sticky="nsew")
    layout = {"sticky": "nsew"}
    if is_button:
        layout["children"] = [("Button.padding", {"sticky": "nsew", "children": [
            ("Button.label", {"sticky": ""})
        ]})]
    style.layout(name, [(element, layout)])
    style.configure(name, background=underlay)
    style.map(name, background=[("!disabled", underlay), ("disabled", underlay)])


def configure_theme(root):
    root.configure(background=BACKGROUND)
    root.option_add("*TCombobox*Listbox.background", FIELD)
    root.option_add("*TCombobox*Listbox.foreground", TEXT)
    root.option_add("*TCombobox*Listbox.selectBackground", BORDER)
    root.option_add("*TCombobox*Listbox.selectForeground", TEXT)
    style = ttk.Style(root)
    style.theme_use("clam")
    root.surface_images = []
    style.configure(".", font=(FONT, 10), background=BACKGROUND, foreground=TEXT,
                    bordercolor=BORDER, lightcolor=BORDER, darkcolor=BORDER)
    style.configure("TLabel", background=BACKGROUND, foreground=TEXT)
    style.configure("PageTitle.TLabel", font=(FONT, 10, "bold"))
    style.configure("Date.TLabel", foreground=MUTED, font=(FONT, 11, "bold"))
    style.configure("TurnInfo.TLabel", background=HERO, foreground="#b5d0c7", font=(FONT, 9))
    style.configure("TurnSuccess.TLabel", background=HERO, foreground=ACCENT, font=(FONT, 9))
    style.configure("TurnError.TLabel", background=HERO, foreground="#ffc2c0", font=(FONT, 9))
    style.configure("Account.TLabel", background=HERO, foreground=TEXT, font=(FONT, 22, "bold"))
    style.configure("Hero.TFrame", background=HERO)
    style.configure("Card.TFrame", background=CARD)
    style.configure("Card.TLabel", background=CARD, foreground=MUTED)
    style.configure("Disclosure.TLabel", background=CARD, foreground=TEXT, font=(FONT, 10, "bold"))
    style.configure("Card.TCheckbutton", background=CARD, foreground=TEXT,
                    indicatorbackground=FIELD, indicatorforeground=ACCENT, padding=(0, 4))
    style.map("Card.TCheckbutton", background=[("active", CARD)], indicatorbackground=[("selected", BORDER)])
    style.configure("TEntry", fieldbackground=FIELD, insertcolor=TEXT, padding=6)
    rounded_style(root, style, "Corner.TCombobox", FIELD, BORDER, 8, 0, (
        ("focus", FIELD, "#c4d5ff", 0),
        ("active", FIELD, "#59697e", 0),
    ), underlay=CARD)
    style.layout("Corner.TCombobox", [("Corner.TCombobox.surface", {"sticky": "nsew", "children": [
        ("Combobox.downarrow", {"side": "right", "sticky": "e"}),
        ("Combobox.padding", {"expand": True, "sticky": "nsew", "children": [
            ("Combobox.textarea", {"sticky": "nsew"})
        ]}),
    ]})])
    style.configure("Corner.TCombobox", fieldbackground=FIELD, arrowcolor=MUTED, padding=(12, 5))
    style.map("Corner.TCombobox", fieldbackground=[("readonly", FIELD)],
              foreground=[("readonly", TEXT)], selectbackground=[("readonly", FIELD)],
              selectforeground=[("readonly", TEXT)])
    style.layout("Minimal.Vertical.TScrollbar", [
        ("Vertical.Scrollbar.trough", {"sticky": "ns", "children": [
            ("Vertical.Scrollbar.thumb", {"expand": True, "sticky": "ns"})
        ]})
    ])
    style.configure("Minimal.Vertical.TScrollbar", width=6, arrowsize=6, borderwidth=0, relief="flat",
                    background="#46566c", lightcolor="#46566c", darkcolor="#46566c",
                    troughcolor=CARD, bordercolor=CARD, gripcount=0)
    style.map("Minimal.Vertical.TScrollbar", background=[("active", "#687b95")])
    style.configure("QueueName.TLabel", background=CARD, foreground=TEXT, font=(FONT, 10, "bold"))
    style.configure("QueueCurrent.TLabel", background=CARD, foreground=ACCENT, font=(FONT, 10, "bold"))
    style.configure("QueueStatus.TLabel", background=CARD, foreground=MUTED, font=(FONT, 9))
    for result, color in (("TP", ACCENT), ("SL", "#ffc2c0"), ("BE", "#d6e1f6")):
        style.configure(f"Result{result}.TLabel", background=CARD, foreground=color, font=(FONT, 9, "bold"))
    style.configure("Trash.TButton", background=CARD, foreground=MUTED,
                    font=("Segoe MDL2 Assets", 12), width=3, padding=(4, 5))
    style.map("Trash.TButton", background=[("!disabled", CARD)],
              foreground=[("focus", "#ffc2c0"), ("active", "#ffc2c0")])
    style.layout("Trash.TButton", [("Button.padding", {"sticky": "nsew", "children": [
        ("Button.label", {"sticky": ""})
    ]})])

    rounded_style(root, style, "TurnCard.TFrame", HERO, "#35474c", 22, 0.26)
    rounded_style(root, style, "DetailCard.TFrame", CARD, BORDER, 18, 0.24)

    for name, background, foreground, hover, underlay, text_size in (
        ("TButton", "#222b3a", TEXT, "#273244", CARD, 10),
        ("Add.TButton", ACCENT, "#11221e", "#c2f7e0", CARD, 10),
        ("Danger.TButton", "#a63540", "#ffffff", "#bb414e", CARD, 10),
        ("Setup.TButton", ACCENT, "#11221e", "#c2f7e0", HERO, 10),
        ("TP.TButton", ACCENT, "#11221e", "#c2f7e0", HERO, 16),
        ("SL.TButton", "#ffc2c0", "#381c22", "#ffd6d4", HERO, 16),
        ("BE.TButton", "#d6e1f6", "#1c2b47", "#e6edfc", HERO, 16),
    ):
        rounded_style(root, style, name, background, background, 12, 0.26, (
            ("disabled", "#263438", "#354448", 0.16),
            ("pressed", background, background, 0.24),
            ("focus", background, "#ffffff", 0.55),
            ("active", hover, hover, 0.57),
        ), underlay=underlay)
        style.configure(name, foreground=foreground, font=(FONT, text_size, "bold"), anchor="center", justify="center",
                        padding=(10, 6, 10, 12))
        style.map(name, foreground=[("disabled", MUTED)])
    rounded_style(root, style, "Tab.TButton", CARD, BORDER, 8, 0.12, (
        ("selected focus", HERO, "#c4d5ff", 0.45),
        ("selected", HERO, "#35474c", 0.24),
        ("focus", CARD, "#c4d5ff", 0.45),
        ("active", "#273244", "#41546d", 0.42),
    ))
    style.configure("Tab.TButton", anchor="center", padding=(8, 4, 8, 10))
    style.map("Tab.TButton", foreground=[("selected", ACCENT)])


def display_day(day):
    return "/".join(reversed(day.split("-")))


class ScrollRows(ttk.Frame):
    """Shared layout for queue accounts and recent results."""

    def __init__(self, parent, visible_rows):
        super().__init__(parent, style="Card.TFrame")
        self.visible_rows = visible_rows
        self.canvas = tk.Canvas(self, background=CARD, highlightthickness=0,
                                width=1, height=1, takefocus=False)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", style="Minimal.Vertical.TScrollbar",
                                       command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.pack(side="left", fill="x", expand=True)
        self.rows = ttk.Frame(self.canvas, style="Card.TFrame")
        self.window = self.canvas.create_window(0, 0, window=self.rows, anchor="nw")
        self.canvas.bind("<Configure>", self.resize_width)
        self.rows.bind("<Configure>", self.resize_height)
        for widget in (self.canvas, self.rows):
            widget.bind("<MouseWheel>", self.scroll)

    def resize_width(self, event):
        self.canvas.itemconfigure(self.window, width=event.width)

    def resize_height(self, _event=None):
        # Separators are interleaved between account or history rows.
        widgets = self.rows.winfo_children()[:2 * self.visible_rows - 1]
        content_height = self.rows.winfo_reqheight()
        height = min(content_height, sum(widget.winfo_reqheight() for widget in widgets))
        self.canvas.configure(height=max(1, height), scrollregion=(0, 0, self.canvas.winfo_width(), content_height))
        if content_height > height and widgets:
            self.scrollbar.pack(side="right", fill="y", padx=(5, 0), before=self.canvas)
        else:
            self.scrollbar.pack_forget()

    def scroll(self, event):
        if self.scrollbar.winfo_manager():
            self.canvas.yview_scroll(-int(event.delta / 120) * 2, "units")
        return "break"

    def reveal(self, row):
        top = self.canvas.canvasy(0)
        height = self.canvas.winfo_height()
        row_top = row.winfo_y()
        row_bottom = row_top + row.winfo_height()
        if row_top < top or row_bottom > top + height:
            target = row_top if row_top < top else row_bottom - height
            self.canvas.yview_moveto(target / self.rows.winfo_height())

    def render(self, items, empty_message, keep_position=True):
        position = self.canvas.yview()[0] if keep_position else 0
        for child in self.rows.winfo_children():
            child.destroy()
        for index, (title, subtitle, current, result, remove) in enumerate(items):
            if index:
                tk.Frame(self.rows, background=BORDER, height=1).pack(fill="x")
            row = ttk.Frame(self.rows, style="Card.TFrame", padding=(2, 4))
            row.pack(fill="x")
            trash = ttk.Button(row, text="\ue74d", style="Trash.TButton", command=remove)
            trash.pack(side="right", padx=(6, 0))
            trash.bind("<FocusIn>", lambda _event, item=row: self.reveal(item))
            if result:
                outcome = ttk.Label(row, text=result, width=3, anchor="center", style=f"Result{result}.TLabel")
                outcome.pack(side="right", padx=(4, 4))
                outcome.bind("<MouseWheel>", self.scroll)
            labels = ttk.Frame(row, style="Card.TFrame")
            labels.pack(side="left", fill="x", expand=True)
            name = ttk.Label(labels, text=title, wraplength=WIDTH - (140 if result else 108),
                             style="QueueCurrent.TLabel" if current else "QueueName.TLabel")
            name.pack(anchor="w")
            detail = ttk.Label(labels, text=subtitle, style="QueueStatus.TLabel")
            detail.pack(anchor="w")
            for widget in (row, labels, name, detail, trash):
                widget.bind("<MouseWheel>", self.scroll)
        if not items:
            ttk.Label(self.rows, text=empty_message, style="Card.TLabel").pack(anchor="w", pady=4)
        self.rows.update_idletasks()
        self.resize_height()
        self.canvas.yview_moveto(position)


class Panel:
    def __init__(self, root):
        self.root = root
        self.root.title("Rotaci\u00f3n de cuentas")
        self.root.iconbitmap(str(Path(__file__).with_name("Trading.ico")))
        self.root.resizable(False, False)
        self.section = None
        self.add_expanded = False
        self.state = None
        self.notice_timer = None
        self.idle_notice = ""
        with closing(rotation.connect()) as db:
            corner, topmost = rotation.window_settings(db)
        self.corner = tk.StringVar(value=next(label for label, value in CORNERS.items() if value == corner))
        self.topmost = tk.BooleanVar(value=topmost)

        configure_theme(root)
        frame = ttk.Frame(root, padding=16)
        frame.pack(fill="both", expand=True)

        header = ttk.Frame(frame)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Turno actual", style="PageTitle.TLabel").pack(side="left")
        self.date_label = ttk.Label(header, style="Date.TLabel")
        self.date_label.pack(side="right")

        outline = ttk.Frame(frame, style="TurnCard.TFrame", padding=(16, 12, 16, 16))
        outline.pack(fill="x")
        hero = ttk.Frame(outline, style="Hero.TFrame")
        hero.pack(fill="x")
        self.headline = tk.StringVar()
        ttk.Label(hero, textvariable=self.headline, style="Account.TLabel",
                  wraplength=WIDTH - 72).pack(anchor="w", pady=(0, 8))

        self.results = ttk.Frame(hero, style="Hero.TFrame")
        self.setup = ttk.Button(hero, text="Agregar una cuenta", style="Setup.TButton",
                                command=self.open_add_form)
        self.buttons = []
        for index, result in enumerate(rotation.RESULTS):
            self.results.columnconfigure(index, weight=1, uniform="outcome")
            button = ttk.Button(self.results, text=result, style=f"{result}.TButton",
                                command=lambda value=result: self.record(value))
            button.grid(row=0, column=index, sticky="ew", padx=(0 if index == 0 else 4, 0))
            self.buttons.append(button)

        self.notice_font = font.Font(root=root, family=FONT, size=9)
        self.notice = ttk.Label(hero, style="TurnInfo.TLabel", width=1)
        self.notice.pack(fill="x", pady=(6, 0))
        self.controls = ttk.Frame(frame)
        self.controls.pack(fill="x", pady=(8, 0))
        self.tabs = {}
        for index, label in enumerate(("Cola", "Historial", "Ajustes")):
            self.controls.columnconfigure(index, weight=1, uniform="tabs")
            button = ttk.Button(self.controls, text=label, style="Tab.TButton",
                                command=lambda name=label: self.toggle(name))
            button.grid(row=0, column=index, sticky="ew", padx=2)
            button.bind("<Return>", lambda event, name=label: self.toggle_from_keyboard(name))
            button.bind("<space>", lambda event, name=label: self.toggle_from_keyboard(name))
            self.tabs[label] = button

        self.details = ttk.Frame(frame, style="DetailCard.TFrame", padding=(16, 12, 16, 16))
        self.sections = {
            "Cola": self.build_queue(),
            "Historial": self.build_history(),
            "Ajustes": self.build_settings(),
        }
        self.root.attributes("-topmost", topmost)
        self.refresh()
        self.anchor()
        # Windows applies the dark title bar independently of the Tk theme.
        hwnd = int(self.root.wm_frame(), 0)
        dark = ctypes.c_int(1)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark), ctypes.sizeof(dark))
        self.root.after(1500, self.poll)

    def show_notice(self, message="", appearance="TurnInfo.TLabel"):
        if self.notice_timer is not None:
            self.root.after_cancel(self.notice_timer)
            self.notice_timer = None
        text = message or self.idle_notice
        max_width = WIDTH - 66
        if self.notice_font.measure(text) > max_width:
            while self.notice_font.measure(text + "\u2026") > max_width:
                text = text[:-1]
            text = text.rstrip() + "\u2026"
        self.notice.configure(text=text, style=appearance)
        if message:
            self.notice_timer = self.root.after(5500, self.show_notice)

    def build_queue(self):
        frame = ttk.Frame(self.details, style="Card.TFrame")
        self.queue_view = ScrollRows(frame, visible_rows=2)
        self.queue_view.pack(fill="x")
        self.add_toggle = ttk.Frame(frame, style="Card.TFrame", cursor="hand2", takefocus=True,
                                    padding=(2, 4))
        self.add_toggle.pack(fill="x", pady=(6, 0))
        title = ttk.Label(self.add_toggle, text="Agregar una cuenta", style="Disclosure.TLabel",
                          cursor="hand2")
        title.pack(side="left")
        self.add_arrow = ttk.Label(self.add_toggle, text="\u25b8", style="Disclosure.TLabel",
                                   cursor="hand2")
        self.add_arrow.pack(side="left", padx=(6, 0))
        for widget in (self.add_toggle, title, self.add_arrow):
            widget.bind("<Button-1>", self.toggle_add)
        self.add_toggle.bind("<Return>", self.toggle_add)
        self.add_toggle.bind("<space>", self.toggle_add)
        self.add_form = ttk.Frame(frame, style="Card.TFrame")
        ttk.Label(self.add_form, text="Nombre de la cuenta", style="Card.TLabel").pack(anchor="w", pady=(0, 2))
        row = ttk.Frame(self.add_form, style="Card.TFrame")
        row.pack(fill="x")
        self.name = ttk.Entry(row)
        self.name.pack(side="left", fill="x", expand=True, padx=(0, 4))
        self.name.bind("<Return>", self.add_account)
        ttk.Button(row, text="A\u00f1adir", style="Add.TButton", command=self.add_account).pack(side="right")
        return frame

    def open_add_form(self):
        if self.section != "Cola":
            self.toggle("Cola")
        if not self.add_expanded:
            self.toggle_add()
        else:
            self.name.focus_set()

    def toggle_add(self, _event=None):
        self.add_expanded = not self.add_expanded
        if self.add_expanded:
            self.add_arrow.configure(text="\u25be")
            self.add_form.pack(fill="x", pady=(4, 0))
            self.name.focus_set()
        else:
            self.add_arrow.configure(text="\u25b8")
            self.add_form.pack_forget()
            self.add_toggle.focus_set()
        self.anchor()

    def render_queue(self, accounts, keep_position):
        rows = []
        for account in sorted(accounts, key=lambda item: bool(item["exhausted"])):
            current = account == self.current
            status = f"Agotada ({account['exhausted']})" if account["exhausted"] else (
                "En turno" if current else "En espera"
            )
            rows.append((account["name"], status, current, None,
                         lambda item=account: self.remove_account(item)))
        self.queue_view.render(rows, "A\u00fan no hay cuentas", keep_position)

    def build_history(self):
        frame = ttk.Frame(self.details, style="Card.TFrame")
        self.history_view = ScrollRows(frame, visible_rows=5)
        self.history_view.pack(fill="x")
        return frame

    def build_settings(self):
        frame = ttk.Frame(self.details, style="Card.TFrame")
        ttk.Label(frame, text="Esquina de la pantalla", style="Card.TLabel").pack(anchor="w")
        choices = ttk.Combobox(frame, state="readonly", style="Corner.TCombobox",
                               values=tuple(CORNERS), textvariable=self.corner)
        choices.pack(fill="x", pady=(4, 8))
        choices.bind("<<ComboboxSelected>>", self.save_settings)
        ttk.Checkbutton(frame, text="Siempre encima", variable=self.topmost, style="Card.TCheckbutton",
                        command=self.save_settings).pack(anchor="w")
        tk.Frame(frame, background=BORDER, height=1).pack(fill="x", pady=(8, 8))
        ttk.Button(frame, text="Borrar todos los datos", style="Danger.TButton",
                   command=self.clear_all).pack(fill="x")
        return frame

    def clear_all(self):
        confirmed = messagebox.askyesno(
            "Borrar todos los datos",
            "Se borrar\u00e1n todas las cuentas, el historial y las preferencias del panel.\n\n"
            "Tendr\u00e1s que agregar las cuentas de nuevo. Esta acci\u00f3n es irreversible.\n\n"
            "\u00bfQuieres continuar?",
            icon=messagebox.WARNING, default=messagebox.NO, parent=self.root,
        )
        if not confirmed:
            return
        try:
            with closing(rotation.connect()) as db, db:
                rotation.clear_all(db)
                corner, topmost = rotation.window_settings(db)
        except sqlite3.Error:
            self.show_notice("No se pudo borrar. Vuelve a intentarlo.", "TurnError.TLabel")
            return

        self.corner.set(next(label for label, value in CORNERS.items() if value == corner))
        self.topmost.set(topmost)
        self.root.attributes("-topmost", topmost)
        self.name.delete(0, "end")
        self.refresh()
        self.show_notice("Datos borrados. Agrega tus cuentas de nuevo.", "TurnSuccess.TLabel")
        self.anchor()

    def toggle_from_keyboard(self, name):
        self.toggle(name, keep_focus=True)
        return "break"

    def toggle(self, name, keep_focus=False):
        if not keep_focus:
            self.root.focus_set()
        if self.section:
            self.sections[self.section].pack_forget()
            self.tabs[self.section].state(["!selected"])
        if self.section == name:
            self.section = None
            self.details.pack_forget()
        else:
            self.section = name
            self.tabs[name].state(["selected"])
            self.details.pack(fill="x", pady=(8, 0))
            self.sections[name].pack(fill="x")
        self.anchor()

    def anchor(self):
        self.root.update_idletasks()
        self.root.geometry(f"{WIDTH}x{self.root.winfo_reqheight()}")
        self.root.update_idletasks()
        user32 = ctypes.windll.user32
        work = wintypes.RECT()
        if not user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(work), 0):
            work.right, work.bottom = self.root.winfo_screenwidth(), self.root.winfo_screenheight()
        # Tk devuelve el identificador del contenido. Windows posiciona su ventana exterior.
        hwnd = int(self.root.wm_frame(), 0)
        bounds = wintypes.RECT()
        user32.GetWindowRect(hwnd, ctypes.byref(bounds))
        vertical, horizontal = CORNERS[self.corner.get()].split("-")
        x = work.left + MARGIN if horizontal == "left" else work.right - (bounds.right - bounds.left) - MARGIN
        y = work.top + MARGIN if vertical == "top" else work.bottom - (bounds.bottom - bounds.top) - MARGIN
        user32.SetWindowPos(hwnd, None, x, y, 0, 0, 0x0015)

    def save_settings(self, _event=None):
        try:
            with closing(rotation.connect()) as db, db:
                rotation.save_window_settings(db, CORNERS[self.corner.get()], self.topmost.get())
        except sqlite3.Error as exc:
            messagebox.showerror("Ajustes", str(exc), parent=self.root)
            return
        self.root.attributes("-topmost", self.topmost.get())
        self.anchor()

    def refresh(self):
        day = rotation.today()
        with closing(rotation.connect()) as db:
            db.execute("BEGIN")
            accounts = rotation.queue(db, day)
            last = rotation.latest_id(db)
            history = db.execute("""
                SELECT entries.id, entries.day, accounts.name, entries.result
                FROM entries JOIN accounts ON accounts.id = entries.account
                ORDER BY entries.id DESC LIMIT 20
            """).fetchall()
        state = (day, accounts, last, history)
        if state == self.state:
            return False
        queue_changed = self.state is None or accounts != self.state[1]
        previous_current = self.current["id"] if self.state and self.current else None
        history_changed = self.state is None or history != self.state[3]
        self.state = state
        self.date_label.configure(text=display_day(day))
        self.current = next((account for account in accounts if not account["exhausted"]), None)
        if self.current:
            self.setup.pack_forget()
            self.results.pack(fill="x", before=self.notice)
            title = self.current["name"]
            following = next((item["name"] for item in accounts
                              if item != self.current and not item["exhausted"]), None)
            self.idle_notice = f"Siguiente: {following}" if following else "\u00daltima cuenta disponible"
        else:
            self.results.pack_forget()
            if accounts:
                self.setup.pack_forget()
                title = "Todas agotadas"
                self.idle_notice = "La cola se reanuda al cambiar el d\u00eda."
            else:
                title = "Empieza tu rotaci\u00f3n"
                self.idle_notice = "A\u00f1ade las cuentas en el orden de uso."
                self.setup.pack(fill="x", before=self.notice)
        self.headline.set(title)
        if self.notice_timer is None:
            self.show_notice()

        if queue_changed:
            current_id = self.current["id"] if self.current else None
            self.render_queue(accounts, keep_position=current_id == previous_current)
        if history_changed:
            rows = [
                (item["name"], display_day(item["day"]), False, item["result"],
                 lambda entry=item: self.remove_entry(entry))
                for item in history
            ]
            self.history_view.render(rows, "Todav\u00eda no hay resultados")
        return True

    def poll(self):
        try:
            if self.refresh():
                self.anchor()
        except sqlite3.Error:
            self.show_notice("No se pudo actualizar. Reintentando.", "TurnError.TLabel")
        finally:
            self.root.after(1500, self.poll)

    def apply(self, action, **fields):
        try:
            with closing(rotation.connect()) as db, db:
                rotation.update(db, {"action": action, **fields}, rotation.today())
        except ValueError as exc:
            self.show_notice(str(exc), "TurnError.TLabel")
            self.refresh()
            self.anchor()
            return False
        except sqlite3.Error:
            self.show_notice("No se pudo guardar. Vuelve a intentarlo.", "TurnError.TLabel")
            return False

        self.refresh()
        if action == "BE":
            self.show_notice("BE registrado. Se mantiene el turno.", "TurnSuccess.TLabel")
        elif action in rotation.RESULTS:
            self.show_notice(f"{action} registrado. Turno actualizado.", "TurnSuccess.TLabel")
        else:
            self.show_notice()
        self.anchor()
        return True

    def record(self, action):
        day, _, last, _ = self.state
        account = str(self.current["id"]) if self.current else ""
        self.apply(action, account=account, last=str(last), day=day)

    def add_account(self, _event=None):
        if self.apply("add", name=self.name.get()):
            self.name.delete(0, "end")

    def remove_entry(self, entry):
        detail = f"{entry['name']} \u00b7 {display_day(entry['day'])} \u00b7 {entry['result']}"
        if messagebox.askyesno("Eliminar registro", f"\u00bfEliminar este registro?\n\n{detail}",
                               parent=self.root):
            self.apply("delete_entry", entry=str(entry["id"]))

    def remove_account(self, account):
        if messagebox.askyesno("Eliminar cuenta", f"\u00bfQuitar {account['name']} de la cola?",
                               parent=self.root):
            self.apply("remove", account=str(account["id"]))


def main():
    rotation.initialize()
    root = tk.Tk()
    Panel(root)
    root.mainloop()
