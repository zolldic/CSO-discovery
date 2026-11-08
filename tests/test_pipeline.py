import csv
import json
import os
import tempfile
import unittest

from csodisc import cbpf, export, iati, merge, pipeline

HERE = os.path.dirname(__file__)
FIX = os.path.join(HERE, "fixtures", "cbpf_sample.csv")
NARR = {"P-1": "ltpgtltbrgtZARA Foundation is the lead partner. ZARA works in Darfur nbsp for GBV.",
        "P-2": "ZARA runs clinics. See UN and OCHA guidance.",
        "P-3": ""}


def fake_fetch(code, cache_dir=None):
    return {"title": "t-" + code, "description": iati.clean(NARR[code])}


class Gate(unittest.TestCase):
    def test_select_filters_year_type_and_parses_budget(self):
        rows = cbpf.select(FIX)
        self.assertEqual([r["ChfProjectCode"] for r in rows], ["P-1", "P-2", "P-3"])
        self.assertEqual(rows[1]["Budget"], 50000.5)

    def test_clean_strips_dportal_entity_residue(self):
        self.assertEqual(iati.clean("ltpgtltbrgtHello nbsp world lt/pgt"), "Hello world")

    def test_candidates_rank_and_stoplist(self):
        c = iati.candidates(iati.clean(NARR["P-1"] + " " + NARR["P-2"]))
        self.assertEqual(c[0], "ZARA")
        self.assertNotIn("UN", c)
        self.assertNotIn("GBV", c)

    def test_parse_activity_handles_empty_response(self):
        self.assertEqual(iati.parse_activity({"xson": []}), {"title": "", "description": ""})

    def test_pipeline_totals_and_safety_defaults(self):
        with tempfile.TemporaryDirectory() as d:
            _, partners = pipeline.run(cbpf.select(FIX), d, fetch=fake_fetch)
            top = partners[0]
            self.assertEqual((top["partner_code"], top["projects"], top["total_budget_usd"]), ("2.2", 1, 200000.0))
            p11 = next(p for p in partners if p["partner_code"] == "1.1")
            self.assertEqual(p11["total_budget_usd"], 150000.5)
            self.assertTrue(p11["candidates"].startswith("ZARA"))
            self.assertEqual({p["partner_code"]: p["status"] for p in partners}, {"1.1": "unverified", "2.2": "no_candidates"})
            self.assertTrue(all(p["publishable"] == "no" for p in partners))
            self.assertEqual(len(list(csv.DictReader(open(os.path.join(d, "projects.csv"))))), 3)

    def test_empty_narrative_yields_no_candidates_not_crash(self):
        self.assertEqual(iati.candidates(""), [])

    def test_arabic_org_marker_yields_candidate(self):
        c = iati.candidates("تنفذ منظمة الأمل للتنمية المشروع في دارفور")
        self.assertTrue(any(x.startswith("منظمة الأمل") for x in c))


class Export(unittest.TestCase):
    P = [{"partner_code": "1.1", "projects": 2, "total_budget_usd": 150000.5},
         {"partner_code": "2.2", "projects": 1, "total_budget_usd": 200000.0}]

    def _verified(self, d, rows):
        path = os.path.join(d, "verified.csv")
        with open(path, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, export.VERIFIED_FIELDS)
            w.writeheader()
            w.writerows(rows)
        return path

    def test_default_redacted_has_no_name_fields_and_stable_pseudonym(self):
        rows = export.build(self.P, {}, reveal=False)
        self.assertEqual(set(rows[0]), set(export.REDACTED_FIELDS))
        self.assertEqual(rows[0]["pseudonym"], export.pseudonym("1.1"))
        self.assertNotEqual(export.pseudonym("1.1"), export.pseudonym("2.2"))

    def test_reveal_requires_evidence_url(self):
        with tempfile.TemporaryDirectory() as d:
            v = export.load_verified(self._verified(d, [
                {"partner_code": "1.1", "confirmed_name": "ZARA", "evidence_url": "https://zara.example/about", "confidence": "high"},
                {"partner_code": "2.2", "confirmed_name": "Guess Org", "evidence_url": "", "confidence": "low"}]))
        self.assertEqual(list(v), ["1.1"])
        rows = export.build(self.P, v, reveal=True)
        self.assertEqual(rows[0]["confirmed_name"], "ZARA")
        self.assertEqual(rows[1]["confirmed_name"], "")

    def test_missing_verified_file_means_nothing_revealed(self):
        self.assertEqual(export.load_verified("/nonexistent.csv"), {})
        self.assertEqual(export.build(self.P, {}, reveal=True)[0]["confirmed_name"], "")

    def test_cli_default_never_writes_names(self):
        with tempfile.TemporaryDirectory() as d:
            pipeline.run(cbpf.select(FIX), d, fetch=fake_fetch)
            export.main(["--out", d])
            txt = open(os.path.join(d, "export_redacted.csv"), encoding="utf-8").read()
            self.assertNotIn("ZARA", txt)
            self.assertNotIn("t-P-1", txt)


class Merge(unittest.TestCase):
    PARTNERS = [{"partner_code": "1.1", "total_budget_usd": "150000.5"}]
    PROJECTS = [{"partner_code": "1.1", "start": "2025-06-01"}, {"partner_code": "1.1", "start": "2025-01-01"}]
    V = [{"partner_code": "1.1", "confirmed_name": "ZARA", "evidence_url": "https://zara.example/about", "confidence": "high"},
         {"partner_code": "1.1", "confirmed_name": "NoEvidence", "evidence_url": "", "confidence": "low"},
         {"partner_code": "9.9", "confirmed_name": "Ghost", "evidence_url": "https://x.example", "confidence": "low"}]
    G = [{"name": "Beta", "donor": "Fund", "funding_type": "sub_grant", "amount": "100", "currency": "USD",
          "evidence_url": "https://fund.example/beta"},
         {"name": "Gamma", "donor": "Fund", "funding_type": "vibes", "evidence_url": "https://fund.example/g"},
         {"name": "Delta", "donor": "Fund", "funding_type": "direct", "evidence_url": ""}]

    def test_evidence_and_type_gates(self):
        rows, rejected = merge.build(self.V, self.G, self.PARTNERS, self.PROJECTS)
        self.assertEqual([r["name"] for r in rows], ["Beta", "ZARA"])
        self.assertEqual(len(rejected), 4)

    def test_decoded_rows_take_amount_and_period_from_pipeline_and_stay_private(self):
        rows, _ = merge.build(self.V, [], self.PARTNERS, self.PROJECTS)
        z = rows[0]
        self.assertEqual((z["amount"], z["period"], z["publishable"]), ("150000.5", "2025-01-01..2025-06-01", "no"))

    def test_cli_writes_schema_columns(self):
        with tempfile.TemporaryDirectory() as d:
            pipeline.run(cbpf.select(FIX), d, fetch=fake_fetch)
            vp = os.path.join(d, "verified.csv")
            with open(vp, "w", encoding="utf-8", newline="") as f:
                w = csv.DictWriter(f, export.VERIFIED_FIELDS)
                w.writeheader()
                w.writerow({"partner_code": "1.1", "confirmed_name": "ZARA", "evidence_url": "https://z.example", "confidence": "high"})
            merge.main(["--out", d, "--verified", vp, "--grants", os.path.join(d, "none.csv")])
            rows = list(csv.DictReader(open(os.path.join(d, "organizations.csv"), encoding="utf-8")))
            self.assertEqual(list(rows[0]), merge.FIELDS)
            self.assertEqual(rows[0]["amount"], "150000.5")


if __name__ == "__main__":
    unittest.main()
