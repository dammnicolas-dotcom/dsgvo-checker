"""Tests für dsgvo_checker.py (Art. 13 DSGVO Pflichtangaben-Check)."""

import json
import subprocess
import sys
import unittest
from pathlib import Path

PROJEKT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJEKT_ROOT))

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

    def test_gefunden_ueber_kontaktdaten_des_verantwortlichen(self):
        text = "Kontaktdaten des Verantwortlichen: Max Mustermann, Telefon: 030 1234567"
        self.assertTrue(pruefe_verantwortlicher(text).gefunden)

    def test_gefunden_ueber_verantwortliche_stelle_mit_adresse(self):
        text = "Verantwortliche Stelle ist die Musterfirma GmbH, Musterstraße 5, 12345 Musterstadt."
        self.assertTrue(pruefe_verantwortlicher(text).gefunden)

    def test_fehlt_ohne_kontaktdaten(self):
        # Bezeichnung allein reicht nicht - Art. 13 Abs. 1 lit. a fordert
        # zusätzlich konkrete Kontaktangaben.
        text = "Der Verantwortliche im Sinne der DSGVO informiert Sie hiermit."
        self.assertFalse(pruefe_verantwortlicher(text).gefunden)

    def test_fehlt_bei_kontaktdaten_ohne_bezeichnung(self):
        # Kontaktdaten allein (z.B. ein allgemeines Impressum) reichen nicht -
        # es muss erkennbar sein, dass es sich um den Verantwortlichen handelt.
        text = "Erreichen Sie uns unter kontakt@example.com oder telefonisch."
        self.assertFalse(pruefe_verantwortlicher(text).gefunden)

    def test_fehlt_ganz_ohne_hinweis(self):
        self.assertFalse(pruefe_verantwortlicher("Diese Seite nutzt Cookies.").gefunden)


class ZweckTest(unittest.TestCase):
    def test_gefunden_ueber_zweck_der_verarbeitung(self):
        text = "Der Zweck der Verarbeitung ist die Bearbeitung Ihrer Anfrage."
        self.assertTrue(pruefe_zweck(text).gefunden)

    def test_gefunden_ueber_verarbeitungszweck(self):
        text = "Der Verarbeitungszweck ergibt sich aus dem jeweiligen Kontaktanlass."
        self.assertTrue(pruefe_zweck(text).gefunden)

    def test_gefunden_ueber_zu_folgenden_zwecken(self):
        text = "Ihre Daten werden zu folgenden Zwecken verarbeitet: Vertragsabwicklung und Support."
        self.assertTrue(pruefe_zweck(text).gefunden)

    def test_gefunden_ueber_wir_verarbeiten_ihre_daten_fuer(self):
        text = "Wir verarbeiten Ihre Daten für die Zusendung unseres Newsletters."
        self.assertTrue(pruefe_zweck(text).gefunden)

    def test_fehlt(self):
        self.assertFalse(pruefe_zweck("Wir nehmen Datenschutz ernst.").gefunden)

    def test_fehlt_bei_verarbeiten_ohne_zweckangabe(self):
        # Bloße Erwähnung von "verarbeiten" ohne Zweck- oder Grund-Bezug
        # darf keinen falschen Treffer auslösen.
        text = "Wir verarbeiten Ihre Daten mit größter Sorgfalt."
        self.assertFalse(pruefe_zweck(text).gefunden)


class RechtsgrundlageTest(unittest.TestCase):
    def test_gefunden_ueber_artikel_verweis(self):
        text = "Rechtsgrundlage der Verarbeitung ist Art. 6 Abs. 1 lit. b DSGVO."
        self.assertTrue(pruefe_rechtsgrundlage(text).gefunden)

    def test_gefunden_ueber_rechtliche_grundlage(self):
        text = "Die rechtliche Grundlage für die Datenverarbeitung ist Ihre Einwilligung."
        self.assertTrue(pruefe_rechtsgrundlage(text).gefunden)

    def test_gefunden_ueber_artikelverweis_ohne_punkte(self):
        text = "Grundlage der Verarbeitung ist Art 6 Abs 1 DSGVO."
        self.assertTrue(pruefe_rechtsgrundlage(text).gefunden)

    def test_fehlt(self):
        self.assertFalse(pruefe_rechtsgrundlage("Wir verarbeiten Ihre Daten sorgfältig.").gefunden)

    def test_fehlt_bei_anderem_artikel_verweis(self):
        # Ein Verweis auf einen anderen DSGVO-Artikel ist kein Hinweis auf
        # die Rechtsgrundlage der Verarbeitung.
        text = "Weitere Informationen finden Sie in Art. 12 DSGVO."
        self.assertFalse(pruefe_rechtsgrundlage(text).gefunden)


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

    def test_gefunden_ueber_rechte_der_betroffenen_person(self):
        text = "Rechte der betroffenen Person: Im Folgenden informieren wir Sie über Ihre Rechte."
        self.assertTrue(pruefe_betroffenenrechte(text).gefunden)

    def test_gefunden_ueber_mindestens_zwei_einzelrechte(self):
        text = "Sie haben ein Recht auf Auskunft und ein Recht auf Löschung."
        self.assertTrue(pruefe_betroffenenrechte(text).gefunden)

    def test_gefunden_ueber_berichtigung_und_einschraenkung(self):
        text = "Ihnen stehen ein Recht auf Berichtigung sowie ein Recht auf Einschränkung der Verarbeitung zu."
        self.assertTrue(pruefe_betroffenenrechte(text).gefunden)

    def test_gefunden_ueber_widerspruch_und_widerruf(self):
        text = "Sie haben ein Recht auf Widerspruch sowie ein Recht auf Widerruf Ihrer Einwilligung."
        self.assertTrue(pruefe_betroffenenrechte(text).gefunden)

    def test_gefunden_ueber_datenuebertragbarkeit_und_auskunft(self):
        text = "Es besteht ein Recht auf Datenübertragbarkeit und ein Recht auf Auskunft."
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


class CliTest(unittest.TestCase):
    def _lauf(self, *args: str) -> subprocess.CompletedProcess:
        return subprocess.run(
            [sys.executable, "dsgvo_checker.py", *args],
            cwd=PROJEKT_ROOT,
            capture_output=True,
            text=True,
        )

    def test_exit_code_0_bei_vollstaendiger_erklaerung(self):
        ergebnis = self._lauf("examples/beispiel_vollstaendig.md")
        self.assertEqual(ergebnis.returncode, 0)
        self.assertIn("5/5 Pflichtangaben gefunden", ergebnis.stdout)

    def test_exit_code_1_bei_unvollstaendiger_erklaerung(self):
        ergebnis = self._lauf("examples/beispiel_unvollstaendig.md")
        self.assertEqual(ergebnis.returncode, 1)
        self.assertIn("0/5 Pflichtangaben gefunden", ergebnis.stdout)

    def test_json_ausgabe_ist_valides_json_mit_fuenf_eintraegen(self):
        ergebnis = self._lauf("--json", "examples/beispiel_vollstaendig.md")
        self.assertEqual(ergebnis.returncode, 0)
        daten = json.loads(ergebnis.stdout)
        self.assertEqual(len(daten), 5)
        self.assertTrue(all(eintrag["gefunden"] for eintrag in daten))
        self.assertEqual(daten[0]["id"], "verantwortlicher")

    def test_json_ausgabe_zeigt_fehlende_pflichtangaben(self):
        ergebnis = self._lauf("--json", "examples/beispiel_unvollstaendig.md")
        self.assertEqual(ergebnis.returncode, 1)
        daten = json.loads(ergebnis.stdout)
        self.assertTrue(all(not eintrag["gefunden"] for eintrag in daten))


if __name__ == "__main__":
    unittest.main()
