# Phase 1: Backend API Development Implementation

This document provides the detailed implementation for Phase 1 of the PostgreSQL integration with the Analytics Dashboard. It includes specific code examples for each step in this phase.

## Step 1.1: Create Basic Analytics API Endpoint

Add the following route to `main.py`:

```python
@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    """
    API endpoint to serve analytics data for the dashboard.
    Accepts optional date range parameters.
    """
    try:
        # Get date range parameters from request
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        logger.info(f"Analytics data requested with date range: {start_date} to {end_date}")
        
        # Get analytics data from database (to be implemented)
        analytics_data = {"status": "success", "message": "Analytics endpoint working"}
        
        return jsonify(analytics_data), 200
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
```

## Step 1.2: Implement Core Analytics Data Function

Add the following function to `main.py`:

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
        
        # Get time-based metrics (to be implemented)
        time_metrics = []
        
        # Combine all data
        analytics_data = {
            "feedback_summary": feedback_summary,
            "query_analytics": query_analytics,
            "tag_distribution": tag_distribution,
            "time_metrics": time_metrics
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
            "time_metrics": []
        }
```

Now update the `api_analytics` function to use this new function:

```python
@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    """
    API endpoint to serve analytics data for the dashboard.
    Accepts optional date range parameters.
    """
    try:
        # Get date range parameters from request
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        logger.info(f"Analytics data requested with date range: {start_date} to {end_date}")
        
        # Get analytics data from database
        analytics_data = get_analytics_data(start_date, end_date)
        
        return jsonify(analytics_data), 200
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
```

## Step 1.3: Implement Time-Based Metrics Function

Add the following function to `main.py`:

```python
def get_time_based_metrics(start_date=None, end_date=None):
    """
    Get time-based metrics from the database.
    
    Args:
        start_date (str, optional): Start date for filtering data (YYYY-MM-DD)
        end_date (str, optional): End date for filtering data (YYYY-MM-DD)
        
    Returns:
        list: List of dictionaries containing daily metrics
    """
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Build query with date filters if provided
            query = """
                SELECT 
                    DATE(timestamp) as date,
                    COUNT(*) as interaction_count,
                    COUNT(CASE WHEN 'Looks Good / Accurate & Clear' = ANY(feedback_tags) THEN 1 END) as positive_count
                FROM votes
            """
            
            params = []
            if start_date and end_date:
                query += " WHERE timestamp BETWEEN %s AND %s"
                params.extend([start_date, end_date])
            
            query += " GROUP BY DATE(timestamp) ORDER BY date"
            
            cursor.execute(query, params)
            daily_metrics = cursor.fetchall()
            
            # Convert date objects to strings for JSON serialization
            for metric in daily_metrics:
                if isinstance(metric['date'], datetime.date):
                    metric['date'] = metric['date'].isoformat()
            
            return daily_metrics
    except Exception as e:
        logger.error(f"Error getting time-based metrics: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return []
    finally:
        if conn is not None:
            conn.close()
```

Now update the `get_analytics_data` function to use this new function:

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
        
        # Combine all data
        analytics_data = {
            "feedback_summary": feedback_summary,
            "query_analytics": query_analytics,
            "tag_distribution": tag_distribution,
            "time_metrics": time_metrics
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
            "time_metrics": []
        }
```

## Testing Phase 1

After implementing these changes, you can test the API endpoint by:

1. Starting the Flask application:
   ```
   python main.py
   ```

2. Making a request to the API endpoint:
   ```
   curl http://localhost:5002/api/analytics
   ```

3. Testing with date range parameters:
   ```
   curl "http://localhost:5002/api/analytics?start_date=2025-01-01&end_date=2025-06-18"
   ```

The API should return a JSON response with the basic analytics data structure. At this point, the time-based metrics will be populated with real data, while the other sections will use the existing methods from DatabaseManager.

## Next Steps

After successfully implementing and testing Phase 1, proceed to Phase 2: Database Manager Enhancement to add the additional methods needed for complete analytics data.
