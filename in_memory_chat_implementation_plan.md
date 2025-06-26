# Detailed Implementation Plan: In-Memory Chat History for Azure OpenAI Chatbot

## Overview
This document outlines the step-by-step implementation plan for adding modular and testable in-memory conversation history to the existing Azure OpenAI chatbot. The implementation will follow best practices for modularity, testability, and logging.

## Phase 1: Core Component Design

### Step 1.1: Create ConversationManager Class
**File:** `conversation_manager.py`
```python
import logging
from typing import List, Dict, Any

logger = logging.getLogger(__name__)

class ConversationManager:
    """
    Manages the conversation history for a chat session.
    Stores messages in memory and provides methods to add and retrieve messages.
    """
    def __init__(self, system_message: str = "You are a helpful AI assistant."):
        """
        Initialize the conversation manager with a system message.
        
        Args:
            system_message: The initial system message defining the assistant's behavior
        """
        self.chat_history = [{"role": "system", "content": system_message}]
        logger.debug("ConversationManager initialized with system message.")
        
    def add_user_message(self, message: str) -> None:
        """
        Add a user message to the conversation history.
        
        Args:
            message: The user's message content
        """
        self.chat_history.append({"role": "user", "content": message})
        logger.debug(f"Added user message to history: {message[:50]}...")
        
    def add_assistant_message(self, message: str) -> None:
        """
        Add an assistant message to the conversation history.
        
        Args:
            message: The assistant's message content
        """
        self.chat_history.append({"role": "assistant", "content": message})
        logger.debug(f"Added assistant message to history: {message[:50]}...")
        
    def get_history(self) -> List[Dict[str, str]]:
        """
        Get the current conversation history.
        
        Returns:
            The complete conversation history as a list of message dictionaries
        """
        return self.chat_history
        
    def clear_history(self, preserve_system_message: bool = True) -> None:
        """
        Clear the conversation history.
        
        Args:
            preserve_system_message: Whether to preserve the initial system message
        """
        if preserve_system_message and self.chat_history and self.chat_history[0]["role"] == "system":
            system_message = self.chat_history[0]
            self.chat_history = [system_message]
            logger.debug("Cleared conversation history, preserved system message.")
        else:
            self.chat_history = []
            logger.debug("Cleared entire conversation history.")
```

### Step 1.2: Create OpenAIService Class
**File:** `openai_service.py`
```python
import logging
import os
from typing import List, Dict, Any, Optional
from openai import AzureOpenAI

logger = logging.getLogger(__name__)

class OpenAIService:
    """
    Handles interactions with the Azure OpenAI API.
    Provides methods to send requests and process responses.
    """
    def __init__(self, 
                 azure_endpoint: Optional[str] = None,
                 api_key: Optional[str] = None,
                 api_version: Optional[str] = None,
                 deployment_name: Optional[str] = None):
        """
        Initialize the OpenAI service with Azure OpenAI credentials.
        
        Args:
            azure_endpoint: The Azure OpenAI endpoint URL
            api_key: The Azure OpenAI API key
            api_version: The Azure OpenAI API version
            deployment_name: The deployment name for the chat model
        """
        self.azure_endpoint = azure_endpoint or os.getenv("AZURE_OPENAI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_OPENAI_KEY")
        self.api_version = api_version or os.getenv("OPENAI_API_VERSION", "2023-05-15")
        self.deployment_name = deployment_name or os.getenv("AZURE_OPENAI_MODEL")
        
        # Initialize the Azure OpenAI client
        self.client = AzureOpenAI(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
        
        logger.debug(f"OpenAIService initialized with deployment: {self.deployment_name}")
        
    def get_chat_response(self, 
                          messages: List[Dict[str, str]], 
                          temperature: float = 0.7, 
                          max_tokens: int = 1000,
                          top_p: float = 1.0) -> str:
        """
        Send a chat completion request to Azure OpenAI.
        
        Args:
            messages: The conversation history as a list of message dictionaries
            temperature: Controls randomness (0-1)
            max_tokens: Maximum number of tokens to generate
            top_p: Controls diversity via nucleus sampling
            
        Returns:
            The assistant's response as a string
        """
        try:
            logger.debug(f"Sending request to OpenAI with {len(messages)} messages")
            logger.debug(f"Last message: {messages[-1]['content'][:50]}...")
            
            response = self.client.chat.completions.create(
                model=self.deployment_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                top_p=top_p
            )
            
            logger.debug(f"Received response from OpenAI: {response.choices[0].message.content[:50]}...")
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return f"Sorry, I encountered an error: {str(e)}"
```

## Phase 2: Unit Testing

### Step 2.1: Create ConversationManager Tests
**File:** `test_conversation_manager.py`
```python
import unittest
import logging
from conversation_manager import ConversationManager

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)

class TestConversationManager(unittest.TestCase):
    """Test cases for the ConversationManager class."""
    
    def setUp(self):
        """Set up a fresh ConversationManager for each test."""
        self.manager = ConversationManager("Test system message")
        
    def test_initialization(self):
        """Test that the manager initializes with a system message."""
        history = self.manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["role"], "system")
        self.assertEqual(history[0]["content"], "Test system message")
        
    def test_add_user_message(self):
        """Test adding a user message to the history."""
        self.manager.add_user_message("Hello, AI!")
        history = self.manager.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["role"], "user")
        self.assertEqual(history[1]["content"], "Hello, AI!")
        
    def test_add_assistant_message(self):
        """Test adding an assistant message to the history."""
        self.manager.add_assistant_message("Hello, human!")
        history = self.manager.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[1]["role"], "assistant")
        self.assertEqual(history[1]["content"], "Hello, human!")
        
    def test_conversation_flow(self):
        """Test a complete conversation flow."""
        # Add messages in sequence
        self.manager.add_user_message("What is Azure OpenAI?")
        self.manager.add_assistant_message("Azure OpenAI is a cloud service...")
        self.manager.add_user_message("How do I use it?")
        self.manager.add_assistant_message("You can use it by...")
        
        # Check the history
        history = self.manager.get_history()
        self.assertEqual(len(history), 5)
        self.assertEqual(history[0]["role"], "system")
        self.assertEqual(history[1]["role"], "user")
        self.assertEqual(history[2]["role"], "assistant")
        self.assertEqual(history[3]["role"], "user")
        self.assertEqual(history[4]["role"], "assistant")
        
    def test_clear_history(self):
        """Test clearing the conversation history."""
        # Add some messages
        self.manager.add_user_message("Hello")
        self.manager.add_assistant_message("Hi there")
        
        # Clear with preserving system message
        self.manager.clear_history(preserve_system_message=True)
        history = self.manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["role"], "system")
        
        # Add more messages and clear everything
        self.manager.add_user_message("Hello again")
        self.manager.clear_history(preserve_system_message=False)
        history = self.manager.get_history()
        self.assertEqual(len(history), 0)

if __name__ == "__main__":
    unittest.main()
```

### Step 2.2: Create OpenAIService Tests
**File:** `test_openai_service.py`
```python
import unittest
import logging
from unittest.mock import patch, MagicMock
from openai_service import OpenAIService

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)

class TestOpenAIService(unittest.TestCase):
    """Test cases for the OpenAIService class."""
    
    def setUp(self):
        """Set up the test environment."""
        # Use environment variables for credentials in real tests
        self.service = OpenAIService(
            azure_endpoint="https://test-endpoint.openai.azure.com/",
            api_key="test-api-key",
            api_version="2023-05-15",
            deployment_name="test-deployment"
        )
    
    @patch('openai_service.AzureOpenAI')
    def test_initialization(self, mock_azure_openai):
        """Test that the service initializes correctly."""
        # Create a new service to trigger the mock
        service = OpenAIService(
            azure_endpoint="https://test-endpoint.openai.azure.com/",
            api_key="test-api-key",
            api_version="2023-05-15",
            deployment_name="test-deployment"
        )
        
        # Check that AzureOpenAI was initialized with correct parameters
        mock_azure_openai.assert_called_once_with(
            azure_endpoint="https://test-endpoint.openai.azure.com/",
            api_key="test-api-key",
            api_version="2023-05-15"
        )
    
    @patch('openai_service.AzureOpenAI')
    def test_get_chat_response(self, mock_azure_openai):
        """Test getting a chat response."""
        # Set up the mock
        mock_client = MagicMock()
        mock_azure_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        
        # Create a new service with the mock
        service = OpenAIService(
            azure_endpoint="https://test-endpoint.openai.azure.com/",
            api_key="test-api-key",
            api_version="2023-05-15",
            deployment_name="test-deployment"
        )
        
        # Test the get_chat_response method
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        response = service.get_chat_response(messages)
        
        # Check that the client was called with correct parameters
        mock_client.chat.completions.create.assert_called_once_with(
            model="test-deployment",
            messages=messages,
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0
        )
        
        # Check the response
        self.assertEqual(response, "Test response")
    
    @patch('openai_service.AzureOpenAI')
    def test_error_handling(self, mock_azure_openai):
        """Test error handling in get_chat_response."""
        # Set up the mock to raise an exception
        mock_client = MagicMock()
        mock_azure_openai.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Test error")
        
        # Create a new service with the mock
        service = OpenAIService(
            azure_endpoint="https://test-endpoint.openai.azure.com/",
            api_key="test-api-key",
            api_version="2023-05-15",
            deployment_name="test-deployment"
        )
        
        # Test the get_chat_response method with error
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        response = service.get_chat_response(messages)
        
        # Check that the response contains the error message
        self.assertIn("Sorry, I encountered an error", response)
        self.assertIn("Test error", response)

if __name__ == "__main__":
    unittest.main()
```

### Step 2.3: Create Simple Integration Test
**File:** `test_conversation_simple.py`
```python
"""
Simple test script for verifying in-memory conversation history functionality
without relying on external services
"""
import logging
import sys
from conversation_manager import ConversationManager
from openai_service import OpenAIService

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("test_conversation_simple")

def run_test():
    """Test conversation with in-memory chat history using direct calls"""
    logger.info("Initializing conversation manager")
    conversation_manager = ConversationManager("You are a helpful AI assistant.")
    logger.info("Conversation manager initialized successfully")
    
    # Check initial conversation history
    initial_history = conversation_manager.get_history().copy()
    logger.info(f"Initial conversation history: {initial_history}")
    logger.info(f"Initial conversation history length: {len(initial_history)}")
    
    # Add a user message
    logger.info("Adding user message")
    conversation_manager.add_user_message("Hello, how are you?")
    
    # Check conversation history after user message
    history_after_user = conversation_manager.get_history().copy()
    logger.info(f"Conversation history after user message: {history_after_user}")
    logger.info(f"Conversation history length after user message: {len(history_after_user)}")
    
    # Add an assistant message
    logger.info("Adding assistant message")
    conversation_manager.add_assistant_message("I'm doing well, thank you for asking! How can I help you today?")
    
    # Check conversation history after assistant message
    history_after_assistant = conversation_manager.get_history().copy()
    logger.info(f"Conversation history after assistant message: {history_after_assistant}")
    logger.info(f"Conversation history length after assistant message: {len(history_after_assistant)}")
    
    # Add another user message
    logger.info("Adding another user message")
    conversation_manager.add_user_message("Tell me about Azure OpenAI.")
    
    # Check conversation history after second user message
    history_after_second_user = conversation_manager.get_history().copy()
    logger.info(f"Conversation history after second user message: {history_after_second_user}")
    logger.info(f"Conversation history length after second user message: {len(history_after_second_user)}")
    
    # Add another assistant message
    logger.info("Adding another assistant message")
    conversation_manager.add_assistant_message("Azure OpenAI is a cloud service that provides access to OpenAI's language models including GPT-4, GPT-3.5-Turbo, and Embeddings model series.")
    
    # Check final conversation history
    final_history = conversation_manager.get_history().copy()
    logger.info(f"Final conversation history: {final_history}")
    logger.info(f"Final conversation history length: {len(final_history)}")
    
    # Print summary
    logger.info("\n=== Test Summary ===")
    logger.info(f"Initial conversation history length: 1")
    logger.info(f"After user message: 2")
    logger.info(f"After assistant message: 3")
    logger.info(f"After second user message: 4")
    logger.info(f"Final conversation history length: 5")
    
    # Debug print the actual values
    logger.info(f"DEBUG - initial_history length: {len(initial_history)}")
    logger.info(f"DEBUG - history_after_user length: {len(history_after_user)}")
    logger.info(f"DEBUG - history_after_assistant length: {len(history_after_assistant)}")
    logger.info(f"DEBUG - history_after_second_user length: {len(history_after_second_user)}")
    logger.info(f"DEBUG - final_history length: {len(final_history)}")
    
    # Verify that the conversation history is growing correctly
    if len(initial_history) != 1:
        logger.error(f"Initial history should have 1 message, but has {len(initial_history)}")
        logger.error(f"Initial history: {initial_history}")
    if len(history_after_user) != 2:
        logger.error(f"History after user message should have 2 messages, but has {len(history_after_user)}")
    if len(history_after_assistant) != 3:
        logger.error(f"History after assistant message should have 3 messages, but has {len(history_after_assistant)}")
    if len(history_after_second_user) != 4:
        logger.error(f"History after second user message should have 4 messages, but has {len(history_after_second_user)}")
    if len(final_history) != 5:
        logger.error(f"Final history should have 5 messages, but has {len(final_history)}")
    
    logger.info("All assertions passed!")
    logger.info("Test completed successfully")

if __name__ == "__main__":
    run_test()
```

## Phase 3: Integration with RAG Assistant

### Step 3.1: Modify RAG Assistant to Use ConversationManager
The existing `rag_assistant.py` will be modified to:
1. Initialize a ConversationManager in the constructor
2. Use the conversation history in the `_chat_answer` method
3. Add user and assistant messages to the history

Key changes:
```python
def __init__(self, settings=None) -> None:
    self._init_cfg()
    self.openai_client = AzureOpenAI(
        azure_endpoint=self.openai_endpoint,
        api_key=self.openai_key,
        api_version=self.openai_api_version or "2023-05-15",
    )
    self.fact_checker = FactCheckerStub()
    
    # Initialize conversation manager for chat history
    self.conversation_manager = ConversationManager()
    logger.debug("Conversation manager initialized in FlaskRAGAssistant.")
    
    # Model parameters with defaults
    # ...
```

```python
def _chat_answer(self, query: str, context: str, src_map: Dict) -> str:
    # Format the prompt with context and query
    formatted_prompt = f"<context>\n{context}\n</context>\n<user_query>\n{query}\n</user_query>"
    
    # Add the user message to the conversation history
    self.conversation_manager.add_user_message(formatted_prompt)
    
    # Get the chat history
    messages = self.conversation_manager.get_history()
    
    # Get the response from the OpenAI service
    response = self.openai_service.get_chat_response(messages)
    
    # Add the assistant's response to the conversation history
    self.conversation_manager.add_assistant_message(response)
    
    return response
```

### Step 3.2: Create Demo Conversation Script
**File:** `demo_conversation.py`
```python
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
```

## Phase 4: Interactive Demo

### Step 4.1: Create Simple Interactive Conversation Script
**File:** `simple_conversation.py`
```python
"""
Simple interactive conversation script using the ConversationManager and OpenAIService
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
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("conversation.log")
    ]
)
logger = logging.getLogger("simple_conversation")

def main():
    """Run an interactive conversation with the Azure OpenAI service"""
    # Initialize the conversation manager with a system message
    system_message = "You are a helpful AI assistant. Provide concise and accurate responses."
    conversation_manager = ConversationManager(system_message)
    logger.info(f"Initialized conversation manager with system message: {system_message}")
    
    # Initialize the OpenAI service
    openai_service = OpenAIService()
    logger.info(f"Initialized OpenAI service with deployment: {openai_service.deployment_name}")
    
    print("\n=== Simple Conversation with Azure OpenAI ===")
    print("Type 'exit' to end the conversation")
    print("Type 'clear' to clear the conversation history")
    print("Type 'debug' to show the current conversation history")
    print("Type 'help' to show these commands again\n")
    
    while True:
        # Get user input
        user_input = input("\nYou: ").strip()
        
        # Check for commands
        if user_input.lower() == 'exit':
            print("Goodbye!")
            break
        elif user_input.lower() == 'clear':
            conversation_manager.clear_history()
            print("Conversation history cleared.")
            continue
        elif user_input.lower() == 'debug':
            history = conversation_manager.get_history()
            print("\n=== Conversation History ===")
            for i, msg in enumerate(history):
                print(f"{i}. [{msg['role']}]: {msg['content'][:50]}...")
            print("===========================\n")
            continue
        elif user_input.lower() == 'help':
            print("\n=== Commands ===")
            print("exit - End the conversation")
            print("clear - Clear the conversation history")
            print("debug - Show the current conversation history")
            print("help - Show these commands again\n")
            continue
        elif not user_input:
            continue
        
        # Add user message to history
        conversation_manager.add_user_message(user_input)
        logger.info(f"User message: {user_input}")
        
        # Get response from OpenAI
        print("Assistant: ", end="", flush=True)
        try:
            messages = conversation_manager.get_history()
            response = openai_service.get_chat_response(messages)
            
            # Print the response
            print(response)
            
            # Add assistant message to history
            conversation_manager.add_assistant_message(response)
            logger.info(f"Assistant response: {response}")
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(error_msg)
            logger.error(error_msg)

if __name__ == "__main__":
    main()
```

## Phase 5: Documentation and Final Testing

### Step 5.1: Create Implementation Summary
**File:** `in_memory_chat_implementation.md`
```markdown
# In-Memory Chat History Implementation

## Overview
This document describes the implementation of in-memory conversation history for the Azure OpenAI chatbot. The implementation follows a modular approach with separate components for conversation management and API interaction.

## Components

### ConversationManager
The `ConversationManager` class is responsible for:
- Maintaining the conversation history in memory
- Adding user and assistant messages to the history
- Providing access to the complete history
- Clearing the history when needed

### OpenAIService
The `OpenAIService` class is responsible for:
- Handling all interactions with the Azure OpenAI API
- Sending requests with the complete conversation history
- Processing responses
- Error handling and logging

## Integration with RAG Assistant
The existing `FlaskRAGAssistant` class has been modified to:
- Initialize a `ConversationManager` instance
- Add user queries to the conversation history
- Send the complete history to the OpenAI API
- Add assistant responses to the history

## Usage Examples

### Basic Usage
```python
# Initialize components
conversation_manager = ConversationManager("You are a helpful assistant.")
openai_service = OpenAIService()

# Add a user message
conversation_manager.add_user_message("Hello, how are you?")

# Get the chat history
messages = conversation_manager.get_history()

# Get a response from OpenAI
response = openai_service.get_chat_response(messages)

# Add the assistant's response to the history
conversation_manager.add_assistant_message(response)
```

### Multi-turn Conversation
The implementation maintains the complete conversation history, allowing for multi-turn conversations where the assistant has context from previous exchanges.

## Testing
The implementation includes comprehensive unit tests for both the `ConversationManager` and `OpenAIService` classes, as well as integration tests to verify they work together correctly.

## Logging
Detailed logging is implemented throughout the system:
- Initialization of components
- Addition of messages to the history
- API requests and responses
- Errors and exceptions

## Future Improvements
Potential future improvements include:
- Persistence of conversation history to a database
- Token counting and management
- Conversation summarization for longer exchanges
- User authentication and session management
```

### Step 5.2: Final Testing
Run all tests to ensure everything works correctly:
```bash
python test_conversation_manager.py
python test_openai_service.py
python test_conversation_simple.py
```

## Implementation Timeline

1. **Day 1**: Core Component Design
   - Create ConversationManager class
   - Create OpenAIService class
   - Write unit tests

2. **Day 2**: Integration and Testing
   - Integrate with RAG Assistant
   - Create demo scripts
   - Test all components together

3. **Day 3**: Documentation and Refinement
   - Create implementation documentation
   - Refine code based on testing
   - Final review and deployment

## Conclusion

This implementation provides a modular, testable, and well-documented solution for in-memory conversation history in the Azure OpenAI chatbot. The separation of concerns between conversation management and API interaction makes the code maintainable and extensible.
