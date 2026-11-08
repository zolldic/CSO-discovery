"""Join stages 1 and 2 into projects.csv and partners.csv. Every partner row is unverified by design."""
import csv
import os

from . import cbpf, iati

PROJECT_FIELDS = ["project_code", "partner_code", "year", "start", "budget_usd", "title", "candidates"]
PARTNER_FIELDS = ["partner_code", "projects", "total_budget_usd", "candidates", "status", "publishable"]


def run(rows, out_dir, fetch=iati.fetch_activity, cache_dir=None):
    projects, by_partner = [], {}
    for r in rows:
        act = fetch(r["ChfProjectCode"], cache_dir=cache_dir)
        cands = iati.candidates(act["description"])
        projects.append({"project_code": r["ChfProjectCode"], "partner_code": r["PartnerCode"],
                         "year": r["AllocationYear"], "start": r["ProjectStartDate"][:10],
                         "budget_usd": r["Budget"], "title": act["title"] or r["ProjectTitle"],
                         "candidates": "|".join(cands)})
        p = by_partner.setdefault(r["PartnerCode"], {"projects": 0, "total": 0.0, "c": {}})
        p["projects"] += 1
        p["total"] += r["Budget"]
        for c in cands:
            p["c"][c] = p["c"].get(c, 0) + 1
    partners = [{"partner_code": k, "projects": v["projects"], "total_budget_usd": round(v["total"], 2),
                 "candidates": "|".join(sorted(v["c"], key=lambda c: (-v["c"][c], c))[:5]),
                 "status": "unverified" if v["c"] else "no_candidates", "publishable": "no"}
                for k, v in sorted(by_partner.items(), key=lambda kv: -kv[1]["total"])]
    os.makedirs(out_dir, exist_ok=True)
    for name, fields, data in (("projects.csv", PROJECT_FIELDS, projects), ("partners.csv", PARTNER_FIELDS, partners)):
        with open(os.path.join(out_dir, name), "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fields)
            w.writeheader()
            w.writerows(data)
    return projects, partners
