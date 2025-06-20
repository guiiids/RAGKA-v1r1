# Phase 6: Testing and Optimization Implementation

This document provides the detailed implementation for Phase 6 of the PostgreSQL integration with the Analytics Dashboard. It includes specific strategies and code examples for testing, optimization, and handling edge cases.

## Step 6.1: End-to-End Testing

Create a comprehensive testing plan to verify the complete flow from database to dashboard:

### Manual Testing Checklist

Create a file called `testing_checklist.md` with the following content:

```markdown
# Analytics Dashboard Testing Checklist

## API Endpoints Testing

- [ ] `/api/analytics` returns correct data structure
  - [ ] Test with no date parameters
  - [ ] Test with valid date range
  - [ ] Test with invalid date range
  - [ ] Verify all required data sections are present

- [ ] `/api/analytics/export` generates downloadable files
  - [ ] JSON format works correctly
  - [ ] CSV format works correctly
  - [ ] Excel format works correctly (if openpyxl is installed)
  - [ ] Test with date range parameters

- [ ] `/analytics` route serves the dashboard HTML

## Database Methods Testing

- [ ] `get_feedback_summary()` returns correct data
  - [ ] Verify counts match actual database records
  - [ ] Test with empty database

- [ ] `get_query_analytics()` returns correct data
  - [ ] Verify counts match actual database records
  - [ ] Test with empty database

- [ ] `get_tag_distribution()` returns correct data
  - [ ] Verify counts match actual database records
  - [ ] Test with empty database

- [ ] `get_response_time_metrics()` returns correct data
  - [ ] Verify metrics match actual database records
  - [ ] Test with empty database
  - [ ] Test with missing evaluation_json fields

- [ ] `get_token_usage_metrics()` returns correct data
  - [ ] Verify metrics match actual database records
  - [ ] Test with empty database
  - [ ] Test with missing evaluation_json fields

- [ ] `get_recent_interactions()` returns correct data
  - [ ] Verify interactions match actual database records
  - [ ] Test with empty database
  - [ ] Test with limit parameter

- [ ] `get_time_based_metrics()` returns correct data
  - [ ] Verify metrics match actual database records
  - [ ] Test with empty database
  - [ ] Test with date range parameters

## Frontend Testing

- [ ] Dashboard loads correctly
  - [ ] All sections are visible
  - [ ] No JavaScript errors in console

- [ ] Data fetching works
  - [ ] Loading indicators show during fetch
  - [ ] Error handling works for failed requests

- [ ] Charts display correctly
  - [ ] All charts render with data
  - [ ] Charts handle empty data gracefully
  - [ ] Charts update when date range changes

- [ ] Date range picker works
  - [ ] Default range is set correctly
  - [ ] Changing date range updates data
  - [ ] Preset buttons work correctly

- [ ] Export functionality works
  - [ ] Export dropdown opens
  - [ ] All export formats work
  - [ ] Loading indicator shows during export
  - [ ] Downloaded files contain correct data

- [ ] Recent interactions table works
  - [ ] Table shows correct data
  - [ ] Pagination info is accurate
  - [ ] "View" buttons work (if implemented)

## Cross-Browser Testing

- [ ] Chrome
- [ ] Firefox
- [ ] Safari
- [ ] Edge

## Responsive Design Testing

- [ ] Desktop (1920x1080)
- [ ] Laptop (1366x768)
- [ ] Tablet (768x1024)
- [ ] Mobile (375x667)

## Performance Testing

- [ ] Dashboard loads in under 3 seconds
- [ ] Data fetching completes in under 2 seconds
- [ ] Charts render in under 1 second
- [ ] Export generation completes in under 5 seconds
```

### Automated Testing

Create a file called `test_analytics.py` with the following content:

```python
import unittest
import json
import os
import sys
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import application modules
from main import app, get_analytics_data, get_time_based_metrics
from db_manager import DatabaseManager

class TestAnalyticsAPI(unittest.TestCase):
    """Test cases for the analytics API endpoints."""
    
    def setUp(self):
        """Set up test client and mock data."""
        self.app = app.test_client()
        self.app.testing = True
        
        # Mock data for testing
        self.mock_feedback_summary = {
            'total_feedback': 100,
            'positive_feedback': 75,
            'negative_feedback': 25,
            'recent_feedback': [
                {'vote_id': 1, 'user_query': 'Test query', 'feedback_tags': ['Looks Good / Accurate & Clear'], 'comment': 'Great!', 'timestamp': datetime.now()}
            ]
        }
        
        self.mock_query_analytics = {
            'total_queries': 100,
            'queries_with_feedback': 100,
            'successful_queries': 75,
            'recent_queries': [
                {'user_query': 'Test query', 'timestamp': datetime.now()}
            ]
        }
        
        self.mock_tag_distribution = [
            {'tag': 'Looks Good / Accurate & Clear', 'count': 75},
            {'tag': 'Incomplete', 'count': 15},
            {'tag': 'Factual Error', 'count': 10}
        ]
        
        self.mock_response_time_metrics = {
            'avg_response_time': 2.5,
            'min_response_time': 1.0,
            'max_response_time': 5.0
        }
        
        self.mock_token_usage_metrics = {
            'total_prompt_tokens': 50000,
            'total_completion_tokens': 30000,
            'total_tokens': 80000,
            'avg_tokens_per_interaction': 800,
            'daily_usage': [
                {'date': datetime.now().date().isoformat(), 'daily_tokens': 10000}
            ]
        }
        
        self.mock_recent_interactions = [
            {
                'vote_id': 1,
                'user_query': 'Test query',
                'feedback_status': 'Positive',
                'response_time': '2.5s',
                'tokens': '800',
                'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        ]
        
        self.mock_time_metrics = [
            {
                'date': datetime.now().date().isoformat(),
                'interaction_count': 10,
                'positive_count': 8
            }
        ]
    
    @patch.object(DatabaseManager, 'get_feedback_summary')
    @patch.object(DatabaseManager, 'get_query_analytics')
    @patch.object(DatabaseManager, 'get_tag_distribution')
    @patch.object(DatabaseManager, 'get_response_time_metrics')
    @patch.object(DatabaseManager, 'get_token_usage_metrics')
    @patch.object(DatabaseManager, 'get_recent_interactions')
    def test_api_analytics_endpoint(self, mock_recent, mock_token, mock_response, mock_tag, mock_query, mock_feedback):
        """Test the /api/analytics endpoint."""
        # Set up mocks
        mock_feedback.return_value = self.mock_feedback_summary
        mock_query.return_value = self.mock_query_analytics
        mock_tag.return_value = self.mock_tag_distribution
        mock_response.return_value = self.mock_response_time_metrics
        mock_token.return_value = self.mock_token_usage_metrics
        mock_recent.return_value = self.mock_recent_interactions
        
        # Mock the get_time_based_metrics function
        with patch('main.get_time_based_metrics', return_value=self.mock_time_metrics):
            # Test without date parameters
            response = self.app.get('/api/analytics')
            self.assertEqual(response.status_code, 200)
            data = json.loads(response.data)
            
            # Verify structure
            self.assertIn('feedback_summary', data)
            self.assertIn('query_analytics', data)
            self.assertIn('tag_distribution', data)
            self.assertIn('time_metrics', data)
            self.assertIn('response_time_metrics', data)
            self.assertIn('token_usage_metrics', data)
            self.assertIn('recent_interactions', data)
            
            # Test with date parameters
            response = self.app.get('/api/analytics?start_date=2025-01-01&end_date=2025-06-18')
            self.assertEqual(response.status_code, 200)
    
    @patch.object(DatabaseManager, 'get_recent_interactions')
    def test_export_endpoints(self, mock_recent):
        """Test the export endpoints."""
        # Set up mock
        mock_recent.return_value = self.mock_recent_interactions
        
        # Test JSON export
        with patch('main.get_analytics_data', return_value={'recent_interactions': self.mock_recent_interactions}):
            response = self.app.get('/api/analytics/export')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'application/json')
            
            # Test CSV export
            response = self.app.get('/api/analytics/export?format=csv')
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.content_type, 'text/csv')
            
            # Test with date parameters
            response = self.app.get('/api/analytics/export?start_date=2025-01-01&end_date=2025-06-18')
            self.assertEqual(response.status_code, 200)
    
    def test_analytics_dashboard_route(self):
        """Test the /analytics route."""
        response = self.app.get('/analytics')
        self.assertEqual(response.status_code, 200)

class TestDatabaseMethods(unittest.TestCase):
    """Test cases for the database methods."""
    
    @patch('psycopg2.connect')
    def test_get_feedback_summary(self, mock_connect):
        """Test the get_feedback_summary method."""
        from datetime import datetime, timedelta
        # Set up mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [{'total_feedback': 100}, {'positive_feedback': 75}]
        mock_cursor.fetchall.return_value = [{'vote_id': 1, 'user_query': 'Test', 'feedback_tags': ['Looks Good'], 'comment': '', 'timestamp': datetime.now()}]
        
        # Set up mock connection
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Call the method without date filters
        result = DatabaseManager.get_feedback_summary()
        
        # Verify result keys
        self.assertIn('total_feedback', result)
        self.assertIn('positive_feedback', result)
        self.assertIn('negative_feedback', result)
        self.assertIn('recent_feedback', result)
        
        # Call the method with date filters
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        result_with_dates = DatabaseManager.get_feedback_summary(start_date=start_date, end_date=end_date)
        
        # Verify result keys again
        self.assertIn('total_feedback', result_with_dates)
        self.assertIn('positive_feedback', result_with_dates)
        self.assertIn('negative_feedback', result_with_dates)
        self.assertIn('recent_feedback', result_with_dates)
    
    # Add similar tests for other database methods

if __name__ == '__main__':
    unittest.main()
```

### Load Testing

Create a file called `load_test.py` with the following content:

```python
import time
import requests
import concurrent.futures
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime

def make_request(url):
    """Make a request to the API and return the response time."""
    start_time = time.time()
    response = requests.get(url)
    end_time = time.time()
    return {
        'status_code': response.status_code,
        'response_time': end_time - start_time,
        'timestamp': datetime.now().strftime('%H:%M:%S')
    }

def run_load_test(url, num_requests, concurrency):
    """Run a load test with the specified number of requests and concurrency."""
    print(f"Running load test on {url}")
    print(f"Number of requests: {num_requests}")
    print(f"Concurrency: {concurrency}")
    print("--------------------------------------------------")
    
    results = []
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(make_request, url) for _ in range(num_requests)]
        
        for i, future in enumerate(concurrent.futures.as_completed(futures)):
            result = future.result()
            results.append(result)
            print(f"Request {i+1}/{num_requests}: {result['status_code']} in {result['response_time']:.2f}s")
    
    return results

def analyze_results(results):
    """Analyze the results of the load test."""
    response_times = [r['response_time'] for r in results]
    status_codes = [r['status_code'] for r in results]
    
    # Calculate statistics
    avg_response_time = np.mean(response_times)
    min_response_time = np.min(response_times)
    max_response_time = np.max(response_times)
    p95_response_time = np.percentile(response_times, 95)
    
    success_rate = status_codes.count(200) / len(status_codes) * 100
    
    print("\nResults:")
    print(f"Average response time: {avg_response_time:.2f}s")
    print(f"Minimum response time: {min_response_time:.2f}s")
    print(f"Maximum response time: {max_response_time:.2f}s")
    print(f"95th percentile response time: {p95_response_time:.2f}s")
    print(f"Success rate: {success_rate:.2f}%")
    
    # Plot response times
    plt.figure(figsize=(10, 6))
    plt.plot(range(len(response_times)), response_times, marker='o', linestyle='-', markersize=3)
    plt.axhline(y=avg_response_time, color='r', linestyle='--', label=f'Average: {avg_response_time:.2f}s')
    plt.axhline(y=p95_response_time, color='g', linestyle='--', label=f'95th percentile: {p95_response_time:.2f}s')
    plt.xlabel('Request Number')
    plt.ylabel('Response Time (s)')
    plt.title('Response Times')
    plt.legend()
    plt.grid(True)
    plt.savefig('response_times.png')
    
    # Plot response time histogram
    plt.figure(figsize=(10, 6))
    plt.hist(response_times, bins=20, alpha=0.7, color='blue')
    plt.axvline(x=avg_response_time, color='r', linestyle='--', label=f'Average: {avg_response_time:.2f}s')
    plt.axvline(x=p95_response_time, color='g', linestyle='--', label=f'95th percentile: {p95_response_time:.2f}s')
    plt.xlabel('Response Time (s)')
    plt.ylabel('Frequency')
    plt.title('Response Time Distribution')
    plt.legend()
    plt.grid(True)
    plt.savefig('response_time_histogram.png')
    
    print("\nPlots saved as 'response_times.png' and 'response_time_histogram.png'")

if __name__ == "__main__":
    # Configuration
    base_url = "http://localhost:5002"
    endpoints = [
        "/api/analytics",
        "/api/analytics?start_date=2025-01-01&end_date=2025-06-18"
    ]
    num_requests = 50
    concurrency = 5
    
    for endpoint in endpoints:
        url = base_url + endpoint
        results = run_load_test(url, num_requests, concurrency)
        analyze_results(results)
        print("\n")
```

## Step 6.2: Performance Optimization

### Database Query Optimization

Update the database methods in `db_manager.py` to include query optimization:

```python
@staticmethod
def get_feedback_summary():
    """Get summary statistics of collected feedback with optimized queries."""
    conn = None
    try:
        conn = DatabaseManager.get_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            # Use a single query to get counts instead of multiple queries
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_feedback,
                    COUNT(CASE WHEN 'Looks Good / Accurate & Clear' = ANY(feedback_tags) THEN 1 END) as positive_feedback
                FROM votes
            """)
            counts = cursor.fetchone()
            total_feedback = counts['total_feedback']
            positive_feedback = counts['positive_feedback']
            
            # Get recent feedback (last 5 entries) with index hint
            cursor.execute(
                """
                SELECT vote_id, user_query, feedback_tags, comment, timestamp
                FROM votes
                ORDER BY timestamp DESC
                LIMIT 5
                """
            )
            recent_feedback = cursor.fetchall()
            
            summary = {
                'total_feedback': total_feedback,
                'positive_feedback': positive_feedback,
                'negative_feedback': total_feedback - positive_feedback,
                'recent_feedback': recent_feedback
            }
            
            return summary
    except Exception as e:
        logger.error(f"Error generating feedback summary: {e}")
        return {
            'total_feedback': 0,
            'positive_feedback': 0,
            'negative_feedback': 0,
            'recent_feedback': []
        }
    finally:
        if conn is not None:
            conn.close()
```

### Add Database Indexes

Create a file called `add_indexes.sql` with the following content:

```sql
-- Add indexes to improve query performance

-- Index on timestamp for time-based queries
CREATE INDEX IF NOT EXISTS idx_votes_timestamp ON votes (timestamp);

-- Index on feedback_tags for tag-based queries
CREATE INDEX IF NOT EXISTS idx_votes_feedback_tags ON votes USING GIN (feedback_tags);

-- Index on evaluation_json for JSON field queries
CREATE INDEX IF NOT EXISTS idx_votes_evaluation_json ON votes USING GIN (evaluation_json);

-- Analyze the table to update statistics
ANALYZE votes;
```

Create a script to apply these indexes:

```python
#!/usr/bin/env python3
import os
import psycopg2
from dotenv import load_dotenv
from config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_SSL_MODE
)

def apply_indexes():
    """Apply database indexes to improve query performance."""
    # Load environment variables
    load_dotenv()
    
    # Read SQL file
    with open('add_indexes.sql', 'r') as f:
        sql = f.read()
    
    # Connect to database
    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        sslmode=POSTGRES_SSL_MODE
    )
    
    try:
        with conn.cursor() as cursor:
            # Execute SQL
            cursor.execute(sql)
            conn.commit()
            print("Indexes applied successfully")
    except Exception as e:
        print(f"Error applying indexes: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    apply_indexes()
```

### Add Caching

Add caching to the API endpoints to improve performance:

```python
from functools import wraps
from datetime import datetime, timedelta

# Simple in-memory cache
cache = {}
cache_ttl = 300  # 5 minutes

def cached(ttl=cache_ttl):
    """
    Decorator to cache function results.
    
    Args:
        ttl (int): Time to live in seconds
        
    Returns:
        Decorated function
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Create cache key from function name and arguments
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if result is in cache and not expired
            if key in cache:
                result, timestamp = cache[key]
                if datetime.now() - timestamp < timedelta(seconds=ttl):
                    logger.debug(f"Cache hit for {key}")
                    return result
            
            # Call function and cache result
            result = func(*args, **kwargs)
            cache[key] = (result, datetime.now())
            logger.debug(f"Cache miss for {key}, caching result")
            
            return result
        return wrapper
    return decorator

# Apply cache to analytics data function
@cached(ttl=300)  # 5 minutes
def get_analytics_data(start_date=None, end_date=None):
    """
    Gather all analytics data from various database methods.
    Results are cached for 5 minutes.
    
    Args:
        start_date (str, optional): Start date for filtering data (YYYY-MM-DD)
        end_date (str, optional): End date for filtering data (YYYY-MM-DD)
        
    Returns:
        dict: Dictionary containing all analytics data
    """
    # ... existing implementation ...
```

## Step 6.3: Error Handling and Edge Cases

### Improve Error Handling

Update the API endpoints with better error handling:

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
        
        # Validate date parameters if provided
        if start_date and end_date:
            try:
                # Validate date format
                datetime.strptime(start_date, '%Y-%m-%d')
                datetime.strptime(end_date, '%Y-%m-%d')
                
                # Validate date range
                if start_date > end_date:
                    return jsonify({
                        "error": "Invalid date range: start_date must be before or equal to end_date"
                    }), 400
            except ValueError:
                return jsonify({
                    "error": "Invalid date format: dates must be in YYYY-MM-DD format"
                }), 400
        
        logger.info(f"Analytics data requested with date range: {start_date} to {end_date}")
        
        # Get analytics data from database
        analytics_data = get_analytics_data(start_date, end_date)
        
        return jsonify(analytics_data), 200
    except Exception as e:
        logger.error(f"Error getting analytics data: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "error": "An internal server error occurred. Please try again later.",
            "details": str(e) if app.debug else None
        }), 500
```

### Handle Edge Cases

Update the frontend JavaScript to handle edge cases:

```javascript
// Function to fetch analytics data from API
function fetchAnalyticsData(startDate = null, endDate = null) {
    // Show loading indicators
    showLoadingState();
    
    // Build API URL with date parameters if provided
    let apiUrl = '/api/analytics';
    if (startDate && endDate) {
        apiUrl += `?start_date=${startDate}&end_date=${endDate}`;
    }
    
    // Fetch data from API with timeout
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 30000);  // 30 second timeout
    
    fetch(apiUrl, { signal: controller.signal })
        .then(response => {
            clearTimeout(timeoutId);
            
            if (!response.ok) {
                if (response.status === 400) {
                    // Handle validation errors
                    return response.json().then(data => {
                        throw new Error(data.error || 'Invalid request');
                    });
                } else if (response.status === 404) {
                    throw new Error('API endpoint not found');
                } else if (response.status === 500) {
                    throw new Error('Server error');
                } else {
                    throw new Error(`HTTP error! Status: ${response.status}`);
                }
            }
            
            return response.json();
        })
        .then(data => {
            // Check if data has the expected structure
            if (!data || typeof data !== 'object') {
                throw new Error('Invalid data format received from API');
            }
            
            // Update dashboard with real data
            updateDashboardMetrics(data);
            updateCharts(data);
            populateRecentInteractions(data.recent_interactions);
            
            // Update last updated timestamp
            document.getElementById('last-updated').textContent = new Date().toLocaleString();
            
            // Hide loading indicators
            hideLoadingState();
        })
        .catch(error => {
            console.error('Error fetching analytics data:', error);
            
            // Show appropriate error message based on error type
            if (error.name === 'AbortError') {
                showErrorMessage('Request timed out. The server took too long to respond.');
            } else {
                showErrorMessage(`Failed to load analytics data: ${error.message}`);
            }
            
            // Hide loading indicators
            hideLoadingState();
            
            // Show empty state for charts
            updateChartsWithEmptyState();
        });
}

// Function to update charts with empty state
function updateChartsWithEmptyState() {
    // Update each chart with empty data
    updateInteractionsChart([]);
    updateFeedbackChart({ positive_feedback: 0, negative_feedback: 0 });
    updateCategoriesChart([]);
    updateResponseTimeChart([]);
    updateTokenUsageChart([]);
    updateFeedbackTagsChart([]);
    
    // Update metrics with zeros
    document.getElementById('total-interactions').textContent = '0';
    document.getElementById('positive-feedback').textContent = '0%';
    document.getElementById('avg-response-time').textContent = 'N/A';
    document.getElementById('token-usage').textContent = '0';
    
    // Clear table
    const tableBody = document.getElementById('recent-interactions-table');
    if (tableBody) {
        tableBody.innerHTML = `
            <tr>
                <td colspan="7" class="px-6 py-4 text-center text-gray-500">No data available</td>
            </tr>
        `;
    }
}
```

## Testing and Deployment

### Create a Deployment Checklist

Create a file called `deployment_checklist.md` with the following content:

```markdown
# Deployment Checklist

## Pre-Deployment

- [ ] Run all tests and ensure they pass
- [ ] Verify database connection parameters in .env
- [ ] Apply database indexes
- [ ] Update requirements.txt with new dependencies
- [ ] Set appropriate logging levels
- [ ] Disable debug mode in production

## Deployment Steps

1. **Backup Database**
   - [ ] Create a backup of the PostgreSQL database

2. **Update Code**
   - [ ] Pull latest code from repository
   - [ ] Install/update dependencies
   - [ ] Apply database migrations if needed

3. **Configuration**
   - [ ] Update environment variables if needed
   - [ ] Set appropriate permissions on files
   - [ ] Configure web server (if using)

4. **Testing**
   - [ ] Verify API endpoints work
   - [ ] Check dashboard loads correctly
   - [ ] Test with real data

5. **Monitoring**
   - [ ] Set up logging
   - [ ] Configure error notifications
   - [ ] Set up performance monitoring

## Post-Deployment

- [ ] Verify dashboard is accessible
- [ ] Check logs for errors
- [ ] Monitor performance
- [ ] Document any issues or changes
```

### Create a Performance Monitoring Script

Create a file called `monitor_performance.py` with the following content:

```python
#!/usr/bin/env python3
import time
import requests
import psutil
import matplotlib.pyplot as plt
import numpy as np
from datetime import datetime
import os
import json

def monitor_endpoint(url, duration=60, interval=1):
    """
    Monitor an endpoint for a specified duration.
    
    Args:
        url (str): URL to monitor
        duration (int): Duration in seconds
        interval (int): Interval between requests in seconds
        
    Returns:
        dict: Monitoring results
    """
    print(f"Monitoring {url} for {duration} seconds (interval: {interval}s)")
    
    start_time = time.time()
    end_time = start_time + duration
    
    results = {
        'timestamps': [],
        'response_times': [],
        'status_codes': [],
        'cpu_usage': [],
        'memory_usage': []
    }
    
    while time.time() < end_time:
        # Record timestamp
        timestamp = datetime.now().strftime('%H:%M:%S')
        results['timestamps'].append(timestamp)
        
        # Record system metrics
        results['cpu_usage'].append(psutil.cpu_percent())
        results['memory_usage'].append(psutil.virtual_memory().percent)
        
        # Make request
        try:
            request_start = time.time()
            response = requests.get(url, timeout=10)
            request_end = time.time()
            
            # Record response metrics
            results['response_times'].append(request_end - request_start)
            results['status_codes'].append(response.status_code)
            
            print(f"[{timestamp}] {response.status_code} in {request_end - request_start:.2f}s (CPU: {results['cpu_usage'][-1]}%, Memory: {results['memory_usage'][-1]}%)")
        except Exception as e:
            # Record error
            results['response_times'].append(None)
            results['status_codes'].append(None)
            
            print(f"[{timestamp}] Error: {e}")
        
        # Wait for next interval
        time.sleep(interval)
    
    return results

def analyze_results(results, endpoint):
    """
    Analyze monitoring results.
    
    Args:
        results (dict): Monitoring results
        endpoint (str): Endpoint being monitored
    """
    # Filter out None values
    response_times = [t for t in results['response_times'] if t is not None]
    
    if not response_times:
        print("No successful requests to analyze")
        return
    
    # Calculate statistics
    avg_response_time = np.mean(response_times)
    min_response_time = np.min(response_times)
    max_response_time = np.max(response_times)
    p95_response_time = np.percentile(response_times, 95)
    
    success_count = results['status_codes'].count(200)
    total_count = len([s for s in results['status_codes'] if s is not None])
    success_rate = (success_count / total_count * 100) if total_count > 0 else 0
    
    avg_cpu = np.mean(results['cpu_usage'])
    avg_memory = np.mean(results['memory_usage'])
    
    print("\nResults:")
    print(f"Average response time: {avg_response_time:.2f}s")
    print(f"Minimum response time: {min_response_time:.2f}s")
    print(f"Maximum response time: {max_response_time:.2f}s")
    print(f"95th percentile response time: {p95_response_time:.2f}s")
    print
