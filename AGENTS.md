# Instructions for AI agents

This repo finds which Sudanese civil society organizations received donor funding, including partners that donors masked. It is meant to be operated by you, an AI agent, with a researcher supervising.

Read, in this order: `ETHICS.md`, then `docs/PLAYBOOK.md`. Follow the playbook step by step.

## Setup
None. Python 3.9+ and the standard library only. No API key. Run from the repo root.

```bash
python3 -m unittest discover -s tests -t .      # should pass offline
python3 -m csodisc --out out                    # live run (needs internet)
```

## Hard rules
1. **Never guess an organization name.** Confirm a name only when a quote says it. No quote, no row. If unsure, leave it `no_candidates`.
2. **No evidence URL means no row** in `verified.csv` or `grants.csv`. The merge step rejects those rows.
3. **Everything under `out/`, plus `verified.csv` and `grants.csv`, is private.** Never commit it, paste it into a public place, or publish decoded names. Fixtures in `tests/` are synthetic.
4. **Do not decide redact or reveal.** Ask the researcher. Default is redacted.
5. **Do not state a donor relationship that the evidence does not show.** Direct grant, sub-grant and shared theme are different (`docs/organizations.schema.md`).
6. Never record staff names, personal details or field locations.
7. Do not contact an organization or reveal that it was found in a masked source.

## What is deterministic and what is yours
- Code: download, filter, join, sum, rank candidates, pseudonymize, merge. Tested. Do not reimplement it by hand.
- You: reading narratives, deciding who the implementer is, reading donor pages, classifying funding type, checking the organization is live.

## Done means
- `python3 -m unittest discover -s tests -t .` passes.
- `out/organizations.csv` exists and every row has an evidence URL and a funding type.
- You reported which rows are `publishable=no` and why.
- You told the researcher what was left unresolved, with the reason (for example `no_candidates` after the fallback steps).
