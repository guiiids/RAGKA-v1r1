SELECT vote_id,
       user_query,
       bot_response,
       evaluation_json,
       feedback_tags,
       comment,
       "timestamp"
FROM public.votes
LIMIT 1000;