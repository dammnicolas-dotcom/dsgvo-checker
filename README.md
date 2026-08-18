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

## Lokal testen

Voraussetzung: Python 3.9+ (keine externen Abhängigkeiten).

```bash
python3 -m unittest discover -s tests -v
```

Alle Prüffunktionen (`pruefe_verantwortlicher`, `pruefe_zweck`, ...) sind
einzeln unit-getestet, jeweils mit einem Positiv- und einem Negativfall in
`tests/test_dsgvo_checker.py`.

## Grenzen (MVP)

Der Checker erkennt Muster, keine juristische Vollständigkeit oder
inhaltliche Richtigkeit. Ein "OK" bedeutet: ein passendes Muster wurde
gefunden — nicht, dass die Datenschutzerklärung DSGVO-konform ist.
