# Long-run validation box (draft)

Official Geneva prices ↔ professional / national index ↔ Swiss cycle

Series available: bfs_construction_mfh_ch, bfs_impi_condo, bfs_impi_houses, bis_ch_rpp_nominal, bis_ch_rpp_real, ocstat_canton_houses, ocstat_canton_ppe, ocstat_city_ppe, ocstat_construction_housing_ge, ocstat_cpi_geneva, ocstat_cpi_switzerland, ocstat_ppe_implied_m2_existing, ocstat_ppe_implied_m2_new, wuest_houses_lake_geneva, wuest_houses_switzerland, wuest_ppe_lake_geneva, wuest_ppe_switzerland

## ocstat_canton_ppe vs ocstat_city_ppe
- Corr (index 1990=100): 0.998
- Corr (YoY): 0.876
- Direction agreement (YoY): 91% ✓
- CAGR: 2.53% vs 2.89%

## ocstat_canton_ppe vs wuest_ppe_lake_geneva
- Corr (index 1990=100): 0.990
- Corr (YoY): 0.705
- Direction agreement (YoY): 76% ✓
- CAGR: 2.53% vs 2.93%

## ocstat_canton_ppe vs bis_ch_rpp_nominal
- Corr (index 1990=100): 0.960
- Corr (YoY): 0.588
- Direction agreement (YoY): 74% ✓
- CAGR: 2.53% vs 2.38%

## ocstat_canton_ppe vs bfs_impi_condo
- Corr (index 1990=100): 0.997
- Corr (YoY): 0.839
- Direction agreement (YoY): 100% ✓
- CAGR: 2.82% vs 3.62%

## wuest_ppe_lake_geneva vs wuest_ppe_switzerland
- Corr (index 1990=100): 0.986
- Corr (YoY): 0.870
- Direction agreement (YoY): 90% ✓
- CAGR: 3.22% vs 2.79%

## ocstat_canton_ppe vs wuest_ppe_switzerland
- Corr (index 1990=100): 0.964
- Corr (YoY): 0.577
- Direction agreement (YoY): 68% ~
- CAGR: 2.53% vs 2.42%

## wuest_ppe_switzerland vs bis_ch_rpp_nominal
- Corr (index 1990=100): 0.997
- Corr (YoY): 0.835
- Direction agreement (YoY): 90% ✓
- CAGR: 2.79% vs 2.70%

## bfs_impi_condo vs bis_ch_rpp_nominal
- Corr (index 1990=100): 0.998
- Corr (YoY): 0.901
- Direction agreement (YoY): 100% ✓
- CAGR: 3.34% vs 3.47%

## bfs_impi_condo vs wuest_ppe_switzerland
- Corr (index 1990=100): 0.995
- Corr (YoY): 0.718
- Direction agreement (YoY): 100% ✓
- CAGR: 3.54% vs 4.07%

## ocstat_canton_houses vs wuest_houses_lake_geneva
- Corr (index 1990=100): 0.990
- Corr (YoY): 0.662
- Direction agreement (YoY): 79% ✓
- CAGR: 2.50% vs 2.78%

## ocstat_canton_houses vs wuest_houses_switzerland
- Corr (index 1990=100): 0.947
- Corr (YoY): 0.454
- Direction agreement (YoY): 68% ~
- CAGR: 2.50% vs 2.36%

## wuest_houses_lake_geneva vs wuest_houses_switzerland
- Corr (index 1990=100): 0.969
- Corr (YoY): 0.646
- Direction agreement (YoY): 78% ✓
- CAGR: 2.84% vs 2.74%

## ocstat_canton_houses vs bfs_impi_houses
- Corr (index 1990=100): 0.974
- Corr (YoY): 0.725
- Direction agreement (YoY): 71% ✓
- CAGR: 3.91% vs 3.77%

## bfs_impi_houses vs wuest_houses_switzerland
- Corr (index 1990=100): 0.994
- Corr (YoY): 0.875
- Direction agreement (YoY): 88% ✓
- CAGR: 3.92% vs 4.34%

## ocstat_cpi_geneva vs ocstat_cpi_switzerland
- Corr (index 1990=100): 0.999
- Corr (YoY): 0.977
- Direction agreement (YoY): 97% ✓
- CAGR: 2.25% vs 2.19%

## ocstat_canton_ppe vs ocstat_construction_housing_ge
- Corr (index 1990=100): 0.928
- Corr (YoY): 0.298
- Direction agreement (YoY): 76% ✓
- CAGR: 2.53% vs 1.33%

## ocstat_construction_housing_ge vs bfs_construction_mfh_ch
- Corr (index 1990=100): 0.982
- Corr (YoY): 0.806
- Direction agreement (YoY): 79% ✓
- CAGR: 1.98% vs 1.33%

- OCSTAT canton/city PPE: existing+libre from 2006; earlier years use ensemble layout (documented in segment).
- OCSTAT houses: CHF/object (thousands); prefer non-neuves from ~2004, else ensemble — not CHF/m².
- OCSTAT = observed transaction median; Wüest = quality-adjusted hedonic index — levels need not match.
- BIS CH historically related to Wüest nationally — use as open control, not fully independent of Wüest CH.
- Dating: OCSTAT year T = calendar-year transaction median; Wüest = published annual (1985=100); BIS/BFS IMPI = year-end Q4.
- BFS IMPI condo (EGW) / houses (EFH) start ~2017; compare via index_2017 / recent-window charts.
- Deflator: OCSTAT Geneva CPI annual mean (T_05_02_02); index_real_1990 = index_1990 / CPI_1990 * 100.
- Construction: OCSTAT housing construction (T_05_03_1_01, Oct preferred); BFS CH Neubau Mehrfamilienhaus from 1998.
- Implied PPE size (m²): median kCHF×1000 / median CHF/m² from T_05_05_1_4_01 (neufs vs non-neufs, ~2006+).