"""Dark theme: colours, fonts, ttk styles, menus, tooltips.

Values follow PY_TOOL_DESIGN.md (TW1 Quest Creator look). No hex value
outside this file.
"""

import tkinter as tk
from tkinter import ttk

BG = '#14110e'
PANEL = '#1c1813'
FIELD = '#231e17'
CANVAS_BG = '#0f0d0a'
GRID = '#1a1611'
LINE = '#352f26'
SEL = '#3a3122'
INK = '#ece7db'
MUT = '#9a938a'
DIM = '#5c564c'
GOLD = '#d2a044'
GOLD_HI = '#e3b45c'
OK = '#43b563'
ERR = '#e06c60'
HI_SEL = '#ff2a2a'
HI_MARK = '#33ff55'
HI_MARK_2 = '#ffe14d'
ON_GOLD = '#17130b'
HOVER = '#282219'
SCROLL_THUMB = '#7a7061'

CATEGORY_COLORS = ['#e06c60', '#7fbf7f', '#e0a050', '#c090e0',
                   '#5fc7c7', '#d4796b', '#a0b060', '#d0a0a0']
OWN_COLOR = '#6ca0e0'
COMMENT_COLOR = '#4a453d'

# editor feedback colours, as drawn by Dungeons.exe (legend only)
EDITOR_RED = '#e04040'
EDITOR_GREEN = '#40c040'
EDITOR_VIOLET = '#b060e0'
EDITOR_WHITE = '#ece7db'
EDITOR_YELLOW = '#ffe14d'

FONT = ('Segoe UI', 9)
FONT_BOLD = ('Segoe UI', 9, 'bold')
FONT_SMALL = ('Segoe UI', 8)
FONT_MENU = ('Segoe UI', 10)
FONT_BRAND = ('Georgia', 12, 'bold')
FONT_MONO = ('Consolas', 9)
FONT_H1 = ('Segoe UI Semibold', 15)
FONT_H2 = ('Segoe UI Semibold', 11)
FONT_H3 = ('Segoe UI Semibold', 10)
FONT_GUIDE = ('Segoe UI', 10)


def dark_titlebar(window):
    """Dark title bar on Windows, caption colour set explicitly too."""
    try:
        import ctypes
        window.update_idletasks()
        hwnd = ctypes.windll.user32.GetParent(window.winfo_id())
        dwm = ctypes.windll.dwmapi
        flag = ctypes.c_int(1)
        for attr in (20, 19):        # DWMWA_USE_IMMERSIVE_DARK_MODE, pre-20H1
            if dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(flag),
                                         ctypes.sizeof(flag)) == 0:
                break

        def bgr(hex_colour):
            r, g, b = (int(hex_colour[i:i + 2], 16) for i in (1, 3, 5))
            return ctypes.c_int(b << 16 | g << 8 | r)
        for attr, colour in ((35, PANEL), (36, INK)):     # caption, text
            value = bgr(colour)
            dwm.DwmSetWindowAttribute(hwnd, attr, ctypes.byref(value),
                                      ctypes.sizeof(value))
    except Exception:
        pass


def apply_dark_theme(root):
    root.configure(background=BG)
    dark_titlebar(root)
    style = ttk.Style(root)
    style.theme_use('clam')
    style.configure('.', background=BG, foreground=INK, bordercolor=LINE,
                    darkcolor=BG, lightcolor=BG, troughcolor=PANEL,
                    fieldbackground=FIELD, selectbackground=SEL,
                    selectforeground=GOLD_HI, insertcolor=INK, font=FONT)
    style.configure('TLabelframe', bordercolor=LINE)
    style.configure('TLabelframe.Label', foreground=GOLD)
    style.configure('TButton', background=PANEL, padding=(12, 5),
                    borderwidth=1, focusthickness=1, focuscolor=LINE)
    style.map('TButton', background=[('pressed', SEL), ('active', HOVER)],
              foreground=[('disabled', DIM)])
    style.configure('Accent.TButton', background=GOLD, foreground=ON_GOLD)
    style.map('Accent.TButton',
              background=[('pressed', '#b88d3c'), ('active', GOLD_HI),
                          ('disabled', '#6d5b31')],
              foreground=[('disabled', '#3a3226')])
    # Menubutton (Aufklapp-Knopf): clam malt ihn beim Hover fast weiss,
    # die Schrift verschwindet. Immer mit einfaerben.
    style.configure('TMenubutton', background=PANEL, foreground=INK,
                    arrowcolor=MUT, padding=(10, 4), relief='flat',
                    borderwidth=1)
    style.map('TMenubutton',
              background=[('pressed', SEL), ('active', HOVER)],
              foreground=[('active', GOLD_HI), ('disabled', DIM)],
              arrowcolor=[('active', GOLD_HI)])
    style.configure('Tool.TButton', background=PANEL, padding=(9, 4),
                    borderwidth=1, focusthickness=1, focuscolor=LINE)
    style.map('Tool.TButton', background=[('pressed', SEL), ('active', HOVER)],
              foreground=[('disabled', DIM)])
    style.configure('ToolOn.TButton', background=GOLD, foreground=ON_GOLD,
                    padding=(9, 4), borderwidth=1, focusthickness=1,
                    focuscolor=GOLD)
    style.map('ToolOn.TButton',
              background=[('pressed', '#b88d3c'), ('active', GOLD_HI)])
    style.configure('TNotebook', bordercolor=LINE, tabmargins=(8, 6, 8, 0))
    style.configure('TNotebook.Tab', background=PANEL, foreground=MUT,
                    padding=(16, 6), bordercolor=LINE)
    style.map('TNotebook.Tab', background=[('selected', BG)],
              foreground=[('selected', GOLD)])
    style.configure('Treeview', background=FIELD, fieldbackground=FIELD,
                    rowheight=22, bordercolor=LINE)
    style.map('Treeview', background=[('selected', SEL)],
              foreground=[('selected', GOLD_HI)])
    style.configure('Treeview.Heading', background=PANEL, foreground=MUT,
                    bordercolor=LINE, relief='flat', padding=(6, 4))
    style.map('Treeview.Heading',
              background=[('active', HOVER), ('pressed', SEL)],
              foreground=[('active', INK)])
    for cls in ('TCheckbutton', 'TRadiobutton'):
        style.configure(cls, background=BG, foreground=INK,
                        indicatorbackground=FIELD, indicatorforeground=GOLD,
                        bordercolor=LINE, focuscolor=BG, padding=(2, 2))
        style.map(cls,
                  background=[('active', BG), ('pressed', BG),
                              ('selected', BG)],
                  foreground=[('active', GOLD_HI), ('disabled', DIM)],
                  indicatorbackground=[('selected', GOLD), ('pressed', SEL),
                                       ('active', FIELD)],
                  indicatorforeground=[('selected', ON_GOLD)])
    style.configure('TCombobox', arrowcolor=MUT, foreground=INK,
                    fieldbackground=FIELD, background=PANEL,
                    selectbackground=FIELD, selectforeground=INK,
                    bordercolor=LINE, padding=(6, 3))
    style.map('TCombobox',
              fieldbackground=[('readonly', FIELD), ('disabled', PANEL)],
              foreground=[('readonly', INK), ('disabled', DIM)],
              selectbackground=[('readonly', FIELD)],
              selectforeground=[('readonly', INK)],
              arrowcolor=[('active', GOLD)])
    for cls in ('Vertical.TScrollbar', 'Horizontal.TScrollbar'):
        style.configure(cls, background=SCROLL_THUMB, troughcolor=BG,
                        bordercolor=LINE, arrowcolor=MUT,
                        darkcolor=SCROLL_THUMB, lightcolor=SCROLL_THUMB,
                        gripcount=0, relief='flat', arrowsize=13)
        style.map(cls, background=[('pressed', GOLD), ('active', GOLD_HI)],
                  arrowcolor=[('active', GOLD)])
    style.configure('TPanedwindow', background=LINE)
    style.configure('Sash', sashthickness=5, gripcount=0)
    style.configure('TProgressbar', background=GOLD, troughcolor=FIELD,
                    bordercolor=LINE, lightcolor=GOLD, darkcolor=GOLD)
    style.configure('Brand.TLabel', foreground=GOLD, font=FONT_BRAND)
    style.configure('Link.TLabel', foreground=GOLD)
    style.map('Link.TLabel', foreground=[('active', GOLD_HI)])
    style.configure('Panel.TFrame', background=PANEL)
    style.configure('Panel.TLabel', background=PANEL, foreground=INK)
    style.configure('PanelTitle.TLabel', background=PANEL, foreground=GOLD,
                    font=FONT_BOLD, padding=(8, 5))
    style.configure('PanelH2.TLabel', background=PANEL, foreground=GOLD,
                    font=FONT_H2, padding=(8, 6))
    style.configure('Muted.TLabel', foreground=MUT)
    style.configure('PanelMuted.TLabel', background=PANEL, foreground=MUT)
    style.configure('PanelLink.TLabel', background=PANEL, foreground=GOLD)
    style.map('PanelLink.TLabel', foreground=[('active', GOLD_HI)])
    style.configure('Panel.TCheckbutton', background=PANEL, foreground=INK,
                    indicatorbackground=FIELD, indicatorforeground=GOLD,
                    focuscolor=PANEL)
    style.map('Panel.TCheckbutton',
              background=[('active', PANEL), ('pressed', PANEL),
                          ('selected', PANEL)],
              foreground=[('active', GOLD_HI)],
              indicatorbackground=[('selected', GOLD), ('pressed', SEL),
                                   ('active', FIELD)],
              indicatorforeground=[('selected', ON_GOLD)])
    style.configure('Status.TFrame', background=PANEL)
    style.configure('Status.TLabel', background=PANEL, foreground=MUT,
                    padding=(8, 3), font=FONT_SMALL)
    style.configure('StatusOk.TLabel', background=PANEL, foreground=OK,
                    padding=(8, 3), font=FONT_SMALL)
    style.configure('StatusErr.TLabel', background=PANEL, foreground=ERR,
                    padding=(8, 3), font=FONT_SMALL)
    style.configure('StatusSep.TLabel', background=PANEL, foreground=LINE,
                    padding=(0, 3), font=FONT_SMALL)
    style.configure('Menubar.TFrame', background=PANEL)
    style.configure('Menubar.TLabel', background=PANEL, foreground=INK,
                    padding=(12, 5), font=FONT_MENU)
    style.map('Menubar.TLabel', background=[('active', SEL)],
              foreground=[('active', GOLD_HI)])
    style.configure('Help.TLabel', background=PANEL, foreground=GOLD,
                    font=FONT_BOLD, padding=(4, 5))
    style.map('Help.TLabel', foreground=[('active', GOLD_HI)])
    style.configure('Toolbar.TFrame', background=PANEL)
    style.configure('ToolSep.TFrame', background=LINE)
    for pattern, value in (
            ('*Text.background', CANVAS_BG), ('*Text.foreground', INK),
            ('*Text.insertBackground', INK), ('*Text.selectBackground', SEL),
            ('*Text.borderWidth', 0), ('*Text.highlightThickness', 1),
            ('*Text.highlightBackground', LINE),
            ('*Text.highlightColor', GOLD),
            ('*Listbox.background', FIELD), ('*Listbox.foreground', INK),
            ('*Listbox.selectBackground', SEL),
            ('*Listbox.borderWidth', 0), ('*Listbox.highlightThickness', 1),
            ('*Listbox.highlightBackground', LINE),
            ('*Menu.background', PANEL), ('*Menu.foreground', INK),
            ('*Menu.activeBackground', SEL),
            ('*Menu.activeForeground', GOLD_HI),
            ('*Menu.disabledForeground', DIM),
            ('*Menu.selectColor', GOLD),
            ('*Menu.font', FONT_MENU),
            ('*Menu.borderWidth', 1),
            ('*Menu.activeBorderWidth', 0),
            ('*Menu.relief', 'flat'),
            ('*TCombobox*Listbox.background', FIELD),
            ('*TCombobox*Listbox.foreground', INK),
            ('*TCombobox*Listbox.selectBackground', SEL),
            ('*Toplevel.background', BG)):
        root.option_add(pattern, value)


class Menu(tk.Menu):
    """Dropdown / context menu with readable disabled entries."""

    def __init__(self, master=None, **kw):
        kw.setdefault('tearoff', 0)
        kw.setdefault('font', FONT_MENU)
        kw.setdefault('background', PANEL)
        kw.setdefault('foreground', INK)
        kw.setdefault('activebackground', SEL)
        kw.setdefault('activeforeground', GOLD_HI)
        kw.setdefault('disabledforeground', DIM)
        kw.setdefault('relief', 'flat')
        kw.setdefault('activeborderwidth', 0)
        super().__init__(master, **kw)

    @staticmethod
    def _soft_disable(kind, kw):
        if kw.get('state') == 'disabled':
            kw['state'] = 'normal'
            kw['foreground'] = DIM
            kw['activeforeground'] = DIM
            kw['activebackground'] = PANEL
            if kind != 'cascade':
                kw['command'] = lambda: None
        return kw

    def add_command(self, cnf=None, **kw):
        super().add_command(cnf or {}, **self._soft_disable('command', kw))

    def add_checkbutton(self, cnf=None, **kw):
        super().add_checkbutton(cnf or {}, **self._soft_disable('check', kw))

    def add_radiobutton(self, cnf=None, **kw):
        super().add_radiobutton(cnf or {}, **self._soft_disable('radio', kw))

    def add_cascade(self, cnf=None, **kw):
        super().add_cascade(cnf or {}, **self._soft_disable('cascade', kw))


class Tooltip:
    """Small hover tooltip for any widget."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.tip = None
        widget.bind('<Enter>', self._show, add='+')
        widget.bind('<Leave>', self._hide, add='+')
        widget.bind('<ButtonPress>', self._hide, add='+')

    def _show(self, ev):
        if self.tip or not self.text:
            return
        self.tip = tk.Toplevel(self.widget)
        self.tip.wm_overrideredirect(True)
        self.tip.attributes('-topmost', True)
        tk.Label(self.tip, text=self.text, bg=PANEL, fg=INK, bd=1,
                 relief='solid', justify='left', padx=6, pady=3,
                 font=FONT_SMALL).pack()
        self.tip.wm_geometry(f'+{ev.x_root + 14}+{ev.y_root + 12}')

    def _hide(self, ev=None):
        if self.tip:
            self.tip.destroy()
            self.tip = None
