"""Regelbasierter Checker für Pflichtangaben einer Datenschutzerklärung nach Art. 13 DSGVO.

Kein LLM-Aufruf: die Prüfung erfolgt ausschließlich über Keyword-/Regex-Muster,
analog zur Fristberechnung in frist_berechnung.py.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Pruefergebnis:
    id: str
    name: str
    artikel: str
    gefunden: bool
    treffer: list[str] = field(default_factory=list)


def _sucht_muster(text: str, muster: list[str]) -> list[str]:
    treffer = []
    for pattern in muster:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            treffer.append(match.group(0).strip())
    return treffer


VERANTWORTLICHER_MUSTER = [
    r"verantwortlich(?:e|er|en)?\s+(?:im\s+sinne\s+der\s+dsgvo|f(?:ü|ue)r\s+die\s+(?:daten-?verarbeitung|verarbeitung))",
    r"kontaktdaten\s+des\s+verantwortlichen",
    r"verantwortliche\s+stelle",
    r"verantwortlich(?:e|er|en)?\s+ist\b",
    r"f(?:ü|ue)r\s+die\s+(?:daten-?verarbeitung|verarbeitung)\s+zust(?:ä|ae)ndig",
]
# Reine Nennung von "verantwortlich" reicht nicht - es braucht zusätzlich
# tatsächliche Kontaktangaben (Art. 13 Abs. 1 lit. a fordert Name UND Kontaktdaten).
KONTAKT_MUSTER = [
    r"[\w.+-]+@[\w-]+\.[a-z]{2,}",
    r"(?:tel\.?|telefon)\s*:?\s*[+\d]",
    r"stra(?:ß|ss)e\s+\d+",
]

ZWECK_MUSTER = [
    r"zwecke?\s+der\s+(?:daten-?)?verarbeitung",
    r"verarbeitungszweck",
    r"zu\s+folgenden\s+zwecken",
    r"wir\s+verarbeiten\s+ihre\s+daten\s+(?:für|zu)",
    r"(?:nutzen|verwenden)\s+(?:ihre|deine)\s+(?:daten|angaben)(?:,)?\s*(?:für|zu|um)\b",
    r"(?:daten|angaben)\s+werden\s+(?:zur|für)(?:(?!\.).){0,40}?(?:genutzt|verwendet|verarbeitet)",
]

RECHTSGRUNDLAGE_MUSTER = [
    # Negative Lookahead schließt "Rechtsgrundlage" im AGB-Kontext aus (z.B.
    # "Rechtsgrundlage unserer AGB") - das ist keine Rechtsgrundlage der
    # Datenverarbeitung im Sinne von Art. 13 Abs. 1 lit. c DSGVO.
    r"rechtsgrundlage(?:n)?(?!(?:(?!\.).){0,50}?(?:\bagb\b|geschäftsbedingungen))",
    r"rechtliche\s+grundlage",
    r"art\.?\s*6\s*abs\.?\s*1",
]

SPEICHERDAUER_MUSTER = [
    r"speicherdauer",
    r"dauer\s+der\s+speicherung",
    r"l(?:ö|oe)schfrist(?:en)?",
    r"kriterien\s+f(?:ü|ue)r\s+die\s+festlegung\s+der\s+speicherdauer",
    r"solange\s+(?:dies\s+)?(?:erforderlich|notwendig)",
    # Konkrete Fristangabe (Zahl + Zeiteinheit) in der Nähe eines
    # Speicher-Begriffs, in beiden Reihenfolgen - deckt sowohl "für die
    # Dauer von 3 Jahren ... gespeichert" als auch "Speicherung erfolgt
    # für maximal 12 Monate" ab. Begrenzt auf denselben Satz (kein Punkt
    # zwischen Zahl und Speicher-Begriff).
    r"\d+\s+(?:jahren?|monaten?|wochen?|tagen?)(?:(?!\.).){0,50}?(?:gespeichert|aufbewahrt|speicherung)",
    r"(?:gespeichert|aufbewahrt|speicherung)(?:(?!\.).){0,50}?\d+\s+(?:jahren?|monaten?|wochen?|tagen?)",
]

# Art. 13 Abs. 2 lit. b verlangt einen Hinweis auf Betroffenenrechte allgemein;
# eine generische Überschrift reicht, ersatzweise müssen mindestens zwei
# einzelne Rechte konkret benannt sein.
EINZELRECHT_NAMEN = r"(?:auskunft|berichtigung|l(?:ö|oe)schung|einschr(?:ä|ae)nkung|widerspruch|daten(?:ü|ue)bertragbarkeit|widerruf)"

BETROFFENENRECHTE_GENERISCH_MUSTER = [
    r"betroffenenrechte",
    r"ihre\s+rechte\s+als\s+betroffene",
    r"rechte\s+der\s+betroffenen\s+person",
    # Aufzählung mehrerer Rechte hinter einem einzigen "Recht auf"
    # (z.B. "Recht auf Auskunft, Berichtigung, Löschung und Widerspruch").
    rf"recht\s+auf\s+{EINZELRECHT_NAMEN}(?:\s*,\s*{EINZELRECHT_NAMEN})+\s*(?:und|sowie|oder)\s*{EINZELRECHT_NAMEN}",
]
EINZELRECHTE_MUSTER = [
    r"recht\s+auf\s+auskunft",
    r"recht\s+auf\s+berichtigung",
    r"recht\s+auf\s+l(?:ö|oe)schung",
    r"recht\s+auf\s+einschr(?:ä|ae)nkung",
    r"recht\s+auf\s+widerspruch",
    r"recht\s+auf\s+daten(?:ü|ue)bertragbarkeit",
    r"recht\s+auf\s+widerruf",
]


def pruefe_verantwortlicher(text: str) -> Pruefergebnis:
    bezeichner_treffer = _sucht_muster(text, VERANTWORTLICHER_MUSTER)
    kontakt_treffer = _sucht_muster(text, KONTAKT_MUSTER)
    gefunden = bool(bezeichner_treffer) and bool(kontakt_treffer)
    # Treffer nur bei gefunden=True zeigen - sonst wirkt ein FEHLT-Ergebnis
    # inkonsistent, wenn nur einer der beiden Teile (Bezeichner ODER
    # Kontaktdaten) etwas gefunden hat.
    return Pruefergebnis(
        id="verantwortlicher",
        name="Verantwortlicher (Name/Kontaktdaten)",
        artikel="Art. 13 Abs. 1 lit. a DSGVO",
        gefunden=gefunden,
        treffer=bezeichner_treffer + kontakt_treffer if gefunden else [],
    )


def pruefe_zweck(text: str) -> Pruefergebnis:
    treffer = _sucht_muster(text, ZWECK_MUSTER)
    return Pruefergebnis(
        id="zweck",
        name="Zweck der Verarbeitung",
        artikel="Art. 13 Abs. 1 lit. c DSGVO",
        gefunden=bool(treffer),
        treffer=treffer,
    )


def pruefe_rechtsgrundlage(text: str) -> Pruefergebnis:
    treffer = _sucht_muster(text, RECHTSGRUNDLAGE_MUSTER)
    return Pruefergebnis(
        id="rechtsgrundlage",
        name="Rechtsgrundlage der Verarbeitung",
        artikel="Art. 13 Abs. 1 lit. c DSGVO",
        gefunden=bool(treffer),
        treffer=treffer,
    )


def pruefe_speicherdauer(text: str) -> Pruefergebnis:
    treffer = _sucht_muster(text, SPEICHERDAUER_MUSTER)
    return Pruefergebnis(
        id="speicherdauer",
        name="Speicherdauer bzw. Kriterien für deren Festlegung",
        artikel="Art. 13 Abs. 2 lit. a DSGVO",
        gefunden=bool(treffer),
        treffer=treffer,
    )


def pruefe_betroffenenrechte(text: str) -> Pruefergebnis:
    generisch_treffer = _sucht_muster(text, BETROFFENENRECHTE_GENERISCH_MUSTER)
    einzelrechte_treffer = _sucht_muster(text, EINZELRECHTE_MUSTER)
    gefunden = bool(generisch_treffer) or len(einzelrechte_treffer) >= 2
    return Pruefergebnis(
        id="betroffenenrechte",
        name="Hinweis auf Betroffenenrechte",
        artikel="Art. 13 Abs. 2 lit. b DSGVO",
        gefunden=gefunden,
        treffer=generisch_treffer + einzelrechte_treffer,
    )


UNTERSTUETZTE_ENDUNGEN = {".txt", ".md"}


def lade_datenschutzerklaerung(pfad: Path) -> str:
    if pfad.suffix.lower() not in UNTERSTUETZTE_ENDUNGEN:
        endungen = ", ".join(sorted(UNTERSTUETZTE_ENDUNGEN))
        raise ValueError(
            f"Nicht unterstütztes Dateiformat '{pfad.suffix}'. Unterstützt werden: {endungen}."
        )
    return pfad.read_text(encoding="utf-8")


ALLE_PRUEFUNGEN = [
    pruefe_verantwortlicher,
    pruefe_zweck,
    pruefe_rechtsgrundlage,
    pruefe_speicherdauer,
    pruefe_betroffenenrechte,
]


def pruefe_datenschutzerklaerung(text: str) -> list[Pruefergebnis]:
    return [pruefung(text) for pruefung in ALLE_PRUEFUNGEN]


def formatiere_report(ergebnisse: list[Pruefergebnis]) -> str:
    zeilen = ["DSGVO-Checker – Prüfbericht (Art. 13 DSGVO, MVP-Scope)", "=" * 55]
    for ergebnis in ergebnisse:
        status = "OK    " if ergebnis.gefunden else "FEHLT "
        zeilen.append(f"[{status}] {ergebnis.name} ({ergebnis.artikel})")
        if ergebnis.treffer:
            eindeutige_treffer = sorted(set(ergebnis.treffer))
            zeilen.append(f"         Treffer: {', '.join(eindeutige_treffer)}")
    anzahl_gefunden = sum(1 for ergebnis in ergebnisse if ergebnis.gefunden)
    zeilen.append("-" * 55)
    zeilen.append(f"{anzahl_gefunden}/{len(ergebnisse)} Pflichtangaben gefunden.")
    return "\n".join(zeilen)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Prüft eine Datenschutzerklärung auf Pflichtangaben nach Art. 13 DSGVO."
    )
    parser.add_argument("pfad", type=Path, help="Pfad zur Datenschutzerklärung (.txt/.md)")
    parser.add_argument(
        "--json", action="store_true", help="Ausgabe als JSON statt als Textreport"
    )
    args = parser.parse_args()

    try:
        text = lade_datenschutzerklaerung(args.pfad)
    except FileNotFoundError:
        print(f"Fehler: Datei nicht gefunden: {args.pfad}", file=sys.stderr)
        sys.exit(1)
    except ValueError as fehler:
        print(f"Fehler: {fehler}", file=sys.stderr)
        sys.exit(1)

    ergebnisse = pruefe_datenschutzerklaerung(text)

    if args.json:
        print(json.dumps([asdict(ergebnis) for ergebnis in ergebnisse], ensure_ascii=False, indent=2))
    else:
        print(formatiere_report(ergebnisse))

    # Exit-Code 0 nur, wenn alle Pflichtangaben gefunden wurden - damit lässt
    # sich der Checker z.B. als CI-Gate für Datenschutzerklärungen nutzen.
    alle_gefunden = all(ergebnis.gefunden for ergebnis in ergebnisse)
    sys.exit(0 if alle_gefunden else 1)


if __name__ == "__main__":
    main()
