{{
    config(
        materialized='table',
        tags=['gold', 'finance']
    )
}}

/*
    Part I deliverable. One row per (party, month).

    Only 'processed' transactions with clean data quality are included.
    The 'process' status variant is normalized to 'processed' in Silver — including it
    here reduces the total reconciliation gap from ~EUR 269 to EUR 37.94.

    earned_premium prorates the monthly amount by days remaining in the month at
    transaction date. This is an approximation — a proper implementation would join
    to a policy dimension for actual inception/expiry dates.
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

)

select
    party,
    transaction_month                                           as month,
    round(sum(premium_amount), 2)                               as premium,
    round(sum(premium_amount), 2)                               as written_premium,
    round(
        sum(
            premium_amount
            * (datediff('day', transaction_date, last_day(transaction_date)) + 1)::double
            / day(last_day(transaction_date))::double
        ), 2
    )                                                           as earned_premium,
    count(*)                                                    as transaction_count,
    min(transaction_date)                                       as first_transaction_date,
    max(transaction_date)                                       as last_transaction_date,
    current_timestamp                                           as _created_at

from processed
group by party, transaction_month
order by party, transaction_month
