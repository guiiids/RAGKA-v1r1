#!/usr/bin/env python3
"""
compute_feedback_metrics.py

Connects to PostgreSQL to fetch feedback entries and parses logs/openai_calls.jsonl
to compute and print:
  - Total feedback count
  - Positive feedback count & percentage
  - Occurrences of a specific question
  - Average total_tokens per OpenAI call

Usage:
  python compute_feedback_metrics.py [--question "your question"]
"""
import os
import json
import argparse
from psycopg2 import connect
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

DB_PARAMS = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'sslmode': os.getenv('POSTGRES_SSL_MODE', 'require')
}

LOG_PATH = os.path.join('logs', 'openai_calls.jsonl')

POSITIVE_INDICATORS = ['good', 'helpful', 'accurate', 'clear', 'looks good']

def get_feedback_rows():
    sql = "SELECT user_query, feedback_tags FROM votes;"
    conn = connect(**DB_PARAMS)
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql)
            return cur.fetchall()
    finally:
        conn.close()

def is_positive(tags):
    if not tags:
        return False
    for tag in tags:
        tl = tag.lower()
        for p in POSITIVE_INDICATORS:
            if p in tl:
                return True
    return False

def parse_openai_calls():
    tokens = []
    if not os.path.exists(LOG_PATH):
        return tokens
    with open(LOG_PATH, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                tot = entry.get('tokens', {}).get('total_tokens')
                if isinstance(tot, (int, float)):
                    tokens.append(tot)
            except json.JSONDecodeError:
                continue
    return tokens

def main():
    parser = argparse.ArgumentParser(description="Compute feedback and token metrics")
    parser.add_argument(
        '--question', '-q',
        default="what is ilab",
        help="Exact user query to count occurrences of"
    )
    args = parser.parse_args()

    # Feedback metrics
    rows = get_feedback_rows()
    total_fb = len(rows)
    pos_count = sum(1 for r in rows if is_positive(r.get('feedback_tags')))
    pos_pct = (pos_count / total_fb * 100) if total_fb else 0.0

    q_lower = args.question.strip().lower()
    q_count = sum(1 for r in rows if (r.get('user_query') or '').strip().lower() == q_lower)

    # Token metrics
    token_list = parse_openai_calls()
    avg_tokens = (sum(token_list) / len(token_list)) if token_list else 0.0

    # Output
    print(f"Total feedback entries: {total_fb}")
    print(f"Positive feedback: {pos_count} ({pos_pct:.1f}%)")
    print(f"Occurrences of “{args.question}”: {q_count}")
    print(f"Average total_tokens per OpenAI call: {avg_tokens:.1f}")

if __name__ == "__main__":
    main()
