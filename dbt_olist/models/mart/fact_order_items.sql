{{ config(materialized='incremental', schema='mart', unique_key=['order_id', 'item_id']) }}

select * from {{ ref('order_items') }}

{% if is_incremental() %}
where transformed_date > (select max(transformed_date) from {{ this }})
{% endif %}