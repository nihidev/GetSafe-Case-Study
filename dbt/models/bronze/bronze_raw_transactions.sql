{{
    config(
        materialized='table',
        tags=['bronze']
    )
}}

select
    transaction_id,
    created_at,
    premium_amount,
    premium_currency,
    charged_party,
    status,
    _source_file,
    _ingested_at

from {{ source('raw_data', 'raw_transactions') }}
