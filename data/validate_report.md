# Validate report

Date: 2026-08-19. Method: [`VALIDATION.md`](VALIDATION.md).

**0 FAIL · 2 WARN · 16 PASS**

## Coverage

- fact_volume: 1108 rows; years Q 2007–2026; Y 1998–2025
- fact_price: 2956 rows; years 1990–2026

| check | status | detail |
| --- | --- | --- |
| extract_inventory | WARN | raw_inventory.json not found — skipped (run extract.py first) |
| unique_grain | PASS | fact_volume dups=0; fact_price dups=0 |
| chf_x1000 | PASS | max |value_chf - kchf*1000| = 0.0 |
| type_fk | PASS | orphan type_id=none |
| geo_fk | PASS | orphan geo_id=none |
| geo_named_match | PASS | unmatched named labels=0 |
| autres_not_mapped | PASS | Autres rows=730; wrongly mapped=0 |
| geneve_6621 | PASS | fact_price rows with geo_id=6621: 146 |
| ensemble_identity | PASS | house/ppe ensemble != parts in 0/156 periods (tol 0.5) |
| q_sum_eq_year | PASS | complete non-provisional years 2007-2024, mismatches=0 |
| quarters_present | PASS | years with <4 quarters: none; provisional years: [2025, 2026] |
| year_continuity | PASS | no holes from series start to last year |
| no_fake_quarters | PASS | quarterly rows before 2007: 0 |
| quartile_order | PASS | p25<=median<=p75 violations 0/2412 |
| median_suppressed_small_n | PASS | n and no median: 301 rows (OCSTAT hides n<10); n>=10 with no median: 0 |
| unit_sanity | PASS | house median CHF 395000-10500000; PPE CHF/m2 2614-12951 |
| canton_ne_geneve | PASS | 2024 PPE existing libre median: canton=10853.0, Geneve=12597.0 |
| commune_panel_sparse | WARN | named communes with prices: 16 (OCSTAT publishes large communes only, not 45) |

## Notes

- Median missing with n<10 is OCSTAT, not a parse hole.
- `Autres communes…` have empty geo_id on purpose.
- Provisional years (`2025 p` in Excel → `is_provisional=1`) are not compared to the annual table.
