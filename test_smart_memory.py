"""
Test script for the Enhanced Memory Management implementation.
This script demonstrates how to use the enhanced RAG assistant with smart context summarization.
"""
import logging
import sys
import os
from rag_assistant_with_history_copy import FlaskRAGAssistantWithHistory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_smart_memory():
    """Test the enhanced memory management with summarization"""
    # Initialize the RAG assistant with enhanced memory settings
    rag_assistant = FlaskRAGAssistantWithHistory(settings={
        "max_history_turns": 2,  # Keep only 2 recent turns
        "summarization_settings": {
            "enabled": True,
            "max_summary_tokens": 500,
            "summary_temperature": 0.3
        }
    })
    
    logger.info("Initialized RAG assistant with smart memory management")
    logger.info(f"Settings: max_history_turns={rag_assistant.max_history_turns}")
    logger.info(f"Summarization settings: {rag_assistant.summarization_settings}")
    
    # Simulate a conversation with multiple turns
    queries = [
        "What are the key features of the Agilent 1290 Infinity II LC System?",
        "How does it compare to the 1260 Infinity II?",
        "What maintenance procedures are recommended?",
        "Are there any common troubleshooting issues?",
        "Can you tell me about the warranty options?",
        "What software is compatible with this system?"
    ]
    
    # Process each query in sequence
    for i, query in enumerate(queries):
        print(f"\n--- Query {i+1}: {query} ---")
        
        try:
            # Generate response
            answer, cited_sources, _, _, _ = rag_assistant.generate_rag_response(query)
            
            # Print response and citation count
            print(f"Response: {answer[:100]}...")
            print(f"Citations: {len(cited_sources)}")
            
            # After 3rd query, check if summarization was triggered
            if i == 3:
                history = rag_assistant.conversation_manager.get_history()
                print(f"\nHistory length: {len(history)}")
                
                # Check for summary message
                for msg in history:
                    if msg['role'] == 'system' and 'Previous conversation summary' in msg['content']:
                        print(f"Found summary message: {msg['content'][:100]}...")
                        break
        except Exception as e:
            print(f"Error processing query: {e}")
            # Continue with next query

if __name__ == "__main__":
    test_smart_memory()
