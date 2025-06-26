"""
Unit tests for the ConversationManager class
"""
import unittest
import logging
from conversation_manager import ConversationManager

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TestConversationManager(unittest.TestCase):
    """Test cases for the ConversationManager class"""
    
    def setUp(self):
        """Set up a new ConversationManager instance for each test"""
        self.default_system_message = "You are a helpful AI assistant."
        self.custom_system_message = "You are a specialized AI assistant for technical support."
        self.manager = ConversationManager(self.default_system_message)
    
    def test_initialization(self):
        """Test that the ConversationManager initializes with the correct system message"""
        # Test with default system message
        manager = ConversationManager()
        self.assertEqual(len(manager.chat_history), 1)
        self.assertEqual(manager.chat_history[0]["role"], "system")
        self.assertEqual(manager.chat_history[0]["content"], "You are a helpful AI assistant.")
        
        # Test with custom system message
        manager = ConversationManager(self.custom_system_message)
        self.assertEqual(len(manager.chat_history), 1)
        self.assertEqual(manager.chat_history[0]["role"], "system")
        self.assertEqual(manager.chat_history[0]["content"], self.custom_system_message)
    
    def test_add_user_message(self):
        """Test adding a user message to the conversation history"""
        user_message = "Hello, how are you?"
        self.manager.add_user_message(user_message)
        
        self.assertEqual(len(self.manager.chat_history), 2)
        self.assertEqual(self.manager.chat_history[1]["role"], "user")
        self.assertEqual(self.manager.chat_history[1]["content"], user_message)
    
    def test_add_assistant_message(self):
        """Test adding an assistant message to the conversation history"""
        assistant_message = "I'm doing well, thank you for asking!"
        self.manager.add_assistant_message(assistant_message)
        
        self.assertEqual(len(self.manager.chat_history), 2)
        self.assertEqual(self.manager.chat_history[1]["role"], "assistant")
        self.assertEqual(self.manager.chat_history[1]["content"], assistant_message)
    
    def test_get_history(self):
        """Test retrieving the complete conversation history"""
        user_message = "What's the weather like today?"
        assistant_message = "It's sunny and warm."
        
        self.manager.add_user_message(user_message)
        self.manager.add_assistant_message(assistant_message)
        
        history = self.manager.get_history()
        
        self.assertEqual(len(history), 3)
        self.assertEqual(history[0]["role"], "system")
        self.assertEqual(history[0]["content"], self.default_system_message)
        self.assertEqual(history[1]["role"], "user")
        self.assertEqual(history[1]["content"], user_message)
        self.assertEqual(history[2]["role"], "assistant")
        self.assertEqual(history[2]["content"], assistant_message)
    
    def test_clear_history_preserve_system(self):
        """Test clearing the conversation history while preserving the system message"""
        user_message = "Can you help me with a coding problem?"
        assistant_message = "Of course, what's the issue?"
        
        self.manager.add_user_message(user_message)
        self.manager.add_assistant_message(assistant_message)
        
        self.assertEqual(len(self.manager.chat_history), 3)
        
        self.manager.clear_history(preserve_system_message=True)
        
        self.assertEqual(len(self.manager.chat_history), 1)
        self.assertEqual(self.manager.chat_history[0]["role"], "system")
        self.assertEqual(self.manager.chat_history[0]["content"], self.default_system_message)
    
    def test_clear_history_complete(self):
        """Test clearing the entire conversation history including the system message"""
        user_message = "Can you help me with a coding problem?"
        assistant_message = "Of course, what's the issue?"
        
        self.manager.add_user_message(user_message)
        self.manager.add_assistant_message(assistant_message)
        
        self.assertEqual(len(self.manager.chat_history), 3)
        
        self.manager.clear_history(preserve_system_message=False)
        
        self.assertEqual(len(self.manager.chat_history), 0)
    
    def test_conversation_flow(self):
        """Test a complete conversation flow with multiple exchanges"""
        # First exchange
        self.manager.add_user_message("Hello!")
        self.manager.add_assistant_message("Hi there! How can I help you today?")
        
        # Second exchange
        self.manager.add_user_message("I need help with Python.")
        self.manager.add_assistant_message("I'd be happy to help with Python. What specific question do you have?")
        
        # Third exchange
        self.manager.add_user_message("How do I use list comprehensions?")
        self.manager.add_assistant_message("List comprehensions are a concise way to create lists in Python...")
        
        history = self.manager.get_history()
        
        self.assertEqual(len(history), 7)  # 1 system + 3 user + 3 assistant
        self.assertEqual(history[0]["role"], "system")
        self.assertEqual(history[1]["role"], "user")
        self.assertEqual(history[1]["content"], "Hello!")
        self.assertEqual(history[2]["role"], "assistant")
        self.assertEqual(history[3]["role"], "user")
        self.assertEqual(history[3]["content"], "I need help with Python.")
        self.assertEqual(history[4]["role"], "assistant")
        self.assertEqual(history[5]["role"], "user")
        self.assertEqual(history[5]["content"], "How do I use list comprehensions?")
        self.assertEqual(history[6]["role"], "assistant")

if __name__ == "__main__":
    unittest.main()
