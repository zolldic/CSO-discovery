# sudan-cso-discovery

A research method, and a small tool, for finding which Sudanese civil society organizations (CSOs) received donor funding, including partners that donors deliberately mask.

You clone it, point an AI agent (or yourself) at it, and get a verified, evidence-backed list of funded organizations. Python 3.9+, standard library only, no API key, no setup.

## Why this exists

I wanted to offer communications, social media and visibility consultancy to Sudanese organizations in democracy, human rights, women's rights, media and peacebuilding. Cold-pitching every organization is wasteful. The useful targets are organizations that are active now, have a donor to report to, and have a budget, so I needed to know who was actually funded from 2024 through 2026, inside Sudan and in the exile hubs of Kampala and Nairobi.

That turned out to be hard, and the way I solved it is the part worth documenting. (How I used the list to pitch is a separate story and not part of this repo.)

## The problem: wartime Sudan breaks the usual sources

- **Pre-war registries are stale.** Many organizations dissolved or went dormant after fighting began in April 2023. Searching old NGO registries gives mostly false positives.
- **Donors redact partner names for duty of care.** Staff of local organizations have been detained, extorted and targeted by both sides of the war. So transparency registers mask them:
  - US foreign assistance data redacts recipient names (FATAA 2016 exemptions).
  - The UN OCHA pooled fund (CBPF) export on the Humanitarian Data Exchange replaces national partner names with `"National NGO"` or `"Others"`. You get a project code, a budget, dates and an opaque `PartnerCode`, and no name.

A keyword search across these sources finds almost nothing useful.

## The method

Two independent routes. Together they produced my first list of 17 organizations.

### Route 1: decode the masked UN grants (automated here)

The same projects that CBPF masks are also published as open aid data (IATI). The project description is free text written by the partner, and it often names the implementer. CBPF project codes are also IATI activity identifiers, so the two datasets join on the project code.

```
HDX CBPF CSV -> keep masked rows (2024-2026 by default)
             -> d-portal narrative for each project (IATI)
             -> rank organization-name candidates per PartnerCode
             -> a person confirms each name from the quote
```

A worked example, anonymized: one masked project of about $1.5M had a narrative that began "X is the first national NGO leading the GBV Area of Responsibility...". That sentence names the implementer. Grouping by `PartnerCode` then tied the same organization to four more grants across 2024 to 2026, more than $4M in total. The masked CSV alone could never show that. The sentence did. A person read it and confirmed it. The tool does not make that call.

### Route 2: read what donors publish about their grantees (manual, documented)

Several funders name their grantees themselves: Center for Disaster Philanthropy, Sigrid Rausing Trust, UN Women's WPHF, NED, UNESCO, and the Free Press Unlimited / GFMD media consortium. Those pages need a browser or careful reading, so a script does not do them. The playbook gives the procedure per source: what to extract, what counts as evidence, and how to classify the funding.

The classification matters. A **direct** grant, a **sub-grant** through a consortium lead, and a **thematic** match (same topic, no relationship shown) are different things. Calling a sub-grantee a direct grantee of the donor is the mistake this method is built to avoid.

### The split between code and judgment

If the same input must give the same output, it is code: download, filter, join, sum, rank, pseudonymize, merge. These are deterministic and tested. Deciding whether a sentence names the implementer, whether a grant is direct, and whether an organization is still active needs reading, so it stays with a person or an AI agent holding the quote.

### The final product

One row per organization and grant: name, sector, base, donor, funding type, amount, period, evidence URL and quote, verification status, and whether it can be published. Schema: `docs/organizations.schema.md`. A row without an evidence URL is rejected.

## What it is and is not

**It is** a repeatable pipeline for Route 1, a step-by-step playbook for Route 2, a schema for the result, and ethics guardrails that default to privacy.

**It is not**
- a list of organizations. That list stays private (see `ETHICS.md`).
- a way to auto-identify anyone. Candidates are a heuristic and a person verifies each one.
- coverage of the donor registries in code. Those are documented procedures.
- a ranking of organizations by sector, or a tracker of funding over time.

## Quick start

```bash
git clone <this repo> && cd sudan-cso-discovery
make setup                                     # optional: run tests before each commit
python3 -m unittest discover -s tests -t .     # offline check, should pass
python3 -m csodisc --out out                   # fetch, join, rank candidates (needs internet)
```

Useful flags: `--years 2025 2026`, `--types "National NGO"`, `--csv local.csv` (use a CSV you already downloaded).

### With an AI agent (any agent)

Open the repo in your agent and say:

> Read AGENTS.md, then follow docs/PLAYBOOK.md. Ask me before deciding redact or reveal.

`AGENTS.md` is the plain-Markdown convention that Codex, Cursor, Copilot, Gemini CLI and others read, and you can paste it into any other agent. Claude Code users also get `skills/sudan-cso-discovery/`, which just points to the same files. There is one set of instructions, so agents do not drift apart.

### By hand

1. Run the command above. Open `out/partners.csv` and read the top candidates per partner code.
2. Open the cached narrative (`out/cache/<project>.json`) to confirm. Record each confirmation in `verified.csv` with an evidence URL (template: `docs/verified.template.csv`).
3. Add donor-published grantees in `grants.csv` (template: `docs/grants.template.csv`) following `docs/PLAYBOOK.md`, Part D.
4. Assemble: `python3 -m csodisc.merge --out out --verified verified.csv --grants grants.csv`.

### Share or keep private

```bash
# default: pseudonyms (PARTNER-xxxxxx), project counts and budget totals. No names.
python3 -m csodisc.export --out out
# opt in: names only partners confirmed in verified.csv with an http(s) evidence_url
python3 -m csodisc.export --out out --verified verified.csv --reveal
```

`partners.csv`, `projects.csv`, `organizations.csv`, `verified.csv`, `grants.csv` and `out/cache/` are private working files. They are gitignored and never exported.

## Results (live run, 2026-11-08)

- 22 masked national-partner projects from 2024 to 2026, USD 19.80M in total (USD 18.40M labelled `National NGO`, USD 1.40M labelled `Others`).
- 15 distinct `PartnerCode` values.
- 8 of 15 partners produced candidates. 7 produced none; all 7 had an empty narrative in d-portal.
- Projects: 15 of 22 had at least one candidate (68%). Partner coverage is the number that matters and it is 8 of 15.
- On the two partners I verified by hand, the true name was in the top 5 candidates (hit@5 2 of 2). That is a smoke test, not a benchmark.
- Totals reproduce: the two largest partners decode to the same sums as my manual research, to the cent.

Outcome moved: reading narratives by hand for every funding round is replaced by one command plus review of a ranked list. `evals/live_eval.py` tracks hit@5 with an 80% threshold against a private golden file.

## What went wrong along the way

- d-portal strips `&` and `;` from HTML entities, leaving text like `ltpgtltbrgt` and `nbsp`. The cleaner removes these tokens and has a test.
- The first heuristic surfaced programme terms (HNRP, GBV, ministries). A stoplist helps, but candidates stay noisy by design. Output is never auto-labelled as verified.
- Counting "projects with any candidate" as coverage overstates accuracy. The eval measures hit@5 against known answers instead.
- My manual write-up said "over $18.5M". The live filter gives $19.80M, because the filter includes `Others` as well as `National NGO`. Always quote the filter with the number.

## Limits

- **Coverage is about half.** Route 1 works only when the narrative names the implementer.
- **Candidates are noisy.** Expect programme terms, ministries and clusters. Ranking helps, it does not decide. The stoplist is English and humanitarian-cluster specific.
- **Arabic is partial.** Names are caught only after a marker word (منظمة, جمعية, مؤسسة, شبكة, مبادرة, تحالف, مركز).
- **Pseudonyms are not anonymous.** They are an unsalted hash of the partner code. Anyone with the public CBPF CSV can recompute them. They hide names from casual readers, not from a motivated one.
- **The eval is tiny.** Two data points, and the golden file is private.
- **Third-party dependency.** d-portal is not run by this project. Calls are cached under `out/cache/` and rate limited to one every 0.5 s. The official IATI Datastore needs a free subscription key and is not used.
- **Publication lag.** IATI data appears after the grant. The newest grants may have no narrative yet.
- **Donor pages change.** The playbook's URLs and extraction notes need rechecking.

## Read before you use it

`ETHICS.md`. This method can expose organizations that donors masked to protect staff from arrest or targeting. The repo ships code and method only, and fixtures are synthetic. Do not publish names you have not confirmed, and think about whether naming an organization helps or harms it. Contact organizations only through channels they publish, and never tell them you found them in a masked source.

## Layout

| Path | Role |
| :-- | :-- |
| `AGENTS.md` | Rules and workflow for any AI agent |
| `docs/PLAYBOOK.md` | Step-by-step procedure, including per-donor steps |
| `docs/organizations.schema.md` | Schema of the final file, with templates |
| `csodisc/cbpf.py` | HDX download and redaction filter |
| `csodisc/iati.py` | d-portal fetch, entity cleanup, candidate ranking |
| `csodisc/pipeline.py` | join, aggregate, write CSVs |
| `csodisc/merge.py` | assemble `organizations.csv` from confirmed rows, with evidence gates |
| `csodisc/export.py` | redacted-by-default export, opt-in reveal with evidence gate |
| `tests/` | gate tests on synthetic fixtures, no network |
| `evals/live_eval.py` | periodic hit@5 check against a private golden file |
| `skills/sudan-cso-discovery/` | Claude Code skill, a pointer to the files above |
| `ETHICS.md` | what to consider before using or sharing output |

## Not built yet

- IATI publishers beyond OCHA (FCDO, EU).
- A way to store the evidence quote automatically during verification.
- An Arabic stoplist.
- Per-donor adapters for the registries in Route 2.

## License

MIT. See `LICENSE`.
