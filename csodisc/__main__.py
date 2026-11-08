import argparse
import os
import sys

from . import cbpf, pipeline

NOTICE = ("DUTY OF CARE: out/ holds names the donor deliberately redacted. Do not publish, commit, or share "
          "it. Confirm each candidate by hand and treat 'publishable' as 'no' unless the org itself is public.\n")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="csodisc", description="Decode redacted Sudan CBPF partners via IATI.")
    ap.add_argument("--out", default="out")
    ap.add_argument("--years", nargs="+", default=["2024", "2025", "2026"])
    ap.add_argument("--types", nargs="+", default=["National NGO", "Others"])
    ap.add_argument("--csv", help="use a local CBPF CSV instead of downloading")
    a = ap.parse_args(argv)
    os.makedirs(a.out, exist_ok=True)
    src = a.csv or os.path.join(a.out, "sdn_cbpf_project_summary.csv")
    if not a.csv:
        cbpf.fetch(src)
    rows = cbpf.select(src, tuple(a.years), tuple(a.types))
    projects, partners = pipeline.run(rows, a.out, cache_dir=os.path.join(a.out, "cache"))
    hit = sum(1 for p in projects if p["candidates"])
    pc = sum(1 for p in partners if p["status"] == "unverified")
    total = sum(p["budget_usd"] for p in projects)
    sys.stderr.write(NOTICE)
    print(f"projects={len(projects)} (USD {total:,.0f}) partners={len(partners)} | "
          f"projects_with_candidates={hit} ({hit / max(len(projects), 1):.0%}) "
          f"partners_with_candidates={pc} no_candidates={len(partners) - pc} -> {a.out}/partners.csv")


if __name__ == "__main__":
    main()
