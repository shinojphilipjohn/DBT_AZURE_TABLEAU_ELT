with customer as 
(SELECT 
customer_id,
unique_id,
zip_code
from {{ ref('customer') }}
)
,geo_freq as (
SELECT
zip_code,
avg(latitude) as latitude,
avg(longitude) as longitude,
city,
state,
count(*) as freq
from {{ ref('geolocation') }}
group by zip_code,state,city
),
zip_code_filter as(
    SELECT
zip_code,
latitude,
longitude,
city,
state,
ROW_NUMBER() over( PARTITION BY zip_code order by freq desc) as rn
from geo_freq
)
, geo as(
select 
zip_code,
latitude,
longitude,
city,
state
from zip_code_filter
where rn=1)

select 
c.customer_id,
c.unique_id,
c.zip_code,
g.latitude,
g.longitude,
g.city,
g.state,
GETUTCDATE() as transformed_date
from customer c
left join geo g
on c.zip_code=g.zip_code
