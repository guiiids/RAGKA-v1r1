# Phase 3 Implementation Guide: Database Schema Enhancement

**Date:** June 22, 2025  
**Version:** 1.0  
**Related Documents:** 
- [Analytics Logging Strategy](analytics_logging_strategy.md)
- [RAG Analytics Implementation Plan](rag_analytics_implementation_plan.md)
- [Phase 1 Implementation Guide](phase1_implementation_guide.md)
- [Phase 2 Implementation Guide](phase2_implementation_guide.md)

## Overview

This document provides detailed implementation guidance for Phase 3 of the RAG Analytics Logging System. Phase 3 focuses on creating a robust database structure to store and analyze the collected metrics from Phases 1 and 2.

## Prerequisites

Before beginning Phase 3 implementation, ensure you have:

1. Successfully completed Phase 2 implementation
2. Verified that the comprehensive instrumentation is working correctly
3. Confirmed that the error tracking system is functioning properly
4. Created backups of the current database schema and data

## Implementation Steps

### 1. Enhanced Database Schema

#### 1.1 Create RAG Query Performance Table

Create a new SQL file called `rag_query_performance_schema.sql`:

```sql
-- Create table for RAG query performance metrics
CREATE TABLE IF NOT EXISTS rag_query_performance (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    user_query TEXT NOT NULL,
    
    -- Latency metrics
    embedding_time_ms INTEGER,
    search_time_ms INTEGER,
    context_prep_time_ms INTEGER,
    llm_time_ms INTEGER,
    post_processing_time_ms INTEGER,
    total_time_ms INTEGER,
    
    -- Token metrics
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    
    -- Retrieval metrics
    num_chunks_retrieved INTEGER,
    num_chunks_cited INTEGER,
    avg_chunk_relevance FLOAT,
    
    -- Response metrics
    response_length INTEGER,
    has_citations BOOLEAN,
    num_citations INTEGER,
    
    -- Feedback metrics (updated later)
    feedback_id INTEGER,
    feedback_positive BOOLEAN,
    feedback_tags TEXT[],
    
    -- Raw data references
    log_file_path TEXT,
    log_line_number INTEGER
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_rag_query_performance_request_id ON rag_query_performance(request_id);
CREATE INDEX IF NOT EXISTS idx_rag_query_performance_timestamp ON rag_query_performance(timestamp);
CREATE INDEX IF NOT EXISTS idx_rag_query_performance_feedback_id ON rag_query_performance(feedback_id);
```

#### 1.2 Create Token Usage Aggregation Table

Create a new SQL file called `token_usage_schema.sql`:

```sql
-- Create table for token usage aggregation
CREATE TABLE IF NOT EXISTS token_usage_daily (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    model_name TEXT NOT NULL,
    prompt_tokens BIGINT NOT NULL DEFAULT 0,
    completion_tokens BIGINT NOT NULL DEFAULT 0,
    total_tokens BIGINT NOT NULL DEFAULT 0,
    estimated_cost NUMERIC(10,4) NOT NULL DEFAULT 0,
    UNIQUE (date, model_name)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_token_usage_daily_date ON token_usage_daily(date);
CREATE INDEX IF NOT EXISTS idx_token_usage_daily_model_name ON token_usage_daily(model_name);
```

#### 1.3 Create Latency Metrics Table

Create a new SQL file called `latency_metrics_schema.sql`:

```sql
-- Create table for latency metrics aggregation
CREATE TABLE IF NOT EXISTS latency_metrics (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    hour INTEGER NOT NULL,
    component TEXT NOT NULL,  -- 'embedding', 'search', 'context', 'llm', 'post', 'total'
    avg_time_ms FLOAT NOT NULL,
    min_time_ms FLOAT NOT NULL,
    max_time_ms FLOAT NOT NULL,
    p50_time_ms FLOAT NOT NULL,
    p90_time_ms FLOAT NOT NULL,
    p95_time_ms FLOAT NOT NULL,
    p99_time_ms FLOAT NOT NULL,
    count INTEGER NOT NULL,
    UNIQUE (date, hour, component)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_latency_metrics_date ON latency_metrics(date);
CREATE INDEX IF NOT EXISTS idx_latency_metrics_component ON latency_metrics(component);
```

#### 1.4 Create Query Patterns Table

Create a new SQL file called `query_patterns_schema.sql`:

```sql
-- Create table for query patterns analysis
CREATE TABLE IF NOT EXISTS query_patterns (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    query_hash TEXT NOT NULL,  -- Hash of normalized query
    query_template TEXT NOT NULL,  -- Normalized query with placeholders
    count INTEGER NOT NULL,
    avg_tokens INTEGER NOT NULL,
    avg_response_time_ms FLOAT NOT NULL,
    UNIQUE (date, query_hash)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_query_patterns_date ON query_patterns(date);
CREATE INDEX IF NOT EXISTS idx_query_patterns_query_hash ON query_patterns(query_hash);
```

#### 1.5 Create User Feedback Table

Create a new SQL file called `user_feedback_schema.sql`:

```sql
-- Create table for user feedback
CREATE TABLE IF NOT EXISTS user_feedback (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    feedback_positive BOOLEAN NOT NULL,
    feedback_comment TEXT,
    feedback_tags TEXT[],
    follow_up_question TEXT,
    session_id TEXT,
    UNIQUE (request_id)
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_user_feedback_request_id ON user_feedback(request_id);
CREATE INDEX IF NOT EXISTS idx_user_feedback_timestamp ON user_feedback(timestamp);
CREATE INDEX IF NOT EXISTS idx_user_feedback_session_id ON user_feedback(session_id);
```

#### 1.6 Create Database Views

Create a new SQL file called `analytics_views.sql`:

```sql
-- View for combined query performance and feedback
CREATE OR REPLACE VIEW query_performance_with_feedback AS
SELECT
    qp.*,
    uf.feedback_positive,
    uf.feedback_comment,
    uf.feedback_tags,
    uf.follow_up_question
FROM
    rag_query_performance qp
LEFT JOIN
    user_feedback uf ON qp.request_id = uf.request_id;

-- View for hourly performance metrics
CREATE OR REPLACE VIEW hourly_performance_metrics AS
SELECT
    DATE_TRUNC('hour', timestamp) AS hour,
    COUNT(*) AS query_count,
    AVG(total_time_ms) AS avg_total_time_ms,
    AVG(embedding_time_ms) AS avg_embedding_time_ms,
    AVG(search_time_ms) AS avg_search_time_ms,
    AVG(context_prep_time_ms) AS avg_context_prep_time_ms,
    AVG(llm_time_ms) AS avg_llm_time_ms,
    AVG(post_processing_time_ms) AS avg_post_processing_time_ms,
    SUM(total_tokens) AS total_tokens,
    AVG(total_tokens) AS avg_tokens_per_query
FROM
    rag_query_performance
GROUP BY
    hour
ORDER BY
    hour;

-- View for feedback statistics
CREATE OR REPLACE VIEW feedback_statistics AS
SELECT
    DATE_TRUNC('day', timestamp) AS day,
    COUNT(*) AS total_feedback,
    SUM(CASE WHEN feedback_positive THEN 1 ELSE 0 END) AS positive_feedback,
    SUM(CASE WHEN NOT feedback_positive THEN 1 ELSE 0 END) AS negative_feedback,
    ROUND(100.0 * SUM(CASE WHEN feedback_positive THEN 1 ELSE 0 END) / COUNT(*), 2) AS positive_percentage,
    COUNT(DISTINCT session_id) AS unique_sessions
FROM
    user_feedback
GROUP BY
    day
ORDER BY
    day;
```

### 2. ETL Processes

#### 2.1 Create Daily Aggregation Job for Token Usage

Create a new Python file called `token_usage_etl.py`:

```python
#!/usr/bin/env python3
"""
ETL script for aggregating token usage data on a daily basis.
"""

import os
import sys
import json
import logging
import datetime
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('token_usage_etl.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'raganalytics')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

# Model cost mapping (per 1000 tokens)
MODEL_COSTS = {
    'gpt-4': {'prompt': 0.03, 'completion': 0.06},
    'gpt-4-turbo': {'prompt': 0.01, 'completion': 0.03},
    'gpt-3.5-turbo': {'prompt': 0.0015, 'completion': 0.002},
    'text-embedding-ada-002': {'prompt': 0.0001, 'completion': 0.0},
    'default': {'prompt': 0.01, 'completion': 0.02}
}

def get_db_connection():
    """Create a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def get_raw_token_data(conn, start_date, end_date):
    """
    Retrieve raw token usage data from the logs table.
    
    Args:
        conn: Database connection
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        
    Returns:
        List of token usage records
    """
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT
                DATE_TRUNC('day', timestamp) AS day,
                request->>'model' AS model_name,
                tokens->>'prompt_tokens' AS prompt_tokens,
                tokens->>'completion_tokens' AS completion_tokens,
                tokens->>'total_tokens' AS total_tokens
            FROM
                rag_logs
            WHERE
                timestamp >= %s AND timestamp < %s
                AND request->>'model' IS NOT NULL
                AND tokens->>'prompt_tokens' IS NOT NULL
        """
        
        cursor.execute(query, (start_date, end_date))
        results = cursor.fetchall()
        cursor.close()
        
        return results
    
    except Exception as e:
        logger.error(f"Error retrieving raw token data: {e}")
        raise

def aggregate_token_data(raw_data):
    """
    Aggregate token usage data by day and model.
    
    Args:
        raw_data: Raw token usage records
        
    Returns:
        Dictionary with aggregated token usage
    """
    aggregated = {}
    
    for record in raw_data:
        day, model_name, prompt_tokens, completion_tokens, total_tokens = record
        
        day_str = day.strftime('%Y-%m-%d')
        
        if not model_name:
            model_name = 'unknown'
            
        key = (day_str, model_name)
        
        if key not in aggregated:
            aggregated[key] = {
                'prompt_tokens': 0,
                'completion_tokens': 0,
                'total_tokens': 0
            }
        
        try:
            aggregated[key]['prompt_tokens'] += int(prompt_tokens or 0)
            aggregated[key]['completion_tokens'] += int(completion_tokens or 0)
            aggregated[key]['total_tokens'] += int(total_tokens or 0)
        except (ValueError, TypeError) as e:
            logger.warning(f"Error parsing token values: {e}, record: {record}")
    
    return aggregated

def calculate_costs(aggregated_data):
    """
    Calculate estimated costs based on token usage.
    
    Args:
        aggregated_data: Aggregated token usage data
        
    Returns:
        Dictionary with token usage and costs
    """
    result = []
    
    for (day_str, model_name), tokens in aggregated_data.items():
        # Get cost rates for the model
        if model_name in MODEL_COSTS:
            cost_rates = MODEL_COSTS[model_name]
        else:
            cost_rates = MODEL_COSTS['default']
        
        # Calculate costs
        prompt_cost = (tokens['prompt_tokens'] / 1000) * cost_rates['prompt']
        completion_cost = (tokens['completion_tokens'] / 1000) * cost_rates['completion']
        total_cost = prompt_cost + completion_cost
        
        result.append({
            'date': day_str,
            'model_name': model_name,
            'prompt_tokens': tokens['prompt_tokens'],
            'completion_tokens': tokens['completion_tokens'],
            'total_tokens': tokens['total_tokens'],
            'estimated_cost': round(total_cost, 4)
        })
    
    return result

def save_aggregated_data(conn, aggregated_data):
    """
    Save aggregated token usage data to the database.
    
    Args:
        conn: Database connection
        aggregated_data: Aggregated token usage and cost data
    """
    try:
        cursor = conn.cursor()
        
        # Prepare data for batch insert
        insert_data = [
            (
                item['date'],
                item['model_name'],
                item['prompt_tokens'],
                item['completion_tokens'],
                item['total_tokens'],
                item['estimated_cost']
            )
            for item in aggregated_data
        ]
        
        # Insert or update data
        query = """
            INSERT INTO token_usage_daily
                (date, model_name, prompt_tokens, completion_tokens, total_tokens, estimated_cost)
            VALUES
                %s
            ON CONFLICT (date, model_name) DO UPDATE SET
                prompt_tokens = EXCLUDED.prompt_tokens,
                completion_tokens = EXCLUDED.completion_tokens,
                total_tokens = EXCLUDED.total_tokens,
                estimated_cost = EXCLUDED.estimated_cost
        """
        
        execute_values(cursor, query, insert_data)
        conn.commit()
        cursor.close()
        
        logger.info(f"Successfully saved {len(aggregated_data)} token usage records")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving aggregated token data: {e}")
        raise

def main():
    """Main ETL process."""
    try:
        # Calculate date range for yesterday
        today = datetime.datetime.now().date()
        yesterday = today - datetime.timedelta(days=1)
        start_date = datetime.datetime.combine(yesterday, datetime.time.min)
        end_date = datetime.datetime.combine(today, datetime.time.min)
        
        logger.info(f"Starting token usage ETL for {yesterday}")
        
        # Connect to database
        conn = get_db_connection()
        
        # Get raw data
        raw_data = get_raw_token_data(conn, start_date, end_date)
        logger.info(f"Retrieved {len(raw_data)} raw token usage records")
        
        # Aggregate data
        aggregated_data = aggregate_token_data(raw_data)
        logger.info(f"Aggregated into {len(aggregated_data)} daily model records")
        
        # Calculate costs
        cost_data = calculate_costs(aggregated_data)
        
        # Save to database
        save_aggregated_data(conn, cost_data)
        
        conn.close()
        logger.info("Token usage ETL completed successfully")
    
    except Exception as e:
        logger.error(f"Error in token usage ETL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 2.2 Create Daily Aggregation Job for Latency Metrics

Create a new Python file called `latency_metrics_etl.py`:

```python
#!/usr/bin/env python3
"""
ETL script for aggregating latency metrics data on an hourly basis.
"""

import os
import sys
import json
import logging
import datetime
import numpy as np
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('latency_metrics_etl.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'raganalytics')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

# Components to track
COMPONENTS = [
    'embedding',
    'search',
    'context',
    'llm',
    'post',
    'total'
]

def get_db_connection():
    """Create a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def get_raw_latency_data(conn, start_date, end_date):
    """
    Retrieve raw latency data from the logs table.
    
    Args:
        conn: Database connection
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        
    Returns:
        Dictionary with raw latency data by hour and component
    """
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT
                DATE_TRUNC('hour', timestamp) AS hour,
                latency_metrics->>'embedding_time_ms' AS embedding_time_ms,
                latency_metrics->>'search_time_ms' AS search_time_ms,
                latency_metrics->>'context_prep_time_ms' AS context_time_ms,
                latency_metrics->>'llm_time_ms' AS llm_time_ms,
                latency_metrics->>'post_time_ms' AS post_time_ms,
                latency_metrics->>'total_time_ms' AS total_time_ms
            FROM
                rag_logs
            WHERE
                timestamp >= %s AND timestamp < %s
                AND latency_metrics->>'total_time_ms' IS NOT NULL
        """
        
        cursor.execute(query, (start_date, end_date))
        results = cursor.fetchall()
        cursor.close()
        
        # Organize data by hour and component
        organized_data = {}
        
        for record in results:
            hour, embedding, search, context, llm, post, total = record
            
            if hour not in organized_data:
                organized_data[hour] = {
                    'embedding': [],
                    'search': [],
                    'context': [],
                    'llm': [],
                    'post': [],
                    'total': []
                }
            
            try:
                if embedding:
                    organized_data[hour]['embedding'].append(float(embedding))
                if search:
                    organized_data[hour]['search'].append(float(search))
                if context:
                    organized_data[hour]['context'].append(float(context))
                if llm:
                    organized_data[hour]['llm'].append(float(llm))
                if post:
                    organized_data[hour]['post'].append(float(post))
                if total:
                    organized_data[hour]['total'].append(float(total))
            except (ValueError, TypeError) as e:
                logger.warning(f"Error parsing latency values: {e}, record: {record}")
        
        return organized_data
    
    except Exception as e:
        logger.error(f"Error retrieving raw latency data: {e}")
        raise

def calculate_percentiles(values):
    """
    Calculate percentiles for a list of values.
    
    Args:
        values: List of numeric values
        
    Returns:
        Dictionary with percentile values
    """
    if not values:
        return {
            'avg': 0,
            'min': 0,
            'max': 0,
            'p50': 0,
            'p90': 0,
            'p95': 0,
            'p99': 0
        }
    
    return {
        'avg': float(np.mean(values)),
        'min': float(np.min(values)),
        'max': float(np.max(values)),
        'p50': float(np.percentile(values, 50)),
        'p90': float(np.percentile(values, 90)),
        'p95': float(np.percentile(values, 95)),
        'p99': float(np.percentile(values, 99))
    }

def aggregate_latency_data(raw_data):
    """
    Aggregate latency data by hour and component.
    
    Args:
        raw_data: Raw latency data organized by hour and component
        
    Returns:
        List of aggregated latency records
    """
    aggregated = []
    
    for hour, components in raw_data.items():
        hour_date = hour.date()
        hour_num = hour.hour
        
        for component, values in components.items():
            if not values:
                continue
            
            percentiles = calculate_percentiles(values)
            
            aggregated.append({
                'date': hour_date,
                'hour': hour_num,
                'component': component,
                'avg_time_ms': round(percentiles['avg'], 2),
                'min_time_ms': round(percentiles['min'], 2),
                'max_time_ms': round(percentiles['max'], 2),
                'p50_time_ms': round(percentiles['p50'], 2),
                'p90_time_ms': round(percentiles['p90'], 2),
                'p95_time_ms': round(percentiles['p95'], 2),
                'p99_time_ms': round(percentiles['p99'], 2),
                'count': len(values)
            })
    
    return aggregated

def save_aggregated_data(conn, aggregated_data):
    """
    Save aggregated latency data to the database.
    
    Args:
        conn: Database connection
        aggregated_data: Aggregated latency data
    """
    try:
        cursor = conn.cursor()
        
        # Prepare data for batch insert
        insert_data = [
            (
                item['date'],
                item['hour'],
                item['component'],
                item['avg_time_ms'],
                item['min_time_ms'],
                item['max_time_ms'],
                item['p50_time_ms'],
                item['p90_time_ms'],
                item['p95_time_ms'],
                item['p99_time_ms'],
                item['count']
            )
            for item in aggregated_data
        ]
        
        # Insert or update data
        query = """
            INSERT INTO latency_metrics
                (date, hour, component, avg_time_ms, min_time_ms, max_time_ms, 
                 p50_time_ms, p90_time_ms, p95_time_ms, p99_time_ms, count)
            VALUES
                %s
            ON CONFLICT (date, hour, component) DO UPDATE SET
                avg_time_ms = EXCLUDED.avg_time_ms,
                min_time_ms = EXCLUDED.min_time_ms,
                max_time_ms = EXCLUDED.max_time_ms,
                p50_time_ms = EXCLUDED.p50_time_ms,
                p90_time_ms = EXCLUDED.p90_time_ms,
                p95_time_ms = EXCLUDED.p95_time_ms,
                p99_time_ms = EXCLUDED.p99_time_ms,
                count = EXCLUDED.count
        """
        
        execute_values(cursor, query, insert_data)
        conn.commit()
        cursor.close()
        
        logger.info(f"Successfully saved {len(aggregated_data)} latency metric records")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error saving aggregated latency data: {e}")
        raise

def main():
    """Main ETL process."""
    try:
        # Calculate date range for yesterday
        today = datetime.datetime.now().date()
        yesterday = today - datetime.timedelta(days=1)
        start_date = datetime.datetime.combine(yesterday, datetime.time.min)
        end_date = datetime.datetime.combine(today, datetime.time.min)
        
        logger.info(f"Starting latency metrics ETL for {yesterday}")
        
        # Connect to database
        conn = get_db_connection()
        
        # Get raw data
        raw_data = get_raw_latency_data(conn, start_date, end_date)
        logger.info(f"Retrieved latency data for {len(raw_data)} hours")
        
        # Aggregate data
        aggregated_data = aggregate_latency_data(raw_data)
        logger.info(f"Aggregated into {len(aggregated_data)} hourly component records")
        
        # Save to database
        save_aggregated_data(conn, aggregated_data)
        
        conn.close()
        logger.info("Latency metrics ETL completed successfully")
    
    except Exception as e:
        logger.error(f"Error in latency metrics ETL: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 2.3 Create Daily Aggregation Job for Query Patterns

Create a new Python file called `query_patterns_etl.py`:

```python
#!/usr/bin/env python3
"""
ETL script for analyzing query patterns on a daily basis.
"""

import os
import sys
import json
import logging
import datetime
import hashlib
import re
from typing import Dict, Any, List
import psycopg2
from psycopg2.extras import execute_values

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('query_patterns_etl.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'raganalytics')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

def get_db_connection():
    """Create a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def get_raw_query_data(conn, start_date, end_date):
    """
    Retrieve raw query data from the logs table.
    
    Args:
        conn: Database connection
        start_date: Start date for data retrieval
        end_date: End date for data retrieval
        
    Returns:
        List of query records
    """
    try:
        cursor = conn.cursor()
        
        query = """
            SELECT
                DATE_TRUNC('day', timestamp) AS day,
                query_metrics->>'query_text' AS query_text,
                tokens->>'total_tokens' AS total_tokens,
                latency_metrics->>'total_time_ms' AS total_time_ms
            FROM
                rag_logs
            WHERE
                timestamp >= %s AND timestamp < %s
                AND query_metrics->>'query_text' IS NOT NULL
        """
        
        cursor.execute(query, (start_date, end_date))
        results = cursor.fetchall()
        cursor.close()
        
        return results
    
    except Exception as e:
        logger.error(f"Error retrieving raw query data: {e}")
        raise

def normalize_query(query_text):
    """
    Normalize a query by replacing specific entities with placeholders.
    
    Args:
        query_text: The original query text
        
    Returns:
        Normalized query template and a hash of the template
    """
    if not query_text:
        return "empty_query", "empty_query_hash"
    
    # Replace numbers
    normalized = re.sub(r'\b\d+\b', '[NUMBER]', query_text)
    
    # Replace dates
    normalized = re.sub(r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b', '[DATE]', normalized)
    normalized = re.sub(r'\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]* \d{1,2},? \d{2,4}\b', '[DATE]', normalized, flags=re.IGNORECASE)
    
    # Replace emails
    normalized = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', '[EMAIL]', normalized)
    
    # Replace URLs
    normalized = re.sub(r'https?://\S+', '[URL]', normalized)
    
    # Replace proper nouns (simplified approach)
    normalized = re.sub(r'\b[A-Z][a-z]+\b', '[NAME]', normalized)
    
    # Create hash
    query_hash = hashlib.md5(normalized.encode()).hexdigest()
    
    return normalized, query_hash

def aggregate_query_data(raw_data):
    """
    Aggregate query data by day and pattern.
    
    Args:
        raw_data: Raw query records
        
    Returns:
        Dictionary with aggregated query patterns
    """
    aggregated = {}
    
    for record in raw_data:
        day, query_text, total_tokens, total_time_ms = record
