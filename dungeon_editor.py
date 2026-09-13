"""TW1 Dungeon Editor - Fensterrahmen für Dungeons.exe aus dem Two Worlds SDK.

Dungeons.exe (Reality Pump, 2007) hat keine Oberfläche, nur Hotkeys.
Dieses Programm startet die Exe, bettet ihr Fenster ein und legt
Menüleiste, Werkzeugleiste, Hinweis-Panel und Statuszeile darum. Alle
Knöpfe schicken nur die Original-Hotkeys an das eingebettete Fenster.
"""

import ctypes
import json
import os
import subprocess
import sys
import time
import webbrowser
import tkinter as tk
from ctypes import wintypes
from tkinter import ttk, messagebox

import theme
from theme import (BG, PANEL, FIELD, CANVAS_BG, LINE, INK, MUT, GOLD, GOLD_HI,
                   OK, ERR, ON_GOLD, FONT, FONT_BOLD, FONT_SMALL, FONT_MONO,
                   FONT_H2, EDITOR_RED, EDITOR_GREEN, EDITOR_VIOLET,
                   EDITOR_WHITE, EDITOR_YELLOW)

APP_NAME = 'TW1 DUNGEON EDITOR'
APP_TITLE = 'TW1 Dungeon Editor'
VERSION = '0.1.0'
REPO_NAME = 'TW1_DungeonEditor'
GITHUB_URL = f'https://github.com/MedievalDev/{REPO_NAME}'
SITE_URL = 'https://alchemy-fox.de/'
GUIDE_URL = f'https://alchemy-fox.de/game/{REPO_NAME}/'
COMMUNITY_URL = 'https://twmp.alchemy-fox.de/'
LINKS = (('GitHub-Repo', GITHUB_URL), ('Alchemy Fox', SITE_URL),
         ('Guide-Seite', GUIDE_URL), ('Community', COMMUNITY_URL))

FROZEN = getattr(sys, 'frozen', False)
HERE = os.path.dirname(os.path.abspath(sys.executable if FROZEN else __file__))
DATA_DIR = (os.path.join(os.environ.get('LOCALAPPDATA', HERE), 'TW1DungeonEditor')
            if FROZEN else HERE)
CONFIG_PATH = os.path.join(DATA_DIR, 'dungeon_editor_settings.json')
# Orte, an denen Dungeons.exe relativ zum Tool typischerweise liegt: Tool-Ordner
# in SDK/Dungeons, im SDK-Ordner, neben dem SDK-Ordner oder neben dem Tool.
EXE_CANDIDATES = (('..', 'Dungeons.exe'),
                  ('..', 'Dungeons', 'Dungeons.exe'),
                  ('..', 'TwoWorldsSDK', 'Dungeons', 'Dungeons.exe'),
                  ('Dungeons.exe',),
                  ('Dungeons', 'Dungeons.exe'))


def valid_exe(path):
    """Dungeons.exe braucht dungeon.txt und den Data-Ordner daneben."""
    if not path or not os.path.isfile(path):
        return False
    folder = os.path.dirname(path)
    return (os.path.isfile(os.path.join(folder, 'dungeon.txt'))
            and os.path.isdir(os.path.join(folder, 'Data')))


def find_exe(configured):
    """Gespeicherter Pfad, sonst die typischen Orte rund um das Tool."""
    if valid_exe(configured):
        return configured
    for parts in EXE_CANDIDATES:
        path = os.path.normpath(os.path.join(HERE, *parts))
        if valid_exe(path):
            return path
    return ''


def readme_path(exe_path):
    """'Dungeons readme.txt' liegt im SDK unter Documentation."""
    folder = os.path.dirname(exe_path) if exe_path else HERE
    return os.path.normpath(os.path.join(folder, '..', 'Documentation',
                                         'Dungeons readme.txt'))


CLIENT_W, CLIENT_H = 1024, 768
TITLE_PREFIX = 'Dungeons - '

# Reihenfolge wie die Exe mit Tab durchschaltet
MODES = (('dungeon', 'editing dungeon'),
         ('height', 'editing dungeon height'),
         ('type', 'editing dungeon type'),
         ('objects', 'editing objects'),
         ('lights', 'editing lights'))
MODE_INDEX = {key: i for i, (key, _) in enumerate(MODES)}
MODE_BY_TITLE = {title: key for key, title in MODES}

VK = {'F2': 0x71, 'F3': 0x72, 'F4': 0x73, 'F5': 0x74, 'F6': 0x75, 'F8': 0x77,
      'TAB': 0x09, 'PGUP': 0x21, 'PGDN': 0x22,
      'LEFT': 0x25, 'UP': 0x26, 'RIGHT': 0x27, 'DOWN': 0x28}
EXTENDED = {'PGUP', 'PGDN', 'LEFT', 'UP', 'RIGHT', 'DOWN'}

u32 = ctypes.windll.user32
k32 = ctypes.windll.kernel32
WNDENUMPROC = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)


# ---------------------------------------------------------------- Sprache

_LANG = 'de'


def tr(text):
    if _LANG == 'en':
        return EN.get(text, text)
    return text


def system_lang():
    try:
        return 'de' if k32.GetUserDefaultUILanguage() & 0x3FF == 0x07 else 'en'
    except Exception:
        return 'en'


# ---------------------------------------------------------------- Konfig

class Config(dict):
    def __init__(self):
        super().__init__()
        self.update({'lang': system_lang(), 'guide_seen': False,
                     'exe_path': '', 'recent': [],
                     'geometry': '', 'show_panel': True})
        try:
            with open(CONFIG_PATH, encoding='utf-8') as fh:
                self.update(json.load(fh))
        except Exception:
            pass

    def save(self):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            with open(CONFIG_PATH, 'w', encoding='utf-8') as fh:
                json.dump(self, fh, indent=2, ensure_ascii=False)
        except Exception:
            pass

    def add_recent(self, path):
        recent = [p for p in self.get('recent', []) if p.lower() != path.lower()]
        recent.insert(0, path)
        self['recent'] = recent[:8]
        self.save()


# ---------------------------------------------------------------- Exe-Steuerung

class EditorProcess:
    """Startet Dungeons.exe, bettet das Fenster ein, schickt Hotkeys."""

    def __init__(self, exe_path):
        self.exe_path = exe_path
        self.proc = None
        self.hwnd = None

    # -- Start / Ende ------------------------------------------------------
    def start(self):
        cwd = os.path.dirname(self.exe_path)
        self.proc = subprocess.Popen([self.exe_path], cwd=cwd)
        for _ in range(100):
            windows = self._windows_of(self.proc.pid)
            if windows:
                self.hwnd = windows[0]
                return True
            if self.proc.poll() is not None:
                return False
            time.sleep(0.05)
        return False

    def alive(self):
        return (self.proc is not None and self.proc.poll() is None
                and self.hwnd and u32.IsWindow(self.hwnd))

    def stop(self):
        if self.proc and self.proc.poll() is None:
            try:
                self.proc.terminate()
            except Exception:
                pass

    def _windows_of(self, pid):
        out = []

        def cb(h, _):
            q = wintypes.DWORD()
            u32.GetWindowThreadProcessId(h, ctypes.byref(q))
            if q.value == pid and u32.IsWindowVisible(h):
                out.append(h)
            return True
        u32.EnumWindows(WNDENUMPROC(cb), 0)
        return out

    # -- Einbetten ---------------------------------------------------------
    def embed(self, parent_id):
        GWL_STYLE = -16
        WS_CHILD, WS_CAPTION = 0x40000000, 0x00C00000
        WS_THICKFRAME, WS_POPUP = 0x00040000, 0x80000000
        WS_SYSMENU, WS_MINIMIZEBOX, WS_MAXIMIZEBOX = 0x80000, 0x20000, 0x10000
        style = u32.GetWindowLongW(self.hwnd, GWL_STYLE)
        style &= ~(WS_CAPTION | WS_THICKFRAME | WS_POPUP | WS_SYSMENU
                   | WS_MINIMIZEBOX | WS_MAXIMIZEBOX)
        style |= WS_CHILD
        u32.SetWindowLongW(self.hwnd, GWL_STYLE, style)
        u32.SetParent(self.hwnd, parent_id)
        self.place(0, 0)

    def place(self, x, y):
        SWP_NOZORDER, SWP_FRAMECHANGED, SWP_SHOWWINDOW = 0x4, 0x20, 0x40
        u32.SetWindowPos(self.hwnd, 0, x, y, CLIENT_W, CLIENT_H,
                         SWP_NOZORDER | SWP_FRAMECHANGED | SWP_SHOWWINDOW)

    def focus(self):
        try:
            u32.SetFocus(self.hwnd)
        except Exception:
            pass

    # -- Tasten ------------------------------------------------------------
    def key(self, name):
        if not self.alive():
            return
        vk = VK[name]
        scan = u32.MapVirtualKeyW(vk, 0)
        ext = 1 << 24 if name in EXTENDED else 0
        down = 1 | (scan << 16) | ext
        up = down | (1 << 30) | (1 << 31)
        u32.PostMessageW(self.hwnd, 0x100, vk, down)
        u32.PostMessageW(self.hwnd, 0x101, vk, up)

    # -- Titel -------------------------------------------------------------
    def title(self):
        if not self.hwnd:
            return ''
        buf = ctypes.create_unicode_buffer(512)
        u32.GetWindowTextW(self.hwnd, buf, 512)
        return buf.value

    def state(self):
        """(mode_key, file_path, modified) aus dem Fenstertitel."""
        title = self.title()
        if not title.startswith(TITLE_PREFIX):
            return 'dungeon', '', False
        rest = title[len(TITLE_PREFIX):]
        mode_part, _, file_part = rest.partition(' - ')
        modified = file_part.endswith(' *')
        if modified:
            file_part = file_part[:-2]
        if file_part == 'New File':
            file_part = ''
        return MODE_BY_TITLE.get(mode_part, 'dungeon'), file_part, modified

    # -- Dateidialog der Exe fernsteuern ------------------------------------
    def find_dialog(self):
        # Ein eingebettetes Kindfenster kann keinen Dialog besitzen, Windows
        # haengt ihn an das Tk-Fenster. Deshalb ueber die Prozess-ID suchen.
        out = []
        pid = self.proc.pid if self.proc else 0

        def cb(h, _):
            if not u32.IsWindowVisible(h):
                return True
            q = wintypes.DWORD()
            u32.GetWindowThreadProcessId(h, ctypes.byref(q))
            if q.value != pid:
                return True
            buf = ctypes.create_unicode_buffer(64)
            u32.GetClassNameW(h, buf, 64)
            if buf.value == '#32770':
                out.append(h)
            return True
        u32.EnumWindows(WNDENUMPROC(cb), 0)
        return out[0] if out else None

    def _find_edit(self, parent):
        found = []

        def cb(h, _):
            buf = ctypes.create_unicode_buffer(64)
            u32.GetClassNameW(h, buf, 64)
            if buf.value == 'Edit' and u32.IsWindowVisible(h):
                found.append(h)
                return False
            return True
        u32.EnumChildWindows(parent, WNDENUMPROC(cb), 0)
        return found[0] if found else None

    def drive_dialog(self, path, timeout=4.0):
        """Wartet auf den Dateidialog der Exe und bestätigt ihn mit path."""
        deadline = time.time() + timeout
        dlg = None
        while time.time() < deadline and not dlg:
            dlg = self.find_dialog()
            if not dlg:
                time.sleep(0.05)
        if not dlg:
            return False
        edit = None
        while time.time() < deadline and not edit:
            edit = self._find_edit(dlg)
            if not edit:
                time.sleep(0.05)
        if not edit:
            return False
        WM_SETTEXT, WM_COMMAND, IDOK = 0x000C, 0x0111, 1
        u32.SendMessageW(edit, WM_SETTEXT, 0, path)
        time.sleep(0.1)
        u32.SendMessageW(dlg, WM_COMMAND, IDOK, 0)
        return True


# ---------------------------------------------------------------- Hinweise

def mode_hints(mode):
    """Bedienung je Modus, aus 'Dungeons readme.txt' uebersetzt."""
    if mode == 'dungeon':
        return [
            (tr('Linke Maustaste'), tr('Kachel zeichnen')),
            (tr('Rechte Maustaste'), tr('Kachel entfernen')),
            (tr('Klick auf Block'), tr('nächste Blockvariante')),
        ], [
            (EDITOR_RED, tr('Ungültiger Block, kein passender Bausteinsatz')),
            (EDITOR_GREEN, tr('Loch, hier fehlen Blöcke')),
            (EDITOR_VIOLET, tr('Block liegt auf einem anderen, einen verschieben')),
        ]
    if mode == 'height':
        return [
            (tr('Klick auf Block'), tr('Blockvariante / Höhe wechseln')),
            (tr('Weiße Zahl'), tr('Block ändert die Höhe nicht')),
            (tr('Gelbe Zahl'), tr('Block ändert die Höhe')),
        ], [
            (EDITOR_VIOLET, tr('Höhensprung an einer Blockkante oder Dungeon zu hoch')),
        ]
    if mode == 'type':
        return [
            (tr('Linke Maustaste'), tr('einzelnen Block wählen')),
            (tr('Rechte Maustaste'), tr('Blockgruppe wählen')),
            (tr('Mausrad'), tr('Dungeon-Typ setzen (DUN 01..07b, Cave, Mine)')),
        ], [
            (EDITOR_WHITE, tr('Farbe der Auswahl = Typ laut dungeon.txt')),
        ]
    if mode in ('objects', 'lights'):
        return [
            (tr('Linke Maustaste'), tr('Objekt setzen')),
            (tr('Strg + Klick'), tr('Objekttyp aufnehmen')),
            (tr('Umschalt + Klick'), tr('zuletzt gesetztes Objekt entfernen')),
            (tr('Umschalt + Strg + Klick'), tr('alle Objekte dieses Typs entfernen')),
            (tr('Mausrad'), tr('Objekttyp wechseln')),
        ], []
    return [], []


MODE_LABELS = {'dungeon': 'Grundriss', 'height': 'Höhe', 'type': 'Typ',
               'objects': 'Objekte', 'lights': 'Lichter'}

GENERAL_KEYS = (('Tab', 'nächster Modus'), ('F2', 'Speichern'),
                ('F3', 'Öffnen'), ('F4', 'Karten-Offset setzen'),
                ('F5', 'Konsolenskript exportieren'),
                ('F6', 'altes Dungeon laden'), ('F8', 'alles zurücksetzen'),
                ('Bild auf/ab', 'Zoom'), ('Pfeile', 'Ansicht verschieben'))


# ---------------------------------------------------------------- Guide

GUIDE_STEPS = (
    {'title': 'Willkommen',
     'text': 'Dieses Programm ist ein Rahmen um Dungeons.exe aus dem Two Worlds SDK. '
             'Mit dem Editor wurden die Original-Dungeons des Spiels gebaut. '
             'Du malst den Grundriss von oben auf ein Raster, der Editor wählt '
             'die passenden Wand- und Gangbausteine selbst.',
     'widget': None},
    {'title': 'Menüleiste',
     'text': 'Datei, Bearbeiten, Ansicht und Hilfe. Alle Einträge schicken die '
             'Original-Hotkeys an den Editor. Rechts oben schaltest du die '
             'Sprache um.',
     'widget': 'menubar'},
    {'title': 'Werkzeugleiste',
     'text': 'Neu, Öffnen, Speichern und Export, daneben die fünf Modi und der '
             'Zoom. Der aktive Modus ist gold hinterlegt.',
     'widget': 'toolbar'},
    {'title': 'Zeichenfläche',
     'text': 'Das ist das Fenster von Dungeons.exe. Im Modus Grundriss zeichnest '
             'du mit der linken Maustaste Kacheln und entfernst sie mit der '
             'rechten. Buchstaben zeigen den gewählten Baustein.',
     'widget': 'host'},
    {'title': 'Hinweis-Panel',
     'text': 'Rechts stehen immer die Maus- und Tastenbelegung des aktuellen '
             'Modus und die Bedeutung der Fehlfarben rot, grün und violett.',
     'widget': 'panel'},
    {'title': 'Modi',
     'text': 'Grundriss malen, Höhe je Block setzen, Dungeon-Typ zuweisen '
             '(DUN 01 bis 07b, Cave, Mine), Objekte und Lichter wie Fackeln '
             'setzen. Tab schaltet weiter, die Knöpfe springen direkt.',
     'widget': 'mode_box'},
    {'title': 'Export',
     'text': 'Export erzeugt ein Konsolenskript mit createEd-Zeilen. Führe es '
             'im Two Worlds Editor auf einem leeren Untergrund-Level aus und '
             'danach @edundgr.txt, damit unpassierbare Bereiche gesperrt werden.',
     'widget': 'btn_export'},
    {'title': 'Statuszeile',
     'text': 'Unten siehst du Modus, geladene Datei und ob es ungespeicherte '
             'Änderungen gibt. Ein Stern im Editor-Titel bedeutet ungespeichert.',
     'widget': 'statusbar'},
)


class Guide:
    def __init__(self, app):
        self.app = app
        self.i = 0
        self.frames = []
        self.win = None
        self.dont_show = tk.BooleanVar(value=False)

    def start(self):
        self.i = 0
        if self.win:
            self.win.destroy()
        root = self.app.root
        self.win = tk.Toplevel(root, background=PANEL)
        self.win.title(tr('Guide'))
        self.win.transient(root)
        self.win.attributes('-topmost', True)
        self.win.resizable(False, False)
        self.win.protocol('WM_DELETE_WINDOW', self.finish)
        theme.dark_titlebar(self.win)
        self.head = ttk.Label(self.win, style='PanelTitle.TLabel')
        self.head.pack(anchor='w', padx=8, pady=(8, 0))
        self.h2 = ttk.Label(self.win, style='PanelH2.TLabel')
        self.h2.pack(anchor='w', padx=8)
        self.body = ttk.Label(self.win, style='Panel.TLabel', wraplength=360,
                              justify='left', padding=(16, 4))
        self.body.pack(anchor='w', padx=8, pady=(0, 8))
        ttk.Checkbutton(self.win, text=tr('Beim Start nicht mehr anzeigen'),
                        variable=self.dont_show, style='Panel.TCheckbutton'
                        ).pack(anchor='w', padx=20, pady=(0, 8))
        row = ttk.Frame(self.win, style='Panel.TFrame')
        row.pack(fill='x', padx=16, pady=(0, 14))
        self.btn_back = ttk.Button(row, text=tr('Zurück'), command=self.back)
        self.btn_back.pack(side='left')
        self.btn_next = ttk.Button(row, text=tr('Weiter'), style='Accent.TButton',
                                   command=self.next)
        self.btn_next.pack(side='left', padx=8)
        ttk.Button(row, text=tr('Beenden'), command=self.finish).pack(side='right')
        self.show()
        root.update_idletasks()
        x = root.winfo_rootx() + 40
        y = root.winfo_rooty() + 110
        self.win.geometry(f'+{x}+{y}')

    def show(self):
        step = GUIDE_STEPS[self.i]
        self.head.configure(text=tr('Schritt {n} von {total}').format(
            n=self.i + 1, total=len(GUIDE_STEPS)))
        self.h2.configure(text=tr(step['title']))
        self.body.configure(text=tr(step['text']))
        self.btn_back.state(['!disabled'] if self.i else ['disabled'])
        last = self.i == len(GUIDE_STEPS) - 1
        self.btn_next.configure(text=tr('Fertig') if last else tr('Weiter'))
        self.highlight(getattr(self.app, step['widget'], None)
                       if step['widget'] else None)

    def next(self):
        if self.i == len(GUIDE_STEPS) - 1:
            self.finish()
            return
        self.i += 1
        self.show()

    def back(self):
        if self.i:
            self.i -= 1
            self.show()

    def highlight(self, widget):
        for f in self.frames:
            f.destroy()
        self.frames = []
        if widget is None:
            return
        root = self.app.root
        root.update_idletasks()
        x = widget.winfo_rootx() - root.winfo_rootx()
        y = widget.winfo_rooty() - root.winfo_rooty()
        w, h, t = widget.winfo_width(), widget.winfo_height(), 3
        for fx, fy, fw, fh in ((x, y, w, t), (x, y + h - t, w, t),
                               (x, y, t, h), (x + w - t, y, t, h)):
            f = tk.Frame(root, background=GOLD)
            f.place(x=fx, y=fy, width=fw, height=fh)
            f.lift()
            self.frames.append(f)

    def finish(self):
        self.highlight(None)
        if self.dont_show.get() or self.i == len(GUIDE_STEPS) - 1:
            self.app.cfg['guide_seen'] = True
            self.app.cfg.save()
        if self.win:
            self.win.destroy()
            self.win = None


# ---------------------------------------------------------------- App

class App:
    def __init__(self):
        global _LANG
        self.cfg = Config()
        _LANG = self.lang = self.cfg.get('lang', 'de')
        self.restart = False
        self.editor = EditorProcess(find_exe(self.cfg.get('exe_path', '')))
        self.mode = 'dungeon'
        self.file = ''
        self.modified = False
        self.mode_buttons = {}
        self.pending_mode = None
        self.root = tk.Tk()
        self.root.withdraw()
        self.root.title(APP_TITLE)
        theme.apply_dark_theme(self.root)
        self.guide = Guide(self)
        self.build()
        self.root.protocol('WM_DELETE_WINDOW', self.on_close)
        self.root.bind('<Configure>', self.on_configure)
        self.root.update_idletasks()
        self.fit_window()
        self.root.deiconify()
        self.root.after(50, self.launch_editor)

    # -- Aufbau ------------------------------------------------------------
    def build(self):
        self.build_menubar()
        self.build_toolbar()
        body = ttk.Frame(self.root)
        body.pack(fill='both', expand=True)
        self.body = body
        self.host = tk.Frame(body, background=CANVAS_BG, width=CLIENT_W,
                             height=CLIENT_H, highlightthickness=1,
                             highlightbackground=LINE)
        self.host.pack(side='left', padx=(8, 4), pady=6)
        self.host.pack_propagate(False)
        self.host_label = tk.Label(self.host, text=tr('Editor wird gestartet ...'),
                                   background=CANVAS_BG, foreground=MUT, font=FONT)
        self.host_label.place(relx=0.5, rely=0.5, anchor='center')
        self.build_panel(body)
        self.build_statusbar()
        for key in ('F2', 'F3', 'F4', 'F5', 'F6', 'F8'):
            self.root.bind(f'<{key}>', lambda ev, k=key: self.send(k))
        self.root.bind('<Tab>', lambda ev: (self.send('TAB'), 'break')[1])
        self.root.bind('<Prior>', lambda ev: self.send('PGUP'))
        self.root.bind('<Next>', lambda ev: self.send('PGDN'))
        for key, name in (('Left', 'LEFT'), ('Right', 'RIGHT'),
                          ('Up', 'UP'), ('Down', 'DOWN')):
            self.root.bind(f'<{key}>', lambda ev, k=name: self.send(k))

    def build_menubar(self):
        bar = ttk.Frame(self.root, style='Menubar.TFrame')
        bar.pack(fill='x')
        self.menubar = bar
        for key, filler in ((tr('Datei'), self._fill_file),
                            (tr('Bearbeiten'), self._fill_edit),
                            (tr('Ansicht'), self._fill_view),
                            (tr('Hilfe'), self._fill_help)):
            item = ttk.Label(bar, text=key, style='Menubar.TLabel')
            item.pack(side='left')
            item.bind('<Button-1>', lambda ev, f=filler, w=item: self._popup(f, w))
            item.bind('<Enter>', lambda ev, w=item: w.state(['active']))
            item.bind('<Leave>', lambda ev, w=item: w.state(['!active']))
        ttk.Label(bar, text=APP_NAME, style='Menubar.TLabel'
                  ).pack(side='right', padx=(0, 6))
        self.build_lang_toggle(bar).pack(side='right', padx=(0, 10))

    def build_lang_toggle(self, bar):
        box = ttk.Frame(bar, style='Menubar.TFrame')
        self.lang_labels = {}
        for i, code in enumerate(('de', 'en')):
            if i:
                ttk.Label(box, text='·', style='Menubar.TLabel',
                          padding=(2, 5)).pack(side='left')
            lbl = ttk.Label(box, text=code.upper(), style='Menubar.TLabel',
                            padding=(4, 5), cursor='hand2')
            lbl.pack(side='left')
            lbl.bind('<Button-1>', lambda ev, c=code: self.set_lang(c))
            self.lang_labels[code] = lbl
        self.paint_lang_toggle()
        return box

    def paint_lang_toggle(self):
        for code, lbl in self.lang_labels.items():
            lbl.configure(foreground=GOLD if code == self.lang else MUT)

    def set_lang(self, code):
        if code == self.lang:
            return
        if not self.confirm_discard():
            self.lang_var.set(self.lang)
            return
        self.cfg['lang'] = code
        self.cfg['reopen'] = self.file
        self.cfg.save()
        self.restart = True
        self.shutdown()

    def _popup(self, filler, widget):
        menu = theme.Menu(self.root)
        filler(menu)
        try:
            menu.tk_popup(widget.winfo_rootx(),
                          widget.winfo_rooty() + widget.winfo_height())
        finally:
            menu.grab_release()

    def _fill_file(self, m):
        m.add_command(label=tr('Neu'), accelerator='F8', command=self.new_file)
        m.add_command(label=tr('Öffnen ...'), accelerator='F3',
                      command=lambda: self.send('F3'))
        recent = theme.Menu(m)
        for path in self.cfg.get('recent', []):
            recent.add_command(label=path, command=lambda p=path: self.open_path(p))
        if not self.cfg.get('recent'):
            recent.add_command(label=tr('(leer)'), state='disabled')
        m.add_cascade(label=tr('Zuletzt geöffnet'), menu=recent)
        m.add_command(label=tr('Speichern ...'), accelerator='F2',
                      command=lambda: self.send('F2'))
        m.add_command(label=tr('Altes Dungeon laden ...'), accelerator='F6',
                      command=lambda: self.send('F6'))
        m.add_separator()
        m.add_command(label=tr('Editor-Exe wählen ...'), command=self.choose_exe)
        m.add_separator()
        m.add_command(label=tr('Konsolenskript exportieren ...'), accelerator='F5',
                      command=lambda: self.send('F5'))
        m.add_separator()
        m.add_command(label=tr('Beenden'), accelerator='Alt+F4', command=self.on_close)

    def _fill_edit(self, m):
        m.add_command(label=tr('Nächster Modus'), accelerator='Tab',
                      command=lambda: self.send('TAB'))
        modes = theme.Menu(m)
        for key, _ in MODES:
            modes.add_command(label=tr(MODE_LABELS[key]),
                              command=lambda k=key: self.set_mode(k))
        m.add_cascade(label=tr('Modus'), menu=modes)
        m.add_separator()
        m.add_command(label=tr('Karten-Offset setzen'), accelerator='F4',
                      command=lambda: self.send('F4'))
        m.add_command(label=tr('Alles zurücksetzen'), accelerator='F8',
                      command=self.new_file)

    def _fill_view(self, m):
        m.add_command(label=tr('Vergrößern'), accelerator=tr('Bild auf'),
                      command=lambda: self.send('PGUP'))
        m.add_command(label=tr('Verkleinern'), accelerator=tr('Bild ab'),
                      command=lambda: self.send('PGDN'))
        move = theme.Menu(m)
        for label, key in ((tr('Links'), 'LEFT'), (tr('Rechts'), 'RIGHT'),
                           (tr('Hoch'), 'UP'), (tr('Runter'), 'DOWN')):
            move.add_command(label=label, command=lambda k=key: self.send(k))
        m.add_cascade(label=tr('Verschieben'), menu=move)
        m.add_separator()
        m.add_checkbutton(label=tr('Hinweis-Panel'), variable=self.panel_var,
                          command=self.toggle_panel)
        m.add_separator()
        lang = theme.Menu(m)
        lang.add_radiobutton(label='Deutsch', value='de', variable=self.lang_var,
                             command=lambda: self.set_lang('de'))
        lang.add_radiobutton(label='English', value='en', variable=self.lang_var,
                             command=lambda: self.set_lang('en'))
        m.add_cascade(label=tr('Sprache'), menu=lang)

    def _fill_help(self, m):
        m.add_command(label=tr('Guide starten'), command=self.guide.start)
        m.add_command(label=tr('Dokumentation'), command=self.show_docs)
        m.add_separator()
        for name, url in LINKS:
            m.add_command(label=f'{name}  ({url})',
                          command=lambda u=url: webbrowser.open(u))
        m.add_separator()
        m.add_command(label=tr('Über'), command=self.show_about)

    def build_toolbar(self):
        self.panel_var = tk.BooleanVar(value=self.cfg.get('show_panel', True))
        self.lang_var = tk.StringVar(value=self.lang)
        bar = ttk.Frame(self.root, style='Toolbar.TFrame', padding=(6, 4))
        bar.pack(fill='x')
        self.toolbar = bar

        def button(text, cmd, tip):
            b = ttk.Button(bar, text=text, style='Tool.TButton', command=cmd)
            b.pack(side='left', padx=2)
            theme.Tooltip(b, tip)
            return b

        def sep():
            ttk.Frame(bar, style='ToolSep.TFrame', width=1).pack(
                side='left', fill='y', padx=6, pady=2)

        button(tr('Neu'), self.new_file, tr('Raster leeren (F8)'))
        button(tr('Öffnen'), lambda: self.send('F3'), tr('Dungeon-Raster laden (F3)'))
        button(tr('Speichern'), lambda: self.send('F2'), tr('Dungeon-Raster speichern (F2)'))
        self.btn_export = button(tr('Export'), lambda: self.send('F5'),
                                 tr('Konsolenskript für den Two Worlds Editor (F5)'))
        sep()
        ttk.Label(bar, text=tr('Modus'), style='PanelMuted.TLabel').pack(
            side='left', padx=(0, 4))
        self.mode_box = ttk.Frame(bar, style='Toolbar.TFrame')
        self.mode_box.pack(side='left')
        for key, _ in MODES:
            b = ttk.Button(self.mode_box, text=tr(MODE_LABELS[key]),
                           style='Tool.TButton',
                           command=lambda k=key: self.set_mode(k))
            b.pack(side='left', padx=1)
            self.mode_buttons[key] = b
        theme.Tooltip(self.mode_box, tr('Tab schaltet im Editor weiter'))
        sep()
        button(tr('Zoom -'), lambda: self.send('PGDN'), tr('Verkleinern (Bild ab)'))
        button(tr('Zoom +'), lambda: self.send('PGUP'), tr('Vergrößern (Bild auf)'))
        button(tr('Offset'), lambda: self.send('F4'), tr('Karten-Offset setzen (F4)'))

    def build_panel(self, body):
        panel = ttk.Frame(body, style='Panel.TFrame', width=300)
        self.panel = panel
        panel.pack_propagate(False)
        if self.panel_var.get():
            panel.pack(side='left', fill='y', padx=(4, 8), pady=6)
        self.panel_title = ttk.Label(panel, style='PanelH2.TLabel')
        self.panel_title.pack(anchor='w')
        self.hint_box = ttk.Frame(panel, style='Panel.TFrame')
        self.hint_box.pack(fill='x', padx=8)
        ttk.Label(panel, text=tr('Allgemeine Tasten'), style='PanelTitle.TLabel'
                  ).pack(anchor='w', pady=(14, 0))
        keys = ttk.Frame(panel, style='Panel.TFrame')
        keys.pack(fill='x', padx=8)
        for i, (key, what) in enumerate(GENERAL_KEYS):
            ttk.Label(keys, text=tr(key), style='Panel.TLabel', font=FONT_BOLD,
                      width=16).grid(row=i, column=0, sticky='w', pady=1)
            ttk.Label(keys, text=tr(what), style='PanelMuted.TLabel'
                      ).grid(row=i, column=1, sticky='w', pady=1)
        ttk.Label(panel, text=tr('Ins Spiel bringen'), style='PanelTitle.TLabel'
                  ).pack(anchor='w', pady=(14, 0))
        ttk.Label(panel, style='PanelMuted.TLabel', wraplength=270, justify='left',
                  padding=(8, 0),
                  text=tr('1. Export (F5) erzeugt ein Skript mit createEd-Zeilen.\n'
                          '2. Im Two Worlds Editor ein leeres Untergrund-Level '
                          'öffnen und das Skript ausführen.\n'
                          '3. Danach @edundgr.txt ausführen, damit unpassierbare '
                          'Bereiche gesperrt werden.\n'
                          '4. Gegner, Truhen und Marker im Two Worlds Editor setzen.')
                  ).pack(anchor='w')
        self.paint_hints()

    def paint_hints(self):
        for child in self.hint_box.winfo_children():
            child.destroy()
        self.panel_title.configure(text=tr('Modus: {mode}').format(
            mode=tr(MODE_LABELS[self.mode])))
        controls, colours = mode_hints(self.mode)
        keys = ttk.Frame(self.hint_box, style='Panel.TFrame')
        keys.pack(fill='x')
        for row, (key, what) in enumerate(controls):
            ttk.Label(keys, text=key, style='Panel.TLabel', font=FONT_BOLD,
                      wraplength=120, justify='left').grid(
                row=row, column=0, sticky='nw', pady=2, padx=(0, 6))
            ttk.Label(keys, text=what, style='PanelMuted.TLabel',
                      wraplength=140, justify='left').grid(
                row=row, column=1, sticky='nw', pady=2)
        if colours:
            ttk.Label(self.hint_box, text=tr('Farben im Editor'),
                      style='PanelTitle.TLabel', padding=(0, 8, 0, 2)).pack(anchor='w')
            cols = ttk.Frame(self.hint_box, style='Panel.TFrame')
            cols.pack(fill='x')
            for row, (colour, what) in enumerate(colours):
                swatch = tk.Frame(cols, background=colour, width=14, height=14)
                swatch.grid(row=row, column=0, sticky='nw', pady=3, padx=(2, 8))
                ttk.Label(cols, text=what, style='PanelMuted.TLabel',
                          wraplength=240, justify='left').grid(
                    row=row, column=1, sticky='nw', pady=2)

    def build_statusbar(self):
        bar = ttk.Frame(self.root, style='Status.TFrame')
        bar.pack(fill='x', side='bottom')
        self.statusbar = bar
        self.st_mode = ttk.Label(bar, style='Status.TLabel')
        self.st_mode.pack(side='left')
        ttk.Label(bar, text='|', style='StatusSep.TLabel').pack(side='left')
        self.st_file = ttk.Label(bar, style='Status.TLabel')
        self.st_file.pack(side='left')
        self.st_msg = ttk.Label(bar, style='Status.TLabel')
        self.st_msg.pack(side='right')

    def fit_window(self):
        self.root.update_idletasks()
        w = self.root.winfo_reqwidth()
        h = self.root.winfo_reqheight()
        geo = self.cfg.get('geometry', '')
        if geo and '+' in geo:
            pos = geo[geo.index('+'):]
        else:
            pos = ''
        self.root.geometry(f'{w}x{h}{pos}')
        self.root.minsize(w, h)

    # -- Editor ------------------------------------------------------------
    def launch_editor(self):
        exe = self.editor.exe_path
        if not exe:
            self.host_label.configure(
                text=tr('Dungeons.exe aus dem Two Worlds SDK nicht gefunden.\n\n'
                        'Datei > Editor-Exe wählen'), foreground=ERR)
            self.root.after(300, self.choose_exe)
            return
        if exe != self.cfg.get('exe_path'):
            self.cfg['exe_path'] = exe
            self.cfg.save()
        if not self.editor.start():
            self.host_label.configure(text=tr('Editor konnte nicht gestartet werden.'),
                                      foreground=ERR)
            return
        self.host_label.place_forget()
        self.editor.embed(self.host.winfo_id())
        self.root.after(200, self.poll)
        reopen = self.cfg.pop('reopen', '')
        if reopen:
            self.cfg.save()
            self.root.after(600, lambda: self.open_path(reopen))
        self.maybe_start_guide()

    def send(self, key):
        self.editor.key(key)
        return 'break'

    def new_file(self):
        if self.modified and not messagebox.askyesno(
                APP_TITLE, tr('Ungespeicherte Änderungen verwerfen?'), parent=self.root):
            return
        self.send('F8')

    def open_path(self, path):
        if not os.path.isfile(path):
            messagebox.showerror(APP_TITLE, tr('Datei nicht gefunden:\n{path}').format(
                path=path), parent=self.root)
            return
        self.send('F3')
        if not self.editor.drive_dialog(path):
            self.status(tr('Dateidialog nicht gefunden, bitte Datei von Hand wählen'),
                        ERR)

    def choose_exe(self):
        from tkinter import filedialog
        path = filedialog.askopenfilename(
            parent=self.root, title=tr('Dungeons.exe wählen'),
            filetypes=[('Dungeons.exe', 'Dungeons.exe'), ('exe', '*.exe')])
        if not path:
            return
        path = os.path.normpath(path)
        if not valid_exe(path):
            messagebox.showerror(APP_TITLE, tr(
                'Neben dieser Exe fehlen dungeon.txt oder der Data-Ordner. '
                'Bitte Dungeons.exe aus dem Ordner TwoWorldsSDK/Dungeons wählen.'),
                parent=self.root)
            return
        if self.confirm_discard():
            self.cfg['exe_path'] = path
            self.cfg.save()
            self.restart = True
            self.shutdown()

    def set_mode(self, key):
        if key == self.mode or not self.editor.alive():
            return
        self.pending_mode = key
        self._step_mode(0)

    def _step_mode(self, tries):
        mode, _, _ = self.editor.state()
        if mode == self.pending_mode or tries >= len(MODES) + 1:
            self.pending_mode = None
            return
        self.send('TAB')
        self.root.after(120, lambda: self._step_mode(tries + 1))

    # -- Zustand -----------------------------------------------------------
    def poll(self):
        if not self.editor.alive():
            self.status(tr('Editor wurde beendet'), ERR)
            self.host_label.configure(text=tr('Editor wurde beendet.'), foreground=ERR)
            self.host_label.place(relx=0.5, rely=0.5, anchor='center')
            return
        mode, file, modified = self.editor.state()
        if mode != self.mode:
            self.mode = mode
            self.paint_hints()
            for key, btn in self.mode_buttons.items():
                btn.configure(style='ToolOn.TButton' if key == mode else 'Tool.TButton')
        if file != self.file:
            self.file = file
            if file and os.path.isfile(file):
                self.cfg.add_recent(os.path.normpath(file))
        self.modified = modified
        self.st_mode.configure(text=tr('Modus: {mode}').format(
            mode=tr(MODE_LABELS[mode])))
        name = file if file else tr('Neue Datei')
        if modified:
            name += '  ' + tr('(ungespeichert)')
        self.st_file.configure(text=name)
        self.root.title(('* ' if modified else '') + APP_TITLE
                        + (f' - {os.path.basename(file)}' if file else ''))
        self.root.after(300, self.poll)

    def status(self, text, colour=None):
        self.st_msg.configure(text=text,
                              style='StatusErr.TLabel' if colour == ERR else
                              'StatusOk.TLabel' if colour == OK else 'Status.TLabel')
        self.root.after(6000, lambda: self.st_msg.configure(text=''))

    def on_configure(self, ev):
        if ev.widget is self.root and self.editor.alive():
            self.cfg['geometry'] = self.root.geometry()

    def toggle_panel(self):
        show = self.panel_var.get()
        self.cfg['show_panel'] = show
        self.cfg.save()
        if show:
            self.panel.pack(side='left', fill='y', padx=(4, 8), pady=6)
        else:
            self.panel.pack_forget()
        self.root.update_idletasks()
        w, h = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        self.root.minsize(w, h)
        self.root.geometry(f'{w}x{h}')

    def maybe_start_guide(self):
        if not self.cfg.get('guide_seen'):
            self.root.after(400, self.guide.start)

    # -- Dialoge -----------------------------------------------------------
    def show_docs(self):
        try:
            with open(readme_path(self.editor.exe_path), encoding='cp1250', errors='replace') as fh:
                text = fh.read()
        except Exception:
            text = tr('Dungeons readme.txt nicht gefunden:\n{path}').format(
                path=readme_path(self.editor.exe_path))
        win = tk.Toplevel(self.root, background=BG)
        win.title(tr('Dokumentation'))
        win.transient(self.root)
        theme.dark_titlebar(win)
        win.geometry('720x640')
        box = tk.Text(win, font=FONT_MONO, wrap='word', padx=10, pady=8)
        sb = ttk.Scrollbar(win, orient='vertical', command=box.yview)
        box.configure(yscrollcommand=sb.set)
        sb.pack(side='right', fill='y')
        box.pack(fill='both', expand=True, padx=(8, 0), pady=8)
        box.insert('1.0', text)
        box.configure(state='disabled')

    def show_about(self):
        win = tk.Toplevel(self.root, background=BG)
        win.title(tr('Über'))
        win.transient(self.root)
        win.resizable(False, False)
        theme.dark_titlebar(win)
        frame = ttk.Frame(win, padding=16)
        frame.pack(fill='both', expand=True)
        ttk.Label(frame, text=APP_TITLE, style='Brand.TLabel').pack(anchor='w')
        ttk.Label(frame, text=tr('Version {v}').format(v=VERSION), style='Muted.TLabel'
                  ).pack(anchor='w')
        ttk.Label(frame, wraplength=420, justify='left', padding=(0, 10),
                  text=tr('Rahmen mit Menü, Werkzeugleiste und Hinweisen um '
                          'Dungeons.exe aus dem Two Worlds SDK (Reality Pump, 2007). '
                          'Der eingebettete Editor bleibt unverändert; alle Knöpfe '
                          'schicken seine Original-Hotkeys.')).pack(anchor='w')
        ttk.Label(frame, text=tr('Editor-Exe: {path}').format(path=self.editor.exe_path),
                  style='Muted.TLabel', wraplength=420, justify='left').pack(anchor='w')
        for name, url in LINKS:
            lnk = ttk.Label(frame, text=f'{name}: {url}', style='Link.TLabel',
                            cursor='hand2')
            lnk.pack(anchor='w', padx=(12, 0), pady=1)
            lnk.bind('<Button-1>', lambda e, u=url: webbrowser.open(u))
        ttk.Button(frame, text=tr('Schließen'), style='Accent.TButton',
                   command=win.destroy).pack(anchor='e', pady=(14, 0))

    # -- Ende --------------------------------------------------------------
    def confirm_discard(self):
        """True, wenn nichts ungespeichert ist oder der Nutzer verwerfen will."""
        return not self.modified or messagebox.askyesno(
            APP_TITLE, tr('Ungespeicherte Änderungen verwerfen?'), parent=self.root)

    def on_close(self):
        if self.modified and not messagebox.askyesno(
                APP_TITLE, tr('Ungespeicherte Änderungen verwerfen und beenden?'),
                parent=self.root):
            return
        self.shutdown()

    def shutdown(self):
        self.cfg['geometry'] = self.root.geometry()
        self.cfg.save()
        self.editor.stop()
        self.root.destroy()

    def run(self):
        self.root.mainloop()


def main():
    while True:
        app = App()
        app.run()
        if not app.restart:
            break


# ---------------------------------------------------------------- Englisch

EN = {
    'Datei': 'File', 'Bearbeiten': 'Edit', 'Ansicht': 'View', 'Hilfe': 'Help',
    'Neu': 'New', 'Öffnen ...': 'Open ...', 'Zuletzt geöffnet': 'Recent files',
    '(leer)': '(empty)', 'Speichern ...': 'Save ...',
    'Altes Dungeon laden ...': 'Load old dungeon ...',
    'Editor-Exe wählen ...': 'Choose editor exe ...',
    'Konsolenskript exportieren ...': 'Export console script ...',
    'Beenden': 'Quit', 'Nächster Modus': 'Next mode', 'Modus': 'Mode',
    'Karten-Offset setzen': 'Set map offset', 'Alles zurücksetzen': 'Reset everything',
    'Vergrößern': 'Zoom in', 'Verkleinern': 'Zoom out', 'Bild auf': 'Page Up',
    'Bild ab': 'Page Down', 'Links': 'Left', 'Rechts': 'Right', 'Hoch': 'Up',
    'Runter': 'Down', 'Verschieben': 'Scroll', 'Hinweis-Panel': 'Hint panel',
    'Sprache': 'Language', 'Guide starten': 'Start guide',
    'Dokumentation': 'Documentation', 'Über': 'About',
    'Öffnen': 'Open', 'Speichern': 'Save', 'Export': 'Export',
    'Raster leeren (F8)': 'Clear grid (F8)',
    'Dungeon-Raster laden (F3)': 'Load dungeon grid (F3)',
    'Dungeon-Raster speichern (F2)': 'Save dungeon grid (F2)',
    'Konsolenskript für den Two Worlds Editor (F5)':
        'Console script for the Two Worlds Editor (F5)',
    'Tab schaltet im Editor weiter': 'Tab cycles modes in the editor',
    'Zoom -': 'Zoom -', 'Zoom +': 'Zoom +', 'Offset': 'Offset',
    'Verkleinern (Bild ab)': 'Zoom out (Page Down)',
    'Vergrößern (Bild auf)': 'Zoom in (Page Up)',
    'Karten-Offset setzen (F4)': 'Set map offset (F4)',
    'Grundriss': 'Layout', 'Höhe': 'Height', 'Typ': 'Type', 'Objekte': 'Objects',
    'Lichter': 'Lights',
    'Linke Maustaste': 'Left mouse button', 'Rechte Maustaste': 'Right mouse button',
    'Klick auf Block': 'Click on block', 'Kachel zeichnen': 'draw tile',
    'Kachel entfernen': 'remove tile', 'nächste Blockvariante': 'next block variant',
    'Ungültiger Block, kein passender Bausteinsatz':
        'Invalid block, no matching block set',
    'Loch, hier fehlen Blöcke': 'Hole, blocks must be added',
    'Block liegt auf einem anderen, einen verschieben':
        'Block sits on another one, move one of them',
    'Blockvariante / Höhe wechseln': 'change block variant / height',
    'Weiße Zahl': 'White number', 'Gelbe Zahl': 'Yellow number',
    'Block ändert die Höhe nicht': 'block keeps the height',
    'Block ändert die Höhe': 'block changes the height',
    'Höhensprung an einer Blockkante oder Dungeon zu hoch':
        'Height mismatch at a block joint, or dungeon too high',
    'einzelnen Block wählen': 'select single block',
    'Blockgruppe wählen': 'select group of blocks', 'Mausrad': 'Mouse wheel',
    'Dungeon-Typ setzen (DUN 01..07b, Cave, Mine)':
        'set dungeon type (DUN 01..07b, Cave, Mine)',
    'Farbe der Auswahl = Typ laut dungeon.txt':
        'Selection colour = type as defined in dungeon.txt',
    'Objekt setzen': 'place object', 'Strg + Klick': 'Ctrl + click',
    'Objekttyp aufnehmen': 'pick up object type', 'Umschalt + Klick': 'Shift + click',
    'zuletzt gesetztes Objekt entfernen': 'remove last placed object',
    'Umschalt + Strg + Klick': 'Shift + Ctrl + click',
    'alle Objekte dieses Typs entfernen': 'remove all objects of this type',
    'Objekttyp wechseln': 'change object type',
    'nächster Modus': 'next mode', 'Öffnen': 'Open',
    'Konsolenskript exportieren': 'export console script',
    'altes Dungeon laden': 'load old dungeon', 'alles zurücksetzen': 'reset everything',
    'Bild auf/ab': 'Page Up/Down', 'Zoom': 'Zoom', 'Pfeile': 'Arrows',
    'Ansicht verschieben': 'scroll view', 'Allgemeine Tasten': 'General keys',
    'Ins Spiel bringen': 'Getting it into the game',
    '1. Export (F5) erzeugt ein Skript mit createEd-Zeilen.\n'
    '2. Im Two Worlds Editor ein leeres Untergrund-Level öffnen und das Skript '
    'ausführen.\n3. Danach @edundgr.txt ausführen, damit unpassierbare Bereiche '
    'gesperrt werden.\n4. Gegner, Truhen und Marker im Two Worlds Editor setzen.':
        '1. Export (F5) writes a script of createEd lines.\n'
        '2. Open an empty underground level in the Two Worlds Editor and run the '
        'script.\n3. Then run @edundgr.txt so impassable areas get disabled.\n'
        '4. Place enemies, chests and markers in the Two Worlds Editor.',
    'Modus: {mode}': 'Mode: {mode}', 'Farben im Editor': 'Colours in the editor',
    'Neue Datei': 'New file', '(ungespeichert)': '(unsaved)',
    'Editor wird gestartet ...': 'Starting editor ...',
    'Dungeons.exe aus dem Two Worlds SDK nicht gefunden.\n\nDatei > Editor-Exe wählen':
        'Dungeons.exe from the Two Worlds SDK not found.\n\nFile > Choose editor exe',
    'Neben dieser Exe fehlen dungeon.txt oder der Data-Ordner. '
    'Bitte Dungeons.exe aus dem Ordner TwoWorldsSDK/Dungeons wählen.':
        'dungeon.txt or the Data folder is missing next to this exe. '
        'Please choose Dungeons.exe from the TwoWorldsSDK/Dungeons folder.',
    'Editor konnte nicht gestartet werden.': 'The editor could not be started.',
    'Editor wurde beendet': 'Editor has exited', 'Editor wurde beendet.': 'Editor has exited.',
    'Ungespeicherte Änderungen verwerfen?': 'Discard unsaved changes?',
    'Ungespeicherte Änderungen verwerfen und beenden?':
        'Discard unsaved changes and quit?',
    'Datei nicht gefunden:\n{path}': 'File not found:\n{path}',
    'Dateidialog nicht gefunden, bitte Datei von Hand wählen':
        'File dialog not found, please pick the file by hand',
    'Dungeons.exe wählen': 'Choose Dungeons.exe',
    'Dungeons readme.txt nicht gefunden:\n{path}': 'Dungeons readme.txt not found:\n{path}',
    'Version {v}': 'Version {v}', 'Editor-Exe: {path}': 'Editor exe: {path}',
    'Rahmen mit Menü, Werkzeugleiste und Hinweisen um Dungeons.exe aus dem Two '
    'Worlds SDK (Reality Pump, 2007). Der eingebettete Editor bleibt unverändert; '
    'alle Knöpfe schicken seine Original-Hotkeys.':
        'Menu, toolbar and hints around Dungeons.exe from the Two Worlds SDK '
        '(Reality Pump, 2007). The embedded editor is untouched; every button just '
        'sends its original hotkeys.',
    'Schließen': 'Close', 'Guide': 'Guide',
    'Beim Start nicht mehr anzeigen': "Don't show at startup",
    'Zurück': 'Back', 'Weiter': 'Next', 'Fertig': 'Done',
    'Schritt {n} von {total}': 'Step {n} of {total}',
    'Willkommen': 'Welcome', 'Menüleiste': 'Menu bar', 'Werkzeugleiste': 'Toolbar',
    'Zeichenfläche': 'Drawing area', 'Modi': 'Modes', 'Statuszeile': 'Status bar',
    'Dieses Programm ist ein Rahmen um Dungeons.exe aus dem Two Worlds SDK. Mit dem '
    'Editor wurden die Original-Dungeons des Spiels gebaut. Du malst den Grundriss '
    'von oben auf ein Raster, der Editor wählt die passenden Wand- und '
    'Gangbausteine selbst.':
        'This program wraps Dungeons.exe from the Two Worlds SDK. The original '
        'dungeons of the game were built with it. You paint the layout top-down on '
        'a grid and the editor picks the matching wall and corridor blocks itself.',
    'Datei, Bearbeiten, Ansicht und Hilfe. Alle Einträge schicken die '
    'Original-Hotkeys an den Editor. Rechts oben schaltest du die Sprache um.':
        'File, Edit, View and Help. Every entry sends the original hotkeys to the '
        'editor. Top right switches the language.',
    'Neu, Öffnen, Speichern und Export, daneben die fünf Modi und der Zoom. Der '
    'aktive Modus ist gold hinterlegt.':
        'New, Open, Save and Export, next to them the five modes and the zoom. The '
        'active mode is highlighted in gold.',
    'Das ist das Fenster von Dungeons.exe. Im Modus Grundriss zeichnest du mit der '
    'linken Maustaste Kacheln und entfernst sie mit der rechten. Buchstaben zeigen '
    'den gewählten Baustein.':
        'This is the window of Dungeons.exe. In Layout mode the left mouse button '
        'draws tiles and the right one removes them. Letters show the chosen block.',
    'Rechts stehen immer die Maus- und Tastenbelegung des aktuellen Modus und die '
    'Bedeutung der Fehlfarben rot, grün und violett.':
        'The right side always lists mouse and key bindings of the current mode and '
        'what the error colours red, green and violet mean.',
    'Grundriss malen, Höhe je Block setzen, Dungeon-Typ zuweisen (DUN 01 bis 07b, '
    'Cave, Mine), Objekte und Lichter wie Fackeln setzen. Tab schaltet weiter, die '
    'Knöpfe springen direkt.':
        'Paint the layout, set the height per block, assign the dungeon type (DUN 01 '
        'to 07b, Cave, Mine), place objects and lights such as torches. Tab cycles, '
        'the buttons jump directly.',
    'Export erzeugt ein Konsolenskript mit createEd-Zeilen. Führe es im Two Worlds '
    'Editor auf einem leeren Untergrund-Level aus und danach @edundgr.txt, damit '
    'unpassierbare Bereiche gesperrt werden.':
        'Export writes a console script of createEd lines. Run it in the Two Worlds '
        'Editor on an empty underground level, then run @edundgr.txt so impassable '
        'areas get disabled.',
    'Unten siehst du Modus, geladene Datei und ob es ungespeicherte Änderungen '
    'gibt. Ein Stern im Editor-Titel bedeutet ungespeichert.':
        'The bottom shows mode, loaded file and whether there are unsaved changes. '
        'A star in the editor title means unsaved.',
    'Tab': 'Tab', 'F2': 'F2', 'F3': 'F3', 'F4': 'F4', 'F5': 'F5', 'F6': 'F6',
    'F8': 'F8',
}


if __name__ == '__main__':
    main()
