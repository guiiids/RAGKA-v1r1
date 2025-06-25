#!/usr/bin/env python3
"""
Feedback Dashboard - Final Version 2 (Fixed)

A single-file script that connects directly to PostgreSQL and generates a dashboard
displaying all feedback data in a clean, minimalist table with Tailwind styling,
plus additional metrics summary above the table and two charts:
- Requests per hour (last 6 hours)
- Word cloud of queries and tags

Usage:
    python feedback_dashboard_final_2.py

Requirements:
    - psycopg2-binary
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
import json
import collections
import re

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

# Path to OpenAI calls log
LOG_PATH = os.path.join('logs', 'openai_calls.jsonl')

# HTML template for the dashboard
HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
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
        
        @media (max-width: 1024px) { .truncate-text { max-width: 200px; } }
        @media (max-width: 768px) { .truncate-text { max-width: 150px; } }
        
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
        
        .badge-green { background-color: #d1fae5; color: #065f46; }
        .badge-red { background-color: #fee2e2; color: #b91c1c; }
        .badge-yellow { background-color: #fef3c7; color: #92400e; }
        .badge-blue { background-color: #dbeafe; color: #1e40af; }
        .badge-gray { background-color: #f3f4f6; color: #4b5563; }
        .size-4 { width: 1rem; height: 1rem; }
    </style>
</head>
<body class="bg-gray-100">
    <div class="container mx-auto px-4 py-8">
        <header class="mb-8">
            <h1 class="text-2xl font-bold text-gray-800">Feedback Dashboard</h1>
            <p class="text-sm text-gray-500 mt-2">Displaying all feedback data from PostgreSQL database</p>
        </header>
        
        <!-- Metrics Summary Section -->
        <div class="mb-6 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            __METRICS_SUMMARY__
        </div>

        <!-- Charts Section -->
        <div class="my-8 bg-white p-6 rounded-lg shadow-md">
          <h2 class="text-xl font-semibold mb-4">Requests Per Hour (Last 6 Hours)</h2>
          <canvas id="requestsPerHourChart" class="w-full h-64"></canvas>
        </div>
        <div class="my-8 bg-white p-6 rounded-lg shadow-md">
          <h2 class="text-xl font-semibold mb-4">Word Cloud of Queries and Tags</h2>
          <canvas id="wordCloudCanvas" width="600" height="400"></canvas>
        </div>
        
        <div class="relative isolate overflow-hidden bg-white py-24 sm:py-32">
          <!-- Decorative background gradient element -->
          <div class="absolute -top-80 left-[max(6rem,33%)] -z-10 transform-gpu blur-3xl sm:left-1/2 md:top-20 lg:ml-20 xl:top-3 xl:ml-56" aria-hidden="true">
            <div class="aspect-[801/1036] w-[50.0625rem] bg-gradient-to-tr from-[#ff80b5] to-[#9089fc] opacity-30" style="clip-path: polygon(63.1% 29.6%, 100% 17.2%, 76.7% 3.1%, 48.4% 0.1%, 44.6% 4.8%, 54.5% 25.4%, 59.8% 49.1%, 55.3% 57.9%, 44.5% 57.3%, 27.8% 48%, 35.1% 81.6%, 0% 97.8%, 39.3% 100%, 35.3% 81.5%, 97.2% 52.8%, 63.1% 29.6%)"></div>
          </div>
  
          <!-- Centered content area -->
          <div class="mx-auto max-w-7xl px-6 lg:px-8">
              <!-- User's feedback analytics list, styled as a glassmorphism card -->
              <div class="bg-white/80 backdrop-blur-sm shadow-2xl rounded-2xl p-6 sm:p-10 max-w-6xl mx-auto space-y-8 text-gray-800 ring-1 ring-gray-900/5">
                  <h2 class="text-3xl font-bold tracking-tight border-b border-gray-200 pb-4 text-gray-900">Feedback Analytics Overview</h2>
                  <div class="grid md:grid-cols-2 gap-8">
                      <!-- Card 1 -->
                      <div class="bg-gray-50/70 rounded-xl p-6 shadow-sm ring-1 ring-gray-900/5">
                          <h3 class="text-xl font-semibold mb-2 text-gray-900">1. Feedback Volume Over Time</h3>
                          <p class="text-sm leading-relaxed text-gray-700">Show total feedback counts per day/week/month to spot usage spikes or lulls.<br>Overlay positive vs. negative trends to see sentiment shifts over time.</p>
                      </div>
                      <!-- Card 2 -->
                      <div class="bg-gray-50/70 rounded-xl p-6 shadow-sm ring-1 ring-gray-900/5">
                          <h3 class="text-xl font-semibold mb-2 text-gray-900">2. Positive vs. Negative Ratio</h3>
                          <p class="text-sm leading-relaxed text-gray-700">A simple card showing % positive feedback this period.<br>A sparkline next to it tracking change over the last N days.</p>
                      </div>
                      <!-- Card 3 -->
                      <div class="bg-gray-50/70 rounded-xl p-6 shadow-sm ring-1 ring-gray-900/5">
                          <h3 class="text-xl font-semibold mb-2 text-gray-900">3. Tag Frequency Distribution</h3>
                          <p class="text-sm leading-relaxed text-gray-700">Count of each feedback tag (e.g. “helpful”, “inaccurate”, “confusing”).<br>Helps identify the most common user concerns or praises.</p>
                      </div>
                      <!-- Card 4 -->
                      <div class="bg-gray-50/70 rounded-xl p-6 shadow-sm ring-1 ring-gray-900/5">
                          <h3 class="text-xl font-semibold mb-2 text-gray-900">4. Top Queries by Feedback</h3>
                          <p class="text-sm leading-relaxed text-gray-700">List the top 10 user queries that received the most feedback.<br>Show counts and average sentiment per query.</p>
                      </div>
                  </div>
              </div>
          </div>
        </div>
  
        <div class="bg-white shadow-md rounded-lg overflow-hidden">
            <div class="p-4 border-b border-gray-200">
                <div class="flex justify-between items-center mb-4">
                    <div>
                        <h2 class="text-lg font-semibold text-gray-700">All Feedback</h2>
                        <p class="text-sm text-gray-500">Total: <span id="total-count">__TOTAL_COUNT__</span> entries</p>
                    </div>
                    <div class="flex items-center">
                        <input type="text" id="search-input" placeholder="Search..." class="px-3 py-2 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent" />
                    </div>
                </div>
            </div>
            
            <div class="overflow-x-auto">
                <table class="min-w-full divide-y divide-gray-200">
                    <thead class="bg-gray-50">
                        <tr>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Timestamp</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User Query</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Response</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Tags</th>
                            <th scope="col" class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Comments</th>
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
            query = "SELECT vote_id, user_query, bot_response, feedback_tags, comment, timestamp FROM votes ORDER BY timestamp DESC"
            cursor.execute(query)
            feedback_data = cursor.fetchall()
            
            result = []
            for row in feedback_data:
                if row.get('timestamp'):
                    row['timestamp'] = row['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                if row.get('feedback_tags') is None:
                    row['feedback_tags'] = []
                result.append(dict(row))
            return result
    except Exception as e:
        print(f"Error fetching feedback data: {e}")
        return []
    finally:
        if conn:
            conn.close()

def get_total_queries():
    """Fetch total number of distinct user queries from the database."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT COUNT(DISTINCT user_query) FROM votes;")
            result = cursor.fetchone()
            return result[0] if result else 0
    except Exception as e:
        print(f"Error fetching total queries: {e}")
        return 0
    finally:
        if conn:
            conn.close()

def determine_feedback_status(tags):
    """Determine if feedback is positive or negative based on tags."""
    if not tags:
        return {'status': 'Negative', 'class': 'badge badge-red'}
    
    positive_indicators = ['good', 'accurate', 'helpful', 'clear', 'looks good']
    if any(indicator in tag.lower() for tag in tags for indicator in positive_indicators):
        return {'status': 'Positive', 'class': 'badge badge-green'}
    
    return {'status': 'Negative', 'class': 'badge badge-red'}

def create_tag_badges(tags):
    """Create HTML for tag badges."""
    if not tags:
        return '<span class="text-gray-400">No tags</span>'
    
    badges_html = []
    for tag in tags:
        tag_lower = tag.lower()
        if any(s in tag_lower for s in ["good", "accurate", "helpful"]):
            badge_class = "badge badge-green"
        elif any(s in tag_lower for s in ["incorrect", "wrong"]):
            badge_class = "badge badge-red"
        elif any(s in tag_lower for s in ["unclear", "confusing", "incomplete"]):
            badge_class = "badge badge-yellow"
        else:
            badge_class = "badge badge-blue"
        badges_html.append(f'<span class="{badge_class}">{html.escape(tag)}</span>')
    
    return ''.join(badges_html)

def generate_table_rows(feedback_data):
    """Generate HTML table rows for feedback data."""
    if not feedback_data:
        return '<tr><td colspan="6" class="px-6 py-4 text-center text-gray-500">No feedback data available.</td></tr>'
    
    rows_html = []
    for feedback in feedback_data:
        user_query = html.escape(feedback.get('user_query', ''))
        bot_response = html.escape(feedback.get('bot_response', ''))
        comment = html.escape(feedback.get('comment', '') or '')
        timestamp = feedback.get('timestamp', '')
        tags = feedback.get('feedback_tags', [])
        
        status = determine_feedback_status(tags)
        status_badge = f'<span class="{status["class"]}">{status["status"]}</span>'
        tag_badges = create_tag_badges(tags)
        
        row = f"""
            <tr class="hover:bg-gray-50">
                <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">{timestamp}</td>
                <td class="px-6 py-4 text-sm text-gray-500"><div class="truncate-text" title="{user_query}">{user_query}</div></td>
                <td class="px-6 py-4 text-sm text-gray-500"><div class="truncate-text" title="{bot_response}">{bot_response}</div></td>
                <td class="px-6 py-4 text-sm">{status_badge}</td>
                <td class="px-6 py-4 text-sm">{tag_badges}</td>
                <td class="px-6 py-4 text-sm text-gray-500"><div class="truncate-text" title="{comment}">{comment}</div></td>
            </tr>
        """
        rows_html.append(row)
    
    return ''.join(rows_html)

def parse_openai_calls():
    """Parse the openai_calls.jsonl log file to compute total tokens per call."""
    tokens = []
    if not os.path.exists(LOG_PATH):
        return tokens
    with open(LOG_PATH, 'r') as f:
        for line in f:
            try:
                entry = json.loads(line)
                tot = entry.get('usage', {}).get('total_tokens')
                if isinstance(tot, (int, float)):
                    tokens.append(tot)
            except (json.JSONDecodeError, AttributeError):
                continue
    return tokens

def generate_metrics_summary_html(metrics):
    """Generate the HTML for the metrics summary section."""
    def metric_block(label, value, badge_color, badge_icon_svg, badge_text=""):
        return f'''
<article class="flex items-end justify-between rounded-lg border border-gray-100 bg-white p-6">
  <div>
    <p class="text-sm text-gray-500">{label}</p>
    <p class="text-2xl font-medium text-gray-900">{value}</p>
  </div>
  <div class="inline-flex gap-2 rounded-lg bg-{badge_color}-100 p-2 text-{badge_color}-600">
    {badge_icon_svg}
    <span class="text-xs font-medium">{badge_text}</span>
  </div>
</article>
'''
    up_arrow_svg = '<svg xmlns="http://www.w3.org/2000/svg" class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 7h8m0 0v8m0-8l-8 8-4-4-6 6"/></svg>'
    info_svg = '<svg xmlns="http://www.w3.org/2000/svg" class="size-4" fill="none" viewBox="0 0 24 24" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 16h-1v-4h-1m1-4h.01M12 20a8 8 0 100-16 8 8 0 000 16z"/></svg>'
    
    blocks = [
        metric_block("Total Queries", metrics['total_queries'], "blue", info_svg),
        metric_block("Total Feedback Entries", metrics['total_feedback'], "blue", info_svg),
        metric_block("Positive Feedback", f"{metrics['positive_feedback_count']} ({metrics['positive_feedback_pct']:.1f}%)", "green", up_arrow_svg, f"{metrics['positive_feedback_pct']:.1f}%"),
        metric_block("Avg. Tokens per Call", f"{metrics['avg_tokens']:.1f}", "blue", info_svg)
    ]
    return "\n".join(blocks)

def get_requests_per_hour():
    """Fetch count of requests grouped by hour from the database for the last 6 hours."""
    conn = None
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT to_char(date_trunc('hour', timestamp), 'YYYY-MM-DD HH24:00') AS hour, COUNT(*) AS count
                FROM votes
                WHERE timestamp >= NOW() - INTERVAL '6 hours'
                GROUP BY hour ORDER BY hour;
            """)
            return {row[0]: row[1] for row in cursor.fetchall()}
    except Exception as e:
        print(f"Error fetching requests per hour: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def get_word_frequencies():
    """Compute word frequencies from user queries and feedback tags, robustly handling tag formats."""
    conn = None
    word_counts = collections.Counter()
    try:
        conn = get_db_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT user_query, feedback_tags FROM votes;")
            rows = cursor.fetchall()
            for user_query, feedback_tags_data in rows:
                if user_query:
                    words = re.findall(r'\b\w+\b', user_query.lower())
                    word_counts.update(words)
                
                if not feedback_tags_data:
                    continue

                tags_to_process = []
                if isinstance(feedback_tags_data, list):
                    tags_to_process = feedback_tags_data
                elif isinstance(feedback_tags_data, str):
                    try:
                        # Safer parsing than eval()
                        parsed_tags = json.loads(feedback_tags_data)
                        if isinstance(parsed_tags, list):
                            tags_to_process = parsed_tags
                        else:
                            tags_to_process.append(str(parsed_tags))
                    except json.JSONDecodeError:
                        # Fallback for non-JSON strings (e.g., "{tag1,tag2}")
                        tags_to_process.append(feedback_tags_data)
                
                for tag in tags_to_process:
                    if isinstance(tag, str):
                        tag_words = re.findall(r'\b\w+\b', tag.lower())
                        word_counts.update(tag_words)
        
        # Remove common English stop words for a cleaner word cloud
        stop_words = set(['i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours', 'he', 'him', 'his', 'she', 'her', 'hers', 'it', 'its', 'they', 'them', 'their', 'theirs', 'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'of', 'at', 'by', 'for', 'with', 'about', 'to', 'from', 'in', 'out', 'on', 'off', 'over', 'so', 'than', 'too', 'very', 's', 't', 'can', 'will', 'just', 'don', 'should', 'now'])
        for word in stop_words:
            word_counts.pop(word, None)
            
        return dict(word_counts)
    except Exception as e:
        print(f"Error computing word frequencies: {e}")
        return {}
    finally:
        if conn:
            conn.close()

def generate_dashboard_html(feedback_data, metrics):
    """Generate complete HTML for the dashboard."""
    table_rows = generate_table_rows(feedback_data)
    metrics_summary_html = generate_metrics_summary_html(metrics)
    
    # FIX: Ensure all of the last 6 hours are represented in the chart data
    now = datetime.now()
    requests_per_hour_db = get_requests_per_hour()
    chart_labels = [(now - timedelta(hours=i)).strftime('%Y-%m-%d %H:00') for i in range(5, -1, -1)]
    chart_counts = [requests_per_hour_db.get(label, 0) for label in chart_labels]
    requests_per_hour_labels_json = json.dumps(chart_labels)
    requests_per_hour_counts_json = json.dumps(chart_counts)
    
    # FIX: Get word frequencies for word cloud
    word_freqs = get_word_frequencies()
    word_cloud_data_json = json.dumps(list(word_freqs.items()))
    
    # Replace placeholders
    html_content = HTML_TEMPLATE
    html_content = html_content.replace('__TABLE_ROWS__', table_rows)
    html_content = html_content.replace('__TOTAL_COUNT__', str(len(feedback_data)))
    html_content = html_content.replace('__GENERATION_TIME__', datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    html_content = html_content.replace('__DB_HOST__', DB_PARAMS.get('host', 'N/A'))
    html_content = html_content.replace('__METRICS_SUMMARY__', metrics_summary_html)
    
    # Add chart scripts
    chart_html = f"""
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/wordcloud/dist/wordcloud2.min.js"></script>
    <script>
      // Requests per hour chart
      const ctx = document.getElementById('requestsPerHourChart').getContext('2d');
      new Chart(ctx, {{
          type: 'bar',
          data: {{
              labels: {requests_per_hour_labels_json},
              datasets: [{{
                  label: 'Requests per Hour',
                  data: {requests_per_hour_counts_json},
                  backgroundColor: 'rgba(59, 130, 246, 0.7)',
                  borderColor: 'rgba(59, 130, 246, 1)',
                  borderWidth: 1
              }}]
          }},
          options: {{
              scales: {{ y: {{ beginAtZero: true, ticks: {{ stepSize: 1 }} }} }},
              responsive: true,
              maintainAspectRatio: false
          }}
      }});

      // Word cloud
      const wordCloudData = {word_cloud_data_json};
      if (wordCloudData.length > 0) {{
          WordCloud(document.getElementById('wordCloudCanvas'), {{
              list: wordCloudData,
              gridSize: 10,
              weightFactor: 5,
              fontFamily: 'Segoe UI, Tahoma, Geneva, Verdana, sans-serif',
              color: 'random-dark',
              rotateRatio: 0.5,
              backgroundColor: '#fff'
          }});
      }}
    </script>
    """
    html_content = html_content.replace('</body>', chart_html + '</body>')
    
    return html_content

def main():
    """Main function to generate and display the dashboard."""
    try:
        print("Connecting to PostgreSQL database...")
        feedback_data = get_all_feedback()
        print(f"Retrieved {len(feedback_data)} feedback records.")
        
        total_queries = get_total_queries()
        total_feedback = len(feedback_data)
        positive_feedback_count = sum(1 for fb in feedback_data if determine_feedback_status(fb.get('feedback_tags', [])).get('status') == 'Positive')
        positive_feedback_pct = (positive_feedback_count / total_feedback * 100) if total_feedback else 0.0
        
        token_list = parse_openai_calls()
        avg_tokens = (sum(token_list) / len(token_list)) if token_list else 0.0
        
        metrics = {
            'total_queries': total_queries,
            'total_feedback': total_feedback,
            'positive_feedback_count': positive_feedback_count,
            'positive_feedback_pct': positive_feedback_pct,
            'avg_tokens': avg_tokens
        }
        
        print("Generating dashboard HTML...")
        html_content = generate_dashboard_html(feedback_data, metrics)
        
        output_path = Path('feedback_dashboard.html')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        print(f"Dashboard generated at: {output_path.absolute()}")
        webbrowser.open(output_path.absolute().as_uri())
        print("Dashboard opened in your default web browser.")
        
    except Exception as e:
        print(f"An error occurred while generating the dashboard: {e}")

if __name__ == '__main__':
    main()
