{{ config(materialized='incremental', schema='mart',
    unique_key='order_id') }}

select * from {{ ref('orders') }}

{% if is_incremental() %}
where transformed_date > (select max(transformed_date) from {{ this }})
{% endif %}