"""Stage 4: assemble the per-organization record (docs/organizations.schema.md) from confirmed work.

Two inputs, both written by a person or agent after reading evidence:
  verified.csv  partner_code,confirmed_name,evidence_url,confidence      (OCHA decoded partners)
  grants.csv    name,domain,base,donor,funding_type,amount,currency,period,evidence_url,evidence_quote
                                                                         (donor-published grantees)

A row without an http(s) evidence_url is rejected. Output is private: out/organizations.csv names organizations.
"""
import argparse
import csv
import os
import sys

FIELDS = ["name", "domain", "base", "donor", "funding_type", "amount", "currency", "period",
          "evidence_url", "evidence_quote", "source", "partner_code", "status", "publishable"]
GRANT_FIELDS = ["name", "domain", "base", "donor", "funding_type", "amount", "currency", "period",
                "evidence_url", "evidence_quote"]
FUNDING_TYPES = {"direct", "sub_grant", "thematic"}


def _has_url(v):
    return (v or "").strip().lower().startswith(("http://", "https://"))


def _read(path):
    if not path or not os.path.exists(path):
        return []
    with open(path, encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def period(projects):
    starts = sorted(p["start"] for p in projects if p.get("start"))
    return f"{starts[0]}..{starts[-1]}" if starts else ""


def from_verified(verified, partners, projects):
    """OCHA rows. Amount and period come from the pipeline output, never typed by hand."""
    by_code = {p["partner_code"]: p for p in partners}
    out, rejected = [], []
    for v in verified:
        code = (v.get("partner_code") or "").strip()
        if not (v.get("confirmed_name") or "").strip() or not _has_url(v.get("evidence_url")) or code not in by_code:
            rejected.append(f"verified:{code or '?'}")
            continue
        mine = [p for p in projects if p["partner_code"] == code]
        out.append({"name": v["confirmed_name"].strip(), "domain": "", "base": "", "donor": "UN OCHA Sudan Humanitarian Fund",
                    "funding_type": "direct", "amount": by_code[code]["total_budget_usd"], "currency": "USD",
                    "period": period(mine), "evidence_url": v["evidence_url"].strip(), "evidence_quote": "",
                    "source": "cbpf_decoded", "partner_code": code, "status": "verified",
                    # decoded from a redacted source: private unless the org names itself publicly
                    "publishable": "no"})
    return out, rejected


def from_grants(grants):
    out, rejected = [], []
    for g in grants:
        name = (g.get("name") or "").strip()
        if not name or not _has_url(g.get("evidence_url")) or (g.get("funding_type") or "").strip() not in FUNDING_TYPES:
            rejected.append(f"grant:{name or '?'}")
            continue
        row = {k: (g.get(k) or "").strip() for k in GRANT_FIELDS}
        row.update(source="donor_published", partner_code="", status="verified", publishable="yes")
        out.append(row)
    return out, rejected


def build(verified, grants, partners, projects):
    a, ra = from_verified(verified, partners, projects)
    b, rb = from_grants(grants)
    return sorted(a + b, key=lambda r: (r["name"].lower(), r["donor"])), ra + rb


def main(argv=None):
    ap = argparse.ArgumentParser(prog="csodisc.merge", description="Assemble out/organizations.csv from verified.csv and grants.csv.")
    ap.add_argument("--out", default="out")
    ap.add_argument("--verified", default="verified.csv")
    ap.add_argument("--grants", default="grants.csv")
    a = ap.parse_args(argv)
    partners = _read(os.path.join(a.out, "partners.csv"))
    projects = _read(os.path.join(a.out, "projects.csv"))
    rows, rejected = build(_read(a.verified), _read(a.grants), partners, projects)
    path = os.path.join(a.out, "organizations.csv")
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, FIELDS)
        w.writeheader()
        w.writerows(rows)
    sys.stderr.write("PRIVATE: organizations.csv names organizations. Re-read ETHICS.md before sharing any part of it.\n")
    if rejected:
        sys.stderr.write(f"rejected (no name, no http(s) evidence_url, bad funding_type or unknown partner_code): {', '.join(rejected)}\n")
    print(f"{len(rows)} organization rows, {len(rejected)} rejected -> {path}")


if __name__ == "__main__":
    main()
