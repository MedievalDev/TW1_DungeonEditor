"""Guide-Fenster: Hilfe > Guide (F1).

Kapitelbaum links, Text rechts, Suchfeld oben, Deutsch und Englisch
(PY_TOOL_DESIGN.md 6.2). Tabellen werden aus denselben Daten erzeugt, die
das Tool benutzt (Tastenliste, Modus-Hinweise), oder live aus der
``dungeon.txt`` neben der Dungeons.exe gelesen. Jede Tabelle nennt darunter
ihre Quelle; ``test_guide.py`` prüft das.

Das Modul importiert nichts aus dungeon_editor.py. Alles, was es vom Tool
braucht (Sprache, Übersetzung, Tastenliste, Exe-Pfad), kommt über ``ctx``.
"""

import os
import re
import tkinter as tk
from tkinter import ttk

import theme


class Ctx:
    """Was die Kapitel vom Tool brauchen. Das App-Objekt erfüllt das auch."""

    def __init__(self, lang='de', tr=None, general_keys=(), mode_hints=None,
                 mode_labels=None, exe_path=''):
        self.lang = lang
        self.tr = tr or (lambda s: s)
        self.general_keys = general_keys
        self.mode_hints = mode_hints or (lambda mode: ([], []))
        self.mode_labels = mode_labels or {}
        self.exe_path = exe_path


def _l(ctx, de, en):
    return de if ctx.lang == 'de' else en


def _table(head, rows):
    out = ['| ' + ' | '.join(head) + ' |', '|' + '---|' * len(head)]
    out += ['| ' + ' | '.join(str(c) for c in r) + ' |' for r in rows]
    return '\n'.join(out)


def _source(ctx, de, en):
    return _l(ctx, 'Quelle: ', 'Source: ') + _l(ctx, de, en)


# ---------------------------------------------------------------- SDK-Daten

def read_dungeon_txt(exe_path):
    """dungeon.txt neben der Exe lesen.

    Gibt (typen, gruppen) zurück: typen = [(name, bloecke, nummer, (r, g, b),
    [gruppennamen])], gruppen = {name: (art, [(objekt, objekt_id, mesh,
    bitmap, reichweite, farbe oder None)])}. Leere Listen, wenn die Datei
    fehlt.
    """
    path = os.path.join(os.path.dirname(exe_path or ''), 'dungeon.txt')
    types, groups = [], {}
    try:
        with open(path, encoding='cp1250', errors='replace') as fh:
            lines = [ln.strip() for ln in fh]
    except OSError:
        return types, groups
    i = 0
    while i < len(lines):
        head = lines[i].rstrip('{').split()
        i += 1
        if not head:
            continue
        body = []
        while i < len(lines) and '}' not in lines[i]:
            if lines[i] and lines[i] != '{':
                body.append(lines[i].split())
            i += 1
        i += 1
        if head[0] in ('Addons', 'Lights') and len(head) >= 2:
            items = []
            for p in body:
                if len(p) < 4:
                    continue
                rng = p[4] if len(p) > 4 else '0'
                rgb = tuple(p[5:8]) if len(p) >= 8 else None
                items.append((p[0], p[1], p[2], p[3], rng, rgb))
            groups[head[1]] = (head[0], items)
        elif head[0] == 'Dungeon' and len(head) >= 7:
            types.append((head[1], head[2], head[3], tuple(head[4:7]),
                          [' '.join(p) for p in body]))
    return types, groups


def list_grids(exe_path):
    """Raster im SDK-Ordner Dungeons\\Dungeons: [(datei, skript oder '')]."""
    folder = os.path.join(os.path.dirname(exe_path or ''), 'Dungeons')
    try:
        names = sorted(os.listdir(folder))
    except OSError:
        return []
    scripts = {n.lower() for n in names}
    out = []
    for n in names:
        full = os.path.join(folder, n)
        if not os.path.isfile(full) or os.path.getsize(full) < 1_000_000:
            continue                       # Raster sind rund 1,1 MB groß
        base = n[:-4] if n.lower().endswith('.txt') else n
        script = next((s for s in (base + 'src.txt', base + 'scr.txt', base + '.txt')
                       if s.lower() in scripts and s.lower() != n.lower()), '')
        out.append((n, script))
    return out


# ---------------------------------------------------------------- Kapitel

def ch_start(ctx):
    rows = [(ctx.tr(k), ctx.tr(w)) for k, w in ctx.general_keys]
    return _l(ctx, """# Einstieg

Der TW1 Dungeon Editor ist ein Rahmen um **Dungeons.exe** aus dem Two Worlds
SDK. Mit diesem Editor wurden laut SDK-Notizen die Dungeons des Spiels gebaut.
Du malst den Grundriss von oben auf ein Raster, der Editor wählt die passenden
Wand- und Gangbausteine und schreibt am Ende ein Konsolenskript für den Two
Worlds Editor.

Das Fenster hat vier Bereiche:

- **Menüleiste und Werkzeugleiste** oben: Datei, Modi, Zoom. Alle Knöpfe
  schicken nur die Original-Tasten an den Editor.
- **Zeichenfläche** links: das eingebettete Fenster von Dungeons.exe, fest
  1024 x 768 Pixel.
- **Hinweis-Panel** rechts: Maus und Tasten des aktuellen Modus, Warnfarben,
  Checkliste für den Weg ins Spiel.
- **Statusleiste** unten: Modus, Datei, ungespeichert, Checkliste.

Das `?` neben Titeln erklärt beim Überfahren und springt beim Klick in das
passende Kapitel. Den kurzen Rundgang startest du unter Hilfe > Rundgang
starten.

## Tasten
""", """# Getting started

TW1 Dungeon Editor is a frame around **Dungeons.exe** from the Two Worlds SDK.
According to the SDK notes, the game's dungeons were built with this editor.
You paint the layout top-down on a grid, the editor picks the matching wall
and corridor blocks and in the end writes a console script for the Two Worlds
Editor.

The window has four areas:

- **Menu bar and toolbar** at the top: file, modes, zoom. Every button just
  sends the original keys to the editor.
- **Canvas** on the left: the embedded Dungeons.exe window, fixed at
  1024 x 768 pixels.
- **Hint panel** on the right: mouse and keys of the current mode, warning
  colours, checklist for the way into the game.
- **Status bar** at the bottom: mode, file, unsaved, checklist.

The `?` next to titles explains on hover and jumps to the matching chapter on
click. The short tour is under Help > Start tour.

## Keys
""") + _table([_l(ctx, 'Taste', 'Key'), _l(ctx, 'Wirkung', 'Effect')], rows) + '\n\n' + _source(
        ctx, "SDK `Documentation\\Dungeons readme.txt`, Abschnitt 1. Zoom-Richtung gemessen am 14.09.2026: Bild ab zoomt hinein, Bild auf heraus.",
        "SDK `Documentation\\Dungeons readme.txt`, section 1. Zoom direction measured on 14 Sep 2026: Page Down zooms in, Page Up zooms out.")


def ch_first(ctx):
    return _l(ctx, """# Erstes Dungeon in 10 Minuten

1. **Original ansehen:** Datei > Öffnen, `Dungeons\\Dungeons\\7.txt` aus dem
   SDK wählen. Das ist das kleinste Beispiel. Mit den Modus-Knöpfen durch
   Höhe, Typ und Lichter schalten.
2. **Neu:** Werkzeugleiste > Neu leert das Raster.
3. **Zwei Räume und ein Gang:** im Modus Grundriss mit der linken Maustaste
   einen Raum von 4 x 4 Kacheln malen, einen Gang von 7 Kacheln nach rechts und
   einen zweiten Raum von 3 x 3. Solange nichts rot, grün oder violett ist,
   passt jede Kachel.
4. **Speichern:** Werkzeugleiste > Speichern (F2), Name zum Beispiel
   `meindungeon.txt`. Das ist das Raster zum Weiterbearbeiten.
5. **Exportieren:** Werkzeugleiste > Export (F5), Name zum Beispiel
   `meindungeon_src.txt`. Das ist das Skript für den Two Worlds Editor.
6. **Ins Spiel:** weiter im Kapitel "Export und Weg ins Spiel". Die Schritte
   stehen auch als Checkliste im Hinweis-Panel.

Gemessen am 14.09.2026: Der Grundriss aus Schritt 3 ergibt 31 Kacheln und 19
Skriptzeilen. Große Wandstücke belegen mehrere Kacheln.
""", """# First dungeon in 10 minutes

1. **Look at an original:** File > Open, pick `Dungeons\\Dungeons\\7.txt` from
   the SDK. It is the smallest sample. Use the mode buttons to step through
   height, type and lights.
2. **New:** toolbar > New clears the grid.
3. **Two rooms and a corridor:** in Layout mode, paint a 4 x 4 room with the
   left mouse button, a corridor of 7 tiles to the right and a second 3 x 3
   room. As long as nothing is red, green or violet, every tile fits.
4. **Save:** toolbar > Save (F2), name it e.g. `mydungeon.txt`. That is the
   grid for later edits.
5. **Export:** toolbar > Export (F5), name it e.g. `mydungeon_src.txt`. That is
   the script for the Two Worlds Editor.
6. **Into the game:** continue with the chapter "Export and the way into the
   game". The steps are also a checklist in the hint panel.

Measured on 14 Sep 2026: the layout from step 3 gives 31 tiles and 19 script
lines. Large wall pieces cover several tiles.
""")


def _mode_chapter(ctx, mode, intro_de, intro_en, source_de, source_en, extra=''):
    controls, colours = ctx.mode_hints(mode)
    text = _l(ctx, intro_de, intro_en)
    text += '\n' + _table([_l(ctx, 'Eingabe', 'Input'), _l(ctx, 'Wirkung', 'Effect')],
                          controls) + '\n\n' + _source(ctx, source_de, source_en) + '\n'
    if colours:
        text += '\n## ' + _l(ctx, 'Farben im Editor', 'Colours in the editor') + '\n\n'
        names = {theme.EDITOR_RED: _l(ctx, 'Rot', 'Red'),
                 theme.EDITOR_GREEN: _l(ctx, 'Grün', 'Green'),
                 theme.EDITOR_VIOLET: _l(ctx, 'Violett', 'Violet'),
                 theme.EDITOR_WHITE: _l(ctx, 'Auswahlfarbe', 'Selection colour')}
        text += _table([_l(ctx, 'Farbe', 'Colour'), _l(ctx, 'Bedeutung', 'Meaning')],
                       [(names.get(c, c), w) for c, w in colours]) + '\n\n'
        text += _source(ctx, source_de, source_en) + '\n'
    return text + extra


def ch_layout(ctx):
    return _mode_chapter(
        ctx, 'dungeon',
        """# Grundriss

Hier entsteht die Form des Dungeons. Du malst nur, wo Raum sein soll. Welche
Wand, Ecke oder welcher Gang daraus wird, entscheidet der Editor. Die
Buchstaben A bis M zeigen den gewählten Baustein, etwa `DUN_WALL_B` oder
`DUN_CORR_K`.
""", """# Layout

This is where the shape of the dungeon is made. You only paint where there
should be space. Which wall, corner or corridor that becomes is up to the
editor. The letters A to M show the chosen block, e.g. `DUN_WALL_B` or
`DUN_CORR_K`.
""",
        "SDK `Dungeons readme.txt`, Abschnitt 2.", "SDK `Dungeons readme.txt`, section 2.",
        _l(ctx, """
## Fallen

- **Rot heißt nicht falsch gemalt**, sondern: Für diese Form gibt es keinen
  Baustein. Oft hilft eine Kachel mehr oder weniger an der Ecke.
- **Kein Rückgängig.** Der alte Editor kennt keins. Oft mit F2 speichern.
""", """
## Pitfalls

- **Red does not mean painted wrong**, it means there is no block for this
  shape. Often one tile more or less at the corner helps.
- **No undo.** The old editor has none. Save often with F2.
"""))


def ch_height(ctx):
    return _mode_chapter(
        ctx, 'height',
        """# Höhe

Gänge dürfen steigen und fallen. Jeder Block hat eine Höhe, die Zahl auf dem
Block. Ein Klick wechselt zur nächsten Variante des Bausteins, und manche
Varianten ändern die Höhe.
""", """# Height

Corridors can rise and fall. Every block has a height, the number on the
block. A click switches to the next variant of the block, and some variants
change the height.
""",
        "SDK `Dungeons readme.txt`, Abschnitt 3.", "SDK `Dungeons readme.txt`, section 3.")


def ch_type(ctx):
    types, _groups = read_dungeon_txt(ctx.exe_path)
    extra = '\n## ' + _l(ctx, 'Dungeon-Typen', 'Dungeon types') + '\n\n'
    if types:
        rows = [(name, f'{blocks} {num}', ' '.join(rgb), ', '.join(g))
                for name, blocks, num, rgb, g in types]
        extra += _table([_l(ctx, 'Name', 'Name'), _l(ctx, 'Bausteine', 'Blocks'),
                         _l(ctx, 'Farbe (RGB)', 'Colour (RGB)'),
                         _l(ctx, 'Objektgruppen', 'Object groups')], rows) + '\n\n'
        extra += _source(ctx, "`dungeon.txt` neben deiner Dungeons.exe, beim Öffnen dieses Kapitels gelesen.",
                         "`dungeon.txt` next to your Dungeons.exe, read when this chapter opens.") + '\n'
    else:
        extra += _l(ctx, "`dungeon.txt` wurde nicht gefunden. Datei > Editor-Exe wählen.\n",
                    "`dungeon.txt` was not found. File > Choose editor exe.\n")
    return _mode_chapter(
        ctx, 'type',
        """# Typ

Jeder Bereich des Dungeons bekommt einen Stil. Der Typ bestimmt, welche
Bausteinfamilie im Skript steht, etwa `DUN_WALL_E_01` oder `Cave_WALL_E_01`.
""", """# Type

Every area of the dungeon gets a style. The type decides which block family
ends up in the script, e.g. `DUN_WALL_E_01` or `Cave_WALL_E_01`.
""",
        "SDK `Dungeons readme.txt`, Abschnitt 4.", "SDK `Dungeons readme.txt`, section 4.", extra)


def ch_objects(ctx):
    _types, groups = read_dungeon_txt(ctx.exe_path)
    extra = '\n## ' + _l(ctx, 'Objekte und Lichter aus dungeon.txt',
                         'Objects and lights from dungeon.txt') + '\n\n'
    if groups:
        rows = []
        for gname, (kind, items) in groups.items():
            for obj, oid, mesh, _bmp, rng, rgb in items:
                rows.append((gname, obj, oid, mesh, rng, ' '.join(rgb) if rgb else '-'))
        extra += _table([_l(ctx, 'Gruppe', 'Group'), 'Name', _l(ctx, 'Objekt-ID', 'Object ID'),
                         'Mesh', _l(ctx, 'Reichweite', 'Range'), _l(ctx, 'Lichtfarbe', 'Light colour')],
                        rows) + '\n\n'
        extra += _source(ctx, "`dungeon.txt` neben deiner Dungeons.exe; Spaltenbedeutung aus `Dungeons readme.txt`, Abschnitt 6.",
                         "`dungeon.txt` next to your Dungeons.exe; column meaning from `Dungeons readme.txt`, section 6.") + '\n'
    else:
        extra += _l(ctx, "`dungeon.txt` wurde nicht gefunden.\n", "`dungeon.txt` was not found.\n")
    extra += _l(ctx, """
Eigene Objekte und Lichter trägst du in `dungeon.txt` ein. Vorher eine
Sicherung der Datei anlegen. Ob selbst eingetragene Objekte im Spiel
funktionieren, ist **ungeprüft**.
""", """
You add your own objects and lights to `dungeon.txt`. Back the file up first.
Whether self-added objects work in the game is **unverified**.
""")
    return _mode_chapter(
        ctx, 'objects',
        """# Objekte und Lichter

In diesen beiden Modi setzt du Fackeln, Lichter und andere Objekte aus den
Gruppen in `dungeon.txt`. Der Modus Lichter zeigt links oben die Liste der
Lichtquellen.
""", """# Objects and lights

In these two modes you place torches, lights and other objects from the
groups in `dungeon.txt`. Lights mode shows the list of light sources at the
top left.
""",
        "SDK `Dungeons readme.txt`, Abschnitt 5.", "SDK `Dungeons readme.txt`, section 5.", extra)


def ch_export(ctx):
    fields = [('x, y', _l(ctx, 'Position in Welteinheiten, 256 je Kachel', 'position in world units, 256 per tile'),
               _l(ctx, 'gemessen', 'measured')),
              ('z', _l(ctx, 'Höhe, Beispiele 4096 bis 4480', 'height, samples 4096 to 4480'),
               _l(ctx, 'gemessen', 'measured')),
              ('alpha', _l(ctx, 'Drehung, in den Beispielen nur 0, 64, 128, 192', 'rotation, samples only use 0, 64, 128, 192'),
               _l(ctx, 'Werte gemessen, Bedeutung ungeprüft', 'values measured, meaning unverified')),
              ('objectID', _l(ctx, 'Baustein, etwa DUN_WALL_D_03', 'block, e.g. DUN_WALL_D_03'),
               _l(ctx, 'belegt', 'proven')),
              ('meshVariant', _l(ctx, 'Variante, in den Beispielen 1 bis 3', 'variant, samples use 1 to 3'),
               _l(ctx, 'gemessen', 'measured'))]
    return _l(ctx, """# Export und Weg ins Spiel

Export (F5) schreibt eine Textdatei mit einer `createEd`-Zeile je Baustein:

```
createEd 18815 25727 4096 64 Cave_WALL_E_01 1
```

## Felder einer Zeile
""", """# Export and the way into the game

Export (F5) writes a text file with one `createEd` line per block:

```
createEd 18815 25727 4096 64 Cave_WALL_E_01 1
```

## Fields of a line
""") + _table([_l(ctx, 'Feld', 'Field'), _l(ctx, 'Inhalt', 'Content'), 'Status'], fields) + '\n\n' + _source(
        ctx, "SDK `Documentation\\Editor console.txt` (Syntax `createEd x y z alpha [beta phi] objectID [meshVariant] [meshScale]`), Werte aus den SDK-Skripten `*src.txt` und einem Export vom 14.09.2026.",
        "SDK `Documentation\\Editor console.txt` (syntax `createEd x y z alpha [beta phi] objectID [meshVariant] [meshScale]`), values from the SDK scripts `*src.txt` and an export on 14 Sep 2026.") + _l(ctx, """

## Ins Spiel

Diese Schritte stehen auch als Checkliste im Hinweis-Panel. Das Tool erledigt
sie nicht selbst, weil sie im Two Worlds Editor passieren.

1. **Offset setzen:** vor dem Export mit Offset (F4) festlegen, wohin das
   Dungeon in der Welt fällt. Die Koordinaten im Skript sind absolut.
2. **Skript in den Spielordner kopieren.** Laut `_info_.txt` im SDK müssen
   Konsolenskripte für den Editor im Spielverzeichnis liegen.
3. **Leeres Untergrund-Level** im Two Worlds Editor öffnen.
4. **Skript ausführen:** in der Editor-Konsole `@meindungeon_src.txt`.
5. **`@edundgr.txt` ausführen** (SDK-Ordner `Game`): färbt das Gelände und
   sperrt unpassierbare Stellen.
6. **Gegner, Truhen, Marker** wie gewohnt setzen.

**Ungeprüft:** Die Schritte 2 bis 5 folgen den SDK-Notizen. Mit diesem Tool
sind sie noch nicht vollständig im Spiel nachgespielt.
""", """

## Into the game

These steps are also a checklist in the hint panel. The tool does not do them
itself, because they happen in the Two Worlds Editor.

1. **Set the offset:** before exporting, use Offset (F4) to decide where the
   dungeon lands in the world. The coordinates in the script are absolute.
2. **Copy the script into the game folder.** According to `_info_.txt` in the
   SDK, console scripts for the editor have to be in the game directory.
3. **Open an empty underground level** in the Two Worlds Editor.
4. **Run the script:** in the editor console `@mydungeon_src.txt`.
5. **Run `@edundgr.txt`** (SDK folder `Game`): colours the terrain and disables
   impassable places.
6. **Place enemies, chests, markers** as usual.

**Unverified:** steps 2 to 5 follow the SDK notes. They have not yet been
replayed all the way into the game with this tool.
""")


def ch_reference(ctx):
    grids = list_grids(ctx.exe_path)
    text = _l(ctx, """# Referenz

## Original-Raster im SDK

Jedes Raster lässt sich mit Öffnen laden. Das Skript daneben zeigt, was der
Editor daraus erzeugt hat.

""", """# Reference

## Original grids in the SDK

Every grid can be loaded with Open. The script next to it shows what the
editor made of it.

""")
    if grids:
        text += _table([_l(ctx, 'Raster', 'Grid'), _l(ctx, 'Skript', 'Script')],
                       [(g, s or '-') for g, s in grids]) + '\n\n'
        text += _source(ctx, "Ordner `Dungeons\\Dungeons` neben deiner Dungeons.exe, beim Öffnen gelesen (Dateien ab 1 MB gelten als Raster).",
                        "folder `Dungeons\\Dungeons` next to your Dungeons.exe, read on open (files from 1 MB count as grids).") + '\n'
    else:
        text += _l(ctx, "Ordner `Dungeons\\Dungeons` nicht gefunden.\n", "Folder `Dungeons\\Dungeons` not found.\n")
    modes = [(ctx.mode_labels.get(k, k), t) for k, t in
             (('dungeon', 'editing dungeon'), ('height', 'editing dungeon height'),
              ('type', 'editing dungeon type'), ('objects', 'editing objects'),
              ('lights', 'editing lights'))]
    text += '\n## ' + _l(ctx, 'Modi in der Tab-Reihenfolge', 'Modes in Tab order') + '\n\n'
    text += _table([_l(ctx, 'Modus', 'Mode'), _l(ctx, 'Fenstertitel der Exe', 'Exe window title')],
                   [(m, f'Dungeons - {t}') for m, t in modes]) + '\n\n'
    text += _source(ctx, "gemessen am 14.09.2026 durch fünfmal Tab.",
                    "measured on 14 Sep 2026 by pressing Tab five times.") + '\n'
    return text


def ch_trouble(ctx):
    rows = _l(ctx, [
        ('Editor startet nicht', 'Exe ohne dungeon.txt oder Data daneben', 'Datei > Editor-Exe wählen, Dungeons.exe aus TwoWorldsSDK\\Dungeons nehmen'),
        ('Zuletzt geöffnet lädt nichts', 'Tool vor 0.1.1', 'auf 0.1.1 oder neuer aktualisieren'),
        ('Zoom + tut nichts', 'Startansicht ist schon die nächste Stufe', 'erst Zoom - benutzen'),
        ('Klick ins Raster wirkt nicht', 'Dateidialog der Exe ist noch offen, oft hinter dem Fenster', 'Dialog in der Taskleiste suchen und schließen'),
        ('Windows warnt beim Start', 'Exe ist nicht signiert', 'Weitere Informationen > Trotzdem ausführen'),
        ('Rote Kacheln', 'kein Baustein für diese Form', 'Kachel an der Ecke ergänzen oder entfernen'),
    ], [
        ('Editor does not start', 'exe without dungeon.txt or Data next to it', 'File > Choose editor exe, take Dungeons.exe from TwoWorldsSDK\\Dungeons'),
        ('Recent files load nothing', 'tool older than 0.1.1', 'update to 0.1.1 or newer'),
        ('Zoom + does nothing', 'default view is already the closest level', 'use Zoom - first'),
        ('Clicks on the grid do nothing', 'the exe\'s file dialog is still open, often behind the window', 'find the dialog in the taskbar and close it'),
        ('Windows warns on start', 'the exe is not signed', 'More info > Run anyway'),
        ('Red tiles', 'no block for this shape', 'add or remove a tile at the corner'),
    ])
    return _l(ctx, "# Fehlersuche\n\n", "# Troubleshooting\n\n") + _table(
        [_l(ctx, 'Was passiert', 'What happens'), _l(ctx, 'Ursache', 'Cause'),
         _l(ctx, 'Was hilft', 'What helps')], rows) + '\n\n' + _source(
        ctx, "Tests und Fehlerbehebungen vom 14.09.2026 (Releases 0.1.1 und 0.1.2), SDK-Readme.",
        "tests and bug fixes from 14 Sep 2026 (releases 0.1.1 and 0.1.2), SDK readme.")


CHAPTERS = (
    ('start', ('Einstieg', 'Getting started'), ch_start),
    ('first', ('Erstes Dungeon in 10 Minuten', 'First dungeon in 10 minutes'), ch_first),
    ('layout', ('Grundriss', 'Layout'), ch_layout),
    ('height', ('Höhe', 'Height'), ch_height),
    ('type', ('Typ', 'Type'), ch_type),
    ('objects', ('Objekte und Lichter', 'Objects and lights'), ch_objects),
    ('export', ('Export und Weg ins Spiel', 'Export and the way into the game'), ch_export),
    ('reference', ('Referenz', 'Reference'), ch_reference),
    ('trouble', ('Fehlersuche', 'Troubleshooting'), ch_trouble),
)

# Modus des Tools -> Kapitel
MODE_CHAPTER = {'dungeon': 'layout', 'height': 'height', 'type': 'type',
                'objects': 'objects', 'lights': 'objects'}


def chapter_text(ctx, cid):
    for key, _title, fn in CHAPTERS:
        if key == cid:
            return fn(ctx)
    return ch_start(ctx)


# ---------------------------------------------------------------- Darstellung

_SEPARATOR = re.compile(r'^\|[\s|:-]+\|?$')
_LIST_ITEM = re.compile(r'^(- |\d+\. )')


def prepare(text):
    """Umbrochene Absatzzeilen zusammenfügen, Tabellen als Monospace-Block."""
    out, para, table, in_code = [], [], [], False

    def flush_para():
        if para:
            out.append(' '.join(x.strip() for x in para))
            para.clear()

    def flush_table():
        if not table:
            return
        rows = [[c.strip().replace('`', '') for c in r.strip().strip('|').split('|')]
                for r in table if not _SEPARATOR.match(r.strip())]
        ncol = max(len(r) for r in rows)
        widths = [max(len(r[i]) if i < len(r) else 0 for r in rows) for i in range(ncol)]
        out.append('```')
        for n, r in enumerate(rows):
            cells = [(r[i] if i < len(r) else '').ljust(widths[i]) for i in range(ncol)]
            out.append('  '.join(cells).rstrip())
            if n == 0:
                out.append('  '.join('-' * w for w in widths))
        out.append('```')
        table.clear()

    for ln in text.split('\n'):
        if ln.startswith('```'):
            flush_para()
            flush_table()
            in_code = not in_code
            out.append(ln)
            continue
        if in_code:
            out.append(ln)
            continue
        if ln.startswith('|'):
            flush_para()
            table.append(ln)
            continue
        flush_table()
        stripped = ln.strip()
        if not stripped or ln.startswith('#'):
            flush_para()
            out.append(ln)
        elif _LIST_ITEM.match(stripped):
            flush_para()
            para.append(ln)
        else:
            para.append(ln)
    flush_para()
    flush_table()
    return '\n'.join(out)


def render_markdown(txt, text):
    """Überschriften, Listen, Codeblöcke, Inline-Code und Fett."""
    in_code = False
    for line in text.split('\n'):
        if line.startswith('```'):
            in_code = not in_code
            continue
        if in_code:
            txt.insert('end', line + '\n', 'code')
            continue
        m = re.match(r'(#{1,3}) (.*)', line)
        if m:
            txt.insert('end', m.group(2) + '\n', 'h%d' % len(m.group(1)))
            continue
        tag = None
        if re.match(r'\s*([-*]|\d+\.) ', line):
            num = re.match(r'\s*(\d+)\. ', line)
            line = (num.group(1) + '. ' if num else '• ') + re.sub(r'^\s*([-*]|\d+\.) ', '', line)
            tag = 'li'
        for part in re.split(r'(`[^`]+`|\*\*[^*]+\*\*)', line):
            extra = (tag,) if tag else ()
            if part.startswith('`') and part.endswith('`') and len(part) > 1:
                txt.insert('end', part[1:-1], ('inline',) + extra)
            elif part.startswith('**') and part.endswith('**') and len(part) > 4:
                txt.insert('end', part[2:-2], ('bold',) + extra)
            else:
                txt.insert('end', part, tag)
        txt.insert('end', '\n', tag)


class GuideWindow:
    """Nicht modal, nur eine Instanz."""

    _open = None

    @classmethod
    def show(cls, app, chapter='start'):
        win = cls._open
        if win is not None:
            try:
                win.win.deiconify()
                win.win.lift()
                win.select(chapter)
                return win
            except tk.TclError:
                cls._open = None
        cls._open = cls(app, chapter)
        return cls._open

    @classmethod
    def close_if_open(cls):
        if cls._open is not None:
            try:
                cls._open.win.destroy()
            except tk.TclError:
                pass
            cls._open = None

    def __init__(self, app, chapter='start'):
        self.app = app
        self.current = 'start'
        self.win = tk.Toplevel(app.root)
        self.win.title(app.tr('TW1 Dungeon Editor Guide'))
        self.win.geometry('1120x760')
        self.win.minsize(820, 520)
        theme.dark_titlebar(self.win)
        self.win.protocol('WM_DELETE_WINDOW', self.close)
        self.win.bind('<Escape>', lambda e: self.close())
        top = ttk.Frame(self.win, padding=(10, 8))
        top.pack(fill='x')
        ttk.Label(top, text=app.tr('Suche')).pack(side='left')
        self.q = tk.StringVar()
        ent = ttk.Entry(top, textvariable=self.q, width=32)
        ent.pack(side='left', padx=6)
        ent.bind('<KeyRelease>', lambda e: self._search())
        self.hits = ttk.Label(top, style='Muted.TLabel')
        self.hits.pack(side='left', padx=8)
        body = ttk.PanedWindow(self.win, orient='horizontal')
        body.pack(fill='both', expand=True)
        left = ttk.Frame(body)
        self.tree = ttk.Treeview(left, show='tree', selectmode='browse')
        self.tree.pack(fill='both', expand=True)
        self.tree.bind('<<TreeviewSelect>>', lambda e: self._show_selected())
        right = ttk.Frame(body)
        sb = ttk.Scrollbar(right, orient='vertical')
        self.txt = tk.Text(right, wrap='word', bd=0, padx=26, pady=20, cursor='arrow',
                           spacing1=2, spacing3=4, yscrollcommand=sb.set, font=theme.FONT_GUIDE)
        sb.configure(command=self.txt.yview)
        sb.pack(side='right', fill='y')
        self.txt.pack(fill='both', expand=True)
        for tag, kw in (('h1', dict(font=theme.FONT_H1, foreground=theme.GOLD, spacing1=18)),
                        ('h2', dict(font=theme.FONT_H2, foreground=theme.GOLD_HI, spacing1=14)),
                        ('h3', dict(font=theme.FONT_H3, foreground=theme.GOLD_HI, spacing1=8)),
                        ('li', dict(lmargin1=20, lmargin2=34)),
                        ('code', dict(font=theme.FONT_MONO, background=theme.FIELD,
                                      lmargin1=16, lmargin2=16)),
                        ('inline', dict(font=theme.FONT_MONO, foreground=theme.GOLD_HI)),
                        ('bold', dict(font=theme.FONT_H3)),
                        ('hit', dict(background=theme.SEL, foreground=theme.GOLD_HI))):
            self.txt.tag_configure(tag, **kw)
        body.add(left, weight=0)
        body.add(right, weight=1)
        self.win.update_idletasks()
        try:
            body.sashpos(0, 270)
        except tk.TclError:
            pass
        self._fill_tree()
        self.select(chapter)

    def close(self):
        GuideWindow._open = None
        self.win.destroy()

    def _fill_tree(self, only=None):
        self.tree.delete(*self.tree.get_children())
        idx = 0 if self.app.lang == 'de' else 1
        for i, (cid, titles, _fn) in enumerate(CHAPTERS, start=1):
            if only is not None and cid not in only:
                continue
            self.tree.insert('', 'end', iid=cid, text=f'{i}. {titles[idx]}')

    def select(self, cid):
        if cid not in {c for c, _t, _f in CHAPTERS}:
            cid = 'start'
        if not self.tree.exists(cid):
            self.q.set('')
            self.hits.configure(text='')
            self._fill_tree()
        self.tree.selection_set(cid)
        self.tree.see(cid)
        self._show(cid)

    def _show_selected(self):
        sel = self.tree.selection()
        if sel and sel[0] != self.current:
            self._show(sel[0])

    def _show(self, cid):
        self.current = cid
        self.txt.configure(state='normal')
        self.txt.delete('1.0', 'end')
        render_markdown(self.txt, prepare(chapter_text(self.app, cid)))
        self._mark_hits()
        self.txt.configure(state='disabled')

    def _search(self):
        needle = self.q.get().strip().lower()
        if not needle:
            self._fill_tree()
            self.hits.configure(text='')
            self.select(self.current)
            return
        found = [cid for cid, _t, fn in CHAPTERS if needle in fn(self.app).lower()]
        self._fill_tree(set(found))
        self.hits.configure(text=self.app.tr('{n} Kapitel').format(n=len(found)))
        if found:
            self.tree.selection_set(found[0])
            self._show(found[0])

    def _mark_hits(self):
        needle = self.q.get().strip()
        self.txt.tag_remove('hit', '1.0', 'end')
        if not needle:
            return
        first, pos = None, '1.0'
        while True:
            pos = self.txt.search(needle, pos, nocase=True, stopindex='end')
            if not pos:
                break
            end = f'{pos}+{len(needle)}c'
            self.txt.tag_add('hit', pos, end)
            first = first or pos
            pos = end
        if first:
            self.txt.see(first)
