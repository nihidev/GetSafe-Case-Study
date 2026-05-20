{{
    config(
        materialized='incremental',
        unique_key=['user_id', 'activity_date'],
        incremental_strategy='delete+insert',
        on_schema_change='sync_all_columns',
        tags=['gold', 'kpi']
    )
}}

/*
    Part II KPI mart. Grain: one row per (user_id, activity_date).

    The core idea is a date spine: we explode each customer's active window
    (started_at → churned_at) into one row per day. All three required KPIs then
    reduce to a simple filter + SUM or COUNT, which is exactly what BI tools can do.

    KPI 1 — active customers per day + product group:
        select activity_date, product_group, count(distinct user_id)
        from gold_fct_customer_activity_daily
        where activity_date = :date
        group by 1, 2

    KPI 2 — premium collected in a date range:
        select product_group, sum(daily_premium)
        from gold_fct_customer_activity_daily
        where activity_date between :start and :end
        group by 1

    KPI 3 — accumulated premium from day 0 until a date:
        select user_id, sum(daily_premium)
        from gold_fct_customer_activity_daily
        where activity_date <= :target_date
        group by 1

    Retroactive churn: when churned_at is backdated, the incremental
    delete+insert strategy removes the now-invalid future rows for that customer
    and re-inserts the corrected window. No full table recompute needed.

    Scale: partition by activity_month. Incremental runs only reprocess customers
    whose updated_at changed since the last run.

    Note: the FROM clause below uses sample data to demonstrate the design.
    In production, replace "silver.customers" with ref('silver_customers').
*/

with customers as (

    -- Sample data illustrating the design. In production swap this for:
    --   select * from ref('silver_customers')
    --   (with the incremental filter on updated_at uncommented below)
    select *
    from (values
        ('USR001', date '2025-01-15', date '2025-02-01', null,              9.99,  'liability'),
        ('USR002', date '2025-01-20', date '2025-02-01', date '2025-04-30', 14.99, 'liability'),
        ('USR003', date '2025-03-01', date '2025-03-15', date '2025-06-30', 7.50,  'household'),
        ('USR004', date '2025-02-10', date '2025-02-15', null,              12.00, 'household'),
        ('USR005', date '2025-01-05', date '2025-01-10', date '2025-03-31', 5.99,  'legal')
    ) t(user_id, acquisition_date, started_at, churned_at, monthly_premium, product_group)

),

date_spine as (

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
        )::date  as activity_date

    from customers c

)

select
    activity_date,
    user_id,
    product_group,
    acquisition_date,
    started_at,
    churned_at,

    -- daily_premium = monthly / days_in_month
    -- ensures sum(daily_premium) over any full month equals monthly_premium exactly
    round(monthly_premium / day(last_day(activity_date)), 6)    as daily_premium,

    monthly_premium,
    (activity_date - acquisition_date)                          as days_since_acquisition,
    strftime(activity_date, '%Y-%m')                            as activity_month,
    current_timestamp                                           as _loaded_at

from date_spine
