import duckdb

# Sample customers — chosen to exercise every edge case in the mart logic.
# USR001: still active, no churn date
# USR002: churned Apr 30 — closed active window
# USR003: started mid-month — tests partial-month proration
# USR004: still active — second household customer so KPI 1 shows count > 1
# USR005: churned Mar 31 — accumulated premium stops at churn date
SAMPLE_CUSTOMERS = [
    ("USR001", "2025-01-15", "2025-02-01", None,         9.99,  "liability"),
    ("USR002", "2025-01-20", "2025-02-01", "2025-04-30", 14.99, "liability"),
    ("USR003", "2025-03-01", "2025-03-15", "2025-06-30", 7.50,  "household"),
    ("USR004", "2025-02-10", "2025-02-15", None,         12.00, "household"),
    ("USR005", "2025-01-05", "2025-01-10", "2025-03-31", 5.99,  "legal"),
]

KPI_QUERIES = {
    "KPI 1 — Active customers per day + product group (Mar 1–5 2025)": """
        select
            activity_date,
            product_group,
            count(distinct user_id)      as active_customers,
            round(sum(daily_premium), 4) as daily_premium_total
        from mart
        where activity_date between '2025-03-01' and '2025-03-05'
        group by activity_date, product_group
        order by activity_date, product_group
    """,
    "KPI 2 — Premium collected per product group in Q1 2025": """
        select
            product_group,
            round(sum(daily_premium), 2) as premium_collected
        from mart
        where activity_date between '2025-01-01' and '2025-03-31'
        group by product_group
        order by product_group
    """,
    "KPI 3 — Accumulated premium per customer up to 2025-04-30": """
        select
            user_id,
            product_group,
            min(started_at)              as started_at,
            max(churned_at)              as churned_at,
            round(sum(daily_premium), 2) as accumulated_premium
        from mart
        where activity_date <= '2025-04-30'
        group by user_id, product_group
        order by user_id
    """,
}


def build_mart(con: duckdb.DuckDBPyConnection) -> int:
    con.execute("""
        create or replace table customers as
        select * from (values
            ('USR001', date '2025-01-15', date '2025-02-01', null,              9.99,  'liability'),
            ('USR002', date '2025-01-20', date '2025-02-01', date '2025-04-30', 14.99, 'liability'),
            ('USR003', date '2025-03-01', date '2025-03-15', date '2025-06-30', 7.50,  'household'),
            ('USR004', date '2025-02-10', date '2025-02-15', null,              12.00, 'household'),
            ('USR005', date '2025-01-05', date '2025-01-10', date '2025-03-31', 5.99,  'legal')
        ) t(user_id, acquisition_date, started_at, churned_at, monthly_premium, product_group)
    """)

    con.execute("""
        create or replace table mart as
        with date_spine as (
            select
                c.user_id,
                c.product_group,
                c.acquisition_date,
                c.started_at,
                c.churned_at,
                c.monthly_premium,
                unnest(
                    generate_series(
                        c.started_at,
                        coalesce(c.churned_at, current_date),
                        interval '1 day'
                    )
                )::date as activity_date
            from customers c
        )
        select
            activity_date,
            user_id,
            product_group,
            acquisition_date,
            started_at,
            churned_at,
            round(monthly_premium / day(last_day(activity_date)), 6) as daily_premium,
            monthly_premium,
            (activity_date - acquisition_date) as days_since_acquisition,
            strftime(activity_date, '%Y-%m')   as activity_month
        from date_spine
    """)

    return con.execute("select count(*) from mart").fetchone()[0]


def run_kpis(con: duckdb.DuckDBPyConnection) -> None:
    for name, sql in KPI_QUERIES.items():
        print(f"\n{name}")
        print("-" * len(name))
        rows = con.execute(sql).fetchall()
        cols = [d[0] for d in con.description]
        print("  " + "  ".join(f"{c:<22}" for c in cols))
        for row in rows:
            print("  " + "  ".join(f"{str(v):<22}" for v in row))


def retroactive_churn_demo(con: duckdb.DuckDBPyConnection) -> None:
    print("\nRetroactive churn demo — USR002 churn date moved from Apr 30 → Feb 28")
    print("-" * 65)

    before = con.execute(
        "select count(*), round(sum(daily_premium), 2) from mart where user_id = 'USR002'"
    ).fetchone()
    print(f"  Before: {before[0]} active days, EUR {before[1]:.2f} accumulated")

    con.execute("update customers set churned_at = date '2025-02-28' where user_id = 'USR002'")
    con.execute("delete from mart where user_id = 'USR002' and activity_date > date '2025-02-28'")

    after = con.execute(
        "select count(*), round(sum(daily_premium), 2) from mart where user_id = 'USR002'"
    ).fetchone()
    print(f"  After:  {after[0]} active days, EUR {after[1]:.2f} accumulated")
    print(f"  Removed {before[0] - after[0]} rows, EUR {before[1] - after[1]:.2f} refunded")
    print("  No full recompute — only USR002's future rows were deleted.")
    print()
    print("  In dbt this is handled automatically by:")
    print("    materialized='incremental', incremental_strategy='delete+insert'")
    print("  When silver.customers.updated_at changes, the incremental run detects")
    print("  the affected customer and re-inserts only their corrected window.")


def main():
    con = duckdb.connect()

    total_rows = build_mart(con)
    print(f"Mart built: {total_rows:,} rows ({len(SAMPLE_CUSTOMERS)} customers, daily grain)\n")

    run_kpis(con)
    retroactive_churn_demo(con)


if __name__ == "__main__":
    main()
