#!/usr/bin/env python3
"""
Liest geburtstag/fragen.csv und erzeugt daraus:
1. Ein Spiel "Geburtstagsquiz" in questions.json (fuers Millionaer-Spiel)
2. geburtstag/kahoot-import.csv (zum Hochladen in Kahoot's "Import spreadsheet")

Nach jeder Aenderung an fragen.csv einfach erneut ausfuehren:
    python3 geburtstag/generate.py
"""
import csv
import json
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_DIR = os.path.dirname(BASE_DIR)
FRAGEN_CSV = os.path.join(BASE_DIR, "fragen.csv")
QUESTIONS_JSON = os.path.join(REPO_DIR, "questions.json")
KAHOOT_CSV = os.path.join(BASE_DIR, "kahoot-import.csv")

LETTER_TO_INDEX = {"A": 0, "B": 1, "C": 2, "D": 3}


def load_fragen():
    with open(FRAGEN_CSV, encoding="utf-8") as f:
        rows = list(csv.DictReader(f))
    if not rows:
        raise SystemExit("fragen.csv enthaelt keine Fragen.")
    for i, row in enumerate(rows, start=1):
        richtig = row["Richtig"].strip().upper()
        if richtig not in LETTER_TO_INDEX:
            raise SystemExit(
                f"Zeile {i}: 'Richtig' muss A, B, C oder D sein, nicht '{row['Richtig']}'"
            )
    return rows


def build_game(rows):
    questions = []
    for row in rows:
        questions.append({
            "question": row["Frage"].strip(),
            "content": [
                row["Antwort A"].strip(),
                row["Antwort B"].strip(),
                row["Antwort C"].strip(),
                row["Antwort D"].strip(),
            ],
            "correct": LETTER_TO_INDEX[row["Richtig"].strip().upper()],
        })
    return {"name": "Geburtstagsquiz", "questions": questions}


def update_questions_json(game):
    with open(QUESTIONS_JSON, encoding="utf-8") as f:
        data = json.load(f)
    games = data["games"]
    existing = next((g for g in games if g.get("name") == "Geburtstagsquiz"), None)
    if existing is not None:
        existing["questions"] = game["questions"]
    else:
        games.append(game)
    with open(QUESTIONS_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent="\t")
        f.write("\n")
    return games.index(existing) + 1 if existing is not None else len(games)


def write_kahoot_csv(rows):
    with open(KAHOOT_CSV, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Question", "Answer 1", "Answer 2", "Answer 3", "Answer 4",
            "Time limit (sec)", "Correct answer(s)",
        ])
        for row in rows:
            correct_index = LETTER_TO_INDEX[row["Richtig"].strip().upper()] + 1
            writer.writerow([
                row["Frage"].strip(),
                row["Antwort A"].strip(),
                row["Antwort B"].strip(),
                row["Antwort C"].strip(),
                row["Antwort D"].strip(),
                30,
                correct_index,
            ])


def main():
    rows = load_fragen()
    game = build_game(rows)
    slot = update_questions_json(game)
    write_kahoot_csv(rows)
    print(f"{len(rows)} Fragen verarbeitet.")
    print(f"questions.json aktualisiert (Spiel Nr. {slot} im Spiel-Dropdown).")
    print(f"Kahoot-Import-Datei geschrieben: {KAHOOT_CSV}")


if __name__ == "__main__":
    main()
