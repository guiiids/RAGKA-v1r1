"""
Unit tests for the integration of ConversationManager and OpenAIService
"""
import unittest
from unittest.mock import patch, MagicMock
import logging
from conversation_manager import ConversationManager
from openai_service import OpenAIService

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TestConversationFlow(unittest.TestCase):
    """Test cases for the conversation flow using ConversationManager and OpenAIService"""
    
    def setUp(self):
        """Set up the test environment"""
        self.system_message = "You are a helpful AI assistant."
        self.conversation_manager = ConversationManager(self.system_message)
        
        # Mock OpenAIService
        self.openai_service = MagicMock(spec=OpenAIService)
        self.openai_service.get_chat_response.return_value = "This is a mock response."
    
    def test_conversation_flow(self):
        """Test a complete conversation flow with multiple exchanges"""
        # First user message
        user_message_1 = "Hello, how are you?"
        self.conversation_manager.add_user_message(user_message_1)
        
        # Get history and check it contains system and user message
        history_1 = self.conversation_manager.get_history()
        self.assertEqual(len(history_1), 2)
        self.assertEqual(history_1[0]["role"], "system")
        self.assertEqual(history_1[0]["content"], self.system_message)
        self.assertEqual(history_1[1]["role"], "user")
        self.assertEqual(history_1[1]["content"], user_message_1)
        
        # Get response from OpenAI service
        response_1 = self.openai_service.get_chat_response(messages=history_1)
        self.conversation_manager.add_assistant_message(response_1)
        
        # Check history after first exchange
        history_2 = self.conversation_manager.get_history()
        self.assertEqual(len(history_2), 3)
        self.assertEqual(history_2[2]["role"], "assistant")
        self.assertEqual(history_2[2]["content"], response_1)
        
        # Second user message
        user_message_2 = "What can you help me with?"
        self.conversation_manager.add_user_message(user_message_2)
        
        # Get history and check it contains all previous messages plus new user message
        history_3 = self.conversation_manager.get_history()
        self.assertEqual(len(history_3), 4)
        self.assertEqual(history_3[3]["role"], "user")
        self.assertEqual(history_3[3]["content"], user_message_2)
        
        # Get response from OpenAI service
        response_2 = self.openai_service.get_chat_response(messages=history_3)
        self.conversation_manager.add_assistant_message(response_2)
        
        # Check history after second exchange
        history_4 = self.conversation_manager.get_history()
        self.assertEqual(len(history_4), 5)
        self.assertEqual(history_4[4]["role"], "assistant")
        self.assertEqual(history_4[4]["content"], response_2)
        
        # Verify OpenAI service was called with the correct messages
        call_args_list = self.openai_service.get_chat_response.call_args_list
        self.assertEqual(len(call_args_list), 2)
        
        # Verify the OpenAI service was called twice
        self.assertEqual(self.openai_service.get_chat_response.call_count, 2)
        
        # Verify the first call included the first user message
        first_call = self.openai_service.get_chat_response.call_args_list[0]
        self.assertIn("messages", first_call[1])
        messages_in_first_call = first_call[1]["messages"]
        self.assertTrue(any(m["role"] == "user" and m["content"] == user_message_1 for m in messages_in_first_call))
        
        # Verify the second call included the second user message
        second_call = self.openai_service.get_chat_response.call_args_list[1]
        self.assertIn("messages", second_call[1])
        messages_in_second_call = second_call[1]["messages"]
        self.assertTrue(any(m["role"] == "user" and m["content"] == user_message_2 for m in messages_in_second_call))
    
    def test_clear_history_effect(self):
        """Test that clearing history affects subsequent exchanges"""
        # Add some messages to the history
        self.conversation_manager.add_user_message("Hello")
        self.openai_service.get_chat_response.return_value = "Hi there!"
        response = self.openai_service.get_chat_response(messages=self.conversation_manager.get_history())
        self.conversation_manager.add_assistant_message(response)
        
        # Verify history has 3 messages (system, user, assistant)
        self.assertEqual(len(self.conversation_manager.get_history()), 3)
        
        # Clear the history (explicitly don't preserve system message)
        self.conversation_manager.clear_history(preserve_system_message=False)
        
        # Verify history is empty
        self.assertEqual(len(self.conversation_manager.get_history()), 0)
        
        # Add a new message
        self.conversation_manager.add_user_message("Do you remember me?")
        
        # Verify history only has the new message
        history = self.conversation_manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[0]["content"], "Do you remember me?")
        
        # Get response from OpenAI service
        response = self.openai_service.get_chat_response(messages=history)
        self.conversation_manager.add_assistant_message(response)
        
        # Verify history has 2 messages (user, assistant)
        history = self.conversation_manager.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "user")
        self.assertEqual(history[1]["role"], "assistant")
    
    def test_preserve_system_message(self):
        """Test that clearing history with preserve_system_message=True keeps the system message"""
        # Add some messages to the history
        self.conversation_manager.add_user_message("Hello")
        self.openai_service.get_chat_response.return_value = "Hi there!"
        response = self.openai_service.get_chat_response(messages=self.conversation_manager.get_history())
        self.conversation_manager.add_assistant_message(response)
        
        # Verify history has 3 messages (system, user, assistant)
        self.assertEqual(len(self.conversation_manager.get_history()), 3)
        
        # Clear the history but preserve system message
        self.conversation_manager.clear_history(preserve_system_message=True)
        
        # Verify history only has the system message
        history = self.conversation_manager.get_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["role"], "system")
        self.assertEqual(history[0]["content"], self.system_message)
        
        # Add a new message
        self.conversation_manager.add_user_message("Do you remember me?")
        
        # Verify history has system message and new user message
        history = self.conversation_manager.get_history()
        self.assertEqual(len(history), 2)
        self.assertEqual(history[0]["role"], "system")
        self.assertEqual(history[1]["role"], "user")
        self.assertEqual(history[1]["content"], "Do you remember me?")

if __name__ == "__main__":
    unittest.main()
