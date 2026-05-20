import argparse
import duckdb
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "duckdb" / "getsafe.duckdb"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--csv", required=True, help="Path to the raw transaction CSV")
    args = parser.parse_args()

    csv_path = Path(args.csv)
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(DB_PATH))

    con.execute("create schema if not exists bronze")
    con.execute("create schema if not exists silver")
    con.execute("create schema if not exists gold")
    con.execute("create schema if not exists seeds")
    con.execute("create schema if not exists snapshots")

    con.execute(f"""
        create or replace table bronze.raw_transactions as
        select
            *,
            '{csv_path.name}'       as _source_file,
            current_timestamp       as _ingested_at
        from read_csv_auto('{csv_path}', header=true)
    """)

    count = con.execute("select count(*) from bronze.raw_transactions").fetchone()[0]
    print(f"Loaded {count:,} rows into bronze.raw_transactions")
    print(f"DuckDB: {DB_PATH}")
    print("\nRun dbt next:")
    print("  cd dbt && dbt deps && dbt seed && dbt run && dbt test")

    con.close()


if __name__ == "__main__":
    main()
