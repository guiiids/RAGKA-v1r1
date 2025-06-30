# Database Migration Instructions

To initialize the `helpee_logs` table and add the `model` column in your production database, please run the following SQL commands in your production PostgreSQL database environment:

```sql
-- Create helpee_logs table if it does not exist
CREATE TABLE IF NOT EXISTS helpee_logs (
    id SERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT now(),
    user_query TEXT NOT NULL,
    response_text TEXT NOT NULL,
    prompt_tokens INT,
    completion_tokens INT,
    total_tokens INT
);

-- Add model column to helpee_logs table
ALTER TABLE helpee_logs
  ADD COLUMN IF NOT EXISTS model TEXT NOT NULL DEFAULT ''X;

-- Create helpee_costs table if it does not exist
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
```

---

## How to Execute These SQL Commands

1. **Using psql command-line tool:**
   - Open a terminal.
   - Connect to your database with:
     ```
     psql -h your_db_host -U your_db_user -d your_db_name
     ```
   - Enter your password when prompted.
   - Copy and paste the above SQL commands into the psql prompt and press Enter to execute them.

2. **Using a GUI database client:**
   - Use tools like pgAdmin, DBeaver, or TablePlus.
   - Connect to your production database.
   - Open a new SQL query window.
   - Paste the SQL commands and run them.

3. **Using a Python script:**
   - If you prefer, I can help you write a Python script to run these migrations programmatically.

---

# Summary of Fixes

- Updated `main.py` to import and instantiate `FlaskRAGAssistantWithHistory` instead of `FlaskRAGAssistantGPT` to fix the `NameError`.
- Provided SQL commands to initialize the required database tables and columns to resolve database errors.
- The new double wand icon feature is integrated in the current codebase and should work once the above fixes are applied.

Please apply the database migrations and redeploy your application. This should resolve the 504 Gateway Timeout and related errors.

If you need further assistance running the migrations or any other help, please let me know.