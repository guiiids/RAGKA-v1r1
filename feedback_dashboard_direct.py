#!/usr/bin/env python3
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import webbrowser
from pathlib import Path
from dotenv import load_dotenv
import json
from datetime import datetime
import html

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

def truncate_text(text, length=100):
    """Truncate text to specified length."""
    if not text:
        return ""
    
    if len(text) <= length:
        return html.escape(text)
    
    return html.escape(text[:length]) + "..."

def create_tag_badges(tags):
    """Create HTML for tag badges."""
    if not tags or len(tags) == 0:
        return '<span class="text-gray-400">No tags</span>'
    
    badges_html = []
    for tag in tags:
        # Determine badge color based on tag content
        color_class = "bg-blue-100 text-blue-800"
        
        tag_lower = tag.lower()
        if "good" in tag_lower or "accurate" in tag_lower:
            color_class = "bg-green-100 text-green-800"
        elif "incorrect" in tag_lower or "wrong" in tag_lower:
            color_class = "bg-red-100 text-red-800"
        elif "unclear" in tag_lower or "confusing" in tag_lower:
            color_class = "bg-yellow-100 text-yellow-800"
        
        badge = f'<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium {color_class} mr-2 mb-1">{html.escape(tag)}</span>'
        badges_html.append(badge)
    
    return ''.join(badges_html)

def generate_table_rows(feedback_data):
    """Generate HTML table rows for feedback data."""
    if not feedback_data or len(feedback_data) == 0:
        return """
            <tr>
                <td colspan="5" class="px-6 py-4 text-center text-gray-500">
                    No feedback data available.
                </td>
            </tr>
        """
    
    rows_html = []
    for feedback in feedback_data:
        user_query = truncate_text(feedback.get('user_query', ''))
        bot_response = truncate_text(feedback.get('bot_response', ''))
        comment = html.escape(feedback.get('comment', '') or '')
        timestamp = feedback.get('timestamp', '')
        
        tag_badges = create_tag_badges(feedback.get('feedback_tags', []))
        
        row = f"""
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{timestamp}</td>
                <td class="px-6 py-4 text-sm text-gray-500" title="{html.escape(feedback.get('user_query', ''))}">
                    {user_query}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500" title="{html.escape(feedback.get('bot_response', ''))}">
                    {bot_response}
                </td>
                <td class="px-6 py-4 text-sm">
                    {tag_badges}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">{comment}</td>
            </tr>
        """
        rows_html.append(row)
    
    return ''.join(rows_html)

def generate_dashboard_html(feedback_data):
    """Generate complete HTML for the dashboard."""
    table_rows = generate_table_rows(feedback_data)
    
    html_content = f"""
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
                            {table_rows}
                        </tbody>
                    </table>
                </div>
            </div>
            
            <div class="mt-4 text-sm text-gray-500">
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                <p>Connected directly to PostgreSQL database: {DB_PARAMS['host']}</p>
            </div>
        </div>
    </body>
    </html>
    """
    
    return html_content

def main():
    """Main function to generate and display the dashboard."""
    try:
        print("Connecting to PostgreSQL database...")
        feedback_data = get_all_feedback()
        print(f"Retrieved {len(feedback_data)} feedback records.")
        
        # Generate HTML content
        html_content = generate_dashboard_html(feedback_data)
        
        # Write to file
        output_path = Path('feedback_dashboard_output.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Dashboard generated at: {output_path.absolute()}")
        
        # Open in browser
        webbrowser.open(output_path.absolute().as_uri())
        print("Dashboard opened in your default web browser.")
        
    except Exception as e:
        print(f"Error generating dashboard: {e}")

if __name__ == '__main__':
    main()
