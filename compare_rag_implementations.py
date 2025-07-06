"""
Script to compare the original and improved RAG implementations
"""
import sys
import json
import logging
import re
from rag_assistant_with_history import FlaskRAGAssistantWithHistory as OriginalRAG
from rag_assistant_with_history_alternate import FlaskRAGAssistantWithHistory as ImprovedRAG
from rag_improvement_logging import get_compare_logger

# Set up logging
logger = get_compare_logger()

# Add console handler for comparison output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - [%(name)s] - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)

def compare_responses(query):
    """
    Compare responses from original and improved RAG implementations
    
    Args:
        query: The user query to test
        
    Returns:
        Tuple of (original_response, improved_response, comparison_metrics)
    """
    logger.info(f"Comparing responses for query: {query}")
    
    # Initialize both RAG implementations
    original_rag = OriginalRAG()
    improved_rag = ImprovedRAG()
    
    # Get responses from both implementations
    logger.info("Getting response from original RAG implementation...")
    original_answer, original_sources, _, _, original_context = original_rag.generate_rag_response(query)
    
    logger.info("Getting response from improved RAG implementation...")
    improved_answer, improved_sources, _, _, improved_context = improved_rag.generate_rag_response(query)
    
    # Calculate comparison metrics
    metrics = {
        "original_length": len(original_answer),
        "improved_length": len(improved_answer),
        "original_sources_count": len(original_sources),
        "improved_sources_count": len(improved_sources),
        "original_context_length": len(original_context),
        "improved_context_length": len(improved_context),
    }
    
    # Check if improved response has numbered steps
    has_numbered_steps = bool(re.search(r'\d+\.\s+[A-Z]', improved_answer))
    metrics["has_numbered_steps"] = has_numbered_steps
    
    # Check if improved response has section headers
    has_section_headers = bool(re.search(r'\*\*[^*]+\*\*', improved_answer))
    metrics["has_section_headers"] = has_section_headers
    
    logger.info(f"Comparison metrics: {json.dumps(metrics, indent=2)}")
    
    return original_answer, improved_answer, metrics

def print_comparison(original, improved, metrics):
    """Print a formatted comparison of the responses"""
    print("\n" + "="*80)
    print("ORIGINAL RESPONSE:")
    print("="*80)
    print(original)
    
    print("\n" + "="*80)
    print("IMPROVED RESPONSE:")
    print("="*80)
    print(improved)
    
    print("\n" + "="*80)
    print("COMPARISON METRICS:")
    print("="*80)
    for key, value in metrics.items():
        print(f"{key}: {value}")
    
    # Print analysis
    print("\n" + "="*80)
    print("ANALYSIS:")
    print("="*80)
    
    # Length comparison
    length_diff = metrics["improved_length"] - metrics["original_length"]
    if length_diff > 0:
        print(f"The improved response is {length_diff} characters longer (+{length_diff/metrics['original_length']*100:.1f}%)")
    else:
        print(f"The improved response is {abs(length_diff)} characters shorter ({length_diff/metrics['original_length']*100:.1f}%)")
    
    # Sources comparison
    sources_diff = metrics["improved_sources_count"] - metrics["original_sources_count"]
    if sources_diff > 0:
        print(f"The improved response cites {sources_diff} more sources")
    elif sources_diff < 0:
        print(f"The improved response cites {abs(sources_diff)} fewer sources")
    else:
        print("Both responses cite the same number of sources")
    
    # Structure comparison
    if metrics["has_numbered_steps"]:
        print("The improved response includes numbered steps")
    else:
        print("The improved response does NOT include numbered steps")
    
    if metrics["has_section_headers"]:
        print("The improved response includes section headers")
    else:
        print("The improved response does NOT include section headers")

def main():
    """Run comparison tests with sample queries"""
    
    # Sample procedural queries
    procedural_queries = [
        "how to add a new calendar?",
        "what are the steps to configure calendar permissions?",
        "guide to setting up a calendar"
    ]
    
    # Sample informational queries
    informational_queries = [
        "what is a calendar?",
        "tell me about calendar features",
        "when was the calendar system released?"
    ]
    
    # Test procedural queries
    print("\n=== TESTING PROCEDURAL QUERIES ===\n")
    for query in procedural_queries:
        original, improved, metrics = compare_responses(query)
        print_comparison(original, improved, metrics)
    
    # Test informational queries
    print("\n=== TESTING INFORMATIONAL QUERIES ===\n")
    for query in informational_queries:
        original, improved, metrics = compare_responses(query)
        print_comparison(original, improved, metrics)

if __name__ == "__main__":
    main()
