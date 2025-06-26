# In-Memory Chat History Implementation for Azure OpenAI Chatbot

## Overview

This document provides an overview of the implementation of in-memory conversation history for the Azure OpenAI chatbot. The implementation follows a modular approach, separating concerns between conversation management and API interactions, making the code more maintainable and testable.

## Components

### 1. ConversationManager

The `ConversationManager` class is responsible for managing the conversation history in memory. It provides methods to:

- Initialize with a system message
- Add user messages to the history
- Add assistant messages to the history
- Retrieve the complete conversation history
- Clear the conversation history

```python
# Example usage
from conversation_manager import ConversationManager

# Initialize with a system message
manager = ConversationManager("You are a helpful AI assistant.")

# Add messages
manager.add_user_message("Hello, how are you?")
manager.add_assistant_message("I'm doing well, thank you for asking!")

# Get the complete history
history = manager.get_history()

# Clear the history
manager.clear_history(preserve_system_message=True)
```

### 2. OpenAIService

The `OpenAIService` class handles interactions with the Azure OpenAI API. It provides methods to:

- Initialize with Azure OpenAI credentials
- Send requests to the API with the conversation history
- Process responses
- Handle errors and logging

```python
# Example usage
from openai_service import OpenAIService

# Initialize with Azure OpenAI credentials
service = OpenAIService(
    azure_endpoint="https://your-endpoint.openai.azure.com",
    api_key="your-api-key",
    api_version="2024-02-01",
    deployment_name="your-deployment-name"
)

# Get a response from the API
response = service.get_chat_response(
    messages=[
        {"role": "system", "content": "You are a helpful AI assistant."},
        {"role": "user", "content": "Hello, how are you?"}
    ],
    temperature=0.7,
    max_tokens=150
)
```

### 3. Integration with RAG Assistant

The `FlaskRAGAssistantWithHistory` class in `rag_assistant_with_history.py` integrates the `ConversationManager` and `OpenAIService` classes with the existing RAG functionality. It:

- Maintains conversation history between requests
- Uses the history when generating responses
- Provides methods to clear the history

### 4. Flask Application

The `main_with_history.py` file provides a Flask application that uses the `FlaskRAGAssistantWithHistory` class to:

- Maintain conversation history for each user session
- Generate responses using the history
- Provide an API endpoint to clear the history

## Example Scripts

### 1. simple_conversation.py

This script demonstrates a simple conversation flow using the `ConversationManager` and `OpenAIService` classes directly.

```bash
python simple_conversation.py
```

### 2. example_rag_with_history.py

This script demonstrates the use of the `FlaskRAGAssistantWithHistory` class for RAG-based conversations with history.

```bash
python example_rag_with_history.py
```

### 3. main_with_history.py

This script runs a Flask application that uses the `FlaskRAGAssistantWithHistory` class to provide a web interface for conversations with history.

```bash
python main_with_history.py
```

## Testing

The implementation includes comprehensive unit tests for the `ConversationManager` and `OpenAIService` classes.

### 1. test_conversation_manager.py

Tests for the `ConversationManager` class, covering:

- Initialization
- Adding user and assistant messages
- Retrieving the history
- Clearing the history
- Complete conversation flow

```bash
python -m unittest test_conversation_manager.py
```

### 2. test_openai_service.py

Tests for the `OpenAIService` class, covering:

- Initialization
- Getting chat responses
- Error handling
- Parameter handling

```bash
python -m unittest test_openai_service.py
```

## Logging

The implementation includes comprehensive debug logging throughout the conversation flow, including:

- When the chat history is initialized
- When user and assistant messages are added to the history
- Before sending requests to the Azure OpenAI API
- After receiving responses from the API
- When the history is cleared
- Any errors or exceptions

## Usage in Production

To use this implementation in production:

1. Ensure the required environment variables are set:
   - `AZURE_OPENAI_ENDPOINT`
   - `AZURE_OPENAI_KEY`
   - `AZURE_OPENAI_API_VERSION`
   - `AZURE_OPENAI_DEPLOYMENT`

2. Import and use the appropriate classes based on your needs:
   - For simple conversations, use `ConversationManager` and `OpenAIService` directly
   - For RAG-based conversations, use `FlaskRAGAssistantWithHistory`
   - For a web interface, use the Flask application in `main_with_history.py`

3. Monitor the logs for any issues or errors

## Conclusion

This implementation provides a modular, testable, and well-logged solution for maintaining conversation history in an Azure OpenAI chatbot. The separation of concerns between conversation management and API interactions makes the code more maintainable and easier to extend in the future.
