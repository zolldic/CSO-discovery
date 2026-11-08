# Ethics and data policy

## Why this exists
OCHA and USAID redact Sudanese partner names under duty of care. Staff of local organizations have been detained, extorted, and targeted by both SAF and RSF. This tool reads public narratives that donors did not redact. That is legal, and it is still dangerous to republish.

## Rules for this repo and its users
1. No dataset of decoded organizations is committed. Fixtures are synthetic. The golden eval file, `verified.csv`, `grants.csv` and everything in `out/` are local and gitignored.
2. Do not publish a decoded partner list, a leadership list, or a security-gap list for named organizations.
3. Prefer organizations that publicly name themselves (own website, donor announcement). Treat everything else as private research.
4. Contact an organization only through channels it publishes. Never reveal that you identified it from a redacted source.
5. If an organization asks to be removed from your notes, delete it.
6. Do not record or share locations, staff names, or field identities found along the way.

## Redact or reveal is the researcher's choice
`python3 -m csodisc.export` writes pseudonyms by default. `--reveal` names only partners listed in `verified.csv` with an `evidence_url`. The tool makes the choice explicit and gated. It does not make revealing safe: the researcher owns that decision and its consequences.

## Reporting a problem
If this tool or its documentation exposes someone who should be protected, open an issue titled "safety" without naming the person, and the maintainer will remove the material.
