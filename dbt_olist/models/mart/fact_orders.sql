{{ config(materialized='incremental', schema='mart') }}

select * from {{ ref('orders') }}

{% if is_incremental() %}
where transformed_at > (select max(transformed_at) from {{ this }})
{% endif %}