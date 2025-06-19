### Key Features:

1. __Overview Section__ with key metrics:

   - Total interactions
   - Positive feedback percentage
   - Average response time
   - Token usage

2. __Interactive Charts__:

   - Interactions over time
   - Feedback distribution (positive vs. negative)
   - Top query categories
   - Response time distribution
   - Token usage by day
   - Feedback tags distribution

3. __Recent Interactions Table__ showing:

   - Query ID
   - User query
   - Feedback status
   - Response time
   - Token usage
   - Timestamp
   - Action buttons

4. __Model Performance Metrics__:

   - Accuracy
   - Relevance
   - Coherence
   - Hallucination rate

5. __Additional Features__:

   - Date range picker for filtering data
   - Export functionality
   - Responsive design using Tailwind CSS
   - Interactive charts using Chart.js

The dashboard is designed to work with the PostgreSQL database structure, which includes the 'votes' table with columns for vote_id, user_query, bot_response, evaluation_json, feedback_tags, comment, and timestamp. It also incorporates data from the OpenAI logs to show token usage and performance metrics.

To use this dashboard:

*** During Testing Only ***

1. Open the analytics_dashboard.html file in a browser
2. Replace the sample data in the JavaScript section with actual data from your database
3. Customize the charts and metrics as needed
