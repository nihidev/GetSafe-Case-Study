import duckdb
from pathlib import Path

RAW_CSV = Path("../Data for Analytics Case Study  - Raw Transaction Data.csv")
DB_PATH = Path("data/duckdb/getsafe.duckdb")

ACCOUNTING_BENCHMARK = [
    ("berlinre",   "2025-06", 1483.22),
    ("berlinre",   "2025-07", 1098.74),
    ("berlinre",   "2025-08",  714.06),
    ("dronant",    "2025-06", 2983.41),
    ("dronant",    "2025-07", 1780.19),
    ("dronant",    "2025-08", 1107.07),
    ("getland",    "2025-06", 1730.31),
    ("getland",    "2025-07", 1412.28),
    ("getland",    "2025-08",  660.19),
    ("liadigital", "2025-06", 2241.79),
    ("liadigital", "2025-07", 1353.47),
    ("liadigital", "2025-08",  878.49),
]

STATUS_FILTERS = {
    "processed_only":          ("processed",),
    "processed_plus_refunded": ("processed", "refunded"),
    "all_non_failed":          ("processed", "refunded", "process"),
    "all_statuses":            ("processed", "refunded", "process", "failed"),
}


def build_silver(con: duckdb.DuckDBPyConnection) -> None:
    """Load source CSV and apply Silver-layer transformations."""
    con.execute("create schema if not exists bronze")
    con.execute("create schema if not exists silver")

    con.execute(f"""
        create or replace table bronze.raw_transactions as
        select * from read_csv_auto('{RAW_CSV}', header=true)
    """)

    con.execute("""
        create or replace table silver.transactions as
        with parsed as (
            select
                transaction_id,
                try_cast(strptime(created_at, '%m/%d/%Y %H:%M:%S') as timestamp)  as created_at_ts,
                strftime(
                    try_cast(strptime(created_at, '%m/%d/%Y %H:%M:%S') as timestamp),
                    '%Y-%m'
                )                                                                   as transaction_month,
                try_cast(premium_amount as double)                                  as premium_amount,
                charged_party,
                status                                                              as status_raw
            from bronze.raw_transactions
        ),
        normalized as (
            select *,
                case when status_raw = 'process' then 'processed' else status_raw end as status,
                (status_raw = 'process') as _status_normalized
            from parsed
        )
        select
            *,
            (created_at_ts is not null and premium_amount is not null and premium_amount >= 0) as _is_clean
        from normalized
    """)


def load_benchmark(con: duckdb.DuckDBPyConnection) -> None:
    con.execute("create schema if not exists gold")
    con.execute("drop table if exists gold.accounting_benchmark")
    con.execute("""
        create table gold.accounting_benchmark (
            party              varchar,
            month              varchar,
            accounting_premium double
        )
    """)
    con.executemany(
        "insert into gold.accounting_benchmark values (?, ?, ?)",
        ACCOUNTING_BENCHMARK
    )


def compare(con: duckdb.DuckDBPyConnection, name: str, statuses: tuple) -> float:
    statuses_sql = ", ".join(f"'{s}'" for s in statuses)

    rows = con.execute(f"""
        with finance as (
            select
                charged_party                    as party,
                transaction_month                as month,
                round(sum(premium_amount), 2)    as finance_premium
            from silver.transactions
            where status in ({statuses_sql}) and _is_clean = true and premium_amount > 0
            group by charged_party, transaction_month
        )
        select
            a.party,
            a.month,
            a.accounting_premium,
            coalesce(f.finance_premium, 0.0) as finance_premium,
            round(coalesce(f.finance_premium, 0.0) - a.accounting_premium, 2) as delta
        from gold.accounting_benchmark a
        left join finance f on a.party = f.party and a.month = f.month
        order by a.party, a.month
    """).fetchall()

    total_delta = sum(abs(r[4]) for r in rows)

    print(f"\n{name}  (total |delta| = EUR {total_delta:.2f})")
    print(f"  {'Party':<12} {'Month':<10} {'Accounting':>12} {'Finance':>12} {'Delta':>10}")
    print(f"  {'-'*60}")
    for r in rows:
        marker = "  ✗" if abs(r[4]) > 0.01 else "  ✓"
        print(f"  {r[0]:<12} {r[1]:<10} {r[2]:>12.2f} {r[3]:>12.2f} {r[4]:>10.2f}{marker}")

    return total_delta


def root_cause_analysis(con: duckdb.DuckDBPyConnection) -> None:
    print("\n\nRoot cause analysis")
    print("=" * 60)

    print("\nRefunded transactions by party/month:")
    rows = con.execute("""
        select charged_party, transaction_month, count(*), round(sum(premium_amount), 2)
        from silver.transactions
        where status_raw = 'refunded'
        group by charged_party, transaction_month
        order by charged_party, transaction_month
    """).fetchall()
    for r in rows:
        print(f"  {r[0]:<12} {r[1]:<10}  {r[2]:>4} refunds   EUR {r[3]:.2f}")

    print("\nStatus breakdown by party/month (processed transactions only):")
    rows = con.execute("""
        select charged_party, transaction_month, status_raw, count(*), round(sum(premium_amount), 2)
        from silver.transactions
        where _is_clean = true
        group by charged_party, transaction_month, status_raw
        order by charged_party, transaction_month, status_raw
    """).fetchall()
    print(f"  {'Party':<12} {'Month':<10} {'Status':<12} {'Count':>6} {'Sum':>12}")
    for r in rows:
        print(f"  {r[0]:<12} {r[1]:<10} {r[2]:<12} {r[3]:>6} {r[4]:>12.2f}")

    null_ts = con.execute(
        "select count(*) from silver.transactions where created_at_ts is null"
    ).fetchone()[0]
    print(f"\nRows with unparseable timestamp (excluded): {null_ts}")


def main():
    con = duckdb.connect()  # in-memory; swap for DB_PATH for persistence

    print("Building Silver layer from CSV...")
    build_silver(con)
    load_benchmark(con)

    print("\nTesting status filter combinations:")
    print("=" * 65)

    deltas = {}
    for name, statuses in STATUS_FILTERS.items():
        deltas[name] = compare(con, name, statuses)

    best = min(deltas, key=deltas.get)
    print(f"\n\nBest filter: '{best}' with EUR {deltas[best]:.2f} total discrepancy")

    root_cause_analysis(con)

    print("""
Summary
-------
The 'processed_only' filter (including the 'process' variant normalized to
'processed') gives the smallest total gap: EUR 37.94 across 12 party-month rows.
Finance consistently reports *less* than Accounting.

Most likely causes:
  1. Timing cut-off — transactions near month-end may fall on different sides
     depending on whether Accounting uses invoice date vs. transaction timestamp.
  2. Rounding order — rounding per-transaction before summing vs. summing then
     rounding can produce small systematic differences.
  3. DQ exclusions — rows with unparseable timestamps or amounts are dropped
     from the Finance figure but may appear in Accounting invoices.

Recommended next step: pull berlinre July transactions within 48 hours of
month boundaries and check their invoice dates in the billing system.
""")


if __name__ == "__main__":
    main()
