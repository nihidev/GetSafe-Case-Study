{% snapshot snp_silver_transactions %}

{{
    config(
        target_schema='snapshots',
        unique_key='transaction_id',
        strategy='check',
        check_cols=['status', 'premium_amount'],
        invalidate_hard_deletes=True
    )
}}

/*
    SCD Type 2 snapshot on silver_transactions.

    Insurance billing systems can retroactively change transaction status (e.g.,
    processed → refunded) or adjust premium amounts after month close. Without a
    snapshot, those changes silently overwrite the current row and it becomes
    impossible to audit what the data looked like at any historical close date.

    Using 'check' on [status, premium_amount]: a new version row is inserted
    whenever either column changes. Each version gets dbt_valid_from / dbt_valid_to
    timestamps so you can reconstruct the exact state at any point in time:

        select *
        from snapshots.snp_silver_transactions
        where dbt_valid_from  <= '2025-08-31'
          and (dbt_valid_to   >  '2025-08-31' or dbt_valid_to is null)

    This is particularly relevant for regulatory reporting (Solvency II, IFRS 17)
    where the auditor may ask "what did your books show as of close date X?"
*/

select
    transaction_id,
    transaction_date,
    transaction_month,
    premium_amount,
    premium_currency,
    party,
    status,
    status_raw,
    _status_normalized,
    _dq_flags,
    _is_clean,
    _bronze_ingested_at,
    _silver_transformed_at

from {{ ref('silver_transactions') }}

{% endsnapshot %}
