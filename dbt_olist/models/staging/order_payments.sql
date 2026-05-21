select
order_id,
	payment_sequential,
	payment_type,
	payment_installments,
	payment_value,
	GETUTCDATE() as transformed_date
    from {{ source('olist', 'olist_order_payments') }}