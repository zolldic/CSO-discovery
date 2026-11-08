"""Periodic eval (network): does the true partner name appear in the top-5 candidates for known partner codes?

Golden pairs are real redacted partners, so they live in a gitignored local file, never in the repo:
  evals/golden.local.json  ->  {"<partner_code>": "<expected name>", ...}
Run: python3 evals/live_eval.py   (exit 1 below THRESHOLD)
"""
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from csodisc import cbpf, pipeline  # noqa: E402

THRESHOLD = 0.8
golden_path = os.path.join(os.path.dirname(__file__), "golden.local.json")
if not os.path.exists(golden_path):
    sys.exit("missing evals/golden.local.json (see docstring)")
golden = json.load(open(golden_path))
with tempfile.TemporaryDirectory() as d:
    src = os.path.join(d, "cbpf.csv")
    cbpf.fetch(src)
    _, partners = pipeline.run(cbpf.select(src), d, cache_dir=os.path.join(d, "cache"))
got = {p["partner_code"]: p["candidates"].split("|") for p in partners}
hits = sum(any(exp.lower() in c.lower() for c in got.get(code, [])) for code, exp in golden.items())
score = hits / len(golden)
print(f"hit@5={hits}/{len(golden)} ({score:.0%}) threshold={THRESHOLD:.0%}")
sys.exit(0 if score >= THRESHOLD else 1)
