# Phase 5: Date Range and Export Functionality Implementation

This document provides the detailed implementation for Phase 5 of the PostgreSQL integration with the Analytics Dashboard. It includes specific code examples for enhancing the date range picker and export functionality.

## Step 5.1: Enhance Date Range Picker

Update the `initDateRangePicker` function in `analytics_dashboard.html` to store selected dates and trigger data refresh:

```javascript
function initDateRangePicker() {
    const dateRangeBtn = document.getElementById('date-range-btn');
    const dateRangeText = document.getElementById('date-range-text');
    
    if (!dateRangeBtn) return;
    
    // Store current date range globally
    window.currentStartDate = moment().subtract(6, 'days').format('YYYY-MM-DD');
    window.currentEndDate = moment().format('YYYY-MM-DD');
    
    // Initialize with daterangepicker library
    $(dateRangeBtn).daterangepicker({
        ranges: {
            'Today': [moment(), moment()],
            'Yesterday': [moment().subtract(1, 'days'), moment().subtract(1, 'days')],
            'Last 7 Days': [moment().subtract(6, 'days'), moment()],
            'Last 30 Days': [moment().subtract(29, 'days'), moment()],
            'This Month': [moment().startOf('month'), moment().endOf('month')],
            'Last Month': [moment().subtract(1, 'month').startOf('month'), moment().subtract(1, 'month').endOf('month')]
        },
        startDate: moment().subtract(6, 'days'),
        endDate: moment(),
        opens: 'left',
        alwaysShowCalendars: true
    }, function(start, end, label) {
        // Update the button text with the selected range
        dateRangeText.textContent = label;
        
        // Store current date range for export and filtering
        window.currentStartDate = start.format('YYYY-MM-DD');
        window.currentEndDate = end.format('YYYY-MM-DD');
        
        // Show loading state
        showLoadingState();
        
        // Fetch new data based on the date range
        fetchAnalyticsData(window.currentStartDate, window.currentEndDate);
        
        // Update last updated text
        document.getElementById('last-updated').textContent = moment().format('MMMM D, YYYY h:mm A');
        
        // Log the date range change
        console.log('Date range changed:', window.currentStartDate, 'to', window.currentEndDate);
    });
    
    // Initialize with default range
    dateRangeText.textContent = 'Last 7 Days';
}
```

## Step 5.2: Implement Export API Endpoint

The export API endpoints were already implemented in Phase 3. Let's enhance them to support more export formats and better error handling:

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
        
        # Get format parameter (default to json)
        export_format = request.args.get("format", "json").lower()
        
        logger.info(f"Analytics data export requested with date range: {start_date} to {end_date}, format: {export_format}")
        
        # Get analytics data from database
        analytics_data = get_analytics_data(start_date, end_date)
        
        # Generate timestamp for filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        if export_format == "csv":
            # Export as CSV (only recent interactions)
            return export_as_csv(analytics_data, timestamp)
        elif export_format == "excel":
            # Export as Excel (more comprehensive)
            return export_as_excel(analytics_data, timestamp)
        else:
            # Default: Export as JSON
            response = Response(
                json.dumps(analytics_data, indent=2, default=str),
                mimetype="application/json",
                headers={"Content-Disposition": f"attachment;filename=analytics_export_{timestamp}.json"}
            )
            return response
            
    except Exception as e:
        logger.error(f"Error exporting analytics data: {e}")
        logger.error(f"Traceback: {traceback.format_exc()}")
        return jsonify({"error": str(e)}), 500

def export_as_csv(analytics_data, timestamp):
    """
    Export analytics data as CSV.
    Focuses on recent interactions for simplicity.
    """
    try:
        # Get recent interactions
        recent_interactions = analytics_data.get("recent_interactions", [])
        
        # Create CSV content
        csv_content = "vote_id,user_query,feedback_status,response_time,tokens,timestamp\n"
        for interaction in recent_interactions:
            # Escape quotes in user query
            user_query = interaction.get('user_query', '').replace('"', '""')
            
            csv_content += f"{interaction.get('vote_id', '')},\"{user_query}\",{interaction.get('feedback_status', '')},{interaction.get('response_time', '')},{interaction.get('tokens', '')},{interaction.get('timestamp', '')}\n"
        
        # Set headers for file download
        response = Response(
            csv_content,
            mimetype="text/csv",
            headers={"Content-Disposition": f"attachment;filename=interactions_export_{timestamp}.csv"}
        )
        
        return response
    except Exception as e:
        logger.error(f"Error exporting as CSV: {e}")
        raise

def export_as_excel(analytics_data, timestamp):
    """
    Export analytics data as Excel.
    More comprehensive than CSV, includes multiple sheets.
    Requires openpyxl package.
    """
    try:
        from io import BytesIO
        from openpyxl import Workbook
        from openpyxl.styles import Font, Alignment, PatternFill
        
        # Create workbook
        wb = Workbook()
        
        # Create Overview sheet
        overview = wb.active
        overview.title = "Overview"
        
        # Add headers
        overview['A1'] = "Analytics Overview"
        overview['A1'].font = Font(bold=True, size=14)
        overview.merge_cells('A1:B1')
        
        # Add summary data
        overview['A3'] = "Total Interactions"
        overview['B3'] = analytics_data.get("feedback_summary", {}).get("total_feedback", 0)
        
        overview['A4'] = "Positive Feedback"
        overview['B4'] = analytics_data.get("feedback_summary", {}).get("positive_feedback", 0)
        
        overview['A5'] = "Negative Feedback"
        overview['B5'] = analytics_data.get("feedback_summary", {}).get("negative_feedback", 0)
        
        overview['A6'] = "Average Response Time"
        overview['B6'] = f"{analytics_data.get('response_time_metrics', {}).get('avg_response_time', 0):.2f}s"
        
        overview['A7'] = "Total Tokens Used"
        overview['B7'] = analytics_data.get("token_usage_metrics", {}).get("total_tokens", 0)
        
        overview['A9'] = "Export Date"
        overview['B9'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # Create Interactions sheet
        interactions = wb.create_sheet("Recent Interactions")
        
        # Add headers
        headers = ["ID", "Query", "Feedback", "Response Time", "Tokens", "Timestamp"]
        for col, header in enumerate(headers, 1):
            cell = interactions.cell(row=1, column=col, value=header)
            cell.font = Font(bold=True)
            cell.fill = PatternFill(start_color="E0E0E0", end_color="E0E0E0", fill_type="solid")
        
        # Add data
        recent_interactions = analytics_data.get("recent_interactions", [])
        for row, interaction in enumerate(recent_interactions, 2):
            interactions.cell(row=row, column=1, value=interaction.get('vote_id', ''))
            interactions.cell(row=row, column=2, value=interaction.get('user_query', ''))
            interactions.cell(row=row, column=3, value=interaction.get('feedback_status', ''))
            interactions.cell(row=row, column=4, value=interaction.get('response_time', ''))
            interactions.cell(row=row, column=5, value=interaction.get('tokens', ''))
            interactions.cell(row=row, column=6, value=interaction.get('timestamp', ''))
        
        # Create Tags sheet
        tags = wb.create_sheet("Feedback Tags")
        
        # Add headers
        tags['A1'] = "Tag"
        tags['B1'] = "Count"
        tags['A1'].font = Font(bold=True)
        tags['B1'].font = Font(bold=True)
        
        # Add data
        tag_distribution = analytics_data.get("tag_distribution", [])
        for row, tag_data in enumerate(tag_distribution, 2):
            tags.cell(row=row, column=1, value=tag_data.get('tag', ''))
            tags.cell(row=row, column=2, value=tag_data.get('count', 0))
        
        # Create Daily Metrics sheet
        daily = wb.create_sheet("Daily Metrics")
        
        # Add headers
        daily['A1'] = "Date"
        daily['B1'] = "Interactions"
        daily['C1'] = "Positive Feedback"
        daily['A1'].font = Font(bold=True)
        daily['B1'].font = Font(bold=True)
        daily['C1'].font = Font(bold=True)
        
        # Add data
        time_metrics = analytics_data.get("time_metrics", [])
        for row, metric in enumerate(time_metrics, 2):
            daily.cell(row=row, column=1, value=metric.get('date', ''))
            daily.cell(row=row, column=2, value=metric.get('interaction_count', 0))
            daily.cell(row=row, column=3, value=metric.get('positive_count', 0))
        
        # Auto-adjust column widths
        for sheet in wb.sheetnames:
            for column in wb[sheet].columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = (max_length + 2)
                wb[sheet].column_dimensions[column_letter].width = adjusted_width
        
        # Save to BytesIO
        output = BytesIO()
        wb.save(output)
        output.seek(0)
        
        # Return as response
        return Response(
            output.getvalue(),
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f"attachment;filename=analytics_export_{timestamp}.xlsx"}
        )
    except ImportError:
        logger.error("openpyxl package not installed, falling back to CSV export")
        return export_as_csv(analytics_data, timestamp)
    except Exception as e:
        logger.error(f"Error exporting as Excel: {e}")
        raise
```

Add the required import for openpyxl to `requirements.txt`:

```
openpyxl==3.1.2
```

## Step 5.3: Connect Export Button

Update the `setupExportButton` function in `analytics_dashboard.html` to provide multiple export options:

```javascript
function setupExportButton() {
    const exportBtn = document.querySelector('button.ml-4');
    if (exportBtn) {
        exportBtn.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Remove any existing dropdown
            const existingDropdown = document.querySelector('.export-dropdown');
            if (existingDropdown) {
                existingDropdown.remove();
            }
            
            // Get current date range
            let exportUrlBase = '/api/analytics/export';
            
            // Add date parameters if a specific range is selected
            if (window.currentStartDate && window.currentEndDate) {
                exportUrlBase += `?start_date=${window.currentStartDate}&end_date=${window.currentEndDate}`;
            }
            
            // Create dropdown menu for export options
            const dropdown = document.createElement('div');
            dropdown.className = 'absolute right-0 mt-2 w-48 bg-white dark:bg-black text-white rounded-md shadow-lg py-1 z-10 export-dropdown';
            dropdown.innerHTML = `
                <a href="${exportUrlBase}" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                    <i class="fas fa-file-code mr-2"></i>Export as JSON
                </a>
                <a href="${exportUrlBase}${exportUrlBase.includes('?') ? '&' : '?'}format=csv" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                    <i class="fas fa-file-csv mr-2"></i>Export as CSV
                </a>
                <a href="${exportUrlBase}${exportUrlBase.includes('?') ? '&' : '?'}format=excel" class="block px-4 py-2 text-sm text-gray-700 hover:bg-gray-100">
                    <i class="fas fa-file-excel mr-2"></i>Export as Excel
                </a>
            `;
            
            // Position the dropdown relative to the button
            const buttonRect = exportBtn.getBoundingClientRect();
            dropdown.style.position = 'fixed';
            dropdown.style.top = (buttonRect.bottom + window.scrollY) + 'px';
            dropdown.style.right = (window.innerWidth - buttonRect.right) + 'px';
            
            // Add to document
            document.body.appendChild(dropdown);
            
            // Close dropdown when clicking outside
            document.addEventListener('click', function closeDropdown(e) {
                if (!dropdown.contains(e.target) && e.target !== exportBtn) {
                    dropdown.remove();
                    document.removeEventListener('click', closeDropdown);
                }
            });
            
            // Prevent event bubbling
            e.stopPropagation();
        });
    }
}
```

## Add Loading and Error States for Export

Add the following functions to handle loading and error states during export:

```javascript
function showExportLoadingState() {
    // Create loading overlay
    const loadingOverlay = document.createElement('div');
    loadingOverlay.className = 'fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 export-loading-overlay';
    loadingOverlay.innerHTML = `
        <div class="bg-white dark:bg-black text-white p-6 rounded-lg shadow-xl flex flex-col items-center">
            <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mb-4"></div>
            <p class="text-lg font-semibold">Preparing Export...</p>
            <p class="text-sm text-gray-500 mt-2">This may take a moment for large datasets.</p>
        </div>
    `;
    
    // Add to document
    document.body.appendChild(loadingOverlay);
    
    // Return the overlay element for later removal
    return loadingOverlay;
}

function hideExportLoadingState() {
    // Remove loading overlay
    const loadingOverlay = document.querySelector('.export-loading-overlay');
    if (loadingOverlay) {
        loadingOverlay.remove();
    }
}

// Modify the export links to show loading state
function setupExportLinks() {
    document.addEventListener('click', function(e) {
        // Check if the clicked element is an export link
        if (e.target.closest('.export-dropdown a')) {
            // Show loading state
            showExportLoadingState();
            
            // Hide loading state after 5 seconds (or when download starts)
            setTimeout(hideExportLoadingState, 5000);
        }
    });
}

// Call this function after initializing the export button
document.addEventListener('DOMContentLoaded', function() {
    // ... other initialization code ...
    
    // Setup export links
    setupExportLinks();
});
```

## Add Date Range Presets

Add the following function to provide quick date range presets:

```javascript
function setupDateRangePresets() {
    // Create preset buttons container
    const presetsContainer = document.createElement('div');
    presetsContainer.className = 'flex items-center space-x-2 mt-4 date-range-presets';
    presetsContainer.innerHTML = `
        <span class="text-sm text-gray-500">Quick Select:</span>
        <button class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded" data-days="7">Last 7 Days</button>
        <button class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded" data-days="30">Last 30 Days</button>
        <button class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded" data-days="90">Last 90 Days</button>
        <button class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded" data-range="month">This Month</button>
        <button class="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 rounded" data-range="year">This Year</button>
    `;
    
    // Add container after the date range button
    const dateRangeBtn = document.getElementById('date-range-btn');
    if (dateRangeBtn && dateRangeBtn.parentNode) {
        dateRangeBtn.parentNode.appendChild(presetsContainer);
    }
    
    // Add event listeners to preset buttons
    presetsContainer.querySelectorAll('button').forEach(button => {
        button.addEventListener('click', function() {
            let start, end;
            
            if (this.dataset.days) {
                // Last X days
                const days = parseInt(this.dataset.days);
                start = moment().subtract(days - 1, 'days');
                end = moment();
            } else if (this.dataset.range === 'month') {
                // This month
                start = moment().startOf('month');
                end = moment().endOf('month');
            } else if (this.dataset.range === 'year') {
                // This year
                start = moment().startOf('year');
                end = moment().endOf('year');
            }
            
            if (start && end) {
                // Update date range picker
                $(dateRangeBtn).data('daterangepicker').setStartDate(start);
                $(dateRangeBtn).data('daterangepicker').setEndDate(end);
                
                // Trigger change event
                $(dateRangeBtn).data('daterangepicker').callback(start, end, this.textContent);
            }
        });
    });
}

// Call this function after initializing the date range picker
document.addEventListener('DOMContentLoaded', function() {
    // ... other initialization code ...
    
    // Setup date range presets after a short delay to ensure date range picker is initialized
    setTimeout(setupDateRangePresets, 500);
});
```

## Testing Phase 5

After implementing these changes, you can test the enhanced date range and export functionality by:

1. Starting the Flask application:
   ```
   python main.py
   ```

2. Accessing the analytics dashboard in a browser:
   ```
   http://localhost:5002/analytics
   ```

3. Testing the date range picker and presets:
   - Click on the date range button to open the picker
   - Select different date ranges and verify the data updates
   - Click on the preset buttons and verify they work correctly

4. Testing the export functionality:
   - Click on the export button to open the dropdown
   - Try each export format (JSON, CSV, Excel)
   - Verify the downloaded files contain the correct data
   - Test with different date ranges

## Next Steps

After successfully implementing and testing Phase 5, proceed to Phase 6: Testing and Optimization to ensure the entire integration works correctly and performs well.
