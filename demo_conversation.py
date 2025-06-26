"""
Demo script showing how to use the ConversationManager and OpenAIService
for a multi-turn conversation with Azure OpenAI
"""
import logging
import sys
import os
from conversation_manager import ConversationManager
from openai_service import OpenAIService

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("demo_conversation")

def run_demo():
    """Run a demo conversation with the Azure OpenAI service"""
    # Initialize the conversation manager with a system message
    logger.info("Initializing conversation manager")
    conversation_manager = ConversationManager(
        "You are a helpful AI assistant specialized in explaining Azure services."
    )
    
    # Initialize the OpenAI service
    logger.info("Initializing OpenAI service")
    openai_service = OpenAIService(
        deployment_name=os.getenv("AZURE_OPENAI_MODEL")
    )
    
    # Start the conversation
    logger.info("Starting conversation")
    
    # First user message
    user_message = "What is Azure OpenAI Service?"
    logger.info(f"User: {user_message}")
    conversation_manager.add_user_message(user_message)
    
    # Get response
    messages = conversation_manager.get_history()
    assistant_response = openai_service.get_chat_response(messages)
    logger.info(f"Assistant: {assistant_response}")
    conversation_manager.add_assistant_message(assistant_response)
    
    # Second user message
    user_message = "How does it compare to regular OpenAI API?"
    logger.info(f"User: {user_message}")
    conversation_manager.add_user_message(user_message)
    
    # Get response (with conversation history)
    messages = conversation_manager.get_history()
    assistant_response = openai_service.get_chat_response(messages)
    logger.info(f"Assistant: {assistant_response}")
    conversation_manager.add_assistant_message(assistant_response)
    
    # Third user message
    user_message = "What are the pricing options?"
    logger.info(f"User: {user_message}")
    conversation_manager.add_user_message(user_message)
    
    # Get response (with full conversation history)
    messages = conversation_manager.get_history()
    assistant_response = openai_service.get_chat_response(messages)
    logger.info(f"Assistant: {assistant_response}")
    conversation_manager.add_assistant_message(assistant_response)
    
    # Show the complete conversation history
    logger.info("\nComplete conversation history:")
    for i, message in enumerate(conversation_manager.get_history()):
        role = message["role"]
        content = message["content"]
        if role == "system":
            logger.info(f"[System]: {content}")
        elif role == "user":
            logger.info(f"[User {i}]: {content}")
        elif role == "assistant":
            logger.info(f"[Assistant {i}]: {content}")

if __name__ == "__main__":
    run_demo()
