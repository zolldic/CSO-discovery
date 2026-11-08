"""Stage 2: fetch the unredacted project narrative from d-portal (IATI) and surface name candidates."""
import json
import os
import re
import time
import urllib.request

from .cbpf import UA

DPORTAL = "https://d-portal.org/q.json?aid=XM-OCHA-CBPF-{code}"
# d-portal strips '&' and ';' from HTML entities, leaving tokens like "ltpgt" and "nbsp".
_TAGS = re.compile(r"lt/?(?:p|br|li|ul|ol|b|i|u|strong|em|span|div)gt|nbsp|amp(?=\s)", re.I)
_STOP = {"UN", "OCHA", "GBV", "SHF", "NGO", "NGOS", "IDP", "IDPS", "SAF", "RSF", "USD", "WASH", "MHPSS",
         "CBPF", "UNICEF", "WHO", "WFP", "UNFPA", "FAO", "IOM", "UNHCR", "HCT", "OPT", "PSEA", "AAP",
         "COVID", "HRP", "HNO", "GAM", "SAM", "FSL", "CCCM", "SGBV", "PSS", "ERR", "ERRS", "EORE", "UXO"}
_SUBJECT = re.compile(r"\b([A-Z][\w&'-]+(?:\s+(?:[A-Z][\w&'-]+|for|of|and|the)){0,7})\s+"
                      r"(?:is|are|has|have|was|were|will|operates|works|implements)\b")


# Arabic org markers followed by up to 4 Arabic words. Heuristic, same caveat as the English subject rule.
_AR = re.compile(r"(?:منظمة|جمعية|مؤسسة|شبكة|مبادرة|تحالف|مركز)(?:\s+[\u0600-\u06FF]{2,}){1,4}")


def clean(text):
    return re.sub(r"\s+", " ", _TAGS.sub(" ", text or "")).strip()


def fetch_activity(code, cache_dir=None, delay=0.5, opener=urllib.request.urlopen):
    """Return {title, description} for a CBPF project code. Cached on disk when cache_dir is set."""
    path = os.path.join(cache_dir, code + ".json") if cache_dir else None
    if path and os.path.exists(path):
        return json.load(open(path, encoding="utf-8"))
    req = urllib.request.Request(DPORTAL.format(code=code), headers=UA)
    with opener(req, timeout=30) as r:
        data = json.loads(r.read().decode("utf-8"))
    time.sleep(delay)
    out = parse_activity(data)
    if path:
        os.makedirs(cache_dir, exist_ok=True)
        json.dump(out, open(path, "w", encoding="utf-8"), ensure_ascii=False)
    return out


def parse_activity(data):
    xs = data.get("xson") or []
    if not xs:
        return {"title": "", "description": ""}
    act = xs[0]["/iati-activities/iati-activity"][0]
    narr = lambda items: " ".join(n.get("", "") for d in items for n in d.get("/narrative", []))
    title = " ".join(n.get("", "") for n in act.get("/title/narrative", []))
    return {"title": clean(title), "description": clean(narr(act.get("/description", [])))}


def candidates(text, top=5):
    """Heuristic only: acronyms and 'X is/has/...' subjects ranked by frequency. A human confirms."""
    counts = {}
    for m in re.findall(r"\b[A-Z][A-Za-z]{2,8}\b", text):
        if m.isupper() and m not in _STOP:
            counts[m] = counts.get(m, 0) + 1
    for m in _SUBJECT.findall(text):
        if m.split()[0].upper() not in _STOP and m not in {"The", "This", "These", "We", "It"}:
            counts[m] = counts.get(m, 0) + 1
    for m in _AR.findall(text):
        counts[m] = counts.get(m, 0) + 1
    return [k for k, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:top]]
