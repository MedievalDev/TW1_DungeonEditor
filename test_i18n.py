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
        if not isinstance(node, ast.Call):
            continue
        name = (node.func.id if isinstance(node.func, ast.Name) else
                node.func.attr if isinstance(node.func, ast.Attribute) else '')
        # tr('...') und self.help_mark(parent, '...', kapitel)
        pos = {'tr': 0, 'help_mark': 1}.get(name)
        if (pos is not None and len(node.args) > pos
                and isinstance(node.args[pos], ast.Constant)
                and isinstance(node.args[pos].value, str)):
            keys.add(node.args[pos].value)
    guide = open(os.path.join(HERE, 'guidebook.py'), encoding='utf-8').read()
    for node in ast.walk(ast.parse(guide)):
        if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                and node.func.attr == 'tr' and node.args
                and isinstance(node.args[0], ast.Constant)):
            keys.add(node.args[0].value)
    keys.update(de.CHECKLIST)
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
