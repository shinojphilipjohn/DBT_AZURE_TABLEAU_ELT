SELECT
product_id,
	product_category_name,
	product_name_lenght as product_name_length,
	product_description_lenght as product_description_length,
    product_photos_qty,
    CAST(product_weight_g AS FLOAT)/1000 as product_weight_kg,
    CAST(product_length_cm AS FLOAT)/100 as product_length_m,
    CAST(product_height_cm AS FLOAT)/100 as product_height_m,
    CAST(product_width_cm AS FLOAT)/100 as product_width_m,
	GETUTCDATE() as transformed_date
    from {{ source('olist', 'olist_products') }}