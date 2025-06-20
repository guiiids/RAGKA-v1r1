#!/usr/bin/env python3
"""
Feedback Dashboard - Final Version

A single-file script that connects directly to PostgreSQL and generates a dashboard
displaying all feedback data in a clean, minimalist table with Tailwind styling.

Usage:
    python feedback_dashboard_final.py

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
from datetime import datetime, timedelta

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
            <div class="p-4 border-b border-gray-200">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <h2 class="text-lg font-semibold text-gray-700">All Feedback</h2>
                        <p class="text-sm text-gray-500">Total: <span id="total-count">__TOTAL_COUNT__</span> entries</p>
                    </div>
                    <div class="flex items-center">
                        <input type="text" id="search-input" placeholder="Search..." class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                    </div>
                </div>
                
                <!-- Date Range Filter -->
                <div class="flex flex-wrap items-center gap-4">
                    <div class="flex items-center">
                        <label for="date-range" class="mr-2 text-sm font-medium text-gray-700">Date Range:</label>
                        <select id="date-range" class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <option value="all">All Time</option>
                            <option value="yesterday">Yesterday</option>
                            <option value="last7">Last 7 Days</option>
                            <option value="last14">Last 14 Days</option>
                            <option value="last30">Last 30 Days</option>
                            <option value="custom">Custom Range</option>
                        </select>
                    </div>
                    
                    <!-- Status Filter -->
                    <div class="flex items-center">
                        <label for="status-filter" class="mr-2 text-sm font-medium text-gray-700">Status:</label>
                        <select id="status-filter" class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                            <option value="all">All</option>
                            <option value="positive">Positive</option>
                            <option value="negative">Negative</option>
                        </select>
                    </div>
                    
                    <div id="custom-date-range" class="hidden flex items-center gap-2">
                        <label for="start-date" class="text-sm font-medium text-gray-700">From:</label>
                        <input type="date" id="start-date" class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                        
                        <label for="end-date" class="text-sm font-medium text-gray-700">To:</label>
                        <input type="date" id="end-date" class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent">
                        
                        <button id="apply-date-filter" class="px-3 py-2 bg-blue-500 text-white rounded-md text-sm hover:bg-blue-600 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2">
                            Apply
                        </button>
                    </div>
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
        // Date range presets
        const dateRangePresets = __DATE_RANGE_PRESETS__;
        
        // Initialize date inputs with today's date
        document.addEventListener('DOMContentLoaded', function() {
            const today = new Date();
            const todayStr = today.toISOString().split('T')[0];
            
            document.getElementById('end-date').value = todayStr;
            
            // Set start date to 7 days ago by default
            const sevenDaysAgo = new Date();
            sevenDaysAgo.setDate(today.getDate() - 7);
            document.getElementById('start-date').value = sevenDaysAgo.toISOString().split('T')[0];
        });
        
        // Date range selector functionality
        document.getElementById('date-range').addEventListener('change', function() {
            const customDateRange = document.getElementById('custom-date-range');
            
            if (this.value === 'custom') {
                customDateRange.classList.remove('hidden');
            } else {
                customDateRange.classList.add('hidden');
                
                if (this.value !== 'all') {
                    const preset = dateRangePresets[this.value];
                    resetAllFilters();
                    filterByDateRange(preset.start_date, preset.end_date);
                } else {
                    // Show all rows when "All Time" is selected
                    resetAllFilters();
                }
            }
        });
        
        // Apply custom date range filter
        document.getElementById('apply-date-filter').addEventListener('click', function() {
            const startDate = document.getElementById('start-date').value;
            const endDate = document.getElementById('end-date').value;
            
            if (startDate && endDate) {
                resetAllFilters();
                filterByDateRange(startDate, endDate);
            }
        });
        
        // Filter table by date range
        function filterByDateRange(startDate, endDate) {
            const rows = document.querySelectorAll('#feedback-table-body tr');
            const startTimestamp = new Date(startDate + 'T00:00:00').getTime();
            const endTimestamp = new Date(endDate + 'T23:59:59').getTime();
            
            let visibleCount = 0;
            
            rows.forEach(row => {
                const dateCell = row.cells[0].textContent.trim();
                const rowTimestamp = new Date(dateCell).getTime();
                
                if (rowTimestamp >= startTimestamp && rowTimestamp <= endTimestamp) {
                    row.style.display = '';
                    visibleCount++;
                } else {
                    row.style.display = 'none';
                }
            });
            
            document.getElementById('total-count').textContent = visibleCount;
            
            // Apply status filter after date filter
            applyStatusFilter();
        }
        
        // Show all rows (reset date filter)
        function showAllRows() {
            const rows = document.querySelectorAll('#feedback-table-body tr');
            
            rows.forEach(row => {
                row.style.display = '';
            });
            
            document.getElementById('total-count').textContent = rows.length;
            
            // Apply status filter after resetting date filter
            applyStatusFilter();
        }
        
        // Status filter functionality
        document.getElementById('status-filter').addEventListener('change', function() {
            // Get current date filter
            const dateFilter = document.getElementById('date-range').value;
            
            if (dateFilter === 'all') {
                resetAllFilters();
                applyStatusFilter();
            } else if (dateFilter === 'custom') {
                // For custom date range, reapply the date filter first
                const startDate = document.getElementById('start-date').value;
                const endDate = document.getElementById('end-date').value;
                
                if (startDate && endDate) {
                    resetAllFilters();
                    filterByDateRange(startDate, endDate);
                    applyStatusFilter();
                } else {
                    resetAllFilters();
                    applyStatusFilter();
                }
            } else {
                // For preset date ranges
                resetAllFilters();
                const preset = dateRangePresets[dateFilter];
                filterByDateRange(preset.start_date, preset.end_date);
                applyStatusFilter();
            }
        });
        
        function applyStatusFilter() {
            const statusFilter = document.getElementById('status-filter').value;
            const rows = document.querySelectorAll('#feedback-table-body tr');
            
            let visibleCount = 0;
            let positiveCount = 0;
            let negativeCount = 0;
            
            // First, count how many of each status we have (for debugging)
            rows.forEach(row => {
                if (row.style.display !== 'none') {
                    const statusCell = row.cells[3].textContent.trim().toLowerCase();
                    if (statusCell.includes('positive')) {
                        positiveCount++;
                    } else if (statusCell.includes('negative')) {
                        negativeCount++;
                    }
                }
            });
            
            console.log(`Before filtering - Positive: ${positiveCount}, Negative: ${negativeCount}`);
            
            if (statusFilter === 'all') {
                // Don't filter by status, but respect other filters
                rows.forEach(row => {
                    if (row.style.display !== 'none') {
                        visibleCount++;
                    }
                });
            } else {
                rows.forEach(row => {
                    if (row.style.display !== 'none') {  // Only filter visible rows (respecting date filter)
                        const statusCell = row.cells[3].textContent.trim().toLowerCase();
                        console.log(`Row status: "${statusCell}"`);
                        
                        if ((statusFilter === 'positive' && statusCell.includes('positive')) || 
                            (statusFilter === 'negative' && statusCell.includes('negative'))) {
                            // Keep row visible
                            visibleCount++;
                        } else {
                            // Hide row
                            row.style.display = 'none';
                        }
                    }
                });
            }
            
            // Debug: Log counts to console
            console.log(`Status filter: ${statusFilter}, Visible count: ${visibleCount}`);
            
            document.getElementById('total-count').textContent = visibleCount;
        }
        
        // Search functionality
        document.getElementById('search-input').addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const rows = document.querySelectorAll('#feedback-table-body tr');
            
            let visibleCount = 0;
            
            rows.forEach(row => {
                if (row.style.display !== 'none') {  // Only search visible rows (respecting date filter)
                    const text = row.textContent.toLowerCase();
                    if (text.includes(searchTerm)) {
                        row.style.display = '';
                        visibleCount++;
                    } else {
                        row.style.display = 'none';
                    }
                }
            });
            
            document.getElementById('total-count').textContent = visibleCount;
            
            // Apply status filter after search
            applyStatusFilter();
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
        
        // Function to reset all filters and show all rows
        function resetAllFilters() {
            const rows = document.querySelectorAll('#feedback-table-body tr');
            rows.forEach(row => {
                row.style.display = '';
            });
            document.getElementById('total-count').textContent = rows.length;
        }
        
        // Initialize with timestamp sorting (newest first) and apply filters
        document.addEventListener('DOMContentLoaded', function() {
            sortTable(0); // Sort by timestamp column
            
            // Initial application of filters
            resetAllFilters();
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

def get_all_feedback(start_date=None, end_date=None):
    """
    Fetch all feedback data from the database.
    
    Args:
        start_date (str, optional): Start date for filtering in 'YYYY-MM-DD' format
        end_date (str, optional): End date for filtering in 'YYYY-MM-DD' format
    
    Returns:
        list: List of feedback data dictionaries
    """
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor(cursor_factory=RealDictCursor) as cursor:
            query = """
                SELECT vote_id, user_query, bot_response, feedback_tags, comment, timestamp
                FROM votes
            """
            
            params = []
            
            # Add date filtering if provided
            if start_date or end_date:
                conditions = []
                
                if start_date:
                    conditions.append("timestamp >= %s")
                    params.append(f"{start_date} 00:00:00")
                
                if end_date:
                    conditions.append("timestamp <= %s")
                    params.append(f"{end_date} 23:59:59")
                
                if conditions:
                    query += " WHERE " + " AND ".join(conditions)
            
            query += " ORDER BY timestamp DESC"
            
            cursor.execute(query, params)
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
    """Determine if feedback is positive or negative based on tags."""
    if not tags or len(tags) == 0:
        return {
            'status': 'Negative',
            'class': 'badge badge-red'
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
    
    # Default to negative for any non-positive feedback
    return {
        'status': 'Negative',
        'class': 'badge badge-red'
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
        
        # Determine feedback status (only Positive or Negative)
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
    
    # Get date range presets for JavaScript
    date_presets = get_date_range_presets()
    date_presets_json = str(date_presets).replace("'", '"')
    
    # Replace placeholders in the template
    html_content = HTML_TEMPLATE
    html_content = html_content.replace('__TABLE_ROWS__', table_rows)
    html_content = html_content.replace('__TOTAL_COUNT__', str(len(feedback_data)))
    html_content = html_content.replace('__GENERATION_TIME__', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    html_content = html_content.replace('__DB_HOST__', DB_PARAMS['host'])
    html_content = html_content.replace('__DATE_RANGE_PRESETS__', date_presets_json)
    
    return html_content

def get_date_range_presets():
    """Generate preset date ranges for filtering."""
    today = datetime.now().date()
    
    return {
        'yesterday': {
            'start_date': (today - timedelta(days=1)).isoformat(),
            'end_date': (today - timedelta(days=1)).isoformat()
        },
        'last7': {
            'start_date': (today - timedelta(days=7)).isoformat(),
            'end_date': today.isoformat()
        },
        'last14': {
            'start_date': (today - timedelta(days=14)).isoformat(),
            'end_date': today.isoformat()
        },
        'last30': {
            'start_date': (today - timedelta(days=30)).isoformat(),
            'end_date': today.isoformat()
        }
    }

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
