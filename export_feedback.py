#!/usr/bin/env python3
"""
export_feedback.py

Periodically exports all rows from the `votes` table in PostgreSQL
to a JSON file at /app/data/fallback/feedback.json. Runs once at startup
and then every hour on the hour.
"""
import os
import json
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from psycopg2.extras import RealDictCursor
from db_manager import DatabaseManager

# Configuration
OUTPUT_DIR = "/app/data/fallback"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "feedback.json")
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"

# Setup logging
logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
logger = logging.getLogger(__name__)

def dump_feedback():
    """Query all feedback rows and write them out as JSON atomically."""
    try:
        # Ensure output directory exists
        os.makedirs(OUTPUT_DIR, exist_ok=True)

        # Fetch all rows from votes table
        conn = DatabaseManager.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("SELECT * FROM votes;")
            rows = cursor.fetchall()
        conn.close()

        # Write to a temp file then rename
        temp_file = OUTPUT_FILE + ".tmp"
        with open(temp_file, "w") as f:
            json.dump(rows, f, indent=2, default=str)
        os.replace(temp_file, OUTPUT_FILE)

        logger.info(f"Exported {len(rows)} feedback entries to {OUTPUT_FILE}")
    except Exception as e:
        logger.error(f"Failed to export feedback: {e}", exc_info=True)

if __name__ == "__main__":
    # Run once immediately
    dump_feedback()

    # Schedule hourly on the hour
    scheduler = BlockingScheduler()
    scheduler.add_job(dump_feedback, trigger="cron", minute=0)
    logger.info("Scheduler started: will export feedback hourly at minute 0")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Shutting down scheduler")
