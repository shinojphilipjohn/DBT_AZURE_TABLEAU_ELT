SELECT
order_id,
	order_item_id as item_id,
	product_id,
	seller_id,
	CAST(shipping_limit_date AS DATETIME2) as shipping_limit_date,
	price,
	freight_value,
	GETUTCDATE() as transformed_date
    from {{ source('olist', 'olist_order_items') }}