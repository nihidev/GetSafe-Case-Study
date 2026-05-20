#!/usr/bin/env bash
set -euo pipefail

# Run the full Getsafe analytics case study end to end.
# Usage: bash run_all.sh --csv "/path/to/raw_transaction_data.csv"

CSV_PATH=""

for arg in "$@"; do
  case $arg in
    --csv=*) CSV_PATH="${arg#*=}" ;;
    --csv)   CSV_PATH="${2:-}"; shift ;;
  esac
  shift || true
done

if [[ -z "$CSV_PATH" ]]; then
  echo "Usage: bash run_all.sh --csv \"/path/to/raw_transaction_data.csv\""
  exit 1
fi

ROOT="$(cd "$(dirname "$0")" && pwd)"
DBT_DIR="$ROOT/dbt"

echo "=================================================="
echo " Getsafe Analytics Case Study"
echo "=================================================="
echo ""

# ── Step 1: Load CSV into DuckDB ──────────────────────
echo "[1/5] Loading source CSV into DuckDB..."
python "$ROOT/analysis/setup_db.py" --csv "$CSV_PATH"
echo ""

# ── Step 2: Install dbt dependencies ─────────────────
echo "[2/5] Installing dbt packages..."
cd "$DBT_DIR"
dbt deps --quiet
echo ""

# ── Step 3: Run dbt (seed → run → test) ──────────────
echo "[3/5] Running dbt pipeline..."
dbt seed  --quiet
dbt run
echo ""

echo "[4/5] Running dbt tests..."
dbt test
echo ""

# ── Step 4: Standalone analysis scripts ──────────────
echo "[5/5] Running analysis scripts..."
cd "$ROOT"
echo ""
echo "--- Reconciliation analysis ---"
python analysis/reconciliation.py

echo ""
echo "--- KPI mart demo ---"
python analysis/kpi_mart_demo.py

echo ""
echo "=================================================="
echo " Done. Query results:"
echo ""
echo "  duckdb data/duckdb/getsafe.duckdb"
echo ""
echo "  SELECT * FROM main_gold.gold_fct_monthly_premiums ORDER BY party, month;"
echo "  SELECT party, month, delta, reconciliation_status"
echo "    FROM main_gold.gold_fct_accounting_reconciliation ORDER BY party, month;"
echo "=================================================="
