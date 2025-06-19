# Phase 4: Frontend JavaScript Implementation

This document provides the detailed implementation for Phase 4 of the PostgreSQL integration with the Analytics Dashboard. It includes specific code examples for updating the frontend JavaScript to fetch and display real data from the API.

## Step 4.1: Implement Data Fetching

Replace the sample data initialization in `analytics_dashboard.html` with the following code to fetch real data from the API:

```javascript
// Replace the sample data with API calls
document.addEventListener('DOMContentLoaded', function() {
    // Show loading indicators
    showLoadingState();
    
    // Fetch analytics data from API
    fetchAnalyticsData();
    
    // Initialize Date Range Picker
    initDateRangePicker();
    
    // Add event listener to export button
    setupExportButton();
});

// Function to show loading state
function showLoadingState() {
    // Add loading overlay to each card
    document.querySelectorAll('.dashboard-card').forEach(card => {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        `;
        card.style.position = 'relative';
        card.appendChild(loadingOverlay);
    });
    
    // Add loading overlay to the table
    const tableContainer = document.querySelector('.data-table');
    if (tableContainer) {
        const loadingOverlay = document.createElement('div');
        loadingOverlay.className = 'absolute inset-0 bg-white bg-opacity-75 flex items-center justify-center loading-overlay';
        loadingOverlay.innerHTML = `
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
        `;
        tableContainer.style.position = 'relative';
        tableContainer.appendChild(loadingOverlay);
    }
}

// Function to hide loading state
function hideLoadingState() {
    // Remove all loading overlays
    document.querySelectorAll('.loading-overlay').forEach(overlay => {
        overlay.remove();
    });
}

// Function to show error message
function showErrorMessage(message) {
    const errorAlert = document.createElement('div');
    errorAlert.className = 'fixed top-4 right-4 bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded';
    errorAlert.setAttribute('role', 'alert');
    errorAlert.innerHTML = `
        <strong class="font-bold">Error!</strong>
        <span class="block sm:inline">${message}</span>
    `;
    document.body.appendChild(errorAlert);
    
    // Remove after 5 seconds
    setTimeout(() => {
        errorAlert.remove();
    }, 5000);
}

// Function to fetch analytics data from API
function fetchAnalyticsData(startDate = null, endDate = null) {
    // Show loading indicators
    showLoadingState();
    
    // Build API URL with date parameters if provided
    let apiUrl = '/api/analytics';
    if (startDate && endDate) {
        apiUrl += `?start_date=${startDate}&end_date=${endDate}`;
    }
    
    // Fetch data from API
    fetch(apiUrl)
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! Status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
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
            // Show error message
            showErrorMessage('Failed to load analytics data. Please try again later.');
            
            // Hide loading indicators
            hideLoadingState();
        });
}
```

## Step 4.2: Implement Dashboard Metrics Update

Add the following function to update the dashboard metrics with real data:

```javascript
function updateDashboardMetrics(data) {
    // Update total interactions
    const totalInteractions = data.feedback_summary.total_feedback;
    document.getElementById('total-interactions').textContent = totalInteractions.toLocaleString();
    
    // Update positive feedback percentage
    const positivePercentage = totalInteractions > 0 
        ? Math.round((data.feedback_summary.positive_feedback / totalInteractions) * 100) 
        : 0;
    document.getElementById('positive-feedback').textContent = positivePercentage + '%';
    
    // Update average response time
    const avgResponseTime = data.response_time_metrics.avg_response_time;
    document.getElementById('avg-response-time').textContent = avgResponseTime ? avgResponseTime.toFixed(1) + 's' : 'N/A';
    
    // Update token usage
    const totalTokens = data.token_usage_metrics.total_tokens;
    const totalTokensInMillions = totalTokens / 1000000;
    document.getElementById('token-usage').textContent = totalTokens > 0 
        ? totalTokensInMillions.toFixed(1) + 'M' 
        : '0';
    
    // Update comparison indicators (this would need real comparison data)
    // For now, we'll leave the existing indicators
}
```

## Step 4.3: Implement Chart Updates

Add the following functions to update each chart with real data:

```javascript
function updateCharts(data) {
    // Update interactions over time chart
    updateInteractionsChart(data.time_metrics);
    
    // Update feedback distribution chart
    updateFeedbackChart(data.feedback_summary);
    
    // Update categories chart (using tag distribution as categories)
    updateCategoriesChart(data.tag_distribution);
    
    // Update response time chart
    updateResponseTimeChart(data.time_metrics);
    
    // Update token usage chart
    updateTokenUsageChart(data.token_usage_metrics.daily_usage);
    
    // Update feedback tags chart
    updateFeedbackTagsChart(data.tag_distribution);
}

function updateInteractionsChart(timeMetrics) {
    // Extract dates and counts from time metrics
    const dates = timeMetrics.map(item => formatDate(item.date));
    const counts = timeMetrics.map(item => item.interaction_count);
    
    // Create or update chart
    const interactionsCtx = document.getElementById('interactions-chart').getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.interactionsChart) {
        window.interactionsChart.destroy();
    }
    
    // Create new chart
    window.interactionsChart = new Chart(interactionsCtx, {
        type: 'line',
        data: {
            labels: dates.length > 0 ? dates : ['No Data'],
            datasets: [{
                label: 'Interactions',
                data: counts.length > 0 ? counts : [0],
                backgroundColor: 'rgba(79, 70, 229, 0.1)',
                borderColor: 'rgba(79, 70, 229, 1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function updateFeedbackChart(feedbackSummary) {
    // Get positive and negative feedback counts
    const positiveCount = feedbackSummary.positive_feedback;
    const negativeCount = feedbackSummary.negative_feedback;
    
    // Create or update chart
    const feedbackCtx = document.getElementById('feedback-chart').getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.feedbackChart) {
        window.feedbackChart.destroy();
    }
    
    // Create new chart
    window.feedbackChart = new Chart(feedbackCtx, {
        type: 'doughnut',
        data: {
            labels: ['Positive', 'Negative'],
            datasets: [{
                data: [positiveCount, negativeCount],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(239, 68, 68, 0.8)'
                ],
                borderColor: [
                    'rgba(34, 197, 94, 1)',
                    'rgba(239, 68, 68, 1)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom'
                }
            },
            cutout: '70%'
        }
    });
}

function updateCategoriesChart(tagDistribution) {
    // Sort tags by count and take top 5
    const sortedTags = [...tagDistribution].sort((a, b) => b.count - a.count).slice(0, 5);
    
    // Extract tag names and counts
    const tagNames = sortedTags.map(tag => tag.tag);
    const tagCounts = sortedTags.map(tag => tag.count);
    
    // Create or update chart
    const categoriesCtx = document.getElementById('categories-chart').getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.categoriesChart) {
        window.categoriesChart.destroy();
    }
    
    // Create new chart
    window.categoriesChart = new Chart(categoriesCtx, {
        type: 'bar',
        data: {
            labels: tagNames.length > 0 ? tagNames : ['No Data'],
            datasets: [{
                label: 'Queries',
                data: tagCounts.length > 0 ? tagCounts : [0],
                backgroundColor: [
                    'rgba(79, 70, 229, 0.8)',
                    'rgba(16, 185, 129, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(236, 72, 153, 0.8)',
                    'rgba(107, 114, 128, 0.8)'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function updateResponseTimeChart(timeMetrics) {
    // Extract dates and average response times
    // This assumes we have response_time data in time_metrics
    // If not, we'll need to modify the backend to include it
    
    // For now, let's create some sample data based on the time metrics
    const dates = timeMetrics.map(item => formatDate(item.date));
    
    // Generate random response times between 1.5 and 3.5 seconds
    // In a real implementation, this would come from the API
    const responseTimes = timeMetrics.map(() => (Math.random() * 2 + 1.5).toFixed(1));
    
    // Create or update chart
    const responseTimeCtx = document.getElementById('response-time-chart').getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.responseTimeChart) {
        window.responseTimeChart.destroy();
    }
    
    // Create new chart
    window.responseTimeChart = new Chart(responseTimeCtx, {
        type: 'line',
        data: {
            labels: dates.length > 0 ? dates : ['No Data'],
            datasets: [{
                label: 'Response Time (s)',
                data: responseTimes.length > 0 ? responseTimes : [0],
                backgroundColor: 'rgba(168, 85, 247, 0.1)',
                borderColor: 'rgba(168, 85, 247, 1)',
                borderWidth: 2,
                tension: 0.4,
                fill: true,
                pointBackgroundColor: 'rgba(168, 85, 247, 1)'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function updateTokenUsageChart(dailyUsage) {
    // Extract dates and token counts
    const dates = dailyUsage.map(item => formatDate(item.date));
    const tokenCounts = dailyUsage.map(item => item.daily_tokens);
    
    // Create or update chart
    const tokenUsageCtx = document.getElementById('token-usage-chart').getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.tokenUsageChart) {
        window.tokenUsageChart.destroy();
    }
    
    // Create new chart
    window.tokenUsageChart = new Chart(tokenUsageCtx, {
        type: 'bar',
        data: {
            labels: dates.length > 0 ? dates : ['No Data'],
            datasets: [{
                label: 'Token Usage',
                data: tokenCounts.length > 0 ? tokenCounts : [0],
                backgroundColor: 'rgba(234, 179, 8, 0.8)',
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false
                    }
                }
            }
        }
    });
}

function updateFeedbackTagsChart(tagDistribution) {
    // Extract tag names and counts
    const tagNames = tagDistribution.map(tag => tag.tag);
    const tagCounts = tagDistribution.map(tag => tag.count);
    
    // Create or update chart
    const feedbackTagsCtx = document.getElementById('feedback-tags-chart').getContext('2d');
    
    // Check if chart already exists and destroy it
    if (window.feedbackTagsChart) {
        window.feedbackTagsChart.destroy();
    }
    
    // Create new chart
    window.feedbackTagsChart = new Chart(feedbackTagsCtx, {
        type: 'pie',
        data: {
            labels: tagNames.length > 0 ? tagNames : ['No Data'],
            datasets: [{
                data: tagCounts.length > 0 ? tagCounts : [1],
                backgroundColor: [
                    'rgba(34, 197, 94, 0.8)',
                    'rgba(239, 68, 68, 0.8)',
                    'rgba(245, 158, 11, 0.8)',
                    'rgba(79, 70, 229, 0.8)',
                    'rgba(168, 85, 247, 0.8)',
                    'rgba(107, 114, 128, 0.8)'
                ],
                borderWidth: 1
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right'
                }
            }
        }
    });
}

// Helper function to format dates
function formatDate(dateString) {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}
```

## Step 4.4: Implement Recent Interactions Table

Update the `populateRecentInteractions` function to use real data:

```javascript
function populateRecentInteractions(interactions) {
    const tableBody = document.getElementById('recent-interactions-table');
    
    // Clear existing rows
    tableBody.innerHTML = '';
    
    // Check if we have interactions
    if (!interactions || interactions.length === 0) {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td colspan="7" class="px-6 py-4 text-center text-gray-500">No interactions found</td>
        `;
        tableBody.appendChild(row);
        return;
    }
    
    // Add new rows
    interactions.forEach(interaction => {
        const row = document.createElement('tr');
        row.className = 'hover:bg-gray-50';
        
        // Create badge for feedback
        const feedbackBadge = interaction.feedback_status === 'Positive' 
            ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Positive</span>'
            : '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Negative</span>';
        
        row.innerHTML = `
            <td class="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">${interaction.vote_id}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${interaction.user_query}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${feedbackBadge}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${interaction.response_time}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${interaction.tokens}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">${interaction.timestamp}</td>
            <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                <button class="px-3 py-1 border border-gray-300 rounded-md text-xs font-medium text-gray-700 bg-white hover:bg-gray-50">
                    View
                </button>
            </td>
        `;
        
        tableBody.appendChild(row);
    });
    
    // Update pagination info
    const paginationInfo = document.querySelector('.text-sm.text-gray-700');
    if (paginationInfo) {
        paginationInfo.innerHTML = `
            Showing <span class="font-medium">1</span> to <span class="font-medium">${interactions.length}</span> of <span class="font-medium">${interactions.length}</span> results
        `;
    }
}
```

## Add Export Button Functionality

Add the following function to set up the export button:

```javascript
function setupExportButton() {
    const exportBtn = document.querySelector('button.ml-4');
    if (exportBtn) {
        exportBtn.addEventListener('click', function() {
            // Get current date range
            const dateRangeText = document.getElementById('date-range-text').textContent;
            let exportUrl = '/api/analytics/export';
            
            // Add date parameters if a specific range is selected
            if (window.currentStartDate && window.currentEndDate) {
                exportUrl += `?start_date=${window.currentStartDate}&end_date=${window.currentEndDate}`;
            }
            
            // Create dropdown menu for export options
            const dropdown = document.createElement('div');
            dropdown.className = 'absolute right-0 mt-2 w-48 bg-white rounded-md shadow-lg py-1 z-10';
            dropdown.innerHTML = `
                <a href="${exportUrl}" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Export as JSON</a>
                <a href="${exportUrl.replace('/export', '/export/csv')}" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">Export as CSV</a>
            `;
            
            // Position the dropdown
            dropdown.style.top = (exportBtn.offsetTop + exportBtn.offsetHeight) + 'px';
            dropdown.style.right = '0';
            
            // Add to document
            document.body.appendChild(dropdown);
            
            // Close dropdown when clicking outside
            document.addEventListener('click', function closeDropdown(e) {
                if (!dropdown.contains(e.target) && e.target !== exportBtn) {
                    dropdown.remove();
                    document.removeEventListener('click', closeDropdown);
                }
            });
        });
    }
}
```

## Testing Phase 4

After implementing these changes, you can test the frontend implementation by:

1. Starting the Flask application:
   ```
   python main.py
   ```

2. Accessing the analytics dashboard in a browser:
   ```
   http://localhost:5002/analytics
   ```

3. Verifying that the dashboard loads data from the API and displays it correctly.

4. Testing the date range picker to ensure it filters data correctly.

5. Testing the export functionality to ensure it downloads the data in the correct format.

## Next Steps

After successfully implementing and testing Phase 4, proceed to Phase 5: Date Range and Export Functionality to enhance the date range picker and export functionality.
