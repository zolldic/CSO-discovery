"""Stage 3: turn private working files into a shareable export. Default is redacted; naming is opt-in.

Reveal mode names only partners the researcher confirmed in verified.csv with an http(s) evidence_url.
Everything else stays pseudonymous (PARTNER-xxxxxx). Candidates and project titles never leave the private dir.
"""
import argparse
import csv
import hashlib
import os
import sys

VERIFIED_FIELDS = ["partner_code", "confirmed_name", "evidence_url", "confidence"]
REDACTED_FIELDS = ["pseudonym", "projects", "total_budget_usd"]
REVEAL_FIELDS = REDACTED_FIELDS + ["confirmed_name", "evidence_url", "confidence"]


def pseudonym(code):
    return "PARTNER-" + hashlib.sha256(code.encode()).hexdigest()[:6].upper()


def load_verified(path):
    """Return {partner_code: row} keeping only rows with a name and an http(s) evidence URL."""
    if not path or not os.path.exists(path):
        return {}
    with open(path, encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    return {r["partner_code"].strip(): r for r in rows
            if r.get("confirmed_name", "").strip() and r.get("evidence_url", "").strip().lower().startswith(("http://", "https://"))}


def build(partners, verified, reveal=False):
    out = []
    for p in partners:
        row = {"pseudonym": pseudonym(p["partner_code"]), "projects": p["projects"],
               "total_budget_usd": p["total_budget_usd"]}
        v = verified.get(p["partner_code"]) if reveal else None
        if reveal:
            row.update(confirmed_name=v["confirmed_name"].strip() if v else "",
                       evidence_url=v["evidence_url"].strip() if v else "",
                       confidence=v.get("confidence", "").strip() if v else "")
        out.append(row)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser(prog="csodisc.export", description="Redacted by default; --reveal names verified partners only.")
    ap.add_argument("--out", default="out")
    ap.add_argument("--verified", help="verified.csv with partner_code,confirmed_name,evidence_url,confidence")
    ap.add_argument("--reveal", action="store_true", help="include names for rows with evidence_url. Your call, your risk.")
    a = ap.parse_args(argv)
    with open(os.path.join(a.out, "partners.csv"), encoding="utf-8", newline="") as f:
        partners = list(csv.DictReader(f))
    verified = load_verified(a.verified)
    rows = build(partners, verified, a.reveal)
    name = "export_revealed.csv" if a.reveal else "export_redacted.csv"
    with open(os.path.join(a.out, name), "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, REVEAL_FIELDS if a.reveal else REDACTED_FIELDS)
        w.writeheader()
        w.writerows(rows)
    named = sum(1 for r in rows if r.get("confirmed_name"))
    if a.reveal:
        sys.stderr.write("REVEAL MODE: this file names organizations. Re-read ETHICS.md before sharing it.\n")
    print(f"{len(rows)} partners, {named} named -> {a.out}/{name}")


if __name__ == "__main__":
    main()
