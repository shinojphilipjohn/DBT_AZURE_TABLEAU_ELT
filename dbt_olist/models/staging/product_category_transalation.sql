SELECT
	product_category_name_english as category_name_english,
	GETUTCDATE() as transformed_date
    from {{ source('olist', 'product_category_name_translation') }}