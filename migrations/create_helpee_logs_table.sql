CREATE TABLE IF NOT EXISTS helpee_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_query TEXT NOT NULL,
    response_text TEXT NOT NULL,
    prompt_tokens INT,
    completion_tokens INT,
    total_tokens INT
);