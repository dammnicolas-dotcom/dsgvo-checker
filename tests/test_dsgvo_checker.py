"""Tests für dsgvo_checker.py (Art. 13 DSGVO Pflichtangaben-Check)."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dsgvo_checker import (
    pruefe_verantwortlicher,
    pruefe_zweck,
    pruefe_rechtsgrundlage,
    pruefe_speicherdauer,
    pruefe_betroffenenrechte,
    pruefe_datenschutzerklaerung,
)


class VerantwortlicherTest(unittest.TestCase):
    def test_gefunden_bei_bezeichnung_und_kontaktdaten(self):
        text = "Verantwortlicher im Sinne der DSGVO: Max Mustermann, Musterstraße 1, kontakt@example.com"
        self.assertTrue(pruefe_verantwortlicher(text).gefunden)

    def test_fehlt_ohne_kontaktdaten(self):
        # Bezeichnung allein reicht nicht - Art. 13 Abs. 1 lit. a fordert
        # zusätzlich konkrete Kontaktangaben.
        text = "Der Verantwortliche im Sinne der DSGVO informiert Sie hiermit."
        self.assertFalse(pruefe_verantwortlicher(text).gefunden)

    def test_fehlt_ganz_ohne_hinweis(self):
        self.assertFalse(pruefe_verantwortlicher("Diese Seite nutzt Cookies.").gefunden)


class ZweckTest(unittest.TestCase):
    def test_gefunden(self):
        text = "Der Zweck der Verarbeitung ist die Bearbeitung Ihrer Anfrage."
        self.assertTrue(pruefe_zweck(text).gefunden)

    def test_fehlt(self):
        self.assertFalse(pruefe_zweck("Wir nehmen Datenschutz ernst.").gefunden)


class RechtsgrundlageTest(unittest.TestCase):
    def test_gefunden_ueber_artikel_verweis(self):
        text = "Rechtsgrundlage der Verarbeitung ist Art. 6 Abs. 1 lit. b DSGVO."
        self.assertTrue(pruefe_rechtsgrundlage(text).gefunden)

    def test_fehlt(self):
        self.assertFalse(pruefe_rechtsgrundlage("Wir verarbeiten Ihre Daten sorgfältig.").gefunden)


class SpeicherdauerTest(unittest.TestCase):
    def test_gefunden(self):
        text = "Die Speicherdauer richtet sich nach den gesetzlichen Aufbewahrungsfristen."
        self.assertTrue(pruefe_speicherdauer(text).gefunden)

    def test_gefunden_ueber_kriterien_fuer_festlegung(self):
        # Art. 13 Abs. 2 lit. a DSGVO lässt statt einer konkreten Speicherdauer
        # auch die Nennung der Kriterien für deren Festlegung genügen.
        text = "Die Kriterien für die Festlegung der Speicherdauer sind die jeweiligen gesetzlichen Aufbewahrungsfristen."
        self.assertTrue(pruefe_speicherdauer(text).gefunden)

    def test_gefunden_ueber_loeschfristen_plural(self):
        text = "Es gelten die gesetzlichen Löschfristen nach § 257 HGB und § 147 AO."
        self.assertTrue(pruefe_speicherdauer(text).gefunden)

    def test_fehlt(self):
        self.assertFalse(pruefe_speicherdauer("Ihre Daten sind bei uns sicher.").gefunden)

    def test_fehlt_bei_speichern_ohne_dauer_angabe(self):
        # Reine Nennung von "speichern" ohne Angabe zur Dauer/den Kriterien
        # darf keinen falschen Treffer auslösen.
        text = "Wir speichern Ihre Daten auf Servern in Deutschland."
        self.assertFalse(pruefe_speicherdauer(text).gefunden)


class BetroffenenrechteTest(unittest.TestCase):
    def test_gefunden_ueber_generische_ueberschrift(self):
        text = "Betroffenenrechte: Sie haben verschiedene Rechte bezüglich Ihrer Daten."
        self.assertTrue(pruefe_betroffenenrechte(text).gefunden)

    def test_gefunden_ueber_mindestens_zwei_einzelrechte(self):
        text = "Sie haben ein Recht auf Auskunft und ein Recht auf Löschung."
        self.assertTrue(pruefe_betroffenenrechte(text).gefunden)

    def test_fehlt_bei_nur_einem_einzelrecht(self):
        text = "Sie haben ein Recht auf Auskunft."
        self.assertFalse(pruefe_betroffenenrechte(text).gefunden)

    def test_fehlt_ganz_ohne_hinweis(self):
        self.assertFalse(pruefe_betroffenenrechte("Diese Seite nutzt Cookies.").gefunden)


class GesamtreportTest(unittest.TestCase):
    def test_vollstaendige_erklaerung_liefert_fuenf_treffer(self):
        text = """
        Verantwortlicher im Sinne der DSGVO: Max Mustermann, Musterstraße 1,
        kontakt@example.com

        Zweck der Verarbeitung ist die Bearbeitung Ihrer Bestellung.
        Rechtsgrundlage der Verarbeitung ist Art. 6 Abs. 1 lit. b DSGVO.
        Die Speicherdauer richtet sich nach den gesetzlichen Aufbewahrungsfristen.
        Betroffenenrechte: Sie haben ein Recht auf Auskunft und Löschung.
        """
        ergebnisse = pruefe_datenschutzerklaerung(text)
        self.assertEqual(len(ergebnisse), 5)
        self.assertTrue(all(e.gefunden for e in ergebnisse))

    def test_leerer_text_liefert_keine_treffer(self):
        ergebnisse = pruefe_datenschutzerklaerung("")
        self.assertTrue(all(not e.gefunden for e in ergebnisse))


if __name__ == "__main__":
    unittest.main()
