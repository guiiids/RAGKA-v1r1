# Phase 1 Implementation Guide: Enhanced Data Collection

**Date:** June 22, 2025  
**Version:** 1.0  
**Related Documents:** 
- [Analytics Logging Strategy](analytics_logging_strategy.md)
- [RAG Analytics Implementation Plan](rag_analytics_implementation_plan.md)

## Overview

This document provides detailed implementation guidance for Phase 1 of the RAG Analytics Logging System. Phase 1 focuses on enhancing the existing logging infrastructure to capture essential metrics without requiring significant architectural changes.

## Prerequisites

Before beginning implementation, ensure you have:

1. Access to the codebase, particularly:
   - `openai_logger.py`
   - `rag_assistant.py`
   - `analytics_dashboard.html`
2. Basic understanding of the current logging system
3. Development environment set up with necessary dependencies
4. Backup of the current system

## Implementation Steps

### 1. Enhance OpenAI Logger

#### 1.1 Add Required Imports

Add the following imports to `openai_logger.py` if they don't already exist:

```python
import uuid
import re
import time
from typing import Dict, List, Any, Optional
```

#### 1.2 Implement Helper Functions

Add these helper functions to `openai_logger.py`:

```python
def count_tokens(text: str) -> int:
    """Estimate token count for a text string."""
    # Simple estimation: 1 token ≈ 4 characters
    return len(text) // 4

def has_citations(response: dict) -> bool:
    """Check if response contains citations."""
    if not response:
        return False
    response_text = response.get("content", "")
    if not response_text:
        return False
    return bool(re.search(r'\[\d+\]', response_text))

def count_citations(response: dict) -> int:
    """Count the number of citations in a response."""
    if not response:
        return 0
    response_text = response.get("content", "")
    if not response_text:
        return 0
    citations = re.findall(r'\[\d+\]', response_text)
    return len(citations)
```

#### 1.3 Enhance Log Record Structure

Modify the `log_openai_call` function to use the enhanced log record structure:

```python
def log_openai_call(request: Dict[str, Any], response: Any) -> None:
    """Log OpenAI API calls with enhanced metrics."""
    try:
        # Extract usage information
        usage = {}
        if hasattr(response, "usage") and response.usage:
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens
            }
        
        # Convert response to dictionary if needed
        resp_dict = {}
        if hasattr(response, "model_dump"):
            resp_dict = response.model_dump()
        elif hasattr(response, "to_dict"):
            resp_dict = response.to_dict()
        else:
            # Try to convert to dict using __dict__
            try:
                resp_dict = response.__dict__
            except:
                # Last resort: convert to string
                resp_dict = {"content": str(response)}
        
        # Create enhanced log record
        record = {
            "timestamp": time.time(),
            "request_id": str(uuid.uuid4()),  # Add unique ID for request tracking
            "request": request,
            
            # Query metrics
            "query_metrics": {
                "query_text": request.get("query_text", ""),
                "query_length": len(request.get("query_text", "")),
                "query_tokens": count_tokens(request.get("query_text", "")),
            },
            
            # Context metrics
            "context_metrics": {
                "context_length": request.get("context_length", 0),
                "num_context_chunks": request.get("num_context_chunks", 0),
                "chunk_relevance_scores": request.get("chunk_relevance_scores", []),
            },
            
            # Latency metrics
            "latency_metrics": {
                "embedding_time_ms": request.get("embedding_time_ms", 0),
                "search_time_ms": request.get("search_time_ms", 0),
                "llm_time_ms": request.get("llm_time_ms", 0),
                "total_time_ms": request.get("total_time_ms", 0),
            },
            
            # Token usage
            "tokens": {
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
                "total_tokens": usage.get("total_tokens", 0)
            },
            
            # Response metrics
            "response_metrics": {
                "response_length": len(str(resp_dict)),
                "has_citations": has_citations(resp_dict),
                "num_citations": count_citations(resp_dict),
            },
            
            # Raw data
            "usage": usage,
            "response": resp_dict
        }
        
        # Log the record
        logger.info(f"OpenAI API call: {json.dumps(record)}")
        
        # Write to log file
        with open(LOG_FILE, "a") as f:
            f.write(json.dumps(record) + "\n")
            
    except Exception as e:
        logger.error(f"Error logging OpenAI call: {e}")
```

### 2. Add Basic Instrumentation to RAG Assistant

#### 2.1 Instrument Embedding Generation

Modify the `generate_embedding` method in `rag_assistant.py`:

```python
def generate_embedding(self, text: str) -> Optional[List[float]]:
    start_time = time.time()
    if not text:
        logger.warning("generate_embedding called with empty text")
        return None
    try:
        request = {
            'model': self.embedding_deployment,
            'input': text.strip(),
            'embedding_start_time': start_time
        }
        resp = self.openai_client.embeddings.create(**request)
        embedding_time_ms = (time.time() - start_time) * 1000
        
        # Add metrics to request for logging
        request['embedding_time_ms'] = embedding_time_ms
        request['query_text'] = text
        
        log_openai_call(request, resp)
        return resp.data[0].embedding
    
    except Exception as exc:
        import traceback
        logger.error("Embedding error: %s\n%s", exc, traceback.format_exc())
        return None
```

#### 2.2 Instrument Vector Search

Modify the `search_knowledge_base` method in `rag_assistant.py`:

```python
def search_knowledge_base(self, query: str) -> List[Dict]:
    start_time = time.time()
    try:
        client = SearchClient(
            endpoint=f"https://{self.search_endpoint}.search.windows.net",
            index_name=self.search_index,
            credential=AzureKeyCredential(self.search_key),
        )
        q_vec = self.generate_embedding(query)
        if not q_vec:
            return []

        vec_q = VectorizedQuery(
            vector=q_vec,
            k_nearest_neighbors=10,
            fields=self.vector_field,
        )
        results = client.search(
            search_text=query,
            vector_queries=[vec_q],
            select=["chunk", "title"],
            top=10,
        )
        
        search_time_ms = (time.time() - start_time) * 1000
        
        # Process results and add metrics
        processed_results = []
        relevance_scores = []
        
        for r in results:
            relevance_score = r.get("@search.score", 0)
            relevance_scores.append(relevance_score)
            
            processed_results.append({
                "chunk": r.get("chunk", ""),
                "title": r.get("title", "Untitled"),
                "relevance": relevance_score,
                "_search_metrics": {
                    "search_time_ms": search_time_ms,
                    "relevance_score": relevance_score,
                }
            })
        
        # Log search metrics
        logger.info(f"Search metrics: query='{query}', time_ms={search_time_ms}, results={len(processed_results)}")
        
        return processed_results
    except Exception as exc:
        import traceback
        logger.error("Search error: %s\n%s", exc, traceback.format_exc())
        return []
```

#### 2.3 Instrument LLM Generation

Modify the `_chat_answer` method in `rag_assistant.py`:

```python
def _chat_answer(self, query: str, context: str, src_map: Dict) -> str:
    start_time = time.time()
    
    # Existing code for preparing the prompt...
    
    # Log detailed payload information
    logger.info("========== OPENAI API REQUEST DETAILS ==========")
    logger.info(f"Model deployment: {self.deployment_name}")
    logger.info(f"Temperature: {self.temperature}")
    logger.info(f"Max tokens: {self.max_tokens}")
    
    # Existing code for logging system prompt and user content...
    
    request = {
        'model': self.deployment_name,
        'messages': messages,
        'max_tokens': self.max_tokens,
        'temperature': self.temperature,
        'top_p': self.top_p,
        'presence_penalty': self.presence_penalty,
        'frequency_penalty': self.frequency_penalty,
        'llm_start_time': start_time,
        'query_text': query,
        'context_length': len(context),
        'num_context_chunks': len(src_map),
    }
    
    resp = self.openai_client.chat.completions.create(**request)
    
    llm_time_ms = (time.time() - start_time) * 1000
    
    # Add metrics to request for logging
    request['llm_time_ms'] = llm_time_ms
    request['total_time_ms'] = llm_time_ms  # This will be the LLM time only
    
    log_openai_call(request, resp)
    
    answer = resp.choices[0].message.content
    logger.info("DEBUG - OpenAI response content: %s", answer)
    
    return answer
```

#### 2.4 Instrument End-to-End Request Processing

Modify the `generate_rag_response` method in `rag_assistant.py`:

```python
def generate_rag_response(
    self, query: str
) -> Tuple[str, List[Dict], List[Dict], Dict[str, Any], str]:
    """
    Returns:
        answer, cited_sources, [], evaluation, context
    """
    total_start_time = time.time()
    metrics = {
        "query": query,
        "timestamp": time.time(),
        "request_id": str(uuid.uuid4()),
    }
    
    try:
        # Search phase
        search_start_time = time.time()
        kb_results = self.search_knowledge_base(query)
        search_time_ms = (time.time() - search_start_time) * 1000
        metrics["search_time_ms"] = search_time_ms
        
        if not kb_results:
            metrics["total_time_ms"] = (time.time() - total_start_time) * 1000
            logger.info(f"RAG metrics (no results): {metrics}")
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

        # LLM generation phase
        llm_start_time = time.time()
        answer = self._chat_answer(query, context, src_map)
        llm_time_ms = (time.time() - llm_start_time) * 1000
        metrics["llm_time_ms"] = llm_time_ms

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
        evaluation = self.fact_checker.evaluate_response(
            query=query,
            answer=answer,
            context=context,
            deployment=self.deployment_name,
        )
        
        post_time_ms = (time.time() - post_start_time) * 1000
        metrics["post_time_ms"] = post_time_ms
        
        # Total time
        metrics["total_time_ms"] = (time.time() - total_start_time) * 1000
        metrics["num_citations"] = len(cited_sources)
        metrics["response_length"] = len(answer)
        
        logger.info(f"RAG metrics: {metrics}")
        
        # Log the query to the database
        try:
            DatabaseManager.log_rag_query(
                query=query,
                response=answer,
                sources=cited_sources,
                context=context,
                metrics=metrics  # Add metrics to database logging
            )
        except Exception as log_exc:
            logger.error(f"Error logging RAG query to database: {log_exc}")
        
        return answer, cited_sources, [], evaluation, context
    
    except Exception as exc:
        import traceback
        logger.error("RAG generation error: %s\n%s", exc, traceback.format_exc())
        
        # Log error metrics
        metrics["error"] = str(exc)
        metrics["total_time_ms"] = (time.time() - total_start_time) * 1000
        logger.info(f"RAG metrics (error): {metrics}")
        
        return (
            "I encountered an error while generating the response.",
            [],
            [],
            {},
            "",
        )
```

### 3. Create Simple Analytics Dashboard

#### 3.1 Create SQL Queries for Basic Metrics

Create a file called `analytics_queries.sql` with the following queries:

```sql
-- Request volume over time (hourly)
SELECT 
    DATE_TRUNC('hour', TO_TIMESTAMP(timestamp)) AS hour,
    COUNT(*) AS request_count
FROM 
    rag_logs
WHERE 
    timestamp >= EXTRACT(EPOCH FROM NOW() - INTERVAL '7 days')
GROUP BY 
    hour
ORDER BY 
    hour;

-- Average response times
SELECT 
    DATE_TRUNC('day', TO_TIMESTAMP(timestamp)) AS day,
    AVG(latency_metrics->>'total_time_ms')::FLOAT AS avg_total_time_ms,
    AVG(latency_metrics->>'embedding_time_ms')::FLOAT AS avg_embedding_time_ms,
    AVG(latency_metrics->>'search_time_ms')::FLOAT AS avg_search_time_ms,
    AVG(latency_metrics->>'llm_time_ms')::FLOAT AS avg_llm_time_ms
FROM 
    rag_logs
WHERE 
    timestamp >= EXTRACT(EPOCH FROM NOW() - INTERVAL '7 days')
GROUP BY 
    day
ORDER BY 
    day;

-- Token usage trends
SELECT 
    DATE_TRUNC('day', TO_TIMESTAMP(timestamp)) AS day,
    SUM((tokens->>'prompt_tokens')::INT) AS total_prompt_tokens,
    SUM((tokens->>'completion_tokens')::INT) AS total_completion_tokens,
    SUM((tokens->>'total_tokens')::INT) AS total_tokens,
    COUNT(*) AS request_count,
    ROUND(AVG((tokens->>'total_tokens')::FLOAT)) AS avg_tokens_per_request
FROM 
    rag_logs
WHERE 
    timestamp >= EXTRACT(EPOCH FROM NOW() - INTERVAL '7 days')
GROUP BY 
    day
ORDER BY 
    day;
```

#### 3.2 Update Analytics Dashboard

Modify `analytics_dashboard.html` to include the new visualizations:

```html
<!-- Add these sections to the existing dashboard -->

<div class="card">
  <div class="card-header">
    <h5>Request Volume Over Time</h5>
  </div>
  <div class="card-body">
    <canvas id="requestVolumeChart"></canvas>
  </div>
</div>

<div class="card mt-4">
  <div class="card-header">
    <h5>Average Response Times</h5>
  </div>
  <div class="card-body">
    <canvas id="responseTimesChart"></canvas>
  </div>
</div>

<div class="card mt-4">
  <div class="card-header">
    <h5>Token Usage Trends</h5>
  </div>
  <div class="card-body">
    <canvas id="tokenUsageChart"></canvas>
  </div>
</div>

<!-- Add this JavaScript to initialize the charts -->
<script>
  // Fetch data from the server
  async function fetchAnalyticsData() {
    try {
      const response = await fetch('/api/analytics/data');
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Error fetching analytics data:', error);
      return null;
    }
  }

  // Initialize charts when the page loads
  document.addEventListener('DOMContentLoaded', async () => {
    const data = await fetchAnalyticsData();
    if (!data) return;
    
    // Request Volume Chart
    const requestVolumeCtx = document.getElementById('requestVolumeChart').getContext('2d');
    new Chart(requestVolumeCtx, {
      type: 'line',
      data: {
        labels: data.requestVolume.map(item => item.hour),
        datasets: [{
          label: 'Request Count',
          data: data.requestVolume.map(item => item.request_count),
          borderColor: 'rgba(75, 192, 192, 1)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.1
        }]
      },
      options: {
        responsive: true,
        scales: {
          y: {
            beginAtZero: true
          }
        }
      }
    });
    
    // Response Times Chart
    const responseTimesCtx = document.getElementById('responseTimesChart').getContext('2d');
    new Chart(responseTimesCtx, {
      type: 'line',
      data: {
        labels: data.responseTimes.map(item => item.day),
        datasets: [
          {
            label: 'Total Time',
            data: data.responseTimes.map(item => item.avg_total_time_ms),
            borderColor: 'rgba(255, 99, 132, 1)',
            backgroundColor: 'rgba(255, 99, 132, 0.2)',
          },
          {
            label: 'Embedding Time',
            data: data.responseTimes.map(item => item.avg_embedding_time_ms),
            borderColor: 'rgba(54, 162, 235, 1)',
            backgroundColor: 'rgba(54, 162, 235, 0.2)',
          },
          {
            label: 'Search Time',
            data: data.responseTimes.map(item => item.avg_search_time_ms),
            borderColor: 'rgba(255, 206, 86, 1)',
            backgroundColor: 'rgba(255, 206, 86, 0.2)',
          },
          {
            label: 'LLM Time',
            data: data.responseTimes.map(item => item.avg_llm_time_ms),
            borderColor: 'rgba(75, 192, 192, 1)',
            backgroundColor: 'rgba(75, 192, 192, 0.2)',
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
              text: 'Time (ms)'
            }
          }
        }
      }
    });
    
    // Token Usage Chart
    const tokenUsageCtx = document.getElementById('tokenUsageChart').getContext('2d');
    new Chart(tokenUsageCtx, {
      type: 'bar',
      data: {
        labels: data.tokenUsage.map(item => item.day),
        datasets: [
          {
            label: 'Prompt Tokens',
            data: data.tokenUsage.map(item => item.total_prompt_tokens),
            backgroundColor: 'rgba(54, 162, 235, 0.5)',
          },
          {
            label: 'Completion Tokens',
            data: data.tokenUsage.map(item => item.total_completion_tokens),
            backgroundColor: 'rgba(255, 99, 132, 0.5)',
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
              text: 'Token Count'
            }
          }
        },
        plugins: {
          tooltip: {
            callbacks: {
              footer: (tooltipItems) => {
                const index = tooltipItems[0].dataIndex;
                const avgTokens = data.tokenUsage[index].avg_tokens_per_request;
                return `Avg. Tokens per Request: ${avgTokens}`;
              }
            }
          }
        }
      }
    });
  });
</script>
```

#### 3.3 Create API Endpoint for Analytics Data

Add a new endpoint to your API server (e.g., in `main.py` or a separate file):

```python
@app.route('/api/analytics/data')
def get_analytics_data():
    """API endpoint to provide analytics data for the dashboard."""
    try:
        # Connect to the database
        conn = DatabaseManager.get_connection()
        cursor = conn.cursor(dictionary=True)
        
        # Request volume data
        cursor.execute("""
            SELECT 
                DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d %H:00') AS hour,
                COUNT(*) AS request_count
            FROM 
                rag_logs
            WHERE 
                timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY))
            GROUP BY 
                hour
            ORDER BY 
                hour
        """)
        request_volume = cursor.fetchall()
        
        # Response times data
        cursor.execute("""
            SELECT 
                DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d') AS day,
                AVG(JSON_EXTRACT(latency_metrics, '$.total_time_ms')) AS avg_total_time_ms,
                AVG(JSON_EXTRACT(latency_metrics, '$.embedding_time_ms')) AS avg_embedding_time_ms,
                AVG(JSON_EXTRACT(latency_metrics, '$.search_time_ms')) AS avg_search_time_ms,
                AVG(JSON_EXTRACT(latency_metrics, '$.llm_time_ms')) AS avg_llm_time_ms
            FROM 
                rag_logs
            WHERE 
                timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY))
            GROUP BY 
                day
            ORDER BY 
                day
        """)
        response_times = cursor.fetchall()
        
        # Token usage data
        cursor.execute("""
            SELECT 
                DATE_FORMAT(FROM_UNIXTIME(timestamp), '%Y-%m-%d') AS day,
                SUM(JSON_EXTRACT(tokens, '$.prompt_tokens')) AS total_prompt_tokens,
                SUM(JSON_EXTRACT(tokens, '$.completion_tokens')) AS total_completion_tokens,
                SUM(JSON_EXTRACT(tokens, '$.total_tokens')) AS total_tokens,
                COUNT(*) AS request_count,
                ROUND(AVG(JSON_EXTRACT(tokens, '$.total_tokens'))) AS avg_tokens_per_request
            FROM 
                rag_logs
            WHERE 
                timestamp >= UNIX_TIMESTAMP(DATE_SUB(NOW(), INTERVAL 7 DAY))
            GROUP BY 
                day
            ORDER BY 
                day
        """)
        token_usage = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({
            'requestVolume': request_volume,
            'responseTimes': response_times,
            'tokenUsage': token_usage
        })
    
    except Exception as e:
        logger.error(f"Error fetching analytics data: {e}")
        return jsonify({'error': str(e)}), 500
```

## Testing

### 1. Test Enhanced Logger

1. Make a sample request to the RAG system
2. Check the logs to ensure the enhanced metrics are being captured
3. Verify that the request ID is being generated correctly
4. Confirm that the timestamp is accurate

### 2. Test Instrumentation

1. Make a sample request to the RAG system
2. Check the logs to ensure timing metrics are being captured for:
   - Embedding generation
   - Vector search
   - LLM inference
   - Total request processing
3. Verify that the metrics are accurate and reasonable

### 3. Test Analytics Dashboard

1. Generate some sample data by making multiple requests to the RAG system
2. Open the analytics dashboard
3. Verify that the visualizations are displaying correctly
4. Check that the data is being updated in real-time

## Rollback Procedure

If issues are encountered during implementation, follow these steps to roll back:

1. Restore the original `openai_logger.py` from backup
2. Remove instrumentation from `rag_assistant.py`
3. Restore the original dashboard

## Next Steps

After successfully implementing Phase 1, proceed to Phase 2: Comprehensive Instrumentation, which will expand on the foundation built in Phase 1.
