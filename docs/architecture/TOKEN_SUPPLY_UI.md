# Tokenomics — Stage 0 baseline (2026-08-25)

Measured on merged main `6786077`, serving stack `/tmp/movrvest-main`,
**rendered DOM at 1280×720** (screenshot first — the pane's viewport
collapses to 0×0 and reported TAO as 7,625px until layout was forced).

Heading today: **"Supply, and what is still to come"**.

| | HYPE | BTC | TAO | ADA |
|---|---:|---:|---:|---:|
| page height | **3,755px** | 2,417px | 1,786px | 2,342px |
| supply section height | **3,262px** | 1,923px | 1,292px | 1,848px |
| rounded boxes in section | **25** | 12 | 10 | 11 |
| paragraphs in section | **60** | 35 | 24 | 32 |
| `<details>` groups | **0** | 0 | 0 | 0 |
| supply figures | **14** | 6 | 6 | 6 |
| pairwise comparisons | **10** | 4 | 3 | 3 |
| unresolved items | 1 | 2 | 1 | 1 |
| caveats | 0 | 0 | 2 | 1 |

The owner's stated baseline (~3,760px, 27 boxes, 72 paragraphs, 0
expandable groups, 14 claims + 10 comparisons) reproduces. My box and
paragraph counts are scoped to the supply `<section>`, which is why
they run slightly under the page-wide figures.

## The shape of the problem

HYPE's 14 figures by typed concept:

| concept | count |
|---|---:|
| `max_supply` | 3 |
| `emitted_supply` | 2 |
| `future_emissions` | 1 |
| `circulating_estimate` | **4** |
| `excluded_balance` | **4** |

- **The protocol maximum renders three times** as separate claim cards
  (`PROTOCOL MAXIMUM 1,000,000,000 HYPE` ×3), then again inside three
  `corroborated` comparison cards. One fact, six boxes.
- **The combinatorial blow-up the ruling names**: 4 circulating readings
  produce **6 pairwise conflict cards** (C(4,2)); 3 max readings produce
  3 corroboration cards. 10 comparisons total, all same-concept on HYPE.
- **4 excluded-balance claims** render as 4 primary cards.

## Typed-carrier finding — the rule fires

`SupplyComparisonResponse` carries `verdict`, `verdict_stated`,
`left_source`, `left_stated`, `right_source`, `right_stated`, `because`
— **and no concept**. Grouping comparisons by concept therefore needs
the smallest typed addition, exactly as the ruling anticipated.

**It must be two-sided, not one.** `compare()` in
`app/domain/supply_semantics.py` returns `COEXIST` when
`left.concept is not right.concept` — *"Different quantities, both able
to be right"* — so a single `concept` field would be false for that
case. **ADA carries a live `coexist` comparison**, so this is not
hypothetical. The carrier will be `left_concept` / `right_concept`,
both read from `SupplyFact.concept`; a comparison groups under a
concept only when both sides share it, and a cross-concept one belongs
to the audit.

Concept mapping in Stage 0 was done by matching source+value **as a
diagnostic only** — that is precisely what the ruling forbids in
production, and the implementation reads the typed carrier instead.

## Corpus controls to protect

- **BTC**: all 4 comparisons `corroborated`, 0 caveats → must stay
  compact and gain **no empty groups** (no `future_emissions`, no
  `excluded_balance` concepts present).
- **TAO**: 2 of 3 comparisons `conflicted`, 2 caveats → must stay honest
  under sparse/conflicting evidence. (Its 21M maximum is genuine, not a
  BTC bleed-through.)
- **ADA**: 1 `coexist` + 1 caveat, all figures dated "15 days ago" →
  every dated/methodological caveat must survive.
