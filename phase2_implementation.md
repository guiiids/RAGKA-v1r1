# Phase 2: Database Manager Enhancement Implementation

This document provides the detailed implementation for Phase 2 of the PostgreSQL integration with the Analytics Dashboard. It includes specific code examples for enhancing the DatabaseManager class with additional analytics methods.

## Step 2.1: Add Response Time Metrics Method

Add the following method to the `DatabaseManager` class in `db_manager.py`:

```python
@staticmethod
def get_response_time_metrics():
    """
    Get response time metrics from the database.
    
    Returns:
        dict: Dictionary containing response time metrics (avg, min, max)
    """
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # This assumes you have a response_time field in evaluation_json
            cursor.execute(
                """
                SELECT 
                    AVG((evaluation_json->>'response_time')::float) as avg_response_time,
                    MIN((evaluation_json->>'response_time')::float) as min_response_time,
                    MAX((evaluation_json->>'response_time')::float) as max_response_time
                FROM votes
                WHERE evaluation_json->>'response_time' IS NOT NULL
                """
            )
            response_time_metrics = cursor.fetchone()
            
            # Handle None values for empty database
            if response_time_metrics and response_time_metrics['avg_response_time'] is None:
                response_time_metrics = {
                    'avg_response_time': 0,
                    'min_response_time': 0,
                    'max_response_time': 0
                }
                
            return response_time_metrics
        
    except Exception as e:
        logger.error(f"Error getting response time metrics: {e}")
        return {
            'avg_response_time': 0,
            'min_response_time': 0,
            'max_response_time': 0
        }
    finally:
        if conn is not None:
            conn.close()
```

## Step 2.2: Add Token Usage Metrics Method

Add the following method to the `DatabaseManager` class in `db_manager.py`:

```python
@staticmethod
def get_token_usage_metrics():
    """
    Get token usage metrics from the database.
    
    Returns:
        dict: Dictionary containing token usage metrics
    """
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # This assumes you have token usage fields in evaluation_json
            cursor.execute(
                """
                SELECT 
                    SUM((evaluation_json->>'prompt_tokens')::int) as total_prompt_tokens,
                    SUM((evaluation_json->>'completion_tokens')::int) as total_completion_tokens,
                    SUM((evaluation_json->>'total_tokens')::int) as total_tokens,
                    AVG((evaluation_json->>'total_tokens')::int) as avg_tokens_per_interaction
                FROM votes
                WHERE evaluation_json->>'total_tokens' IS NOT NULL
                """
            )
            token_metrics = cursor.fetchone()
            
            # Handle None values for empty database
            if token_metrics and token_metrics['total_tokens'] is None:
                token_metrics = {
                    'total_prompt_tokens': 0,
                    'total_completion_tokens': 0,
                    'total_tokens': 0,
                    'avg_tokens_per_interaction': 0
                }
                
            # Get daily token usage for the chart
            cursor.execute(
                """
                SELECT 
                    DATE(timestamp) as date,
                    SUM((evaluation_json->>'total_tokens')::int) as daily_tokens
                FROM votes
                WHERE evaluation_json->>'total_tokens' IS NOT NULL
                GROUP BY DATE(timestamp)
                ORDER BY date
                """
            )
            daily_token_usage = cursor.fetchall()
            
            # Convert date objects to strings for JSON serialization
            for usage in daily_token_usage:
                if isinstance(usage['date'], datetime.date):
                    usage['date'] = usage['date'].isoformat()
            
            # Add daily usage to the metrics
            token_metrics['daily_usage'] = daily_token_usage
                
            return token_metrics
        
    except Exception as e:
        logger.error(f"Error getting token usage metrics: {e}")
        return {
            'total_prompt_tokens': 0,
            'total_completion_tokens': 0,
            'total_tokens': 0,
            'avg_tokens_per_interaction': 0,
            'daily_usage': []
        }
    finally:
        if conn is not None:
            conn.close()
```

## Step 2.3: Add Recent Interactions Method

Add the following method to the `DatabaseManager` class in `db_manager.py`:

```python
@staticmethod
def get_recent_interactions(limit=10):
    """
    Get recent interactions with details.
    
    Args:
        limit (int, optional): Maximum number of interactions to return. Defaults to 10.
        
    Returns:
        list: List of dictionaries containing recent interactions
    """
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(
                """
                SELECT 
                    vote_id,
                    user_query,
                    feedback_tags,
                    (evaluation_json->>'response_time')::float as response_time,
                    (evaluation_json->>'total_tokens')::int as tokens,
                    timestamp
                FROM votes
                ORDER BY timestamp DESC
                LIMIT %s
                """,
                (limit,)
            )
            recent_interactions = cursor.fetchall()
            
            # Process the data for display
            for interaction in recent_interactions:
                # Truncate long queries
                if len(interaction['user_query']) > 50:
                    interaction['user_query'] = interaction['user_query'][:50] + '...'
                
                # Format timestamp
                if isinstance(interaction['timestamp'], datetime.datetime):
                    interaction['timestamp'] = interaction['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                
                # Determine feedback status
                if interaction['feedback_tags'] and 'Looks Good / Accurate & Clear' in interaction['feedback_tags']:
                    interaction['feedback_status'] = 'Positive'
                else:
                    interaction['feedback_status'] = 'Negative'
                
                # Format response time
                if interaction['response_time']:
                    interaction['response_time'] = f"{interaction['response_time']:.1f}s"
                else:
                    interaction['response_time'] = 'N/A'
                
                # Format tokens
                if interaction['tokens']:
                    interaction['tokens'] = f"{interaction['tokens']}"
                else:
                    interaction['tokens'] = 'N/A'
            
            return recent_interactions
        
    except Exception as e:
        logger.error(f"Error getting recent interactions: {e}")
        return []
    finally:
        if conn is not None:
            conn.close()
```

## Update the get_analytics_data Function

Now update the `get_analytics_data` function in `main.py` to use these new methods:

```python
def get_analytics_data(start_date=None, end_date=None):
    """
    Gather all analytics data from various database methods.
    
    Args:
        start_date (str, optional): Start date for filtering data (YYYY-MM-DD)
        end_date (str, optional): End date for filtering data (YYYY-MM-DD)
        
    Returns:
        dict: Dictionary containing all analytics data
    """
    try:
        # Get feedback summary
        feedback_summary = DatabaseManager.get_feedback_summary()
        
        # Get query analytics
        query_analytics = DatabaseManager.get_query_analytics()
        
        # Get tag distribution
        tag_distribution = DatabaseManager.get_tag_distribution()
        
        # Get time-based metrics
        time_metrics = get_time_based_metrics(start_date, end_date)
        
        # Get response time metrics
        response_time_metrics = DatabaseManager.get_response_time_metrics()
        
        # Get token usage metrics
        token_usage_metrics = DatabaseManager.get_token_usage_metrics()
        
        # Get recent interactions
        recent_interactions = DatabaseManager.get_recent_interactions(limit=10)
        
        # Combine all data
        analytics_data = {
            "feedback_summary": feedback_summary,
            "query_analytics": query_analytics,
            "tag_distribution": tag_distribution,
            "time_metrics": time_metrics,
            "response_time_metrics": response_time_metrics,
            "token_usage_metrics": token_usage_metrics,
            "recent_interactions": recent_interactions
        }
        
        return analytics_data
    except Exception as e:
        logger.error(f"Error in get_analytics_data: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        # Return minimal data structure in case of error
        return {
            "feedback_summary": {
                "total_feedback": 0,
                "positive_feedback": 0,
                "negative_feedback": 0,
                "recent_feedback": []
            },
            "query_analytics": {
                "total_queries": 0,
                "queries_with_feedback": 0,
                "successful_queries": 0,
                "recent_queries": []
            },
            "tag_distribution": [],
            "time_metrics": [],
            "response_time_metrics": {
                "avg_response_time": 0,
                "min_response_time": 0,
                "max_response_time": 0
            },
            "token_usage_metrics": {
                "total_prompt_tokens": 0,
                "total_completion_tokens": 0,
                "total_tokens": 0,
                "avg_tokens_per_interaction": 0,
                "daily_usage": []
            },
            "recent_interactions": []
        }
```

## Testing Phase 2

After implementing these changes, you can test the enhanced DatabaseManager methods by:

1. Making sure the necessary imports are added to `db_manager.py`:
   ```python
   import logging
   from datetime import datetime
   from psycopg2.extras import RealDictCursor, Json
   ```

2. Starting the Flask application:
   ```
   python main.py
   ```

3. Making a request to the API endpoint:
   ```
   curl http://localhost:5002/api/analytics
   ```

4. Examining the response to ensure all the new data is included.

## Handling Missing Data

The implementation includes error handling for cases where:
- The database is empty
- The evaluation_json fields are missing or null
- There are no records matching the date range

In all these cases, the methods return default values (zeros or empty arrays) to ensure the dashboard can still render without errors.

## Next Steps

After successfully implementing and testing Phase 2, proceed to Phase 3: Dashboard Route and Integration to create a dedicated route for the analytics dashboard and ensure the API returns complete data.
