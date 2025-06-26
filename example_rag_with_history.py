"""
Example script demonstrating the use of FlaskRAGAssistantWithHistory
"""
import logging
import sys
import os
from rag_assistant_with_history import FlaskRAGAssistantWithHistory

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("rag_history_example.log")
    ]
)
logger = logging.getLogger("example_rag_with_history")

def run_example():
    """Run an example conversation with the RAG assistant with history"""
    # Initialize the RAG assistant with history
    logger.info("Initializing RAG assistant with history")
    rag_assistant = FlaskRAGAssistantWithHistory()
    logger.info(f"RAG assistant initialized with deployment: {rag_assistant.deployment_name}")
    
    # First query
    query1 = "What is Azure OpenAI Service?"
    logger.info(f"First query: {query1}")
    
    answer1, cited_sources1, _, evaluation1, context1 = rag_assistant.generate_rag_response(query1)
    
    logger.info(f"Answer to first query: {answer1[:100]}...")
    logger.info(f"Number of cited sources: {len(cited_sources1)}")
    
    # Second query that references the first
    query2 = "How does it compare to regular OpenAI API?"
    logger.info(f"Second query (referencing first): {query2}")
    
    answer2, cited_sources2, _, evaluation2, context2 = rag_assistant.generate_rag_response(query2)
    
    logger.info(f"Answer to second query: {answer2[:100]}...")
    logger.info(f"Number of cited sources: {len(cited_sources2)}")
    
    # Third query that builds on the conversation
    query3 = "What are the pricing options for the service you just described?"
    logger.info(f"Third query (building on conversation): {query3}")
    
    answer3, cited_sources3, _, evaluation3, context3 = rag_assistant.generate_rag_response(query3)
    
    logger.info(f"Answer to third query: {answer3[:100]}...")
    logger.info(f"Number of cited sources: {len(cited_sources3)}")
    
    # Print the full conversation
    print("\n=== Full Conversation ===\n")
    print(f"User: {query1}")
    print(f"Assistant: {answer1}")
    print()
    print(f"User: {query2}")
    print(f"Assistant: {answer2}")
    print()
    print(f"User: {query3}")
    print(f"Assistant: {answer3}")
    
    # Clear the conversation history
    logger.info("Clearing conversation history")
    rag_assistant.clear_conversation_history()
    
    # New query after clearing history
    query4 = "Tell me about Azure Cognitive Services"
    logger.info(f"New query after clearing history: {query4}")
    
    answer4, cited_sources4, _, evaluation4, context4 = rag_assistant.generate_rag_response(query4)
    
    logger.info(f"Answer to new query: {answer4[:100]}...")
    logger.info(f"Number of cited sources: {len(cited_sources4)}")
    
    print("\n=== New Conversation After Clearing History ===\n")
    print(f"User: {query4}")
    print(f"Assistant: {answer4}")

if __name__ == "__main__":
    run_example()
