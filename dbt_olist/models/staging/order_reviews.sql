SELECT
review_id,
	order_id,
	review_score,
	coalesce(review_comment_title,'No Comment Tile') as review_comment_title,
    coalesce(review_comment_message,'No Comment') as review_comment_message,
	CAST( review_creation_date AS DATETIME2) as review_creation_date,
	CAST(review_answer_timestamp AS DATETIME2) as review_answer_timestamp,
	GETUTCDATE() as transformed_date
    from {{ source('olist', 'olist_order_reviews') }}