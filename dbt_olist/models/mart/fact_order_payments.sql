{{ config(materialized='incremental', schema='mart') }}

select * from {{ ref('order_payments') }}

{% if is_incremental() %}
where transformed_date > (select max(transformed_date) from {{ this }})
{% endif %}