SELECT
prod.product_id,
prod.pro_unique,
prod.product_category_name,
pdcnt.category_name_english,
prod.product_name_length,
prod.product_description_length,
prod.product_photos_qty as product_photos_quantity,
prod.product_weight_kg,
prod.product_length_m,
prod.product_height_m,
prod.product_width_m,
GETUTCDATE() as transformed_date
from {{ ref('products') }} prod
left join 
{{ ref('product_category_name_translation') }} pdcnt
on prod.product_category_name=pdcnt.category_name_spanish