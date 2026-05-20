{{
    config(
        materialized='table',
        tags=['gold', 'finance']
    )
}}

/*
    Part I deliverable. One row per (party, month).

    Only 'processed' transactions are included (status normalized in Silver —
    'process' variant treated as 'processed', reducing total recon gap to EUR 37.94).

    written_premium = gross amount booked at transaction date
    refunded_premium = sum of refunded amounts in the same period
    net_premium      = written_premium - refunded_premium

    Reconciliation note: the accounting benchmark uses gross written premium,
    so the comparison in gold_fct_accounting_reconciliation uses written_premium.
    net_premium is provided for Finance reporting and BI drilldown.

    earned_premium prorates by days remaining in month at transaction date.
    Production: replace transaction_date with actual policy inception date.
*/

with processed as (

    select
        party,
        transaction_month,
        premium_amount,
        transaction_id,
        transaction_date

    from {{ ref('silver_transactions') }}
    where status = 'processed'
      and _is_clean = true
      and premium_amount > 0

),

refunds as (

    select
        party,
        transaction_month,
        round(sum(premium_amount), 2) as refunded_premium,
        count(*)                      as refund_count

    from {{ ref('silver_transactions') }}
    where status_raw = 'refunded'
      and _is_clean = true
      and premium_amount > 0

    group by party, transaction_month

),

aggregated as (

    select
        party,
        transaction_month                                               as month,
        round(sum(premium_amount), 2)                                   as written_premium,
        round(
            sum(
                premium_amount
                * (datediff('day', transaction_date, last_day(transaction_date)) + 1)::double
                / day(last_day(transaction_date))::double
            ), 2
        )                                                               as earned_premium,
        count(*)                                                        as transaction_count,
        min(transaction_date)                                           as first_transaction_date,
        max(transaction_date)                                           as last_transaction_date

    from processed
    group by party, transaction_month

)

select
    a.party,
    a.month,
    a.written_premium                                                   as premium,
    a.written_premium,
    coalesce(r.refunded_premium, 0)                                     as refunded_premium,
    coalesce(r.refund_count, 0)                                         as refund_count,
    round(a.written_premium - coalesce(r.refunded_premium, 0), 2)      as net_premium,
    a.earned_premium,
    a.transaction_count,
    a.first_transaction_date,
    a.last_transaction_date,
    current_timestamp                                                   as _created_at

from aggregated a
left join refunds r
    on a.party = r.party
    and a.month = r.transaction_month

order by a.party, a.month
