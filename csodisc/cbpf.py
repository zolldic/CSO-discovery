"""Stage 1: pull the UN OCHA CBPF project summary from HDX and pick redacted national partners."""
import csv
import urllib.request

HDX_CSV = ("https://data.humdata.org/dataset/afdb5d55-b60b-4385-b882-0e0109308e33/resource/"
           "c0e3bc85-2c76-4c93-84cc-50fa4b5e83ca/download/sdn_cbpf_project_summary.csv")
UA = {"User-Agent": "sudan-cso-discovery (open research tool)"}


def fetch(dest, url=HDX_CSV):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r, open(dest, "wb") as f:
        f.write(r.read())


def select(path, years=("2024", "2025", "2026"), types=("National NGO", "Others")):
    """Rows whose OrganizationName is redacted to a generic type label."""
    with open(path, encoding="utf-8", errors="ignore", newline="") as f:
        rows = [r for r in csv.DictReader(f)
                if r["AllocationYear"] in years and r["OrganizationType"] in types]
    for r in rows:
        r["Budget"] = float(r["Budget"] or 0)
    return rows
