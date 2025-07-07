#!/usr/bin/env python3
"""
Analyze RAG consistency test results using LLM-based evaluation
"""
import argparse
import json
import logging
import os
import re
import sys
import time
from typing import Dict, List, Any, Tuple
import matplotlib.pyplot as plt
import numpy as np
from openai import AzureOpenAI
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/analysis.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Set up OpenAI client
client = AzureOpenAI(
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
)

def parse_log_file(log_file: str) -> List[Dict[str, Any]]:
    """
    Parse the log file to extract response data
    """
    logger.info(f"Parsing log file: {log_file}")
    responses = []
    
    try:
        with open(log_file, 'r') as f:
            for line in f:
                if "RESPONSE_DATA:" in line:
                    # Extract the JSON part
                    json_str = line.split("RESPONSE_DATA:", 1)[1].strip()
                    try:
                        response_data = json.loads(json_str)
                        responses.append(response_data)
                    except json.JSONDecodeError as e:
                        logger.error(f"Error parsing JSON: {e}")
                        continue
    except Exception as e:
        logger.error(f"Error reading log file: {e}")
        return []
    
    logger.info(f"Found {len(responses)} responses in log file")
    return responses

def evaluate_response_with_llm(actual: str, expected: str, query: str, domain: str) -> Dict[str, Any]:
    """
    Use LLM to evaluate the semantic similarity between actual and expected responses
    """
    logger.info(f"Evaluating response for domain: {domain}")
    
    prompt = f"""
    You are an expert evaluator for Retrieval-Augmented Generation (RAG) systems. Your task is to compare an actual response with an expected response and provide a detailed evaluation.
    
    QUERY: {query}
    
    ACTUAL RESPONSE:
    {actual}
    
    EXPECTED RESPONSE:
    {expected}
    
    Please evaluate the actual response compared to the expected response on the following criteria:
    
    1. Overall Similarity (0-10): How semantically similar is the actual response to the expected response?
    2. Information Completeness (0-10): Does the actual response contain all the key information present in the expected response?
    3. Accuracy (0-10): Is the information in the actual response accurate compared to the expected response?
    4. Structure (0-10): Does the actual response follow a similar structure to the expected response?
    5. Clarity (0-10): Is the actual response clear and well-organized?
    
    For each criterion, provide:
    - A numerical score (0-10)
    - A brief explanation for the score
    
    Then provide an overall analysis of the response quality, highlighting strengths and areas for improvement.
    
    Format your response as a JSON object with the following structure:
    {{
        "overall_similarity": {{
            "score": <score>,
            "explanation": "<explanation>"
        }},
        "information_completeness": {{
            "score": <score>,
            "explanation": "<explanation>"
        }},
        "accuracy": {{
            "score": <score>,
            "explanation": "<explanation>"
        }},
        "structure": {{
            "score": <score>,
            "explanation": "<explanation>"
        }},
        "clarity": {{
            "score": <score>,
            "explanation": "<explanation>"
        }},
        "overall_analysis": "<detailed analysis>",
        "average_score": <average of all scores>
    }}
    """
    
    try:
        response = client.chat.completions.create(
            model=os.getenv("AZURE_OPENAI_MODEL"),
            messages=[
                {"role": "system", "content": "You are an expert evaluator for RAG systems."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            max_tokens=2000
        )
        
        result = response.choices[0].message.content
        
        # Extract JSON from the response
        try:
            evaluation = json.loads(result)
            logger.info(f"Evaluation completed for domain: {domain}")
            return evaluation
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing evaluation JSON: {e}")
            # Try to extract JSON using regex
            match = re.search(r'({.*})', result, re.DOTALL)
            if match:
                try:
                    evaluation = json.loads(match.group(1))
                    logger.info(f"Evaluation completed for domain: {domain} (using regex)")
                    return evaluation
                except json.JSONDecodeError:
                    logger.error("Failed to parse JSON even with regex")
            
            # Return a default evaluation
            return {
                "overall_similarity": {"score": 0, "explanation": "Error parsing evaluation"},
                "information_completeness": {"score": 0, "explanation": "Error parsing evaluation"},
                "accuracy": {"score": 0, "explanation": "Error parsing evaluation"},
                "structure": {"score": 0, "explanation": "Error parsing evaluation"},
                "clarity": {"score": 0, "explanation": "Error parsing evaluation"},
                "overall_analysis": "Error parsing evaluation",
                "average_score": 0
            }
    
    except Exception as e:
        logger.error(f"Error calling OpenAI API: {e}")
        # Return a default evaluation
        return {
            "overall_similarity": {"score": 0, "explanation": f"API error: {str(e)}"},
            "information_completeness": {"score": 0, "explanation": f"API error: {str(e)}"},
            "accuracy": {"score": 0, "explanation": f"API error: {str(e)}"},
            "structure": {"score": 0, "explanation": f"API error: {str(e)}"},
            "clarity": {"score": 0, "explanation": f"API error: {str(e)}"},
            "overall_analysis": f"API error: {str(e)}",
            "average_score": 0
        }

def analyze_responses(responses: List[Dict[str, Any]], comparison_dir: str) -> Dict[str, Any]:
    """
    Analyze the responses and generate a comprehensive report
    """
    logger.info("Analyzing responses")
    
    # Create analysis results directory
    analysis_dir = "analysis_results"
    os.makedirs(analysis_dir, exist_ok=True)
    
    # Create visualizations directory
    viz_dir = os.path.join(analysis_dir, "visualizations")
    os.makedirs(viz_dir, exist_ok=True)
    
    # Group responses by domain and query type
    domains = {}
    for response in responses:
        domain = response.get("domain", "Unknown")
        query_type = response.get("query_type", "Unknown")
        
        if domain not in domains:
            domains[domain] = {"initial": [], "followup": []}
        
        domains[domain][query_type].append(response)
    
    # Evaluate each response
    evaluations = {}
    for domain, query_types in domains.items():
        evaluations[domain] = {"initial": [], "followup": []}
        
        for query_type, domain_responses in query_types.items():
            for response in domain_responses:
                # Get the comparison file
                comparison_file = response.get("comparison_file", "")
                if not comparison_file or not os.path.exists(comparison_file):
                    logger.warning(f"Comparison file not found: {comparison_file}")
                    continue
                
                # Read the comparison file to get the expected response
                try:
                    with open(comparison_file, 'r') as f:
                        content = f.read()
                        expected_section = content.split("EXPECTED RESPONSE:", 1)[1].split("=" * 80, 1)[0].strip()
                        expected_response = expected_section
                except Exception as e:
                    logger.error(f"Error reading comparison file: {e}")
                    continue
                
                # Evaluate the response
                actual_response = response.get("response", "")
                query = response.get("query", "")
                
                evaluation = evaluate_response_with_llm(
                    actual=actual_response,
                    expected=expected_response,
                    query=query,
                    domain=domain
                )
                
                # Add metadata to the evaluation
                evaluation["domain"] = domain
                evaluation["query_type"] = query_type
                evaluation["query"] = query
                evaluation["run_index"] = response.get("run_index", 0)
                evaluation["response_time"] = response.get("response_time", 0)
                evaluation["sources_count"] = response.get("sources_count", 0)
                evaluation["missing_phrases"] = response.get("missing_phrases", [])
                evaluation["all_phrases_found"] = response.get("all_phrases_found", False)
                
                # Add to evaluations
                evaluations[domain][query_type].append(evaluation)
    
    # Generate visualizations
    generate_visualizations(evaluations, viz_dir)
    
    # Generate report
    report = generate_report(evaluations)
    
    # Save report
    report_file = os.path.join(analysis_dir, "analysis_report.md")
    with open(report_file, 'w') as f:
        f.write(report)
    
    logger.info(f"Analysis report saved to: {report_file}")
    
    return evaluations

def generate_visualizations(evaluations: Dict[str, Dict[str, List[Dict[str, Any]]]], viz_dir: str):
    """
    Generate visualizations for the evaluations
    """
    logger.info("Generating visualizations")
    
    # 1. Overall scores by domain
    domain_scores = {}
    for domain, query_types in evaluations.items():
        domain_scores[domain] = []
        for query_type, evals in query_types.items():
            for eval in evals:
                domain_scores[domain].append(eval.get("average_score", 0))
    
    # Calculate average scores
    domain_avg_scores = {domain: np.mean(scores) if scores else 0 for domain, scores in domain_scores.items()}
    
    # Create bar chart
    plt.figure(figsize=(10, 6))
    domains = list(domain_avg_scores.keys())
    scores = list(domain_avg_scores.values())
    
    plt.bar(domains, scores, color='skyblue')
    plt.xlabel('Domain')
    plt.ylabel('Average Score (0-10)')
    plt.title('Average Response Quality by Domain')
    plt.ylim(0, 10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add score labels
    for i, score in enumerate(scores):
        plt.text(i, score + 0.1, f"{score:.1f}", ha='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(viz_dir, 'domain_scores.png'))
    plt.close()
    
    # 2. Criteria scores across all domains
    criteria = ['overall_similarity', 'information_completeness', 'accuracy', 'structure', 'clarity']
    criteria_scores = {criterion: [] for criterion in criteria}
    
    for domain, query_types in evaluations.items():
        for query_type, evals in query_types.items():
            for eval in evals:
                for criterion in criteria:
                    score = eval.get(criterion, {}).get("score", 0)
                    criteria_scores[criterion].append(score)
    
    # Calculate average scores for each criterion
    criteria_avg_scores = {criterion: np.mean(scores) if scores else 0 for criterion, scores in criteria_scores.items()}
    
    # Create bar chart
    plt.figure(figsize=(10, 6))
    criteria_labels = ['Similarity', 'Completeness', 'Accuracy', 'Structure', 'Clarity']
    criteria_values = [criteria_avg_scores[criterion] for criterion in criteria]
    
    plt.bar(criteria_labels, criteria_values, color='lightgreen')
    plt.xlabel('Evaluation Criteria')
    plt.ylabel('Average Score (0-10)')
    plt.title('Average Scores by Evaluation Criteria')
    plt.ylim(0, 10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add score labels
    for i, score in enumerate(criteria_values):
        plt.text(i, score + 0.1, f"{score:.1f}", ha='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(viz_dir, 'criteria_scores.png'))
    plt.close()
    
    # 3. Initial vs. Follow-up comparison
    initial_scores = []
    followup_scores = []
    
    for domain, query_types in evaluations.items():
        for eval in query_types.get("initial", []):
            initial_scores.append(eval.get("average_score", 0))
        
        for eval in query_types.get("followup", []):
            followup_scores.append(eval.get("average_score", 0))
    
    # Calculate average scores
    avg_initial = np.mean(initial_scores) if initial_scores else 0
    avg_followup = np.mean(followup_scores) if followup_scores else 0
    
    # Create bar chart
    plt.figure(figsize=(8, 6))
    query_types = ['Initial Queries', 'Follow-up Queries']
    avg_scores = [avg_initial, avg_followup]
    
    plt.bar(query_types, avg_scores, color=['coral', 'cornflowerblue'])
    plt.xlabel('Query Type')
    plt.ylabel('Average Score (0-10)')
    plt.title('Initial vs. Follow-up Query Performance')
    plt.ylim(0, 10)
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    
    # Add score labels
    for i, score in enumerate(avg_scores):
        plt.text(i, score + 0.1, f"{score:.1f}", ha='center')
    
    plt.tight_layout()
    plt.savefig(os.path.join(viz_dir, 'initial_vs_followup.png'))
    plt.close()
    
    logger.info(f"Visualizations saved to: {viz_dir}")

def generate_report(evaluations: Dict[str, Dict[str, List[Dict[str, Any]]]]) -> str:
    """
    Generate a comprehensive analysis report
    """
    logger.info("Generating analysis report")
    
    report = """# RAG Consistency Analysis Report

## Overview

This report presents a comprehensive analysis of the RAG system's response consistency across different domains and query types. The analysis combines both phrase-based validation and LLM-based semantic evaluation to provide a holistic assessment of response quality.

## Summary of Findings

"""
    
    # Calculate overall statistics
    total_evaluations = 0
    total_score = 0
    total_initial = 0
    total_followup = 0
    initial_score = 0
    followup_score = 0
    
    for domain, query_types in evaluations.items():
        for query_type, evals in query_types.items():
            for eval in evals:
                total_evaluations += 1
                total_score += eval.get("average_score", 0)
                
                if query_type == "initial":
                    total_initial += 1
                    initial_score += eval.get("average_score", 0)
                else:
                    total_followup += 1
                    followup_score += eval.get("average_score", 0)
    
    avg_score = total_score / total_evaluations if total_evaluations > 0 else 0
    avg_initial = initial_score / total_initial if total_initial > 0 else 0
    avg_followup = followup_score / total_followup if total_followup > 0 else 0
    
    report += f"- **Total Evaluations**: {total_evaluations}\n"
    report += f"- **Overall Average Score**: {avg_score:.2f} / 10\n"
    report += f"- **Initial Queries Average**: {avg_initial:.2f} / 10\n"
    report += f"- **Follow-up Queries Average**: {avg_followup:.2f} / 10\n\n"
    
    # Add visualizations
    report += "## Visualizations\n\n"
    report += "### Average Response Quality by Domain\n"
    report += "![Domain Scores](visualizations/domain_scores.png)\n\n"
    
    report += "### Average Scores by Evaluation Criteria\n"
    report += "![Criteria Scores](visualizations/criteria_scores.png)\n\n"
    
    report += "### Initial vs. Follow-up Query Performance\n"
    report += "![Initial vs Follow-up](visualizations/initial_vs_followup.png)\n\n"
    
    # Domain-specific analysis
    report += "## Domain-Specific Analysis\n\n"
    
    for domain, query_types in evaluations.items():
        report += f"### {domain}\n\n"
        
        # Calculate domain statistics
        domain_evals = query_types.get("initial", []) + query_types.get("followup", [])
        domain_score = sum(eval.get("average_score", 0) for eval in domain_evals) / len(domain_evals) if domain_evals else 0
        
        report += f"**Average Score**: {domain_score:.2f} / 10\n\n"
        
        # Initial query analysis
        initial_evals = query_types.get("initial", [])
        if initial_evals:
            initial_eval = initial_evals[0]  # Take the first evaluation
            
            report += "#### Initial Query\n\n"
            report += f"**Query**: {initial_eval.get('query', '')}\n\n"
            report += f"**Response Time**: {initial_eval.get('response_time', 0):.2f} seconds\n\n"
            report += f"**Sources Cited**: {initial_eval.get('sources_count', 0)}\n\n"
            
            report += "**Evaluation Scores**:\n"
            report += f"- Similarity: {initial_eval.get('overall_similarity', {}).get('score', 0)} / 10\n"
            report += f"- Completeness: {initial_eval.get('information_completeness', {}).get('score', 0)} / 10\n"
            report += f"- Accuracy: {initial_eval.get('accuracy', {}).get('score', 0)} / 10\n"
            report += f"- Structure: {initial_eval.get('structure', {}).get('score', 0)} / 10\n"
            report += f"- Clarity: {initial_eval.get('clarity', {}).get('score', 0)} / 10\n\n"
            
            report += "**Analysis**:\n"
            report += f"{initial_eval.get('overall_analysis', '')}\n\n"
            
            # Missing phrases
            missing_phrases = initial_eval.get('missing_phrases', [])
            if missing_phrases:
                report += "**Missing Required Phrases**:\n"
                for phrase in missing_phrases:
                    report += f"- {phrase}\n"
                report += "\n"
        
        # Follow-up query analysis
        followup_evals = query_types.get("followup", [])
        if followup_evals:
            followup_eval = followup_evals[0]  # Take the first evaluation
            
            report += "#### Follow-up Query\n\n"
            report += f"**Query**: {followup_eval.get('query', '')}\n\n"
            report += f"**Response Time**: {followup_eval.get('response_time', 0):.2f} seconds\n\n"
            report += f"**Sources Cited**: {followup_eval.get('sources_count', 0)}\n\n"
            
            report += "**Evaluation Scores**:\n"
            report += f"- Similarity: {followup_eval.get('overall_similarity', {}).get('score', 0)} / 10\n"
            report += f"- Completeness: {followup_eval.get('information_completeness', {}).get('score', 0)} / 10\n"
            report += f"- Accuracy: {followup_eval.get('accuracy', {}).get('score', 0)} / 10\n"
            report += f"- Structure: {followup_eval.get('structure', {}).get('score', 0)} / 10\n"
            report += f"- Clarity: {followup_eval.get('clarity', {}).get('score', 0)} / 10\n\n"
            
            report += "**Analysis**:\n"
            report += f"{followup_eval.get('overall_analysis', '')}\n\n"
            
            # Missing phrases
            missing_phrases = followup_eval.get('missing_phrases', [])
            if missing_phrases:
                report += "**Missing Required Phrases**:\n"
                for phrase in missing_phrases:
                    report += f"- {phrase}\n"
                report += "\n"
    
    # Recommendations
    report += "## Recommendations\n\n"
    
    # Generate recommendations based on the evaluations
    recommendations = []
    
    # Check for domains with low scores
    domain_scores = {}
    for domain, query_types in evaluations.items():
        domain_evals = query_types.get("initial", []) + query_types.get("followup", [])
        domain_score = sum(eval.get("average_score", 0) for eval in domain_evals) / len(domain_evals) if domain_evals else 0
        domain_scores[domain] = domain_score
    
    # Sort domains by score
    sorted_domains = sorted(domain_scores.items(), key=lambda x: x[1])
    
    # Add recommendations for the lowest scoring domains
    if sorted_domains:
        lowest_domain, lowest_score = sorted_domains[0]
        if lowest_score < 7:
            recommendations.append(f"1. **Improve {lowest_domain} Domain**: The {lowest_domain} domain has the lowest average score ({lowest_score:.2f}/10). Focus on enhancing the knowledge base and response quality for this domain.")
    
    # Check for follow-up query performance
    if avg_followup < avg_initial:
        recommendations.append(f"2. **Enhance Follow-up Query Handling**: Follow-up queries score lower ({avg_followup:.2f}/10) than initial queries ({avg_initial:.2f}/10). Improve the system's ability to maintain context and provide consistent responses in multi-turn conversations.")
    
    # Check for missing phrases
    missing_phrase_counts = {}
    for domain, query_types in evaluations.items():
        for query_type, evals in query_types.items():
            for eval in evals:
                missing_phrases = eval.get('missing_phrases', [])
                for phrase in missing_phrases:
                    if phrase not in missing_phrase_counts:
                        missing_phrase_counts[phrase] = 0
                    missing_phrase_counts[phrase] += 1
    
    # Sort phrases by frequency
    sorted_phrases = sorted(missing_phrase_counts.items(), key=lambda x: x[1], reverse=True)
    
    # Add recommendations for frequently missing phrases
    if sorted_phrases:
        most_missing, count = sorted_phrases[0]
        if count > 1:
            recommendations.append(f"3. **Address Common Missing Information**: The phrase '{most_missing}' was missing in {count} responses. Ensure the RAG system consistently includes this critical information.")
    
    # Add general recommendations
    recommendations.append("4. **Standardize Response Structure**: Ensure consistent formatting and structure across all domains to improve user experience.")
    recommendations.append("5. **Optimize Response Time**: Work on reducing response time while maintaining quality, especially for complex queries.")
    
    # Add recommendations to report
    for recommendation in recommendations:
        report += f"{recommendation}\n\n"
    
    # Conclusion
    report += "## Conclusion\n\n"
    report += f"The RAG system demonstrates an overall average score of {avg_score:.2f}/10 across all domains and query types. "
    
    if avg_score >= 8:
        report += "This indicates strong performance, with responses generally meeting expectations in terms of content and quality. "
    elif avg_score >= 6:
        report += "This indicates moderate performance, with responses generally containing relevant information but with room for improvement. "
    else:
        report += "This indicates areas for improvement, with responses often missing key information or not meeting quality expectations. "
    
    report += "By addressing the recommendations outlined above, the system's consistency and quality can be further enhanced to provide more accurate and comprehensive responses.\n"
    
    return report

def main():
    parser = argparse.ArgumentParser(description='Analyze RAG consistency test results')
    parser.add_argument('--log-file', type=str, default='logs/rag_consistency_results.log',
                        help='Path to the log file containing test results')
    parser.add_argument('--comparison-dir', type=str, default='comparison_results',
                        help='Directory containing comparison files')
    
    args = parser.parse_args()
    
    # Parse log file
    responses = parse_log_file(args.log_file)
    
    if not responses:
        logger.error("No responses found in log file")
        sys.exit(1)
    
    # Analyze responses
    evaluations = analyze_responses(responses, args.comparison_dir)
    
    logger.info("Analysis completed successfully")

if __name__ == "__main__":
    main()
