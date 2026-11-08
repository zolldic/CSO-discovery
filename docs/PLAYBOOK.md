# Playbook: from masked data to a verified organization list

Written for a person or any AI agent. Do the steps in order. Read `ETHICS.md` first. Everything under `out/`, `verified.csv`, `grants.csv` is private.

Rule of thumb: if the same input must give the same output, a script does it (Part A). If it needs reading and judgment, you do it with the quote in front of you (Parts B to D).

## Part A. Decode the OCHA pooled fund (script)

```bash
python3 -m csodisc --out out
```

Read `out/partners.csv` (one row per `PartnerCode`, with totals and ranked name candidates) and `out/projects.csv` (one row per project, with title and start date). The cached narratives are in `out/cache/<project_code>.json`.

Expected shape of a healthy run: some partners have candidates, some do not. A partner with `status=no_candidates` usually has an empty or generic narrative. That is normal, not a bug.

## Part B. Confirm each candidate (judgment)

For each partner with candidates, open its cached narratives and decide which name, if any, is the **implementer**.

Confirm only when the text says it, for example a self-description ("X is the first national NGO leading..."). A candidate's rank is a hint, never proof. Programme terms, clusters and ministries show up in the list. Ignore them.

Record each confirmation in `verified.csv` (template: `docs/verified.template.csv`). Required: the partner code, the name, an evidence URL (the d-portal record, `https://d-portal.org/q.json?aid=XM-OCHA-CBPF-<project_code>`, or the organization's own page) and a confidence. No evidence URL means no row.

Several projects under one organization: group by `PartnerCode`, never by string. Do not merge two partner codes into one organization unless the evidence says they are the same.

## Part C. Fallback for partners with no candidates (judgment)

In this order. Stop at the first step that names the implementer, and stop trying if none does.

1. Read the project title and location in `projects.csv`. Search that title on the donors' own announcements.
2. Search d-portal by title for the same project under another IATI publisher.
3. Read the Arabic narrative by hand. The heuristic catches names only after a marker word (منظمة, جمعية, مؤسسة, شبكة, مبادرة, تحالف, مركز).
4. Check consortium leads (CFI, Free Press Unlimited, Internews) for the same project.

If nothing names the implementer, leave the partner as `no_candidates`. Never guess a name.

## Part D. Add donor-published grantees (manual, per source)

These sources name their grantees themselves. They need a browser or manual reading, so a script does not do them. Record each row in `grants.csv` (template: `docs/grants.template.csv`). Sites change, so check each URL still works.

| Source | Where | What to extract | What it proves |
| :-- | :-- | :-- | :-- |
| Center for Disaster Philanthropy, Sudan Humanitarian Crisis Fund | `disasterphilanthropy.org/cdp-fund/sudan-humanitarian-crisis-fund/` | Grantee, amount, date and purpose from each grant-round announcement | `direct` grant from CDP |
| Sigrid Rausing Trust | `sigrid-rausing-trust.org/grantees/` | Grantee page: amount, period and purpose, if published | `direct` grant; core or project |
| UN Women WPHF | `wphfund.org/countries/sudan/` and `wphfund.org/our-work/grantees/` | Grantee name, grant type (institutional or programmatic), project summary | `direct` grant. Amount is often only on the project page |
| NED | `ned.org` (Sudan project pages) | Grantee, year, project description, amount | `direct` grant |
| UNESCO / Global Media Defence Fund | `unesco.org` | Prize or emergency-support recipient | A prize is not a grant. Record it only if the page states a grant |
| Free Press Unlimited, GFMD | `freepressunlimited.org`, `gfmd.info` | Consortium partners for a programme | Often `sub_grant` (via a lead). Do not call it direct |

For every row decide the funding type and write it down:

- `direct`: the donor's page says it granted to this organization.
- `sub_grant`: the organization is a consortium partner or sub-grantee of a lead.
- `thematic`: the organization works on the same theme but no funding relationship is shown. Do not assert a donor relationship from a shared theme.

Amounts: copy what is published. If a page gives no amount, leave it blank. Do not estimate or convert currencies.

## Part E. Check the organization is live (judgment)

Pre-war registries produce false positives. Before listing an organization, confirm it was active after April 2023: its own website or social posts with dates. Do not call a page dead on a bare HTTP 200 or a missing page alone. Inspect the page body, and say what you saw.

## Part F. Assemble and export

```bash
python3 -m csodisc.merge --out out --verified verified.csv --grants grants.csv
```

This writes `out/organizations.csv` using the schema in `docs/organizations.schema.md` and rejects rows that break the gates. Fix the rejected rows and run it again.

To share anything, ask the researcher whether to redact or reveal. Do not decide for them.

```bash
python3 -m csodisc.export --out out                                        # pseudonyms, counts and totals only
python3 -m csodisc.export --out out --verified verified.csv --reveal       # names confirmed partners only
```

Remind them of `ETHICS.md` before they share a revealed file.

## Failure modes

- Candidate list holds programme terms: ignore them.
- d-portal returns no activity: the project may not be in IATI yet. Record it as undecodable.
- Newest grants may have no narrative yet (publication lag). Rerun later.
- Counting "projects with a candidate" as accuracy overstates it. Check against names you know are right (`evals/live_eval.py`).
