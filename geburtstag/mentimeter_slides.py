#!/usr/bin/env python3
"""
Erzeugt aus Spiel 1 ("Heikes Geburtstagsfragen") eine PDF-Präsentation im
Millionär-Design: eine Folie (16:9) pro Frage, zum Hochladen in Mentimeter.

    python3 geburtstag/mentimeter_slides.py

Folie 1 ist die Sortierfrage der Auswahlrunde, danach die 15 Fragen.
Die richtige Antwort ist auf den Folien NICHT markiert; die Lösungen gibt das
Skript in der Konsole aus. Die Antwortreihenfolge wird mit festem Seed
gemischt (bei jedem Lauf gleich), damit nicht immer A richtig ist.

Benötigt Google Chrome (wird headless zum PDF-Druck verwendet).
"""
import html
import json
import os
import random
import shutil
import subprocess
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(BASE_DIR)
QUESTIONS_JSON = os.path.join(REPO_DIR, "questions.json")
OUT_PDF = os.path.join(BASE_DIR, "heikes-geburtstagsfragen-slides.pdf")
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"

GAME_INDEX = 0
LETTERS = ["A", "B", "C", "D"]
AMOUNTS = ["50", "100", "200", "300", "500", "1.000", "2.000", "4.000", "8.000",
           "16.000", "32.000", "64.000", "125.000", "500.000", "1.000.000"]


def file_url(path):
    return "file://" + path


def slide_html(label, question, answers):
    answer_boxes = "".join(
        f'<div class="answer"><span class="answer-letter">{LETTERS[i]}:</span>'
        f'<span>{html.escape(a)}</span></div>'
        for i, a in enumerate(answers)
    )
    return (
        '<section class="slide"><div class="slide-inner">'
        f'<img class="slide-logo" src="{file_url(os.path.join(REPO_DIR, "img", "logo.png"))}" />'
        f'<div class="slide-label">{html.escape(label)}</div>'
        f'<div class="question-box"><span>{html.escape(question)}</span></div>'
        f'<div class="answer-grid">{answer_boxes}</div>'
        '</div></section>'
    )


def build():
    with open(QUESTIONS_JSON, encoding="utf-8") as f:
        game = json.load(f)["games"][GAME_INDEX]

    rng = random.Random(70)
    slides, key = [], []

    sort_q = game.get("sortQuestion")
    if sort_q:
        items = list(sort_q["items"])
        shuffled = items[:]
        while shuffled == items:
            rng.shuffle(shuffled)
        slides.append(slide_html("Auswahlrunde", sort_q["question"], shuffled))
        solution = " – ".join(f"{LETTERS[shuffled.index(it)]} ({it})" for it in items)
        key.append(("Auswahlrunde", sort_q["question"], solution))

    for nr, q in enumerate(game["questions"], start=1):
        order = list(range(4))
        rng.shuffle(order)
        answers = [q["content"][i] for i in order]
        correct = order.index(q["correct"])
        label = f"Frage {nr} · {AMOUNTS[nr - 1]} €"
        slides.append(slide_html(label, q["question"], answers))
        key.append((label, q["question"], f"{LETTERS[correct]}: {answers[correct]}"))

    css = file_url(os.path.join(REPO_DIR, "css", "style.css"))
    doc = f"""<!DOCTYPE html>
<html lang="de"><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css?family=Roboto+Slab:400,600,700,800" rel="stylesheet">
<link rel="stylesheet" href="{css}">
<style>
  @page {{ size: 1920px 1080px; margin: 0; }}
  html, body {{ margin: 0; padding: 0; background: #000;
    -webkit-print-color-adjust: exact; print-color-adjust: exact; }}
  .slide {{
    width: 1920px; height: 1080px; overflow: hidden;
    display: flex; align-items: center; justify-content: center;
    background: radial-gradient(ellipse at 50% 40%, #0d3170 0%, #04153a 55%, #000 100%);
    page-break-after: always; break-after: page;
  }}
  .slide:last-child {{ page-break-after: auto; break-after: auto; }}
  .slide-inner {{ width: 960px; text-align: center; transform: scale(1.65); }}
  .slide-logo {{ width: 190px; display: block; margin: 0 auto 8px; }}
  .slide-label {{
    color: #f0c24c; font-weight: 800; font-size: 20px; letter-spacing: 2px;
    text-transform: uppercase; text-shadow: 0 0 16px rgba(240, 194, 74, 0.5);
  }}
  .answer:hover {{ background: linear-gradient(180deg, #16428a 0%, #081d42 100%); }}
</style></head>
<body>{"".join(slides)}</body></html>"""
    return doc, key


def main():
    doc, key = build()
    tmp = tempfile.mkdtemp(prefix="menti-slides-")
    try:
        html_path = os.path.join(tmp, "slides.html")
        with open(html_path, "w", encoding="utf-8") as f:
            f.write(doc)
        subprocess.run([
            CHROME, "--headless=new", "--disable-gpu", "--no-pdf-header-footer",
            f"--user-data-dir={os.path.join(tmp, 'profile')}",
            "--virtual-time-budget=15000", "--allow-file-access-from-files",
            f"--print-to-pdf={OUT_PDF}", file_url(html_path),
        ], check=True, capture_output=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)

    print(f"{len(key)} Folien geschrieben nach {OUT_PDF}\n")
    print("Lösungen:")
    for label, question, solution in key:
        print(f"  {label}: {solution}")


if __name__ == "__main__":
    main()
