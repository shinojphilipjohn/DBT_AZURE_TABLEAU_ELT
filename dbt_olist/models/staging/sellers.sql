SELECT
seller_id,
	seller_zip_code_prefix as zip_code,
	seller_city as city,
	seller_state as state,
	GETUTCDATE() as transformed_date
    from {{ source('olist', 'olist_sellers') }}