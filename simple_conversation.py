"""
Simple example demonstrating the use of ConversationManager and OpenAIService together
"""
import os
import logging
import sys
from dotenv import load_dotenv
from conversation_manager import ConversationManager
from openai_service import OpenAIService

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("simple_conversation.log")
    ]
)
logger = logging.getLogger("simple_conversation")

def run_conversation():
    """Run a simple conversation with the OpenAI API using conversation history"""
    # Get API credentials from environment variables
    azure_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
    api_key = os.getenv("AZURE_OPENAI_KEY")
    api_version = os.getenv("AZURE_OPENAI_API_VERSION", "2024-02-01")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT", "gpt-35-turbo")
    
    if not azure_endpoint or not api_key:
        logger.error("Missing required environment variables: AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_KEY")
        return
    
    logger.info(f"Initializing OpenAI service with endpoint: {azure_endpoint}")
    logger.info(f"Using deployment: {deployment_name}")
    
    # Initialize the OpenAI service
    openai_service = OpenAIService(
        azure_endpoint=azure_endpoint,
        api_key=api_key,
        api_version=api_version,
        deployment_name=deployment_name
    )
    
    # Initialize the conversation manager with a custom system message
    system_message = """You are a helpful AI assistant. 
    You provide clear, concise, and accurate information.
    If you don't know something, you'll admit it rather than making up an answer."""
    
    conversation_manager = ConversationManager(system_message)
    logger.info("Conversation manager initialized with system message")
    
    # Start the conversation
    print("\n=== Starting Conversation ===\n")
    
    # First exchange
    user_message = "Hello! Can you tell me about yourself?"
    print(f"User: {user_message}")
    
    # Add the user message to the conversation history
    conversation_manager.add_user_message(user_message)
    
    # Get the complete conversation history
    messages = conversation_manager.get_history()
    
    # Get a response from the OpenAI service
    try:
        assistant_response = openai_service.get_chat_response(
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        
        # Add the assistant's response to the conversation history
        conversation_manager.add_assistant_message(assistant_response)
        
        print(f"Assistant: {assistant_response}\n")
        
        # Second exchange - the assistant should remember the context
        user_message = "What can you help me with today?"
        print(f"User: {user_message}")
        
        # Add the user message to the conversation history
        conversation_manager.add_user_message(user_message)
        
        # Get the updated conversation history
        messages = conversation_manager.get_history()
        
        # Get another response from the OpenAI service
        assistant_response = openai_service.get_chat_response(
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        
        # Add the assistant's response to the conversation history
        conversation_manager.add_assistant_message(assistant_response)
        
        print(f"Assistant: {assistant_response}\n")
        
        # Third exchange - the assistant should remember both previous exchanges
        user_message = "Can you write a short poem about AI assistants?"
        print(f"User: {user_message}")
        
        # Add the user message to the conversation history
        conversation_manager.add_user_message(user_message)
        
        # Get the updated conversation history
        messages = conversation_manager.get_history()
        
        # Get another response from the OpenAI service
        assistant_response = openai_service.get_chat_response(
            messages=messages,
            temperature=0.8,  # Slightly higher temperature for creativity
            max_tokens=200    # More tokens for the poem
        )
        
        # Add the assistant's response to the conversation history
        conversation_manager.add_assistant_message(assistant_response)
        
        print(f"Assistant: {assistant_response}\n")
        
        # Print the complete conversation history
        print("\n=== Complete Conversation History ===\n")
        for i, message in enumerate(conversation_manager.get_history()):
            role = message["role"].capitalize()
            content = message["content"]
            
            if role == "System":
                print(f"[{role} Message]")
                print(f"{content}\n")
            else:
                print(f"[Exchange {i//2 if role != 'System' else 0}]")
                print(f"{role}: {content}\n")
        
        # Clear the conversation history
        print("\n=== Clearing Conversation History ===\n")
        conversation_manager.clear_history()
        
        # Start a new conversation
        print("\n=== Starting New Conversation ===\n")
        
        # Add a new user message
        user_message = "Do you remember our previous conversation about poetry?"
        print(f"User: {user_message}")
        
        # Add the user message to the conversation history
        conversation_manager.add_user_message(user_message)
        
        # Get the conversation history (should only have the system message and this new user message)
        messages = conversation_manager.get_history()
        
        # Get a response from the OpenAI service
        assistant_response = openai_service.get_chat_response(
            messages=messages,
            temperature=0.7,
            max_tokens=150
        )
        
        # Add the assistant's response to the conversation history
        conversation_manager.add_assistant_message(assistant_response)
        
        print(f"Assistant: {assistant_response}\n")
        
    except Exception as e:
        logger.error(f"Error during conversation: {e}")
        print(f"Error: {e}")

if __name__ == "__main__":
    run_conversation()
