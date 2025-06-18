#!/usr/bin/env python3
"""
Simple script to test database connection using DatabaseManager.
Usage:
  python tets.py
"""
import sys
import logging
from db_manager import DatabaseManager

# Configure basic logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def test_connection():
    try:
        logging.info("Attempting to connect to the database...")
        conn = DatabaseManager.get_connection()
        # psycopg2.connection.closed == 0 means open
        if getattr(conn, 'closed', 1) == 0:
            logging.info("Database connection successful!")
            conn.close()
            sys.exit(0)
        else:
            logging.error("Database connection opened but reported closed state.")
            sys.exit(1)
    except Exception as e:
        logging.error(f"Database connection failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    test_connection()
