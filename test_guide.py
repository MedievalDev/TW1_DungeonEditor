"""Guide und Updater prüfen. Aufruf: py test_guide.py

- Jede Tabelle in jedem Kapitel hat darunter eine Quellenangabe (DE und EN).
- Kapitel liefern Text, auch ohne gefundene Dungeons.exe.
- Die SDK-Tabellen lesen die echte dungeon.txt, wenn das SDK da ist.
- Versionsvergleich des Updaters und der Tausch-Batch nach PY_TOOL_DESIGN 9.3.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dungeon_editor as de  # noqa: E402
import guidebook  # noqa: E402
import updater  # noqa: E402

FAILS = []


def check(cond, msg):
    if not cond:
        FAILS.append(msg)


def ctx(lang, exe):
    de._LANG = lang
    return guidebook.Ctx(lang=lang, tr=de.tr, general_keys=de.GENERAL_KEYS,
                         mode_hints=de.mode_hints,
                         mode_labels={k: de.tr(v) for k, v in de.MODE_LABELS.items()},
                         exe_path=exe)


def tables_have_sources(text):
    """Nach jedem Tabellenblock muss vor der nächsten Überschrift oder Tabelle
    eine Zeile mit 'Quelle:' oder 'Source:' kommen."""
    lines = text.split('\n')
    i, bad = 0, 0
    while i < len(lines):
        if lines[i].startswith('|'):
            while i < len(lines) and lines[i].startswith('|'):
                i += 1
            found = False
            while i < len(lines) and not lines[i].startswith(('|', '#')):
                if 'Quelle:' in lines[i] or 'Source:' in lines[i]:
                    found = True
                    break
                i += 1
            bad += 0 if found else 1
        else:
            i += 1
    return bad


def main():
    sdk_exe = de.find_exe('')
    for exe in ('', sdk_exe):
        for lang in ('de', 'en'):
            c = ctx(lang, exe)
            for cid, titles, fn in guidebook.CHAPTERS:
                text = fn(c)
                check(len(text) > 200, f'{cid}/{lang}: Kapitel fast leer')
                check(text.startswith('# '), f'{cid}/{lang}: keine Überschrift')
                n = tables_have_sources(text)
                check(n == 0, f'{cid}/{lang}/exe={bool(exe)}: {n} Tabelle(n) ohne Quelle')
                check(guidebook.prepare(text), f'{cid}/{lang}: prepare leer')
    if sdk_exe:
        types, groups = guidebook.read_dungeon_txt(sdk_exe)
        check(len(types) == 8, f'dungeon.txt: {len(types)} Typen statt 8')
        check('Lights2' in groups and len(groups['Lights2'][1]) == 13,
              'dungeon.txt: Lights2 nicht mit 13 Einträgen gelesen')
        grids = guidebook.list_grids(sdk_exe)
        check(any(g == '7.txt' and s == '7src.txt' for g, s in grids),
              'SDK-Raster 7.txt mit 7src.txt nicht gefunden')
    else:
        print('SDK nicht gefunden, SDK-Tabellen nicht geprüft')

    check(updater.is_newer('v0.10.0', '0.9.9'), 'Version als Tupel vergleichen')
    check(not updater.is_newer('v0.2.0', '0.2.0'), 'gleiche Version ist nicht neuer')
    check(updater.parse_version('v1.2') == (1, 2, 0), 'v1.2 -> (1, 2, 0)')
    check(updater.REPO == 'MedievalDev/TW1_DungeonEditor', 'REPO falsch')
    check(updater.ASSET == 'TW1DungeonEditor.exe', 'ASSET falsch')
    bat = updater.swap_script(r'C:\x\TW1DungeonEditor.exe', r'C:\x\TW1DungeonEditor.exe.new', 4242)
    check('PID eq 4242' in bat and '" 4242 "' in bat, 'Batch wartet nicht auf die Prozess-ID')
    check('%SystemRoot%\\System32\\tasklist.exe' in bat and '%SystemRoot%\\System32\\find.exe' in bat,
          'tasklist/find ohne vollen Pfad')
    check('\r\n' in bat, 'Batch ohne CRLF')

    for f in FAILS:
        print('FAIL:', f)
    print(f'{len(FAILS)} Fehler')
    return 1 if FAILS else 0


if __name__ == '__main__':
    sys.exit(main())
