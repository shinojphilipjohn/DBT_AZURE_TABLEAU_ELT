SELECT
geolocation_zip_code_prefix as zip_code,
	geolocation_lat as latitude,
	geolocation_lng	 as longitude,
    geolocation_city as city,
	geolocation_state as state,
	GETUTCDATE() as transformed_date
    from {{ source('olist', 'olist_geolocation') }}