-- Migration: add model column to helpee_logs and create helpee_costs table
BEGIN;

-- Add a model column to helpee_logs for per-model cost tracking
ALTER TABLE helpee_logs
  ADD COLUMN model TEXT NOT NULL DEFAULT '';

-- Create helpee_costs table to store detailed cost breakdowns
CREATE TABLE IF NOT EXISTS helpee_costs (
  id SERIAL PRIMARY KEY,
  helpee_log_id INTEGER NOT NULL REFERENCES helpee_logs(id),
  model TEXT NOT NULL,
  prompt_tokens INT,
  completion_tokens INT,
  total_tokens INT,
  prompt_cost NUMERIC,
  completion_cost NUMERIC,
  total_cost NUMERIC,
  timestamp TIMESTAMPTZ NOT NULL DEFAULT now()
);

COMMIT;