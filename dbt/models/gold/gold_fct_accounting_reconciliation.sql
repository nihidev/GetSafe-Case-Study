{{
    config(
        materialized='table',
        tags=['gold', 'finance', 'reconciliation']
    )
}}

/*
    Finance vs Accounting comparison for monthly close.
    One row per (party, month) — same grain as the accounting benchmark.

    Comparison uses written_premium (gross), not net_premium.
    Netting refunds increases the gap, which confirms Accounting reports
    gross written premium — the correct basis for this comparison.

    delta > 0  → Finance reports more than Accounting
    delta < 0  → Finance reports less (consistent pattern in this dataset)

    Tiers:
        MATCH       — |delta| < EUR 0.01
        NEAR_MATCH  — |delta| < 1% of accounting figure
        DISCREPANCY — |delta| >= 1%

    Remaining EUR 37.94 gap (0.28% of total): most likely a timing cutoff.
    Accounting closes on invoice date; Finance uses the transaction timestamp.
    Transactions booked near month-end may land in different periods depending
    on which clock is used. Confirm by pulling boundary transactions from the
    billing system and comparing their invoice dates.
*/

with accounting as (

    select party, month, accounting_premium
    from {{ ref('accounting_closing') }}

),

finance as (

    select
        party,
        month,
        written_premium,
        net_premium,
        refunded_premium,
        transaction_count

    from {{ ref('gold_fct_monthly_premiums') }}

),

reconciled as (

    select
        a.party,
        a.month,
        a.accounting_premium,
        coalesce(f.written_premium, 0.0)                        as finance_premium,
        coalesce(f.net_premium, 0.0)                            as net_premium,
        coalesce(f.refunded_premium, 0.0)                       as refunded_premium,
        coalesce(f.transaction_count, 0)                        as transaction_count,

        -- Primary delta: gross written vs accounting
        round(coalesce(f.written_premium, 0.0) - a.accounting_premium, 2) as delta,

        round(
            abs(coalesce(f.written_premium, 0.0) - a.accounting_premium)
            / nullif(a.accounting_premium, 0) * 100,
            4
        )                                                       as delta_pct,

        -- Net delta: shows refund netting makes the gap wider,
        -- confirming Accounting uses gross written premium
        round(coalesce(f.net_premium, 0.0) - a.accounting_premium, 2) as net_delta,

        case
            when abs(coalesce(f.written_premium, 0.0) - a.accounting_premium) < 0.01
                then 'MATCH'
            when abs(coalesce(f.written_premium, 0.0) - a.accounting_premium)
                / nullif(a.accounting_premium, 0) < 0.01
                then 'NEAR_MATCH'
            else 'DISCREPANCY'
        end                                                     as reconciliation_status,

        abs(coalesce(f.written_premium, 0.0) - a.accounting_premium) < 0.01 as is_reconciled

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
    net_premium,
    refunded_premium,
    net_delta,
    transaction_count,
    delta,
    delta_pct,
    reconciliation_status,
    is_reconciled,
    current_timestamp as _reconciled_at

from reconciled
order by party, month
