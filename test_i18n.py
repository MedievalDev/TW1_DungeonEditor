"""Prueft, dass jeder tr()-Schluessel eine englische Fassung mit gleichen
Platzhaltern hat. Aufruf: py test_i18n.py"""

import ast
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import dungeon_editor as de  # noqa: E402


def literal_keys():
    src = open(os.path.join(HERE, 'dungeon_editor.py'), encoding='utf-8').read()
    tree = ast.parse(src)
    keys = set()
    for node in ast.walk(tree):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                and node.func.id == 'tr' and node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)):
            keys.add(node.args[0].value)
    for step in de.GUIDE_STEPS:
        keys.add(step['title'])
        keys.add(step['text'])
    for key, what in de.GENERAL_KEYS:
        keys.add(key)
        keys.add(what)
    keys.update(de.MODE_LABELS.values())
    return keys


def main():
    missing, bad = [], []
    for key in sorted(literal_keys()):
        if key not in de.EN:
            missing.append(key)
            continue
        ph_de = sorted(re.findall(r'\{\w+\}', key))
        ph_en = sorted(re.findall(r'\{\w+\}', de.EN[key]))
        if ph_de != ph_en:
            bad.append((key, ph_de, ph_en))
    for key in missing:
        print('MISSING EN:', repr(key))
    for key, a, b in bad:
        print('PLACEHOLDER:', repr(key), a, b)
    print(f'{len(literal_keys())} keys, {len(missing)} missing, {len(bad)} bad')
    return 1 if (missing or bad) else 0


if __name__ == '__main__':
    sys.exit(main())
