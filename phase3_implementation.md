# Phase 3: Dashboard Route and Integration Implementation

This document provides the detailed implementation for Phase 3 of the PostgreSQL integration with the Analytics Dashboard. It includes specific code examples for creating a dedicated route for the analytics dashboard and ensuring the API returns complete data.

## Step 3.1: Create Analytics Dashboard Route

Add the following route to `main.py` to serve the analytics dashboard HTML:

```python
@app.route("/analytics", methods=["GET"])
def analytics_dashboard():
    """
    Route to serve the analytics dashboard HTML page.
    """
    try:
        logger.info("Analytics dashboard accessed")
        return send_from_directory('.', 'analytics_dashboard.html')
    except Exception as e:
        logger.error(f"Error serving analytics dashboard: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return "Error loading analytics dashboard", 500
```

This route will serve the `analytics_dashboard.html` file directly from the root directory. If you prefer to keep it in a different location (like a templates folder), you can adjust the path accordingly:

```python
@app.route("/analytics", methods=["GET"])
def analytics_dashboard():
    """
    Route to serve the analytics dashboard HTML page from templates folder.
    """
    try:
        logger.info("Analytics dashboard accessed")
        return render_template_string(open('templates/analytics_dashboard.html').read())
    except Exception as e:
        logger.error(f"Error serving analytics dashboard: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return "Error loading analytics dashboard", 500
```

## Step 3.2: Update API to Return Complete Data

The `get_analytics_data` function was already updated in Phase 2 to include all the necessary data. Let's add an export endpoint to allow downloading the analytics data as a JSON file:

```python
@app.route("/api/analytics/export", methods=["GET"])
def export_analytics():
    """
    API endpoint to export analytics data as a JSON file.
    Accepts optional date range parameters.
    """
    try:
        # Get date range parameters from request
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        logger.info(f"Analytics data export requested with date range: {start_date} to {end_date}")
        
        # Get analytics data from database
        analytics_data = get_analytics_data(start_date, end_date)
        
        # Set headers for file download
        response = Response(
            json.dumps(analytics_data, indent=2, default=str),
            mimetype="application/json",
            headers={"Content-Disposition": f"attachment;filename=analytics_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"}
        )
        
        return response
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
```

Let's also add a CSV export option for users who prefer that format:

```python
@app.route("/api/analytics/export/csv", methods=["GET"])
def export_analytics_csv():
    """
    API endpoint to export analytics data as a CSV file.
    Exports recent interactions in CSV format.
    """
    try:
        # Get date range parameters from request
        start_date = request.args.get("start_date")
        end_date = request.args.get("end_date")
        
        logger.info(f"Analytics CSV export requested with date range: {start_date} to {end_date}")
        
        # Get recent interactions from database
        recent_interactions = DatabaseManager.get_recent_interactions(limit=1000)  # Larger limit for export
        
        # Create CSV content
        csv_content = "vote_id,user_query,feedback_status,response_time,tokens,timestamp\n"
        for interaction in recent_interactions:
            # Escape quotes in user query
            user_query = interaction['user_query'].replace('"', '""')
            
            csv_content += f"{interaction['vote_id']},\"{user_query}\",{interaction['feedback_status']},{interaction['response_time']},{interaction['tokens']},{interaction['timestamp']}\n"
        
        # Set headers for file download
        response = Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=interactions_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"}
        )
        
        return response
    except Exception as e:
        logger.error(f"Error exporting analytics CSV data: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500
```

## Add Necessary Imports

Make sure to add the following imports to `main.py` if they're not already there:

```python
from flask import send_from_directory, Response
from datetime import datetime
import json
import traceback
```

## Testing Phase 3

After implementing these changes, you can test the new routes by:

1. Starting the Flask application:
   ```
   python main.py
   ```

2. Accessing the analytics dashboard in a browser:
   ```
   http://localhost:5002/analytics
   ```

3. Testing the export endpoints:
   ```
   http://localhost:5002/api/analytics/export
   http://localhost:5002/api/analytics/export/csv
   ```

4. Testing with date range parameters:
   ```
   http://localhost:5002/api/analytics/export?start_date=2025-01-01&end_date=2025-06-18
   ```

## Handling Cross-Origin Requests (Optional)

If you need to access the API from a different domain or port, you may need to add CORS support:

```python
from flask_cors import CORS

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
```

Or for specific routes only:

```python
from flask_cors import cross_origin

@app.route("/api/analytics", methods=["GET"])
@cross_origin()  # Enable CORS for this route only
def api_analytics():
    # ... existing code ...
```

## Next Steps

After successfully implementing and testing Phase 3, proceed to Phase 4: Frontend JavaScript Implementation to update the analytics dashboard HTML to fetch and display real data from the API.
