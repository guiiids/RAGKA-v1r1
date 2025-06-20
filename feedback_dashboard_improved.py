#!/usr/bin/env python3
"""
Feedback Dashboard - Improved Standalone Version

A single-file script that connects directly to PostgreSQL and generates a dashboard
displaying all feedback data in a clean, minimalist table with Tailwind styling.

Usage:
    python feedback_dashboard_improved.py

Requirements:
    - psycopg2
    - python-dotenv
"""

import psycopg2
from psycopg2.extras import RealDictCursor
import os
import webbrowser
from pathlib import Path
from dotenv import load_dotenv
import html
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

# HTML template for the dashboard
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Feedback Dashboard</title>
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .truncate-text {
            max-width: 250px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        
        @media (max-width: 1024px) {
            .truncate-text {
                max-width: 200px;
            }
        }
        
        @media (max-width: 768px) {
            .truncate-text {
                max-width: 150px;
            }
        }
        
        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.75rem;
            font-weight: 500;
            line-height: 1;
            margin-right: 0.5rem;
            margin-bottom: 0.25rem;
            white-space: nowrap;
        }
        
        .badge-green {
            background-color: #d1fae5;
            color: #065f46;
        }
        
        .badge-red {
            background-color: #fee2e2;
            color: #b91c1c;
        }
        
        .badge-yellow {
            background-color: #fef3c7;
            color: #92400e;
        }
        
        .badge-blue {
            background-color: #dbeafe;
            color: #1e40af;
        }
        
        .badge-gray {
            background-color: #f3f4f6;
            color: #4b5563;
        }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-2xl font-bold text-gray-800">Feedback Dashboard</h1>
            <p class="text-sm text-gray-500 mt-2">Displaying all feedback data from PostgreSQL database</p>
        </header>
        
        <div class="bg-white shadow-md rounded-lg overflow-hidden">
            <div class="p-4 border-b border-gray-200 flex justify-between items-center">
                <div>
                    <h2 class="text-lg font-semibold text-gray-700">All Feedback</h2>
                    <p class="text-sm text-gray-500">Total: <span id="total-count">__TOTAL_COUNT__</span> entries</p>
                </div>
                <div class="flex items-center">
                    <input type="text" id="search-input" placeholder="Search..." class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                </div>
            </div>
            
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer" onclick="sortTable(0)">
                                Timestamp <span class="sort-icon">↕</span>
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                User Query
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Response
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Status
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Tags
                            </th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                Comments
                            </th>
                        </tr>
                    </thead>
                    <tbody class="bg-white divide-y divide-gray-200" id="feedback-table-body">
                        __TABLE_ROWS__
                    </tbody>
                </table>
            </div>
        </div>
        
        <footer class="mt-8 text-center text-sm text-gray-500">
            <p>Generated on __GENERATION_TIME__</p>
            <p>Connected directly to PostgreSQL database: __DB_HOST__</p>
        </footer>
    </div>

    <script>
        // Search functionality
        document.getElementById('search-input').addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#feedback-table-body tr');
            
            let visibleCount = 0;
            
            rows.forEach(row => {
                const text = row.textContent.toLowerCase();
                if (text.includes(searchTerm)) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            document.getElementById('total-count').textContent = visibleCount;
        });
        
        // Table sorting functionality
        let sortDirection = 1; // 1 for ascending, -1 for descending
        
        function sortTable(columnIndex) {
            const table = document.querySelector('table');
            const tbody = document.getElementById('feedback-table-body');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            
            // Toggle sort direction
            sortDirection = -sortDirection;
            
            // Update sort icons
            document.querySelectorAll('.sort-icon').forEach(icon => {
                icon.textContent = '↕';
            });
            
            const currentIcon = document.querySelectorAll('th')[columnIndex].querySelector('.sort-icon');
            currentIcon.textContent = sortDirection === 1 ? '↑' : '↓';
            
            // Sort the rows
            rows.sort((a, b) => {
                const aValue = a.cells[columnIndex].textContent.trim();
                const bValue = b.cells[columnIndex].textContent.trim();
                
                // For timestamp column, parse as dates
                if (columnIndex === 0) {
                    return sortDirection * (new Date(aValue) - new Date(bValue));
                }
                
                // For text columns, compare as strings
                return sortDirection * aValue.localeCompare(bValue);
            });
            
            // Remove existing rows
            rows.forEach(row => {
                tbody.removeChild(row);
            });
            
            // Add sorted rows
            rows.forEach(row => {
                tbody.appendChild(row);
            });
        }
        
        // Initialize with timestamp sorting (newest first)
        document.addEventListener('DOMContentLoaded', function() {
            sortTable(0); // Sort by timestamp column
        });
    </script>
</body>
</html>"""

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

def determine_feedback_status(tags):
    """Determine the feedback status based on tags."""
    if not tags or len(tags) == 0:
        return {
            'status': 'Neutral',
            'class': 'badge badge-gray'
        }
    
    # Check for positive feedback
    positive_indicators = ['good', 'accurate', 'helpful', 'clear', 'looks good']
    for tag in tags:
        tag_lower = tag.lower()
        for indicator in positive_indicators:
            if indicator in tag_lower:
                return {
                    'status': 'Positive',
                    'class': 'badge badge-green'
                }
    
    # Check for negative feedback
    negative_indicators = ['incorrect', 'wrong', 'bad', 'error', 'unclear', 'confusing', 'irrelevant']
    for tag in tags:
        tag_lower = tag.lower()
        for indicator in negative_indicators:
            if indicator in tag_lower:
                return {
                    'status': 'Negative',
                    'class': 'badge badge-red'
                }
    
    # If no clear positive or negative indicators, check for specific categories
    for tag in tags:
        tag_lower = tag.lower()
        if 'incomplete' in tag_lower:
            return {
                'status': 'Incomplete',
                'class': 'badge badge-yellow'
            }
        elif 'data source quality' in tag_lower:
            return {
                'status': 'Data Issue',
                'class': 'badge badge-blue'
            }
        elif 'other issue' in tag_lower:
            return {
                'status': 'Other Issue',
                'class': 'badge badge-blue'
            }
    
    # Default to neutral
    return {
        'status': 'Other',
        'class': 'badge badge-blue'
    }

def create_tag_badges(tags):
    """Create HTML for tag badges."""
    if not tags or len(tags) == 0:
        return '<span class="text-gray-400">No tags</span>'
    
    badges_html = []
    for tag in tags:
        # Determine badge color based on tag content
        badge_class = "badge badge-blue"
        
        tag_lower = tag.lower()
        if "good" in tag_lower or "accurate" in tag_lower or "helpful" in tag_lower:
            badge_class = "badge badge-green"
        elif "incorrect" in tag_lower or "wrong" in tag_lower:
            badge_class = "badge badge-red"
        elif "unclear" in tag_lower or "confusing" in tag_lower or "incomplete" in tag_lower:
            badge_class = "badge badge-yellow"
        
        badge = f'<span class="{badge_class}">{html.escape(tag)}</span>'
        badges_html.append(badge)
    
    return ''.join(badges_html)

def generate_table_rows(feedback_data):
    """Generate HTML table rows for feedback data."""
    if not feedback_data or len(feedback_data) == 0:
        return """
            <tr>
                <td colspan="6" class="px-6 py-4 text-center text-gray-500">
                    No feedback data available.
                </td>
            </tr>
        """
    
    rows_html = []
    for feedback in feedback_data:
        user_query = html.escape(feedback.get('user_query', '') or '')
        bot_response = html.escape(feedback.get('bot_response', '') or '')
        comment = html.escape(feedback.get('comment', '') or '')
        timestamp = feedback.get('timestamp', '')
        tags = feedback.get('feedback_tags', [])
        
        # Determine feedback status
        status = determine_feedback_status(tags)
        status_badge = f'<span class="{status["class"]}">{status["status"]}</span>'
        
        # Create tag badges
        tag_badges = create_tag_badges(tags)
        
        row = f"""
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{timestamp}</td>
                <td class="px-6 py-4 text-sm text-gray-500">
                    <div class="truncate-text" title="{user_query}">{user_query}</div>
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">
                    <div class="truncate-text" title="{bot_response}">{bot_response}</div>
                </td>
                <td class="px-6 py-4 text-sm">
                    {status_badge}
                </td>
                <td class="px-6 py-4 text-sm">
                    {tag_badges}
                </td>
                <td class="px-6 py-4 text-sm text-gray-500">
                    <div class="truncate-text" title="{comment}">{comment}</div>
                </td>
            </tr>
        """
        rows_html.append(row)
    
    return ''.join(rows_html)

def generate_dashboard_html(feedback_data):
    """Generate complete HTML for the dashboard."""
    table_rows = generate_table_rows(feedback_data)
    
    # Replace placeholders in the template
    html_content = HTML_TEMPLATE
    html_content = html_content.replace('__TABLE_ROWS__', table_rows)
    html_content = html_content.replace('__TOTAL_COUNT__', str(len(feedback_data)))
    html_content = html_content.replace('__GENERATION_TIME__', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    html_content = html_content.replace('__DB_HOST__', DB_PARAMS['host'])
    
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
        output_path = Path('feedback_dashboard.html')
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
