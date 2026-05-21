select 
order_id,
	customer_id,
	order_status,
	CAST(order_purchase_timestamp AS DATETIME2) as order_purchase_timestamp,
	CAST(order_approved_at AS DATETIME2) as order_approved_at,
	CAST(order_delivered_carrier_date AS DATETIME2) as order_delivered_carrier_date,
	CAST(order_delivered_customer_date AS DATETIME2) as order_delivered_customer_date,
	CAST(order_estimated_delivery_date AS DATETIME2) as order_estimated_delivery_date,
	GETUTCDATE() as transformed_date
    from {{ source('olist', 'olist_orders') }}