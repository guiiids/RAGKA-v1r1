# Phase 5 Implementation Guide: Optimization & Feedback Loop

**Date:** June 22, 2025  
**Version:** 1.0  
**Related Documents:** 
- [Analytics Logging Strategy](analytics_logging_strategy.md)
- [RAG Analytics Implementation Plan](rag_analytics_implementation_plan.md)
- [Phase 1 Implementation Guide](phase1_implementation_guide.md)
- [Phase 2 Implementation Guide](phase2_implementation_guide.md)
- [Phase 3 Implementation Guide](phase3_implementation_guide.md)
- [Phase 4 Implementation Guide](phase4_implementation_guide.md)

## Overview

This document provides detailed implementation guidance for Phase 5 of the RAG Analytics Logging System. Phase 5 focuses on using the collected analytics to optimize the RAG system and create a continuous improvement cycle.

## Prerequisites

Before beginning Phase 5 implementation, ensure you have:

1. Successfully completed Phase 4 implementation
2. Verified that the advanced analytics dashboard is functioning properly
3. Confirmed that the anomaly detection system is working correctly
4. Created backups of the current system

## Implementation Steps

### 1. Performance Optimization Framework

#### 1.1 Create Bottleneck Identification System

Create a new Python file called `bottleneck_analyzer.py`:

```python
#!/usr/bin/env python3
"""
Bottleneck identification and analysis for RAG system optimization.
"""

import os
import sys
import json
import logging
import datetime
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('bottleneck_analyzer.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'raganalytics')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

# Analysis parameters
LATENCY_THRESHOLD_MS = 1000  # 1 second
PERCENTILE_THRESHOLD = 95    # 95th percentile
MIN_SAMPLE_SIZE = 100        # Minimum number of samples for reliable analysis

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

def analyze_component_bottlenecks(conn, days=30):
    """
    Analyze component-level bottlenecks in the RAG pipeline.
    
    Args:
        conn: Database connection
        days: Number of days to analyze
        
    Returns:
        Dictionary with bottleneck analysis results
    """
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get component latency data
        query = """
            SELECT
                component,
                AVG(avg_time_ms) AS avg_time,
                MAX(max_time_ms) AS max_time,
                AVG(p95_time_ms) AS p95_time,
                AVG(p99_time_ms) AS p99_time,
                SUM(count) AS sample_count
            FROM
                latency_metrics
            WHERE
                date >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY
                component
            ORDER BY
                avg_time DESC
        """
        
        cursor.execute(query, (days,))
        results = cursor.fetchall()
        
        # Convert to list of dictionaries
        components = [dict(row) for row in results]
        
        # Calculate total latency
        total_avg_time = sum(c['avg_time'] for c in components if c['component'] != 'total')
        
        # Calculate contribution percentages
        for component in components:
            if component['component'] != 'total':
                component['contribution_pct'] = (component['avg_time'] / total_avg_time * 100) if total_avg_time > 0 else 0
            else:
                component['contribution_pct'] = 100
        
        # Identify bottlenecks
        bottlenecks = []
        
        for component in components:
            if component['component'] == 'total':
                continue
                
            if component['sample_count'] < MIN_SAMPLE_SIZE:
                continue
                
            is_bottleneck = False
            bottleneck_reasons = []
            
            # Check if component contributes significantly to total latency
            if component['contribution_pct'] >= 30:
                is_bottleneck = True
                bottleneck_reasons.append(f"Component contributes {component['contribution_pct']:.1f}% to total latency")
            
            # Check if p95 latency exceeds threshold
            if component['p95_time'] >= LATENCY_THRESHOLD_MS:
                is_bottleneck = True
                bottleneck_reasons.append(f"95th percentile latency ({component['p95_time']:.1f} ms) exceeds threshold ({LATENCY_THRESHOLD_MS} ms)")
            
            # Check if max latency is significantly higher than average
            if component['max_time'] >= 5 * component['avg_time']:
                is_bottleneck = True
                bottleneck_reasons.append(f"Maximum latency ({component['max_time']:.1f} ms) is {component['max_time'] / component['avg_time']:.1f}x higher than average")
            
            if is_bottleneck:
                bottlenecks.append({
                    'component': component['component'],
                    'avg_time_ms': component['avg_time'],
                    'p95_time_ms': component['p95_time'],
                    'max_time_ms': component['max_time'],
                    'contribution_pct': component['contribution_pct'],
                    'reasons': bottleneck_reasons,
                    'severity': 'high' if component['contribution_pct'] >= 50 or component['p95_time'] >= 2 * LATENCY_THRESHOLD_MS else 'medium'
                })
        
        # Sort bottlenecks by contribution percentage
        bottlenecks.sort(key=lambda x: x['contribution_pct'], reverse=True)
        
        cursor.close()
        
        return {
            'components': components,
            'bottlenecks': bottlenecks,
            'total_avg_time_ms': next((c['avg_time'] for c in components if c['component'] == 'total'), 0)
        }
    
    except Exception as e:
        logger.error(f"Error analyzing component bottlenecks: {e}")
        raise

def analyze_query_patterns(conn, days=30):
    """
    Analyze query patterns to identify optimization opportunities.
    
    Args:
        conn: Database connection
        days: Number of days to analyze
        
    Returns:
        Dictionary with query pattern analysis results
    """
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get query pattern data
        query = """
            SELECT
                query_template,
                COUNT(*) AS frequency,
                AVG(avg_tokens) AS avg_tokens,
                AVG(avg_response_time_ms) AS avg_response_time_ms
            FROM
                query_patterns
            WHERE
                date >= CURRENT_DATE - INTERVAL '%s days'
            GROUP BY
                query_template
            ORDER BY
                frequency DESC
            LIMIT 20
        """
        
        cursor.execute(query, (days,))
        patterns = [dict(row) for row in cursor.fetchall()]
        
        # Get overall average response time
        avg_query = """
            SELECT
                AVG(avg_response_time_ms) AS overall_avg_time
            FROM
                query_patterns
            WHERE
                date >= CURRENT_DATE - INTERVAL '%s days'
        """
        
        cursor.execute(avg_query, (days,))
        overall_result = cursor.fetchone()
        overall_avg_time = overall_result['overall_avg_time'] if overall_result else 0
        
        # Identify optimization opportunities
        opportunities = []
        
        for pattern in patterns:
            if pattern['frequency'] < 10:
                continue
                
            is_opportunity = False
            opportunity_reasons = []
            
            # Check if pattern is frequent
            if pattern['frequency'] >= 100:
                is_opportunity = True
                opportunity_reasons.append(f"High frequency pattern ({pattern['frequency']} occurrences)")
            
            # Check if response time is significantly higher than average
            if pattern['avg_response_time_ms'] >= 1.5 * overall_avg_time:
                is_opportunity = True
                opportunity_reasons.append(f"Response time ({pattern['avg_response_time_ms']:.1f} ms) is {pattern['avg_response_time_ms'] / overall_avg_time:.1f}x higher than average")
            
            # Check if token usage is high
            if pattern['avg_tokens'] >= 1000:
                is_opportunity = True
                opportunity_reasons.append(f"High token usage ({pattern['avg_tokens']:.0f} tokens per query)")
            
            if is_opportunity:
                opportunities.append({
                    'pattern': pattern['query_template'],
                    'frequency': pattern['frequency'],
                    'avg_response_time_ms': pattern['avg_response_time_ms'],
                    'avg_tokens': pattern['avg_tokens'],
                    'reasons': opportunity_reasons,
                    'potential_savings': (pattern['avg_response_time_ms'] - overall_avg_time) * pattern['frequency'] / 1000,  # in seconds
                    'priority': 'high' if pattern['frequency'] >= 100 and pattern['avg_response_time_ms'] >= 2 * overall_avg_time else 'medium'
                })
        
        # Sort opportunities by potential savings
        opportunities.sort(key=lambda x: x['potential_savings'], reverse=True)
        
        cursor.close()
        
        return {
            'patterns': patterns,
            'opportunities': opportunities,
            'overall_avg_time_ms': overall_avg_time
        }
    
    except Exception as e:
        logger.error(f"Error analyzing query patterns: {e}")
        raise

def analyze_retrieval_quality(conn, days=30):
    """
    Analyze retrieval quality to identify optimization opportunities.
    
    Args:
        conn: Database connection
        days: Number of days to analyze
        
    Returns:
        Dictionary with retrieval quality analysis results
    """
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get retrieval quality data
        query = """
            SELECT
                AVG(avg_chunk_relevance) AS avg_relevance,
                AVG(num_chunks_retrieved) AS avg_chunks_retrieved,
                AVG(num_chunks_cited) AS avg_chunks_cited,
                AVG(CASE WHEN num_chunks_retrieved > 0 THEN 
                    num_chunks_cited::FLOAT / num_chunks_retrieved 
                    ELSE 0 END) AS avg_citation_rate
            FROM
                rag_query_performance
            WHERE
                timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
        """
        
        cursor.execute(query, (days,))
        overall_stats = dict(cursor.fetchone()) if cursor.rowcount > 0 else {
            'avg_relevance': 0,
            'avg_chunks_retrieved': 0,
            'avg_chunks_cited': 0,
            'avg_citation_rate': 0
        }
        
        # Get distribution of relevance scores
        relevance_query = """
            SELECT
                ROUND(avg_chunk_relevance * 10) / 10 AS relevance_bin,
                COUNT(*) AS count
            FROM
                rag_query_performance
            WHERE
                timestamp >= CURRENT_TIMESTAMP - INTERVAL '%s days'
                AND avg_chunk_relevance IS NOT NULL
            GROUP BY
                relevance_bin
            ORDER BY
                relevance_bin
        """
        
        cursor.execute(relevance_query, (days,))
        relevance_distribution = [dict(row) for row in cursor.fetchall()]
        
        # Identify optimization opportunities
        opportunities = []
        
        # Check if average relevance is low
        if overall_stats['avg_relevance'] < 0.7:
            opportunities.append({
                'area': 'retrieval_relevance',
                'issue': 'Low average relevance score',
                'current_value': overall_stats['avg_relevance'],
                'target_value': 0.8,
                'recommendation': 'Improve embedding model or vector search configuration',
                'priority': 'high' if overall_stats['avg_relevance'] < 0.5 else 'medium'
            })
        
        # Check if citation rate is low
        if overall_stats['avg_citation_rate'] < 0.5:
            opportunities.append({
                'area': 'citation_usage',
                'issue': 'Low citation rate',
                'current_value': overall_stats['avg_citation_rate'],
                'target_value': 0.7,
                'recommendation': 'Improve context relevance or adjust prompt to encourage citation',
                'priority': 'high' if overall_stats['avg_citation_rate'] < 0.3 else 'medium'
            })
        
        # Check if retrieving too many chunks
        if overall_stats['avg_chunks_retrieved'] > 5 and overall_stats['avg_chunks_cited'] < 3:
            opportunities.append({
                'area': 'chunk_count',
                'issue': 'Retrieving more chunks than necessary',
                'current_value': overall_stats['avg_chunks_retrieved'],
                'target_value': overall_stats['avg_chunks_cited'] + 1,
                'recommendation': 'Reduce number of chunks retrieved to improve efficiency',
                'priority': 'medium'
            })
        
        cursor.close()
        
        return {
            'overall_stats': overall_stats,
            'relevance_distribution': relevance_distribution,
            'opportunities': opportunities
        }
    
    except Exception as e:
        logger.error(f"Error analyzing retrieval quality: {e}")
        raise

def generate_optimization_recommendations(conn, days=30):
    """
    Generate comprehensive optimization recommendations.
    
    Args:
        conn: Database connection
        days: Number of days to analyze
        
    Returns:
        Dictionary with optimization recommendations
    """
    try:
        # Analyze different aspects of the system
        bottleneck_analysis = analyze_component_bottlenecks(conn, days)
        query_analysis = analyze_query_patterns(conn, days)
        retrieval_analysis = analyze_retrieval_quality(conn, days)
        
        # Combine all opportunities
        all_opportunities = []
        
        # Add bottleneck opportunities
        for bottleneck in bottleneck_analysis['bottlenecks']:
            recommendation = ""
            if bottleneck['component'] == 'embedding':
                recommendation = "Consider caching embeddings or using a faster embedding model"
            elif bottleneck['component'] == 'search':
                recommendation = "Optimize vector search configuration or consider using approximate nearest neighbors"
            elif bottleneck['component'] == 'llm':
                recommendation = "Consider using a smaller/faster model or implementing response streaming"
            elif bottleneck['component'] == 'context':
                recommendation = "Optimize context preparation or reduce context size"
            else:
                recommendation = f"Investigate and optimize the {bottleneck['component']} component"
            
            all_opportunities.append({
                'category': 'performance',
                'component': bottleneck['component'],
                'issue': f"{bottleneck['component']} component is a performance bottleneck",
                'impact': f"Contributes {bottleneck['contribution_pct']:.1f}% to total latency",
                'recommendation': recommendation,
                'priority': bottleneck['severity'],
                'potential_improvement': f"{bottleneck['contribution_pct'] / 2:.1f}% reduction in total latency"
            })
        
        # Add query pattern opportunities
        for opportunity in query_analysis['opportunities']:
            all_opportunities.append({
                'category': 'query_patterns',
                'component': 'general',
                'issue': f"Frequently occurring query pattern with high latency",
                'impact': f"Pattern occurs {opportunity['frequency']} times with {opportunity['avg_response_time_ms']:.1f} ms avg response time",
                'recommendation': "Consider creating specialized handling for this query pattern",
                'priority': opportunity['priority'],
                'potential_improvement': f"{opportunity['potential_savings']:.1f} seconds saved over {days} days"
            })
        
        # Add retrieval quality opportunities
        for opportunity in retrieval_analysis['opportunities']:
            all_opportunities.append({
                'category': 'retrieval',
                'component': opportunity['area'],
                'issue': opportunity['issue'],
                'impact': f"Current value: {opportunity['current_value']:.2f}, Target: {opportunity['target_value']:.2f}",
                'recommendation': opportunity['recommendation'],
                'priority': opportunity['priority'],
                'potential_improvement': "Improved response quality and user satisfaction"
            })
        
        # Sort opportunities by priority and category
        all_opportunities.sort(key=lambda x: (0 if x['priority'] == 'high' else 1, x['category']))
        
        return {
            'system_overview': {
                'total_avg_latency_ms': bottleneck_analysis['total_avg_time_ms'],
                'avg_citation_rate': retrieval_analysis['overall_stats']['avg_citation_rate'],
                'avg_chunks_retrieved': retrieval_analysis['overall_stats']['avg_chunks_retrieved'],
                'avg_relevance': retrieval_analysis['overall_stats']['avg_relevance']
            },
            'opportunities': all_opportunities,
            'analysis_date': datetime.datetime.now().strftime('%Y-%m-%d'),
            'analysis_period_days': days
        }
    
    except Exception as e:
        logger.error(f"Error generating optimization recommendations: {e}")
        raise

def main():
    """Main function to run the bottleneck analyzer."""
    try:
        # Connect to database
        conn = get_db_connection()
        
        # Generate recommendations
        recommendations = generate_optimization_recommendations(conn, days=30)
        
        # Print summary
        print("\n=== RAG System Optimization Recommendations ===\n")
        print(f"Analysis Date: {recommendations['analysis_date']}")
        print(f"Analysis Period: {recommendations['analysis_period_days']} days")
        print("\nSystem Overview:")
        print(f"- Average Total Latency: {recommendations['system_overview']['total_avg_latency_ms']:.1f} ms")
        print(f"- Average Citation Rate: {recommendations['system_overview']['avg_citation_rate']:.2f}")
        print(f"- Average Chunks Retrieved: {recommendations['system_overview']['avg_chunks_retrieved']:.1f}")
        print(f"- Average Relevance Score: {recommendations['system_overview']['avg_relevance']:.2f}")
        
        print("\nOptimization Opportunities:")
        for i, opportunity in enumerate(recommendations['opportunities'], 1):
            print(f"\n{i}. [{opportunity['priority'].upper()}] {opportunity['issue']}")
            print(f"   Component: {opportunity['component']}")
            print(f"   Impact: {opportunity['impact']}")
            print(f"   Recommendation: {opportunity['recommendation']}")
            print(f"   Potential Improvement: {opportunity['potential_improvement']}")
        
        # Save recommendations to file
        output_file = f"optimization_recommendations_{recommendations['analysis_date']}.json"
        with open(output_file, 'w') as f:
            json.dump(recommendations, f, indent=2)
        
        print(f"\nRecommendations saved to {output_file}")
        
        conn.close()
    
    except Exception as e:
        logger.error(f"Error in bottleneck analyzer: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
```

#### 1.2 Create A/B Testing Framework

Create a new Python file called `ab_testing.py`:

```python
#!/usr/bin/env python3
"""
A/B testing framework for RAG system optimization.
"""

import os
import sys
import json
import logging
import datetime
import random
import hashlib
import numpy as np
from typing import Dict, Any, List, Tuple
import psycopg2
from psycopg2.extras import RealDictCursor
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('ab_testing.log')
    ]
)
logger = logging.getLogger(__name__)

# Database connection parameters
DB_HOST = os.environ.get('DB_HOST', 'localhost')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'raganalytics')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

# A/B testing parameters
MIN_SAMPLE_SIZE = 100  # Minimum number of samples for statistical significance
CONFIDENCE_LEVEL = 0.95  # 95% confidence level

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

def create_experiment(conn, name, description, variants, metrics):
    """
    Create a new A/B testing experiment.
    
    Args:
        conn: Database connection
        name: Experiment name
        description: Experiment description
        variants: List of variant names
        metrics: List of metrics to track
        
    Returns:
        Experiment ID
    """
    try:
        cursor = conn.cursor()
        
        # Create experiment
        experiment_query = """
            INSERT INTO ab_experiments (
                name, description, start_date, status, variants, metrics
            ) VALUES (
                %s, %s, %s, %s, %s, %s
            ) RETURNING id
        """
        
        cursor.execute(
            experiment_query,
            (
                name,
                description,
                datetime.datetime.now(),
                'active',
                json.dumps(variants),
                json.dumps(metrics)
            )
        )
        
        experiment_id = cursor.fetchone()[0]
        conn.commit()
        
        cursor.close()
        
        logger.info(f"Created experiment '{name}' with ID {experiment_id}")
        
        return experiment_id
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating experiment: {e}")
        raise

def assign_variant(experiment_id, user_id):
    """
    Assign a variant to a user for an experiment.
    
    Args:
        experiment_id: Experiment ID
        user_id: User ID
        
    Returns:
        Assigned variant
    """
    try:
        # Create a deterministic hash based on experiment ID and user ID
        hash_input = f"{experiment_id}:{user_id}"
        hash_value = int(hashlib.md5(hash_input.encode()).hexdigest(), 16)
        
        # Use the hash to assign a variant (A or B)
        variant = 'A' if hash_value % 2 == 0 else 'B'
        
        return variant
    
    except Exception as e:
        logger.error(f"Error assigning variant: {e}")
        raise

def log_experiment_data(conn, experiment_id, user_id, variant, metrics):
    """
    Log experiment data for a user.
    
    Args:
        conn: Database connection
        experiment_id: Experiment ID
        user_id: User ID
        variant: Assigned variant
        metrics: Dictionary of metric values
    """
    try:
        cursor = conn.cursor()
        
        # Log experiment data
        log_query = """
            INSERT INTO ab_experiment_data (
                experiment_id, user_id, variant, timestamp, metrics
            ) VALUES (
                %s, %s, %s, %s, %s
            )
        """
        
        cursor.execute(
            log_query,
            (
                experiment_id,
                user_id,
                variant,
                datetime.datetime.now(),
                json.dumps(metrics)
            )
        )
        
        conn.commit()
        cursor.close()
        
        logger.debug(f"Logged experiment data for experiment {experiment_id}, user {user_id}, variant {variant}")
    
    except Exception as e:
        conn.rollback()
        logger.error(f"Error logging experiment data: {e}")
        raise

def analyze_experiment(conn, experiment_id):
    """
    Analyze experiment results.
    
    Args:
        conn: Database connection
        experiment_id: Experiment ID
        
    Returns:
        Dictionary with experiment analysis results
    """
    try:
        cursor = conn.cursor(cursor_factory=RealDictCursor)
        
        # Get experiment details
        experiment_query = """
            SELECT
                name, description, start_date, end_date, status, variants, metrics
            FROM
                ab_experiments
            WHERE
                id = %s
        """
        
        cursor.execute(experiment_query, (experiment_id,))
        experiment = dict(cursor.fetchone())
        
        # Parse JSON fields
        experiment['variants'] = json.loads(experiment['variants'])
        experiment['metrics'] = json.loads(experiment['metrics'])
        
        # Get experiment data
        data_query = """
            SELECT
                variant, metrics
            FROM
                ab_experiment_data
            WHERE
                experiment_id = %s
        """
        
        cursor.execute(data_query, (experiment_id,))
        data = [dict(row) for row in cursor.fetchall()]
        
        # Process data by variant
        variant_data = {}
        for variant in experiment['variants']:
            variant_data[variant] = {
                'count': 0,
                'metrics': {metric: [] for metric in experiment['metrics']}
            }
        
        for row in data:
            variant = row['variant']
            metrics_json = json.loads(row['metrics'])
            
            variant_data[variant]['count'] += 1
            
            for metric in experiment['metrics']:
                if metric in metrics_json:
                    variant_data[variant]['metrics'][metric].append(metrics_json[metric])
        
        # Calculate statistics for each metric
        results = {
            'experiment': experiment,
            'sample_sizes': {variant: data['count'] for variant, data in variant_data.items()},
            'metrics': {}
        }
        
        for metric in experiment['metrics']:
            metric_results = {
                'values': {},
                'comparison': {}
            }
            
            # Calculate statistics for each variant
            for variant, data in variant_data.items():
                values = data['metrics'][metric]
                
                if len(values) > 0:
                    metric_results['values'][variant] = {
                        'mean': np.mean(values),
                        'median': np.median(values),
                        'std_dev': np.std(values),
                        'min': np.min(values),
                        'max': np.max(values),
                        'count': len(values)
                    }
                else:
                    metric_results['values'][variant] = {
                        'mean': 0,
                        'median': 0,
                        'std_dev': 0,
                        'min': 0,
                        'max': 0,
                        'count': 0
                    }
            
            # Compare variants if we have enough data
            if len(experiment['variants']) == 2:
                variant_a = experiment['variants'][0]
                variant_b = experiment['variants'][1]
                
                values_a = variant_data[variant_a]['metrics'][metric]
                values_b = variant_data[variant_b]['metrics'][metric]
                
                if len(values_a) >= MIN_SAMPLE_SIZE and len(values_b) >= MIN_SAMPLE_SIZE:
                    # Perform t-test
                    t_stat, p_value = stats.ttest_ind(values_a, values_b, equal_var=False)
                    
                    # Calculate relative difference
                    mean_a = np.mean(values_a)
                    mean_b = np.mean(values_b)
                    
                    if mean_a != 0:
                        relative_diff = (mean_b - mean_a) / mean_a
                    else:
                        relative_diff = 0 if mean_b == 0 else float('inf')
                    
                    # Determine if result is statistically significant
                    is_significant = p_value < (1 - CONFIDENCE_LEVEL)
                    
                    metric_results['comparison'] = {
                        't_statistic': t_stat,
                        'p_value': p_value,
                        'relative_difference': relative_diff,
                        'absolute_difference': mean_b - mean_a,
                        'is_significant': is_significant,
                        'winner': variant_b if is_significant and relative_diff > 0 else (variant_a if is_significant and relative_diff < 0 else None),
                        'improvement': abs(relative_diff) if is_significant else 0
                    }
                else:
                    metric_results['comparison'] = {
                        'error': 'Insufficient data for statistical analysis',
                        'required_sample_size': MIN_SAMPLE_SIZE,
                        'current_sample_sizes': {
                            variant_a: len(values_a),
                            variant_b: len(values_b)
                        }
                    }
            
            results['metrics'][metric] = metric_results
        
        # Determine overall winner
        if len(experiment['variants']) == 2:
            significant_metrics = [
                metric for metric, data in results['metrics'].items()
                if 'comparison' in data and 'is_significant' in data['comparison'] and data['comparison']['is_significant']
            ]
            
            if significant_metrics:
                variant_wins = {variant: 0 for variant in experiment['variants']}
                
                for metric in significant_metrics:
                    winner = results['metrics'][metric]['comparison']['winner']
                    if winner:
                        variant_wins[winner] += 1
                
                max_wins = max(variant_wins.values())
                winners = [variant for variant, wins in variant_wins.items() if wins == max_wins]
                
                if len(winners) == 1:
                    results['overall_winner'] = winners[0]
                    results['winning_metrics'] = [
                        metric for metric in significant_metrics
                        if results['metrics'][metric]['comparison']['winner'] == results['overall_winner']
                    ]
                else:
                    results['overall_winner'] = None
                    results['winning_metrics'] = []
            else:
                results['overall_winner'] = None
