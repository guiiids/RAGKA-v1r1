# Phase 4 Implementation Guide: Advanced Analytics & Visualization

**Date:** June 22, 2025  
**Version:** 1.0  
**Related Documents:** 
- [Analytics Logging Strategy](analytics_logging_strategy.md)
- [RAG Analytics Implementation Plan](rag_analytics_implementation_plan.md)
- [Phase 1 Implementation Guide](phase1_implementation_guide.md)
- [Phase 2 Implementation Guide](phase2_implementation_guide.md)
- [Phase 3 Implementation Guide](phase3_implementation_guide.md)

## Overview

This document provides detailed implementation guidance for Phase 4 of the RAG Analytics Logging System. Phase 4 focuses on enhancing the analytics dashboard with advanced visualizations and insights, building upon the robust database structure created in Phase 3.

## Prerequisites

Before beginning Phase 4 implementation, ensure you have:

1. Successfully completed Phase 3 implementation
2. Verified that the database schema is correctly set up
3. Confirmed that the ETL processes are running properly
4. Created backups of the current dashboard and visualization code

## Implementation Steps

### 1. Enhanced Dashboard

#### 1.1 Create Component-Level Performance Visualization

Update the `analytics_dashboard.html` file to include a component-level performance visualization:

```html
<div class="card mt-4">
  <div class="card-header">
    <h5>Component-Level Performance</h5>
  </div>
  <div class="card-body">
    <div class="row">
      <div class="col-md-8">
        <canvas id="componentPerformanceChart"></canvas>
      </div>
      <div class="col-md-4">
        <div class="form-group">
          <label for="timeRangeSelect">Time Range:</label>
          <select class="form-control" id="timeRangeSelect">
            <option value="day">Last 24 Hours</option>
            <option value="week" selected>Last 7 Days</option>
            <option value="month">Last 30 Days</option>
          </select>
        </div>
        <div class="form-group mt-3">
          <label for="aggregationSelect">Aggregation:</label>
          <select class="form-control" id="aggregationSelect">
            <option value="avg" selected>Average</option>
            <option value="p50">Median (p50)</option>
            <option value="p90">90th Percentile</option>
            <option value="p95">95th Percentile</option>
            <option value="p99">99th Percentile</option>
          </select>
        </div>
        <div class="mt-4">
          <h6>Component Breakdown:</h6>
          <div id="componentBreakdown"></div>
        </div>
      </div>
    </div>
  </div>
</div>
```

Add the corresponding JavaScript to initialize and update the component performance chart:

```javascript
// Component Performance Chart
async function initComponentPerformanceChart() {
  const timeRange = document.getElementById('timeRangeSelect').value;
  const aggregation = document.getElementById('aggregationSelect').value;
  
  const data = await fetchComponentPerformanceData(timeRange, aggregation);
  if (!data) return;
  
  const ctx = document.getElementById('componentPerformanceChart').getContext('2d');
  
  if (window.componentChart) {
    window.componentChart.destroy();
  }
  
  window.componentChart = new Chart(ctx, {
    type: 'line',
    data: {
      labels: data.labels,
      datasets: data.components.map((component, index) => ({
        label: component.name,
        data: component.values,
        borderColor: getComponentColor(component.name),
        backgroundColor: getComponentColor(component.name, 0.2),
        tension: 0.1
      }))
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Time (ms)'
          }
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            footer: (tooltipItems) => {
              const index = tooltipItems[0].dataIndex;
              const counts = data.components.map(c => c.counts[index]);
              const totalCount = counts.reduce((a, b) => a + b, 0);
              return `Request Count: ${totalCount}`;
            }
          }
        }
      }
    }
  });
  
  // Update component breakdown
  updateComponentBreakdown(data);
}

function updateComponentBreakdown(data) {
  const breakdownDiv = document.getElementById('componentBreakdown');
  breakdownDiv.innerHTML = '';
  
  // Calculate the latest values for each component
  const latestIndex = data.labels.length - 1;
  const components = data.components.map(component => ({
    name: component.name,
    value: component.values[latestIndex],
    color: getComponentColor(component.name)
  }));
  
  // Sort components by value (descending)
  components.sort((a, b) => b.value - a.value);
  
  // Calculate total
  const total = components.reduce((sum, component) => sum + component.value, 0);
  
  // Create breakdown items
  components.forEach(component => {
    const percentage = total > 0 ? (component.value / total * 100).toFixed(1) : 0;
    
    const item = document.createElement('div');
    item.className = 'mb-2';
    item.innerHTML = `
      <div class="d-flex justify-content-between align-items-center">
        <span>${component.name}</span>
        <span>${component.value.toFixed(1)} ms (${percentage}%)</span>
      </div>
      <div class="progress">
        <div class="progress-bar" role="progressbar" 
             style="width: ${percentage}%; background-color: ${component.color}" 
             aria-valuenow="${percentage}" aria-valuemin="0" aria-valuemax="100"></div>
      </div>
    `;
    
    breakdownDiv.appendChild(item);
  });
}

function getComponentColor(componentName, alpha = 1) {
  const colors = {
    'embedding': `rgba(54, 162, 235, ${alpha})`,
    'search': `rgba(255, 206, 86, ${alpha})`,
    'context': `rgba(75, 192, 192, ${alpha})`,
    'llm': `rgba(153, 102, 255, ${alpha})`,
    'post': `rgba(255, 159, 64, ${alpha})`,
    'total': `rgba(255, 99, 132, ${alpha})`
  };
  
  return colors[componentName] || `rgba(128, 128, 128, ${alpha})`;
}

async function fetchComponentPerformanceData(timeRange, aggregation) {
  try {
    const response = await fetch(`/api/analytics/component-performance?timeRange=${timeRange}&aggregation=${aggregation}`);
    return await response.json();
  } catch (error) {
    console.error('Error fetching component performance data:', error);
    return null;
  }
}

// Initialize chart and add event listeners
document.addEventListener('DOMContentLoaded', () => {
  initComponentPerformanceChart();
  
  document.getElementById('timeRangeSelect').addEventListener('change', initComponentPerformanceChart);
  document.getElementById('aggregationSelect').addEventListener('change', initComponentPerformanceChart);
});
```

#### 1.2 Create Token Usage Trends Visualization

Add a detailed token usage trends visualization to `analytics_dashboard.html`:

```html
<div class="card mt-4">
  <div class="card-header">
    <h5>Token Usage Trends</h5>
  </div>
  <div class="card-body">
    <div class="row">
      <div class="col-md-9">
        <canvas id="tokenUsageTrendsChart"></canvas>
      </div>
      <div class="col-md-3">
        <div class="form-group">
          <label for="tokenTimeRangeSelect">Time Range:</label>
          <select class="form-control" id="tokenTimeRangeSelect">
            <option value="week" selected>Last 7 Days</option>
            <option value="month">Last 30 Days</option>
            <option value="quarter">Last 90 Days</option>
          </select>
        </div>
        <div class="form-group mt-3">
          <label for="tokenModelSelect">Model:</label>
          <select class="form-control" id="tokenModelSelect">
            <option value="all" selected>All Models</option>
            <!-- Models will be populated dynamically -->
          </select>
        </div>
        <div class="mt-4">
          <h6>Token Usage Summary:</h6>
          <div id="tokenUsageSummary" class="mt-3">
            <!-- Summary will be populated dynamically -->
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
```

Add the corresponding JavaScript to initialize and update the token usage trends chart:

```javascript
// Token Usage Trends Chart
async function initTokenUsageTrendsChart() {
  const timeRange = document.getElementById('tokenTimeRangeSelect').value;
  const model = document.getElementById('tokenModelSelect').value;
  
  const data = await fetchTokenUsageData(timeRange, model);
  if (!data) return;
  
  // Populate model dropdown if needed
  if (data.models && data.models.length > 0) {
    populateModelDropdown(data.models);
  }
  
  const ctx = document.getElementById('tokenUsageTrendsChart').getContext('2d');
  
  if (window.tokenChart) {
    window.tokenChart.destroy();
  }
  
  window.tokenChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: data.dates,
      datasets: [
        {
          label: 'Prompt Tokens',
          data: data.promptTokens,
          backgroundColor: 'rgba(54, 162, 235, 0.7)',
          stack: 'Stack 0'
        },
        {
          label: 'Completion Tokens',
          data: data.completionTokens,
          backgroundColor: 'rgba(255, 99, 132, 0.7)',
          stack: 'Stack 0'
        }
      ]
    },
    options: {
      responsive: true,
      scales: {
        x: {
          stacked: true
        },
        y: {
          stacked: true,
          beginAtZero: true,
          title: {
            display: true,
            text: 'Token Count'
          }
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            footer: (tooltipItems) => {
              const index = tooltipItems[0].dataIndex;
              const cost = data.costs[index];
              return `Estimated Cost: $${cost.toFixed(2)}`;
            }
          }
        }
      }
    }
  });
  
  // Update token usage summary
  updateTokenUsageSummary(data);
}

function populateModelDropdown(models) {
  const dropdown = document.getElementById('tokenModelSelect');
  
  // Keep the "All Models" option
  const allOption = dropdown.options[0];
  
  // Clear existing options
  dropdown.innerHTML = '';
  
  // Add back the "All Models" option
  dropdown.appendChild(allOption);
  
  // Add model options
  models.forEach(model => {
    const option = document.createElement('option');
    option.value = model;
    option.textContent = model;
    dropdown.appendChild(option);
  });
}

function updateTokenUsageSummary(data) {
  const summaryDiv = document.getElementById('tokenUsageSummary');
  
  // Calculate totals
  const totalPromptTokens = data.promptTokens.reduce((sum, val) => sum + val, 0);
  const totalCompletionTokens = data.completionTokens.reduce((sum, val) => sum + val, 0);
  const totalTokens = totalPromptTokens + totalCompletionTokens;
  const totalCost = data.costs.reduce((sum, val) => sum + val, 0);
  
  // Create summary
  summaryDiv.innerHTML = `
    <div class="mb-2">
      <strong>Total Tokens:</strong> ${totalTokens.toLocaleString()}
    </div>
    <div class="mb-2">
      <strong>Prompt Tokens:</strong> ${totalPromptTokens.toLocaleString()} (${(totalPromptTokens / totalTokens * 100).toFixed(1)}%)
    </div>
    <div class="mb-2">
      <strong>Completion Tokens:</strong> ${totalCompletionTokens.toLocaleString()} (${(totalCompletionTokens / totalTokens * 100).toFixed(1)}%)
    </div>
    <div class="mb-2">
      <strong>Estimated Cost:</strong> $${totalCost.toFixed(2)}
    </div>
    <div class="mb-2">
      <strong>Avg. Daily Usage:</strong> ${Math.round(totalTokens / data.dates.length).toLocaleString()} tokens
    </div>
  `;
}

async function fetchTokenUsageData(timeRange, model) {
  try {
    const response = await fetch(`/api/analytics/token-usage?timeRange=${timeRange}&model=${model}`);
    return await response.json();
  } catch (error) {
    console.error('Error fetching token usage data:', error);
    return null;
  }
}

// Initialize chart and add event listeners
document.addEventListener('DOMContentLoaded', () => {
  initTokenUsageTrendsChart();
  
  document.getElementById('tokenTimeRangeSelect').addEventListener('change', initTokenUsageTrendsChart);
  document.getElementById('tokenModelSelect').addEventListener('change', initTokenUsageTrendsChart);
});
```

#### 1.3 Create Retrieval Quality Analysis Visualization

Add a retrieval quality analysis visualization to `analytics_dashboard.html`:

```html
<div class="card mt-4">
  <div class="card-header">
    <h5>Retrieval Quality Analysis</h5>
  </div>
  <div class="card-body">
    <div class="row">
      <div class="col-md-6">
        <canvas id="retrievalQualityChart"></canvas>
      </div>
      <div class="col-md-6">
        <canvas id="citationUsageChart"></canvas>
      </div>
    </div>
    <div class="row mt-4">
      <div class="col-md-12">
        <h6>Chunk Relevance Distribution</h6>
        <canvas id="chunkRelevanceChart"></canvas>
      </div>
    </div>
  </div>
</div>
```

Add the corresponding JavaScript to initialize and update the retrieval quality charts:

```javascript
// Retrieval Quality Analysis Charts
async function initRetrievalQualityCharts() {
  const data = await fetchRetrievalQualityData();
  if (!data) return;
  
  // Retrieval Quality Chart (Scatter plot of relevance vs. citation rate)
  const qualityCtx = document.getElementById('retrievalQualityChart').getContext('2d');
  
  if (window.retrievalQualityChart) {
    window.retrievalQualityChart.destroy();
  }
  
  window.retrievalQualityChart = new Chart(qualityCtx, {
    type: 'scatter',
    data: {
      datasets: [{
        label: 'Chunks',
        data: data.chunkQuality.map(item => ({
          x: item.relevance,
          y: item.citationRate
        })),
        backgroundColor: 'rgba(75, 192, 192, 0.7)',
        pointRadius: 6,
        pointHoverRadius: 8
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: {
          title: {
            display: true,
            text: 'Relevance Score'
          },
          min: 0,
          max: 1
        },
        y: {
          title: {
            display: true,
            text: 'Citation Rate'
          },
          min: 0,
          max: 1
        }
      },
      plugins: {
        tooltip: {
          callbacks: {
            label: (context) => {
              const index = context.dataIndex;
              const item = data.chunkQuality[index];
              return [
                `Relevance: ${item.relevance.toFixed(2)}`,
                `Citation Rate: ${item.citationRate.toFixed(2)}`,
                `Chunk Size: ${item.chunkSize} chars`,
                `Times Retrieved: ${item.retrievalCount}`
              ];
            }
          }
        },
        title: {
          display: true,
          text: 'Chunk Relevance vs. Citation Rate'
        }
      }
    }
  });
  
  // Citation Usage Chart (Pie chart of citation distribution)
  const citationCtx = document.getElementById('citationUsageChart').getContext('2d');
  
  if (window.citationUsageChart) {
    window.citationUsageChart.destroy();
  }
  
  window.citationUsageChart = new Chart(citationCtx, {
    type: 'pie',
    data: {
      labels: ['0 Citations', '1 Citation', '2 Citations', '3+ Citations'],
      datasets: [{
        data: [
          data.citationDistribution.zero,
          data.citationDistribution.one,
          data.citationDistribution.two,
          data.citationDistribution.threeOrMore
        ],
        backgroundColor: [
          'rgba(255, 99, 132, 0.7)',
          'rgba(54, 162, 235, 0.7)',
          'rgba(255, 206, 86, 0.7)',
          'rgba(75, 192, 192, 0.7)'
        ]
      }]
    },
    options: {
      responsive: true,
      plugins: {
        title: {
          display: true,
          text: 'Response Citation Distribution'
        }
      }
    }
  });
  
  // Chunk Relevance Chart (Histogram of relevance scores)
  const relevanceCtx = document.getElementById('chunkRelevanceChart').getContext('2d');
  
  if (window.chunkRelevanceChart) {
    window.chunkRelevanceChart.destroy();
  }
  
  window.chunkRelevanceChart = new Chart(relevanceCtx, {
    type: 'bar',
    data: {
      labels: data.relevanceDistribution.labels,
      datasets: [{
        label: 'Chunk Count',
        data: data.relevanceDistribution.values,
        backgroundColor: 'rgba(153, 102, 255, 0.7)'
      }]
    },
    options: {
      responsive: true,
      scales: {
        x: {
          title: {
            display: true,
            text: 'Relevance Score Range'
          }
        },
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Number of Chunks'
          }
        }
      },
      plugins: {
        title: {
          display: true,
          text: 'Distribution of Chunk Relevance Scores'
        }
      }
    }
  });
}

async function fetchRetrievalQualityData() {
  try {
    const response = await fetch('/api/analytics/retrieval-quality');
    return await response.json();
  } catch (error) {
    console.error('Error fetching retrieval quality data:', error);
    return null;
  }
}

// Initialize charts
document.addEventListener('DOMContentLoaded', () => {
  initRetrievalQualityCharts();
});
```

#### 1.4 Create User Interaction Patterns Visualization

Add a user interaction patterns visualization to `analytics_dashboard.html`:

```html
<div class="card mt-4">
  <div class="card-header">
    <h5>User Interaction Patterns</h5>
  </div>
  <div class="card-body">
    <div class="row">
      <div class="col-md-6">
        <canvas id="feedbackTrendsChart"></canvas>
      </div>
      <div class="col-md-6">
        <canvas id="feedbackTagsChart"></canvas>
      </div>
    </div>
    <div class="row mt-4">
      <div class="col-md-12">
        <h6>Follow-up Question Analysis</h6>
        <div class="table-responsive">
          <table class="table table-striped">
            <thead>
              <tr>
                <th>Pattern</th>
                <th>Frequency</th>
                <th>Avg. Response Time</th>
                <th>Positive Feedback %</th>
              </tr>
            </thead>
            <tbody id="followUpPatternsTable">
              <!-- Follow-up patterns will be populated dynamically -->
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</div>
```

Add the corresponding JavaScript to initialize and update the user interaction charts:

```javascript
// User Interaction Patterns Charts
async function initUserInteractionCharts() {
  const data = await fetchUserInteractionData();
  if (!data) return;
  
  // Feedback Trends Chart
  const trendsCtx = document.getElementById('feedbackTrendsChart').getContext('2d');
  
  if (window.feedbackTrendsChart) {
    window.feedbackTrendsChart.destroy();
  }
  
  window.feedbackTrendsChart = new Chart(trendsCtx, {
    type: 'line',
    data: {
      labels: data.feedbackTrends.dates,
      datasets: [
        {
          label: 'Positive Feedback',
          data: data.feedbackTrends.positive,
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.1
        },
        {
          label: 'Negative Feedback',
          data: data.feedbackTrends.negative,
          borderColor: 'rgba(255, 99, 132, 1)',
          backgroundColor: 'rgba(255, 99, 132, 0.2)',
          tension: 0.1
        }
      ]
    },
    options: {
      responsive: true,
      scales: {
        y: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Feedback Count'
          }
        }
      },
      plugins: {
        title: {
          display: true,
          text: 'Feedback Trends Over Time'
        }
      }
    }
  });
  
  // Feedback Tags Chart
  const tagsCtx = document.getElementById('feedbackTagsChart').getContext('2d');
  
  if (window.feedbackTagsChart) {
    window.feedbackTagsChart.destroy();
  }
  
  window.feedbackTagsChart = new Chart(tagsCtx, {
    type: 'horizontalBar',
    data: {
      labels: data.feedbackTags.map(tag => tag.name),
      datasets: [
        {
          label: 'Positive Feedback',
          data: data.feedbackTags.map(tag => tag.positiveCount),
          backgroundColor: 'rgba(75, 192, 192, 0.7)'
        },
        {
          label: 'Negative Feedback',
          data: data.feedbackTags.map(tag => tag.negativeCount),
          backgroundColor: 'rgba(255, 99, 132, 0.7)'
        }
      ]
    },
    options: {
      indexAxis: 'y',
      responsive: true,
      scales: {
        x: {
          beginAtZero: true,
          title: {
            display: true,
            text: 'Count'
          }
        }
      },
      plugins: {
        title: {
          display: true,
          text: 'Feedback Tags Distribution'
        }
      }
    }
  });
  
  // Populate follow-up patterns table
  populateFollowUpPatternsTable(data.followUpPatterns);
}

function populateFollowUpPatternsTable(patterns) {
  const tableBody = document.getElementById('followUpPatternsTable');
  tableBody.innerHTML = '';
  
  patterns.forEach(pattern => {
    const row = document.createElement('tr');
    
    row.innerHTML = `
      <td>${pattern.pattern}</td>
      <td>${pattern.frequency}</td>
      <td>${pattern.avgResponseTime.toFixed(2)} ms</td>
      <td>${pattern.positiveFeedbackPercentage.toFixed(1)}%</td>
    `;
    
    tableBody.appendChild(row);
  });
}

async function fetchUserInteractionData() {
  try {
    const response = await fetch('/api/analytics/user-interaction');
    return await response.json();
  } catch (error) {
    console.error('Error fetching user interaction data:', error);
    return null;
  }
}

// Initialize charts
document.addEventListener('DOMContentLoaded', () => {
  initUserInteractionCharts();
});
```

### 2. Implement Anomaly Detection

#### 2.1 Create Anomaly Detection Algorithm

Create a new Python file called `anomaly_detection.py`:

```python
#!/usr/bin/env python3
"""
Anomaly detection for RAG analytics metrics.
"""

import os
import sys
import json
import logging
import datetime
import numpy as np
from typing import Dict, Any, List, Tuple
import psycopg2
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('anomaly_detection.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'raganalytics')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

# Anomaly detection parameters
LATENCY_Z_SCORE_THRESHOLD = 3.0  # Z-score threshold for latency anomalies
TOKEN_Z_SCORE_THRESHOLD = 3.0    # Z-score threshold for token usage anomalies
ERROR_RATE_THRESHOLD = 0.05      # Error rate threshold (5%)
FEEDBACK_THRESHOLD = 0.2         # Negative feedback threshold (20%)

def get_db_connection():
    """Create a connection to the PostgreSQL database."""
    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        logger.error(f"Error connecting to database: {e}")
        raise

def detect_latency_anomalies(conn, lookback_days=30, recent_days=1):
    """
    Detect anomalies in latency metrics.
    
    Args:
        conn: Database connection
        lookback_days: Number of days to use as baseline
        recent_days: Number of recent days to check for anomalies
        
    Returns:
        List of latency anomalies
    """
    try:
        cursor = conn.cursor()
        
        # Get baseline latency data
        baseline_end = datetime.datetime.now() - datetime.timedelta(days=recent_days)
        baseline_start = baseline_end - datetime.timedelta(days=lookback_days)
        
        baseline_query = """
            SELECT
                component,
                AVG(avg_time_ms) AS avg_time,
                STDDEV(avg_time_ms) AS stddev_time
            FROM
                latency_metrics
            WHERE
                date >= %s AND date < %s
            GROUP BY
                component
        """
        
        cursor.execute(baseline_query, (baseline_start.date(), baseline_end.date()))
        baseline_results = cursor.fetchall()
        
        # Create baseline statistics
        baseline_stats = {}
        for component, avg_time, stddev_time in baseline_results:
            baseline_stats[component] = {
                'avg': avg_time,
                'stddev': stddev_time if stddev_time is not None else 1.0  # Avoid division by zero
            }
        
        # Get recent latency data
        recent_start = baseline_end
        recent_end = datetime.datetime.now()
        
        recent_query = """
            SELECT
                date,
                component,
                avg_time_ms
            FROM
                latency_metrics
            WHERE
                date >= %s AND date < %s
        """
        
        cursor.execute(recent_query, (recent_start.date(), recent_end.date()))
        recent_results = cursor.fetchall()
        
        # Detect anomalies
        anomalies = []
        
        for date, component, avg_time in recent_results:
            if component not in baseline_stats:
                continue
                
            baseline = baseline_stats[component]
            
            # Calculate z-score
            z_score = (avg_time - baseline['avg']) / baseline['stddev']
            
            if abs(z_score) > LATENCY_Z_SCORE_THRESHOLD:
                anomalies.append({
                    'date': date.strftime('%Y-%m-%d'),
                    'component': component,
                    'metric': 'latency',
                    'value': avg_time,
                    'baseline': baseline['avg'],
                    'z_score': z_score,
                    'severity': 'high' if abs(z_score) > 2 * LATENCY_Z_SCORE_THRESHOLD else 'medium'
                })
        
        cursor.close()
        return anomalies
    
    except Exception as e:
        logger.error(f"Error detecting latency anomalies: {e}")
        raise

def detect_token_usage_anomalies(conn, lookback_days=30, recent_days=1):
    """
    Detect anomalies in token usage.
    
    Args:
        conn: Database connection
        lookback_days: Number of days to use as baseline
        recent_days: Number of recent days to check for anomalies
        
    Returns:
        List of token usage anomalies
    """
    try:
        cursor = conn.cursor()
        
        # Get baseline token usage data
        baseline_end = datetime.datetime.now() - datetime.timedelta(days=recent_days)
        baseline_start = baseline_end - datetime.timedelta(days=lookback_days)
        
        baseline_query = """
            SELECT
                model_name,
                AVG(total_tokens) AS avg_tokens,
                STDDEV(total_tokens) AS stddev_tokens
            FROM
                token_usage_daily
            WHERE
                date >= %s AND date
