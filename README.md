# dsgvo-checker

Deterministischer, regelbasierter Checker für Pflichtangaben einer
Datenschutzerklärung nach Art. 13 DSGVO. Kein LLM-Aufruf — die Prüfung
erfolgt über Keyword-/Regex-Muster, analog zum Schwesterprojekt
[fristenwaechter](https://github.com/dammnicolas-dotcom) (Fristberechnung
nach §§ 187-188 BGB, § 222 ZPO).

## Geprüfte Pflichtangaben (MVP-Scope)

1. Verantwortlicher inkl. Kontaktdaten (Art. 13 Abs. 1 lit. a DSGVO)
2. Zweck der Verarbeitung (Art. 13 Abs. 1 lit. c DSGVO)
3. Rechtsgrundlage der Verarbeitung (Art. 13 Abs. 1 lit. c DSGVO)
4. Speicherdauer bzw. Kriterien für deren Festlegung (Art. 13 Abs. 2 lit. a DSGVO)
5. Hinweis auf Betroffenenrechte (Art. 13 Abs. 2 lit. b DSGVO)

## Nutzung

```bash
python3 dsgvo_checker.py pfad/zur/datenschutzerklaerung.md
```

Beispiel:

```bash
python3 dsgvo_checker.py examples/beispiel_vollstaendig.md
python3 dsgvo_checker.py examples/beispiel_unvollstaendig.md
```

Der Report zeigt pro Pflichtangabe, ob sie gefunden wurde und welche
Textstellen den Treffer ausgelöst haben.

Für die maschinelle Weiterverarbeitung (z.B. in einer CI-Pipeline) gibt es
eine JSON-Ausgabe:

```bash
python3 dsgvo_checker.py --json examples/beispiel_vollstaendig.md
```

Der Exit-Code ist `0`, wenn alle fünf Pflichtangaben gefunden wurden, sonst
`1` — damit lässt sich der Checker als Gate in CI-Pipelines nutzen.

## Lokal testen

Voraussetzung: Python 3.9+ (keine externen Abhängigkeiten).

1. **Unit-Tests ausführen** – deckt alle Prüffunktionen (`pruefe_verantwortlicher`,
   `pruefe_zweck`, ...) einzeln mit Positiv- und Negativfällen sowie die CLI
   (Exit-Codes, `--json`) ab:

   ```bash
   python3 -m unittest discover -s tests -v
   ```

   Erwartung: alle Tests laufen mit `OK` durch (Stand: 43 Tests).

2. **Smoke-Test gegen die Beispieldateien** – prüft den Report und den
   Exit-Code an einem bekannten Fall:

   ```bash
   python3 dsgvo_checker.py examples/beispiel_vollstaendig.md; echo "Exit-Code: $?"
   python3 dsgvo_checker.py examples/beispiel_unvollstaendig.md; echo "Exit-Code: $?"
   ```

   Erwartung: `5/5 Pflichtangaben gefunden.` mit Exit-Code `0` bzw.
   `0/5 Pflichtangaben gefunden.` mit Exit-Code `1`.

3. **Eigene Datenschutzerklärung prüfen** – eigenen Text als `.txt`/`.md`
   ablegen und gegen den Checker laufen lassen, um neue Formulierungen und
   mögliche blinde Flecken der Regex-Muster zu entdecken:

   ```bash
   python3 dsgvo_checker.py pfad/zu/eigener_datenschutzerklaerung.md
   ```

   Bleibt eine tatsächlich vorhandene Pflichtangabe als "FEHLT" markiert,
   ist das ein Hinweis, dass die zugehörige Regex-Liste in
   `dsgvo_checker.py` um die verwendete Formulierung ergänzt werden sollte.

## Grenzen (MVP)

Der Checker erkennt Muster, keine juristische Vollständigkeit oder
inhaltliche Richtigkeit. Ein "OK" bedeutet: ein passendes Muster wurde
gefunden — nicht, dass die Datenschutzerklärung DSGVO-konform ist.
