# `organizations.csv` schema

The final product: one row per organization-and-grant. Written by `python3 -m csodisc.merge` into `out/organizations.csv` (private, gitignored). It is built from two files you or an agent write after reading evidence:

- `verified.csv` for OCHA partners decoded from IATI. Template: `docs/verified.template.csv`.
- `grants.csv` for grantees a donor names itself. Template: `docs/grants.template.csv`.

A row with no `http(s)` `evidence_url` is rejected. Never leave it blank to "fill in later".

## `verified.csv` columns

| Column | Rule |
| :-- | :-- |
| `partner_code` | The CBPF `PartnerCode` exactly as in `out/partners.csv`. Must exist there. |
| `confirmed_name` | The organization's own name, as it writes it. |
| `evidence_url` | Page where the name and the project link are visible (the d-portal activity or the org's own page). |
| `confidence` | `high` (narrative names the org as the implementer), `medium`, `low`. |

Amount and period are not typed here. The merge step takes them from `partners.csv` and `projects.csv` so the totals cannot be mistyped.

## `grants.csv` columns

| Column | Rule |
| :-- | :-- |
| `name` | Organization name as the donor prints it. |
| `domain` | Sector: `governance`, `peacebuilding`, `human_rights`, `womens_rights`, `media`, `humanitarian_mutual_aid`, `protection`, `mine_action`, `mental_health`, or a short phrase. |
| `base` | `Sudan`, `Kampala`, `Nairobi`, or a list joined with `;`. Only what the org publishes about itself. No street addresses or staff locations. |
| `donor` | The funder. |
| `funding_type` | `direct` (donor grant to this org), `sub_grant` (via a consortium lead), `thematic` (same theme only, no relationship shown). |
| `amount`, `currency` | As published. Leave blank if not published. Do not estimate. |
| `period` | As published, e.g. `2026-09` or `2025-01..2027-12`. |
| `evidence_url` | The donor page naming the grant. |
| `evidence_quote` | A short quote from that page. |

## `organizations.csv` output columns

`name, domain, base, donor, funding_type, amount, currency, period, evidence_url, evidence_quote, source, partner_code, status, publishable`

- `source`: `cbpf_decoded` or `donor_published`.
- `status`: `verified` for every row that survives the gates.
- `publishable`: `no` for every `cbpf_decoded` row (the donor masked it). `yes` for donor-published rows, because the donor itself named the grantee. Check `ETHICS.md` before relying on `yes`.
- Funding type matters. A `sub_grant` or `thematic` row must not be described as a direct donor relationship in outreach.
