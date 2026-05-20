# Getsafe Analytics Engineering Case Study

**Stack:** Python 3.11 · DuckDB · dbt-duckdb · dbt_utils

---

## Setup

```bash
pip install dbt-duckdb duckdb

# 1. Load the source CSV into DuckDB (creates the database the dbt models build on)
python analysis/setup_db.py --csv /path/to/raw_transaction_data.csv

# 2. Build the dbt models
cd dbt
dbt deps
dbt seed         # loads the accounting benchmark
dbt run          # builds bronze → silver → gold
dbt test         # runs data quality checks
```

The DuckDB file is created at `data/duckdb/getsafe.duckdb` (configurable via `GETSAFE_DB_PATH` env var in profiles.yml).

To run the reconciliation analysis standalone (no DuckDB setup needed — works entirely in-memory):

```bash
python analysis/reconciliation.py
```

---

## Part I: Data Modeling

### Architecture

I used a Medallion architecture (Bronze → Silver → Gold) with dbt models for each layer:

- **Bronze** (`bronze_raw_transactions`): exact copy of the source CSV with provenance metadata added
- **Silver** (`silver_transactions`): cleaned and typed — parses timestamps, casts numeric fields, normalizes the status column, adds DQ flags
- **Gold** (`gold_fct_monthly_premiums`): the actual data mart answering Part I

This separation pays off even for a small dataset: if the source CSV format changes, only the Bronze model needs updating. Silver and Gold stay stable.

### The Data Mart

`gold_fct_monthly_premiums` produces one row per `(party, month)` with the following key columns:

| Column | Description |
|---|---|
| `party` | Insurance partner (berlinre, dronant, getland, liadigital) |
| `month` | YYYY-MM format (e.g., 2025-06) |
| `premium` | Gross written premium in EUR |
| `earned_premium` | Prorated premium based on days remaining in month |
| `transaction_count` | Number of transactions in the aggregate |

**Status filter:** Only `status = 'processed'` rows are included. The source data also contains a `process` variant which appears to be a misspelling — I normalize this to `processed` in the Silver layer and include it in the premium sum. This decision reduces the total reconciliation gap from ~EUR 269 to EUR 37.94.

**Timestamp format:** The `created_at` column uses US locale format (`M/D/YYYY H:MM:SS`), parsed with `strptime(..., '%m/%d/%Y %H:%M:%S')`.

### Reconciliation Process

The reconciliation model (`gold_fct_accounting_reconciliation`) joins the Finance mart against the accounting benchmark (loaded as a dbt seed) and computes a delta for each `(party, month)`:

```
delta = finance_premium - accounting_premium
```

Rows are classified as:
- `MATCH` — delta < EUR 0.01
- `NEAR_MATCH` — delta < 1% of accounting figure
- `DISCREPANCY` — delta ≥ 1%

In production I'd hook this model into a monitoring alert (Slack/email) so Finance gets notified when any row hits `DISCREPANCY` status at month close.

### Findings

Running the model against the provided benchmark:

| Party | Month | Accounting | Finance | Delta | Status |
|---|---|---|---|---|---|
| berlinre | 2025-06 | 1,483.22 | 1,476.45 | -6.77 | NEAR_MATCH |
| berlinre | 2025-07 | 1,098.74 | 1,084.40 | -14.34 | DISCREPANCY |
| berlinre | 2025-08 | 714.06 | 714.06 | 0.00 | MATCH |
| dronant | 2025-06 | 2,983.41 | 2,983.41 | 0.00 | MATCH |
| dronant | 2025-07 | 1,780.19 | 1,771.90 | -8.29 | NEAR_MATCH |
| dronant | 2025-08 | 1,107.07 | 1,100.99 | -6.08 | NEAR_MATCH |
| getland | 2025-06 | 1,730.31 | 1,730.31 | 0.00 | MATCH |
| getland | 2025-07 | 1,412.28 | 1,412.28 | 0.00 | MATCH |
| getland | 2025-08 | 660.19 | 660.19 | 0.00 | MATCH |
| liadigital | 2025-06 | 2,241.79 | 2,239.33 | -2.46 | NEAR_MATCH |
| liadigital | 2025-07 | 1,353.47 | 1,353.47 | 0.00 | MATCH |
| liadigital | 2025-08 | 878.49 | 878.49 | 0.00 | MATCH |

**Total discrepancy: EUR 37.94** across 12 party-month combinations. Finance consistently reports *less* than Accounting — the delta is always negative or zero.

#### What could explain the remaining gap?

A few candidates:

1. **Cut-off timing.** Accounting closes on the last calendar day of the month using invoice date; the transaction system may timestamp events in a different timezone or use settlement date rather than booking date. Transactions near month-end could fall on either side depending on the clock used.

2. **Rounding methodology.** If Accounting rounds at the individual transaction level before summing, and Finance sums first then rounds, you get systematic small differences — which matches the pattern here (all discrepancies are small and negative).

3. **Transactions excluded by the DQ filter.** The Silver layer drops rows where `created_at` cannot be parsed or `premium_amount` is null. Any such rows would show up in Accounting's invoice but not in Finance's sum. Checking `_dq_flags IS NOT NULL` on Silver would confirm this.

4. **Retroactive adjustments.** Accounting may have applied adjustments after the raw data was exported. This is harder to detect without a CDC log.

The most likely culprit for the berlinre July gap (EUR 14.34) is timing — it's larger than the others and not explained by rounding. I'd start by pulling berlinre's July transactions that sit within 48 hours of the month boundary and checking their effective dates in the billing system.

#### Potential fixes

- Agree on a single "booking date" definition between Finance and Accounting and document it as a dbt variable (`{{ var('close_cutoff_tz') }}`).
- Add a `net_premium` column to the Gold model that subtracts refunded amounts, in case Accounting nets refunds.
- Enable the dbt snapshot on `silver_transactions` so any retroactive status flips are captured with timestamps — this makes it possible to reconstruct the exact state of the data at any past close date.
- Run the reconciliation check automatically after each `dbt run` and alert on any delta > EUR 1.00.

---

## Part II: KPI Mart

### The Problem

The BI tool can only use `SUM` and `COUNT`. But the question "how many customers were active on date X?" requires checking whether X falls between `started_at` and `churned_at` for each customer — that's a range join, which you can't express with aggregate functions alone.

### The Solution: Date Spine

Pre-explode each customer's active window into one row per day. After that, every KPI becomes a straightforward filter + aggregate.

For a customer active from Jan 1 to Jan 3 with a EUR 30/month premium:

```
activity_date | user_id | product_group | daily_premium
2025-01-01    | USR001  | liability     | 0.967742
2025-01-02    | USR001  | liability     | 0.967742
2025-01-03    | USR001  | liability     | 0.967742
```

`daily_premium = monthly_premium / days_in_month` — this way `SUM(daily_premium)` over any full calendar month equals `monthly_premium` exactly, and partial months are automatically prorated.

### The Three KPI Queries

All three queries use only `SUM` and `COUNT`, as required:

**KPI 1 — Active customers per day and product group:**
```sql
select activity_date, product_group, count(distinct user_id) as active_customers
from gold_fct_customer_activity_daily
where activity_date = '2025-03-15'
group by 1, 2
```

**KPI 2 — Premium collected in a date range:**
```sql
select product_group, round(sum(daily_premium), 2) as premium_collected
from gold_fct_customer_activity_daily
where activity_date between '2025-01-01' and '2025-03-31'
group by 1
```

**KPI 3 — Accumulated premium from the beginning until a given date:**
```sql
select user_id, round(sum(daily_premium), 2) as accumulated_premium
from gold_fct_customer_activity_daily
where activity_date <= '2025-04-30'
group by 1
```

### Handling Retroactive Changes

When a customer cancels retroactively (e.g., `churned_at` is moved from April 30 back to February 28), the mart needs to remove the now-invalid rows for that customer. The dbt model uses `materialized='incremental'` with `incremental_strategy='delete+insert'`:

1. Source system updates `silver.customers` (new `churned_at`, updated `updated_at`)
2. Incremental run detects the change via `updated_at > last run timestamp`
3. `delete+insert` removes all rows for that customer and re-inserts the correct active window

No full table recompute needed — only the affected customer's rows are touched.

Concretely in SQL:
```sql
-- remove rows past the new churn date
delete from gold_fct_customer_activity_daily
where user_id = 'USR002' and activity_date > '2025-02-28';
```

### Scalability

At 1M customers × 3-year average tenure, the table is roughly 1.1B rows. A few things keep this manageable:

- **Partition by `activity_month`**: BI queries always filter by date, so the engine can skip irrelevant months via predicate pushdown.
- **Incremental dbt runs**: nightly jobs only reprocess customers whose `updated_at` changed, not the full 1M.
- **Optional summary layer**: for dashboards that don't need user-level drilldown, pre-aggregate `(activity_date, product_group)` in a separate model. Keep the daily grain as the base layer for ad-hoc queries.

---

## dbt Model Lineage

```
raw_transactions (CSV seed)
        │
        ▼
bronze_raw_transactions
        │
        ▼
silver_transactions
        │
        ├──▶ gold_fct_monthly_premiums ──▶ gold_fct_accounting_reconciliation
        │                                           ▲
        │                                  accounting_closing (seed)
        │
        └──▶ gold_fct_customer_activity_daily
```

---

## Notes on the Part II Dataset

The case study PDF describes the columns for Part II but doesn't include a CSV file. The model `gold_fct_customer_activity_daily` demonstrates the approach using a small sample dataset (5 synthetic customers) that covers the key scenarios: still-active customer, closed contract, mid-month start, and retroactive churn. The logic transfers directly to a real `silver.customers` source — just swap the `FROM` clause to `{{ ref('silver_customers') }}`.
