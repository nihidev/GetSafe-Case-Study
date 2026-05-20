{{
    config(
        materialized='table',
        tags=['gold', 'finance', 'reconciliation']
    )
}}

/*
    Finance vs Accounting comparison for monthly close.
    One row per (party, month) — same grain as the accounting benchmark.

    delta > 0  → Finance reports more than Accounting
    delta < 0  → Finance reports less (the pattern we see in this dataset)

    Tiers:
        MATCH       — |delta| < EUR 0.01
        NEAR_MATCH  — |delta| < 1% of accounting figure
        DISCREPANCY — |delta| >= 1%
*/

with accounting as (

    select party, month, accounting_premium
    from {{ ref('accounting_closing') }}

),

finance as (

    select party, month, premium as finance_premium, transaction_count
    from {{ ref('gold_fct_monthly_premiums') }}

),

reconciled as (

    select
        a.party,
        a.month,
        a.accounting_premium,
        coalesce(f.finance_premium, 0.0)                        as finance_premium,
        coalesce(f.transaction_count, 0)                        as transaction_count,

        round(coalesce(f.finance_premium, 0.0) - a.accounting_premium, 2) as delta,

        round(
            abs(coalesce(f.finance_premium, 0.0) - a.accounting_premium)
            / nullif(a.accounting_premium, 0) * 100,
            4
        )                                                       as delta_pct,

        case
            when abs(coalesce(f.finance_premium, 0.0) - a.accounting_premium) < 0.01
                then 'MATCH'
            when abs(coalesce(f.finance_premium, 0.0) - a.accounting_premium)
                / nullif(a.accounting_premium, 0) < 0.01
                then 'NEAR_MATCH'
            else 'DISCREPANCY'
        end                                                     as reconciliation_status,

        abs(coalesce(f.finance_premium, 0.0) - a.accounting_premium) < 0.01 as is_reconciled

    from accounting a
    left join finance f
        on a.party = f.party
        and a.month = f.month

)

select
    party,
    month,
    accounting_premium,
    finance_premium,
    transaction_count,
    delta,
    delta_pct,
    reconciliation_status,
    is_reconciled,
    current_timestamp as _reconciled_at

from reconciled
order by party, month
