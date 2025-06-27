#!/usr/bin/env python3
from flask import Flask, render_template, jsonify
import psycopg2
from psycopg2.extras import RealDictCursor
import os
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# Database connection parameters
DB_PARAMS = {
    'host': os.getenv('POSTGRES_HOST'),
    'port': os.getenv('POSTGRES_PORT'),
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'sslmode': os.getenv('POSTGRES_SSL_MODE', 'require')
}

app = Flask(__name__)

# HTML template for the dashboard
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Feedback Dashboard</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <h1 class="text-2xl font-bold text-gray-800 mb-6">Feedback Dashboard</h1>
        
        <div class="bg-white dark:bg-black text-white shadow-md rounded-lg overflow-hidden">
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User Query</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Response</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tags</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comments</th>
                        </tr>
                    </thead>
                    <tbody class="bg-white dark:bg-black text-white dark:bg-black divide-y divide-gray-200">
                        {% if feedback_data %}
                            {% for feedback in feedback_data %}
                                <tr class="hover:bg-gray-50">
                                    <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{{ feedback.timestamp }}</td>
                                    <td class="px-6 py-4 text-sm text-gray-500" title="{{ feedback.user_query }}">
                                        {{ feedback.user_query|truncate(100) }}
                                    </td>
                                    <td class="px-6 py-4 text-sm text-gray-500" title="{{ feedback.bot_response }}">
                                        {{ feedback.bot_response|truncate(100) }}
                                    </td>
                                    <td class="px-6 py-4 text-sm">
                                        {% if feedback.feedback_tags %}
                                            {% for tag in feedback.feedback_tags %}
                                                {% set color_class = "bg-blue-100 text-blue-800" %}
                                                {% if "good" in tag.lower() or "accurate" in tag.lower() %}
                                                    {% set color_class = "bg-green-100 text-green-800" %}
                                                {% elif "incorrect" in tag.lower() or "wrong" in tag.lower() %}
                                                    {% set color_class = "bg-red-100 text-red-800" %}
                                                {% elif "unclear" in tag.lower() or "confusing" in tag.lower() %}
                                                    {% set color_class = "bg-yellow-100 text-yellow-800" %}
                                                {% endif %}
                                                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {{ color_class }} mr-2 mb-1">{{ tag }}</span>
                                            {% endfor %}
                                        {% else %}
                                            <span class="text-gray-400">No tags</span>
                                        {% endif %}
                                    </td>
                                    <td class="px-6 py-4 text-sm text-gray-500">{{ feedback.comment or "" }}</td>
                                </tr>
                            {% endfor %}
                        {% else %}
                            <tr>
                                <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                                    No feedback data available.
                                </td>
                            </tr>
                        {% endif %}
                    </tbody>
                </table>
            </div>
        </div>
    </div>
</body>
</html>
"""

def get_db_connection():
    """Create and return a database connection."""
    try:
        conn = psycopg2.connect(**DB_PARAMS)
        return conn
    except Exception as e:
        print(f"Database connection error: {e}")
        raise

def get_all_feedback():
    """Fetch all feedback data from the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute("""
                SELECT vote_id, user_query, bot_response, feedback_tags, comment, timestamp
                FROM votes
                ORDER BY timestamp DESC
            """)
            feedback_data = cursor.fetchall()
            
            # Convert to list of dictionaries and format timestamps
            result = []
            for row in feedback_data:
                # Convert timestamp to string format
                if row['timestamp']:
                    row['timestamp'] = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                
                # Ensure feedback_tags is a list
                if row['feedback_tags'] is None:
                    row['feedback_tags'] = []
                
                result.append(dict(row))
            
            return result
    except Exception as e:
        print(f"Error fetching feedback data: {e}")
        return []
    finally:
        if conn:
            conn.close()

@app.template_filter('truncate')
def truncate_filter(text, length=100):
    """Truncate text to specified length."""
    if not text:
        return ""
    
    if len(text) <= length:
        return text
    
    return text[:length] + "..."

@app.route('/')
def dashboard():
    """Render the feedback dashboard."""
    feedback_data = get_all_feedback()
    return render_template_string(DASHBOARD_HTML, feedback_data=feedback_data)

if __name__ == '__main__':
    # Add template_filter to Flask app
    app.jinja_env.filters['truncate'] = truncate_filter
    
    # Run the Flask app
    port = int(os.getenv('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
