# Phase 2 Implementation Guide: Comprehensive Instrumentation

**Date:** June 22, 2025  
**Version:** 1.0  
**Related Documents:** 
- [Analytics Logging Strategy](analytics_logging_strategy.md)
- [RAG Analytics Implementation Plan](rag_analytics_implementation_plan.md)
- [Phase 1 Implementation Guide](phase1_implementation_guide.md)

## Overview

This document provides detailed implementation guidance for Phase 2 of the RAG Analytics Logging System. Phase 2 builds upon the foundation established in Phase 1 by expanding instrumentation across the entire RAG pipeline to capture detailed performance metrics at each stage.

## Prerequisites

Before beginning Phase 2 implementation, ensure you have:

1. Successfully completed Phase 1 implementation
2. Verified that the basic metrics are being captured correctly
3. Confirmed that the analytics dashboard is functioning properly
4. Created backups of the current system

## Implementation Steps

### 1. Complete Pipeline Instrumentation

#### 1.1 Instrument Context Preparation

Modify the `_prepare_context` method in `rag_assistant.py`:

```python
def _prepare_context(self, results: List[Dict]) -> Tuple[str, Dict]:
    start_time = time.time()
    entries, src_map = [], {}
    sid = 1
    valid_chunks = 0
    chunk_lengths = []
    chunk_relevance_scores = []
    
    for res in results[:5]:
        chunk = res["chunk"].strip()
        if not chunk:
            continue

        valid_chunks += 1
        chunk_lengths.append(len(chunk))
        chunk_relevance_scores.append(res.get("relevance", 0))
        formatted_chunk = format_context_text(chunk)

        entries.append(f'<source id="{sid}">{formatted_chunk}</source>')
        src_map[str(sid)] = {
            "title": res["title"],
            "content": formatted_chunk,
            "relevance": res.get("relevance", 0),
            "length": len(chunk)
        }
        sid += 1

    context_str = "\n\n".join(entries)
    if valid_chunks == 0:
        context_str = "[No context available from knowledge base]"
        logging.getLogger(__name__).warning("No valid chunks found in _prepare_context, returning fallback context.")

    context_prep_time_ms = (time.time() - start_time) * 1000
    
    # Log context metrics
    context_metrics = {
        "context_prep_time_ms": context_prep_time_ms,
        "valid_chunks": valid_chunks,
        "total_context_length": len(context_str),
        "avg_chunk_length": sum(chunk_lengths) / len(chunk_lengths) if chunk_lengths else 0,
        "avg_chunk_relevance": sum(chunk_relevance_scores) / len(chunk_relevance_scores) if chunk_relevance_scores else 0,
        "chunk_relevance_scores": chunk_relevance_scores
    }
    
    logger.info(f"Context metrics: {json.dumps(context_metrics)}")
    
    return context_str, src_map
```

#### 1.2 Instrument Post-Processing

Modify the `_filter_cited` method in `rag_assistant.py`:

```python
def _filter_cited(self, answer: str, src_map: Dict) -> List[Dict]:
    start_time = time.time()
    
    cited = []
    cited_ids = set()
    
    # Extract citation IDs from the answer
    citation_matches = re.findall(r'\[(\d+)\]', answer)
    
    for cid in citation_matches:
        if cid in src_map and cid not in cited_ids:
            cited_ids.add(cid)
            cited.append({
                "id": cid,
                "title": src_map[cid]["title"],
                "content": src_map[cid]["content"],
                "relevance": src_map[cid].get("relevance", 0)
            })
    
    post_processing_time_ms = (time.time() - start_time) * 1000
    
    # Log post-processing metrics
    post_metrics = {
        "post_processing_time_ms": post_processing_time_ms,
        "num_citations": len(cited),
        "num_unique_citations": len(cited_ids),
        "citation_coverage": len(cited_ids) / len(src_map) if src_map else 0,
        "cited_ids": list(cited_ids)
    }
    
    logger.info(f"Post-processing metrics: {json.dumps(post_metrics)}")
    
    return cited
```

#### 1.3 Enhance End-to-End Instrumentation

Update the `generate_rag_response` method in `rag_assistant.py` to include more detailed metrics:

```python
def generate_rag_response(
    self, query: str
) -> Tuple[str, List[Dict], List[Dict], Dict[str, Any], str]:
    """
    Returns:
        answer, cited_sources, [], evaluation, context
    """
    total_start_time = time.time()
    request_id = str(uuid.uuid4())
    metrics = {
        "query": query,
        "timestamp": time.time(),
        "request_id": request_id,
        "query_length": len(query),
        "query_tokens": count_tokens(query),
    }
    
    try:
        # Search phase
        search_start_time = time.time()
        kb_results = self.search_knowledge_base(query)
        search_time_ms = (time.time() - search_start_time) * 1000
        metrics["search_time_ms"] = search_time_ms
        metrics["num_results"] = len(kb_results)
        
        if not kb_results:
            metrics["total_time_ms"] = (time.time() - total_start_time) * 1000
            metrics["status"] = "no_results"
            logger.info(f"RAG metrics (no results): {json.dumps(metrics)}")
            return (
                "No relevant information found in the knowledge base.",
                [],
                [],
                {},
                "",
            )

        # Context preparation phase
        context_start_time = time.time()
        context, src_map = self._prepare_context(kb_results)
        context_time_ms = (time.time() - context_start_time) * 1000
        metrics["context_time_ms"] = context_time_ms
        metrics["num_context_chunks"] = len(src_map)
        metrics["context_length"] = len(context)
        
        # Calculate relevance statistics
        relevance_scores = [src_map[sid].get("relevance", 0) for sid in src_map]
        if relevance_scores:
            metrics["avg_chunk_relevance"] = sum(relevance_scores) / len(relevance_scores)
            metrics["max_chunk_relevance"] = max(relevance_scores)
            metrics["min_chunk_relevance"] = min(relevance_scores)
        
        # Calculate chunk length statistics
        chunk_lengths = [src_map[sid].get("length", 0) for sid in src_map]
        if chunk_lengths:
            metrics["avg_chunk_length"] = sum(chunk_lengths) / len(chunk_lengths)
            metrics["max_chunk_length"] = max(chunk_lengths)
            metrics["min_chunk_length"] = min(chunk_lengths)
            metrics["total_chunks_length"] = sum(chunk_lengths)

        # LLM generation phase
        llm_start_time = time.time()
        answer = self._chat_answer(query, context, src_map)
        llm_time_ms = (time.time() - llm_start_time) * 1000
        metrics["llm_time_ms"] = llm_time_ms
        metrics["answer_length"] = len(answer)
        metrics["answer_tokens"] = count_tokens(answer)

        # Post-processing phase
        post_start_time = time.time()
        cited_raw = self._filter_cited(answer, src_map)
        
        # Renumber citations
        renumber_map = {}
        cited_sources = []
        for new_id, src in enumerate(cited_raw, 1):
            old_id = src["id"]
            renumber_map[old_id] = str(new_id)
            entry = {"id": str(new_id), "title": src["title"], "content": src["content"]}
            if "url" in src:
                entry["url"] = src["url"]
            cited_sources.append(entry)
        for old, new in renumber_map.items():
            answer = re.sub(rf"\[{old}\]", f"[{new}]", answer)

        # Evaluation
        eval_start_time = time.time()
        evaluation = self.fact_checker.evaluate_response(
            query=query,
            answer=answer,
            context=context,
            deployment=self.deployment_name,
        )
        eval_time_ms = (time.time() - eval_start_time) * 1000
        
        post_time_ms = (time.time() - post_start_time) * 1000
        metrics["post_time_ms"] = post_time_ms
        metrics["eval_time_ms"] = eval_time_ms
        
        # Citation metrics
        metrics["num_citations"] = len(cited_sources)
        metrics["citation_ratio"] = len(cited_sources) / len(src_map) if src_map else 0
        
        # Evaluation metrics
        if evaluation:
            metrics["evaluation"] = {
                "accuracy_score": evaluation.get("accuracy_score", 0),
                "relevance_score": evaluation.get("relevance_score", 0),
                "coherence_score": evaluation.get("coherence_score", 0),
                "overall_score": evaluation.get("overall_score", 0),
            }
        
        # Total time
        metrics["total_time_ms"] = (time.time() - total_start_time) * 1000
        metrics["response_length"] = len(answer)
        metrics["status"] = "success"
        
        logger.info(f"RAG metrics: {json.dumps(metrics)}")
        
        # Log the query to the database
        try:
            DatabaseManager.log_rag_query(
                query=query,
                response=answer,
                sources=cited_sources,
                context=context,
                metrics=metrics,
                request_id=request_id
            )
        except Exception as log_exc:
            logger.error(f"Error logging RAG query to database: {log_exc}")
        
        return answer, cited_sources, [], evaluation, context
    
    except Exception as exc:
        import traceback
        logger.error("RAG generation error: %s\n%s", exc, traceback.format_exc())
        
        # Log error metrics
        metrics["error"] = str(exc)
        metrics["error_type"] = exc.__class__.__name__
        metrics["error_location"] = traceback.format_exc().split("\n")[-3] if traceback.format_exc() else ""
        metrics["total_time_ms"] = (time.time() - total_start_time) * 1000
        metrics["status"] = "error"
        
        logger.info(f"RAG metrics (error): {json.dumps(metrics)}")
        
        # Log the error to the database
        try:
            DatabaseManager.log_rag_error(
                query=query,
                error=str(exc),
                error_type=exc.__class__.__name__,
                traceback=traceback.format_exc(),
                metrics=metrics,
                request_id=request_id
            )
        except Exception as log_exc:
            logger.error(f"Error logging RAG error to database: {log_exc}")
        
        return (
            "I encountered an error while generating the response.",
            [],
            [],
            {},
            "",
        )
```

### 2. Implement Error Tracking

#### 2.1 Create Error Logging Function

Add a new method to `DatabaseManager` in `db_manager.py`:

```python
@staticmethod
def log_rag_error(query: str, error: str, error_type: str, traceback: str, metrics: Dict, request_id: str) -> None:
    """
    Log RAG errors to the database.
    
    Args:
        query: The user query that caused the error
        error: The error message
        error_type: The type of error (exception class name)
        traceback: The full traceback
        metrics: Performance metrics collected before the error
        request_id: Unique identifier for the request
    """
    try:
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            """
            INSERT INTO rag_errors (
                request_id, timestamp, query, error, error_type, traceback, metrics
            ) VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (
                request_id,
                datetime.datetime.now(),
                query,
                error,
                error_type,
                traceback,
                json.dumps(metrics)
            )
        )
        
        conn.commit()
        cursor.close()
        conn.close()
        
    except Exception as e:
        logger.error(f"Error logging RAG error to database: {e}")
```

#### 2.2 Create Error Database Table

Create a new SQL file called `error_tracking_schema.sql`:

```sql
-- Create table for RAG errors
CREATE TABLE IF NOT EXISTS rag_errors (
    id SERIAL PRIMARY KEY,
    request_id UUID NOT NULL,
    timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    query TEXT NOT NULL,
    error TEXT NOT NULL,
    error_type VARCHAR(100) NOT NULL,
    traceback TEXT,
    metrics JSONB,
    resolved BOOLEAN DEFAULT FALSE,
    resolution_notes TEXT,
    resolution_timestamp TIMESTAMP WITH TIME ZONE
);

-- Create indexes for efficient querying
CREATE INDEX IF NOT EXISTS idx_rag_errors_request_id ON rag_errors(request_id);
CREATE INDEX IF NOT EXISTS idx_rag_errors_timestamp ON rag_errors(timestamp);
CREATE INDEX IF NOT EXISTS idx_rag_errors_error_type ON rag_errors(error_type);
CREATE INDEX IF NOT EXISTS idx_rag_errors_resolved ON rag_errors(resolved);
```

#### 2.3 Add Error Dashboard

Create a new file called `error_dashboard.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG Error Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container mt-4">
        <h1>RAG Error Dashboard</h1>
        
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Error Frequency by Type</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="errorTypeChart"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5>Error Trend Over Time</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="errorTrendChart"></canvas>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="card mt-4">
            <div class="card-header">
                <h5>Recent Errors</h5>
            </div>
            <div class="card-body">
                <table class="table table-striped">
                    <thead>
                        <tr>
                            <th>Timestamp</th>
                            <th>Error Type</th>
                            <th>Query</th>
                            <th>Error</th>
                            <th>Status</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody id="errorTableBody">
                        <!-- Error data will be populated here -->
                    </tbody>
                </table>
            </div>
        </div>
    </div>
    
    <!-- Error Details Modal -->
    <div class="modal fade" id="errorDetailsModal" tabindex="-1">
        <div class="modal-dialog modal-lg">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Error Details</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <h6>Query</h6>
                    <pre id="errorQuery" class="bg-light p-2"></pre>
                    
                    <h6>Error</h6>
                    <pre id="errorMessage" class="bg-light p-2"></pre>
                    
                    <h6>Traceback</h6>
                    <pre id="errorTraceback" class="bg-light p-2"></pre>
                    
                    <h6>Metrics</h6>
                    <pre id="errorMetrics" class="bg-light p-2"></pre>
                    
                    <div id="resolutionSection">
                        <h6>Resolution Notes</h6>
                        <textarea id="resolutionNotes" class="form-control" rows="3"></textarea>
                        <button id="markResolvedBtn" class="btn btn-success mt-2">Mark as Resolved</button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        // Fetch error data from the server
        async function fetchErrorData() {
            try {
                const response = await fetch('/api/errors/data');
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error fetching error data:', error);
                return null;
            }
        }
        
        // Fetch error details
        async function fetchErrorDetails(errorId) {
            try {
                const response = await fetch(`/api/errors/${errorId}`);
                const data = await response.json();
                return data;
            } catch (error) {
                console.error('Error fetching error details:', error);
                return null;
            }
        }
        
        // Mark error as resolved
        async function resolveError(errorId, notes) {
            try {
                const response = await fetch(`/api/errors/${errorId}/resolve`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        resolution_notes: notes
                    })
                });
                return await response.json();
            } catch (error) {
                console.error('Error resolving error:', error);
                return null;
            }
        }
        
        // Initialize charts and tables when the page loads
        document.addEventListener('DOMContentLoaded', async () => {
            const data = await fetchErrorData();
            if (!data) return;
            
            // Error Type Chart
            const errorTypeCtx = document.getElementById('errorTypeChart').getContext('2d');
            new Chart(errorTypeCtx, {
                type: 'pie',
                data: {
                    labels: data.errorTypes.map(item => item.error_type),
                    datasets: [{
                        data: data.errorTypes.map(item => item.count),
                        backgroundColor: [
                            'rgba(255, 99, 132, 0.7)',
                            'rgba(54, 162, 235, 0.7)',
                            'rgba(255, 206, 86, 0.7)',
                            'rgba(75, 192, 192, 0.7)',
                            'rgba(153, 102, 255, 0.7)',
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'right',
                        }
                    }
                }
            });
            
            // Error Trend Chart
            const errorTrendCtx = document.getElementById('errorTrendChart').getContext('2d');
            new Chart(errorTrendCtx, {
                type: 'line',
                data: {
                    labels: data.errorTrend.map(item => item.day),
                    datasets: [{
                        label: 'Error Count',
                        data: data.errorTrend.map(item => item.count),
                        borderColor: 'rgba(255, 99, 132, 1)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    scales: {
                        y: {
                            beginAtZero: true,
                            ticks: {
                                precision: 0
                            }
                        }
                    }
                }
            });
            
            // Populate error table
            const tableBody = document.getElementById('errorTableBody');
            data.recentErrors.forEach(error => {
                const row = document.createElement('tr');
                
                // Format timestamp
                const timestamp = new Date(error.timestamp).toLocaleString();
                
                // Create table cells
                row.innerHTML = `
                    <td>${timestamp}</td>
                    <td>${error.error_type}</td>
                    <td>${error.query.substring(0, 50)}${error.query.length > 50 ? '...' : ''}</td>
                    <td>${error.error.substring(0, 50)}${error.error.length > 50 ? '...' : ''}</td>
                    <td>${error.resolved ? '<span class="badge bg-success">Resolved</span>' : '<span class="badge bg-danger">Open</span>'}</td>
                    <td>
                        <button class="btn btn-sm btn-primary view-details" data-error-id="${error.id}">View Details</button>
                    </td>
                `;
                
                tableBody.appendChild(row);
            });
            
            // Add event listeners for view details buttons
            document.querySelectorAll('.view-details').forEach(button => {
                button.addEventListener('click', async () => {
                    const errorId = button.getAttribute('data-error-id');
                    const errorDetails = await fetchErrorDetails(errorId);
                    
                    if (errorDetails) {
                        document.getElementById('errorQuery').textContent = errorDetails.query;
                        document.getElementById('errorMessage').textContent = errorDetails.error;
                        document.getElementById('errorTraceback').textContent = errorDetails.traceback;
                        document.getElementById('errorMetrics').textContent = JSON.stringify(errorDetails.metrics, null, 2);
                        
                        if (errorDetails.resolved) {
                            document.getElementById('resolutionNotes').value = errorDetails.resolution_notes || '';
                            document.getElementById('resolutionNotes').disabled = true;
                            document.getElementById('markResolvedBtn').style.display = 'none';
                        } else {
                            document.getElementById('resolutionNotes').value = '';
                            document.getElementById('resolutionNotes').disabled = false;
                            document.getElementById('markResolvedBtn').style.display = 'block';
                            
                            // Add event listener for resolve button
                            document.getElementById('markResolvedBtn').onclick = async () => {
                                const notes = document.getElementById('resolutionNotes').value;
                                await resolveError(errorId, notes);
                                
                                // Refresh the page to show updated data
                                window.location.reload();
                            };
                        }
                        
                        // Show the modal
                        const modal = new bootstrap.Modal(document.getElementById('errorDetailsModal'));
                        modal.show();
                    }
                });
            });
        });
    </script>
</body>
</html>
```

#### 2.4 Add API Endpoints for Error Dashboard

Add the following endpoints to your API server (e.g., in `main.py` or a separate file):

```python
@app.route('/api/errors/data')
def get_error_data():
    """API endpoint to provide error data for the dashboard."""
    try:
        # Connect to the database
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Error types data
        cursor.execute("""
            SELECT 
                error_type,
                COUNT(*) as count
            FROM 
                rag_errors
            WHERE 
                timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY 
                error_type
            ORDER BY 
                count DESC
            LIMIT 10
        """)
        error_types = cursor.fetchall()
        
        # Error trend data
        cursor.execute("""
            SELECT 
                DATE_FORMAT(timestamp, '%Y-%m-%d') AS day,
                COUNT(*) as count
            FROM 
                rag_errors
            WHERE 
                timestamp >= NOW() - INTERVAL '30 days'
            GROUP BY 
                day
            ORDER BY 
                day
        """)
        error_trend = cursor.fetchall()
        
        # Recent errors
        cursor.execute("""
            SELECT 
                id,
                request_id,
                timestamp,
                query,
                error,
                error_type,
                resolved
            FROM 
                rag_errors
            ORDER BY 
                timestamp DESC
            LIMIT 50
        """)
        recent_errors = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'errorTypes': error_types,
            'errorTrend': error_trend,
            'recentErrors': recent_errors
        })
    
    except Exception as e:
        logger.error(f"Error fetching error data: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/errors/<int:error_id>')
def get_error_details(error_id):
    """API endpoint to provide detailed information about a specific error."""
    try:
        # Connect to the database
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT 
                id,
                request_id,
                timestamp,
                query,
                error,
                error_type,
                traceback,
                metrics,
                resolved,
                resolution_notes,
                resolution_timestamp
            FROM 
                rag_errors
            WHERE 
                id = %s
        """, (error_id,))
        
        error_details = cursor.fetchone()
        
        cursor.close()
        conn.close()
        
        if error_details:
            # Parse JSON fields
            if error_details['metrics']:
                error_details['metrics'] = json.loads(error_details['metrics'])
            
            return jsonify(error_details)
        else:
            return jsonify({'error': 'Error not found'}), 404
    
    except Exception as e:
        logger.error(f"Error fetching error details: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/errors/<int:error_id>/resolve', methods=['POST'])
def resolve_error(error_id):
    """API endpoint to mark an error as resolved."""
    try:
        data = request.json
        resolution_notes = data.get('resolution_notes', '')
        
        # Connect to the database
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE rag_errors
            SET 
                resolved = TRUE,
                resolution_notes = %s,
                resolution_timestamp = NOW()
            WHERE 
                id = %s
        """, (resolution_notes, error_id))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        return jsonify({'success': True})
    
    except Exception as e:
        logger.error(f"Error resolving error: {e}")
        return jsonify({'error': str(e)}), 500
```

### 3. Implement User Interaction Metrics

#### 3.1 Add Feedback Collection to Frontend

Create a new file called `feedback.js` in the static/js directory:

```javascript
// feedback.js - Collects user feedback on RAG responses

document.addEventListener('DOMContentLoaded', function() {
    // Initialize feedback components
    initFeedbackComponents();
    
    // Add event listeners for feedback buttons
    addFeedbackEventListeners();
});

function initFeedbackComponents() {
    // Find all RAG response containers
    const responseContainers = document.querySelectorAll('.rag-response-container');
    
    // Add feedback UI to each container
    responseContainers.forEach(container => {
        const requestId = container.getAttribute('data-request-id');
        if (!requestId) return;
        
        // Create feedback UI
        const feedbackDiv = document.createElement('div');
        feedbackDiv.className = 'feedback-container mt-3';
        feedbackDiv.innerHTML = `
            <p class="feedback-prompt mb-2">Was this response helpful?</p>
            <div class="feedback-buttons">
                <button class="btn btn-outline-success btn-sm feedback-btn" data-value="positive" data-request-id="${requestId}">
                    <i class="bi bi-hand-thumbs-up"></i> Yes
                </button>
                <button class="btn btn-outline-danger btn-sm feedback-btn" data-value="negative" data-request-id="${requestId}">
                    <i class="bi bi-hand-thumbs-down"></i> No
                </button>
            </div>
            <div class="feedback-details mt-2" style="display: none;">
                <textarea class="form-control feedback-comment" placeholder="Please provide additional feedback (optional)"></textarea>
                <div class="feedback-tags mt-2">
                    <span class="badge bg-secondary feedback-tag" data-tag="accurate">Accurate</span>
                    <span class="badge bg-secondary feedback-tag" data-tag="inaccurate">Inaccurate</span>
                    <span class="badge bg-secondary feedback-tag" data-tag="helpful">Helpful</span>
                    <span class="badge bg-secondary feedback-tag" data-tag="unhelpful">Unhelpful</span>
                    <span class="badge bg-secondary feedback-tag" data-tag="relevant">Relevant</span>
                    <span class="badge bg-secondary feedback-tag" data-tag="irrelevant">Irrelevant</span>
                    <span class="badge bg-secondary feedback-
