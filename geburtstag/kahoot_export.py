#!/usr/bin/env python3
"""
Erzeugt aus Spiel 1 ("Heikes Geburtstagsfragen") in questions.json eine
Kahoot-Import-Datei (.xlsx) für "Import spreadsheet" im Kahoot-Editor.

    python3 geburtstag/kahoot_export.py

Kahoot-Grenzen: Frage max. 120 Zeichen, Antworten max. 75 Zeichen.
Zu lange Fragen bekommen unten in KAHOOT_KURZFASSUNG eine kürzere Version;
im Millionär-Spiel selbst bleibt der Originaltext.

Die Antwortreihenfolge wird (mit festem Seed, also bei jedem Export gleich)
gemischt, damit die richtige Antwort in Kahoot nicht immer auf Platz 1 liegt.

Die Sortierfrage der Auswahlrunde kann Kahoot nicht per Tabelle importieren
(nur normale Quizfragen) – die muss im Kahoot-Editor als "Puzzle"-Frage
von Hand angelegt werden.
"""
import json
import os
import random
import zipfile
from xml.sax.saxutils import escape

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(BASE_DIR)
QUESTIONS_JSON = os.path.join(REPO_DIR, "questions.json")
OUT_XLSX = os.path.join(BASE_DIR, "kahoot-import-heike.xlsx")

GAME_INDEX = 0
TIME_LIMIT = 30  # erlaubt: 5, 10, 20, 30, 60, 90, 120, 240
MAX_QUESTION = 120
MAX_ANSWER = 75

# Kürzere Fassungen für Fragen, die über Kahoots 120-Zeichen-Grenze gehen
KAHOOT_KURZFASSUNG = {
    14: "Heike hat am selben Tag Geburtstag wie eine Hollywood-Schauspielerin. In welchem Kultfilm spielte diese mit?",
    15: "Hengstparade Moritzburg (klingt fast wie Kronsohn Moritz): Welche Reiter-Vorführung bildet dort den Abschluss?",
}


def build_rows():
    with open(QUESTIONS_JSON, encoding="utf-8") as f:
        game = json.load(f)["games"][GAME_INDEX]

    rng = random.Random(70)
    rows = []
    for nr, q in enumerate(game["questions"], start=1):
        text = KAHOOT_KURZFASSUNG.get(nr, q["question"])
        order = list(range(4))
        rng.shuffle(order)
        answers = [q["content"][i] for i in order]
        correct = order.index(q["correct"]) + 1

        if len(text) > MAX_QUESTION:
            raise SystemExit(f"Frage {nr} ist {len(text)} Zeichen lang (max. {MAX_QUESTION}): {text}")
        for a in answers:
            if len(a) > MAX_ANSWER:
                raise SystemExit(f"Antwort in Frage {nr} ist {len(a)} Zeichen lang (max. {MAX_ANSWER}): {a}")

        rows.append([text] + answers + [TIME_LIMIT, correct])
    return rows


def col_letter(i):
    return "ABCDEFGHIJ"[i]


def cell_xml(ref, value):
    if isinstance(value, int):
        return f'<c r="{ref}"><v>{value}</v></c>'
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{escape(value)}</t></is></c>'


def write_xlsx(path, header, rows):
    sheet_rows = []
    for r, values in enumerate([header] + rows, start=1):
        cells = "".join(cell_xml(f"{col_letter(c)}{r}", v) for c, v in enumerate(values))
        sheet_rows.append(f'<row r="{r}">{cells}</row>')

    sheet = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
        '<cols><col min="1" max="1" width="70" customWidth="1"/>'
        '<col min="2" max="5" width="40" customWidth="1"/>'
        '<col min="6" max="7" width="16" customWidth="1"/></cols>'
        f'<sheetData>{"".join(sheet_rows)}</sheetData></worksheet>'
    )
    files = {
        "[Content_Types].xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
            '<Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
            '</Types>'
        ),
        "_rels/.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
            '</Relationships>'
        ),
        "xl/workbook.xml": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
            'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            '<sheets><sheet name="Sheet1" sheetId="1" r:id="rId1"/></sheets></workbook>'
        ),
        "xl/_rels/workbook.xml.rels": (
            '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/>'
            '</Relationships>'
        ),
        "xl/worksheets/sheet1.xml": sheet,
    }
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as z:
        for name, content in files.items():
            z.writestr(name, content)


def main():
    header = ["Question", "Answer 1", "Answer 2", "Answer 3", "Answer 4", "Time limit", "Correct answer(s)"]
    rows = build_rows()
    write_xlsx(OUT_XLSX, header, rows)
    print(f"{len(rows)} Fragen exportiert nach {OUT_XLSX}")
    for nr, row in enumerate(rows, start=1):
        print(f"{nr:2}. [{len(row[0]):3} Z.] {row[0]}  ->  richtig: Antwort {row[6]} ({row[row[6]]})")


if __name__ == "__main__":
    main()
