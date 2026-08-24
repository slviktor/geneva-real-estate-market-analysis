# Local Wüest exports (git-ignored)

**Do not commit** XLS/CSV here when publishing the public repo.

## Fetch (local analysis)

```bash
python step_1/long_run/scripts/fetch_wuest_local.py
# If download is blocked, re-parse existing XLS:
# python step_1/long_run/scripts/fetch_wuest_local.py --from-local
python step_1/long_run/scripts/transform_long_run.py
python step_1/long_run/scripts/viz_long_run.py
```

Source form: [Wüest Partner — Transaction price index](https://www.wuest.io/online_services_classic/transaktionspreisindex/index_e.phtml)  
(`nutzung=2` apartments · `nutzung=3` houses · Lake Geneva + Switzerland · XLS)

## Files produced

| File | Role |
|------|------|
| `wuest_transaction_ppe_lake_geneva_raw.xls` | raw PPE export |
| `wuest_transaction_houses_lake_geneva_raw.xls` | raw houses export |
| `wuest_ppe_lake_geneva.csv` / `wuest_ppe_switzerland.csv` | PPE annual points |
| `wuest_houses_lake_geneva.csv` / `wuest_houses_switzerland.csv` | houses annual points |
| `*.meta.txt` | retrieval / dating notes |

## Dating

```csv
year,index
1985,100.0
2025,354.8
```

- **Published annual only** (Wüest base 1985=100), as on the export / website.
- Incomplete calendar years are dropped (quarterly present but Q4 missing).
- Charts rebase to **1990 = 100** in transform.
- Details: [`../TIME_ALIGNMENT.md`](../TIME_ALIGNMENT.md).

## Cite on charts

> Source: Wüest Partner.  
> Data used for analysis/visualisation; underlying Wüest Partner dataset is not redistributed.
