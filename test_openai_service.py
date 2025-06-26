"""
Unit tests for the OpenAIService class
"""
import unittest
from unittest.mock import patch, MagicMock
import logging
from openai_service import OpenAIService

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

class TestOpenAIService(unittest.TestCase):
    """Test cases for the OpenAIService class"""
    
    def setUp(self):
        """Set up a new OpenAIService instance for each test"""
        self.azure_endpoint = "https://test-endpoint.openai.azure.com"
        self.api_key = "test-api-key"
        self.api_version = "2024-02-01"
        self.deployment_name = "test-deployment"
        
        # Create the service with mock values
        self.service = OpenAIService(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            deployment_name=self.deployment_name
        )
    
    def test_initialization(self):
        """Test that the OpenAIService initializes with the correct values"""
        self.assertEqual(self.service.azure_endpoint, self.azure_endpoint)
        self.assertEqual(self.service.api_key, self.api_key)
        self.assertEqual(self.service.api_version, self.api_version)
        self.assertEqual(self.service.deployment_name, self.deployment_name)
        self.assertIsNotNone(self.service.client)
    
    @patch('openai_service.AzureOpenAI')
    @patch('openai_service.log_openai_call')
    def test_get_chat_response(self, mock_log_openai_call, mock_azure_openai):
        """Test getting a chat response from the OpenAI API"""
        # Set up the mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "This is a test response."
        
        # Set up the mock client
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_azure_openai.return_value = mock_client
        
        # Create a new service with the mocked client
        service = OpenAIService(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            deployment_name=self.deployment_name
        )
        
        # Test messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        # Call the method
        response = service.get_chat_response(
            messages=messages,
            temperature=0.5,
            max_tokens=500,
            top_p=0.9
        )
        
        # Verify the response
        self.assertEqual(response, "This is a test response.")
        
        # Verify the client was called with the correct parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["model"], self.deployment_name)
        self.assertEqual(call_args["messages"], messages)
        self.assertEqual(call_args["temperature"], 0.5)
        self.assertEqual(call_args["max_tokens"], 500)
        self.assertEqual(call_args["top_p"], 0.9)
        
        # Verify the logger was called
        mock_log_openai_call.assert_called_once()
    
    @patch('openai_service.AzureOpenAI')
    def test_get_chat_response_error(self, mock_azure_openai):
        """Test error handling when getting a chat response"""
        # Set up the mock client to raise an exception
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API error")
        mock_azure_openai.return_value = mock_client
        
        # Create a new service with the mocked client
        service = OpenAIService(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            deployment_name=self.deployment_name
        )
        
        # Test messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        # Call the method and expect an exception
        with self.assertRaises(Exception) as context:
            service.get_chat_response(messages=messages)
        
        # Verify the exception message
        self.assertEqual(str(context.exception), "API error")
        
        # Verify the client was called
        mock_client.chat.completions.create.assert_called_once()
    
    @patch('openai_service.AzureOpenAI')
    @patch('openai_service.log_openai_call')
    def test_get_chat_response_with_default_params(self, mock_log_openai_call, mock_azure_openai):
        """Test getting a chat response with default parameters"""
        # Set up the mock response
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Default params response."
        
        # Set up the mock client
        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response
        mock_azure_openai.return_value = mock_client
        
        # Create a new service with the mocked client
        service = OpenAIService(
            azure_endpoint=self.azure_endpoint,
            api_key=self.api_key,
            api_version=self.api_version,
            deployment_name=self.deployment_name
        )
        
        # Test messages
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello, how are you?"}
        ]
        
        # Call the method with default parameters
        response = service.get_chat_response(messages=messages)
        
        # Verify the response
        self.assertEqual(response, "Default params response.")
        
        # Verify the client was called with the default parameters
        mock_client.chat.completions.create.assert_called_once()
        call_args = mock_client.chat.completions.create.call_args[1]
        self.assertEqual(call_args["temperature"], 0.3)  # Default temperature
        self.assertEqual(call_args["max_tokens"], 1000)  # Default max_tokens
        self.assertEqual(call_args["top_p"], 1.0)  # Default top_p
        
        # Verify the logger was called
        mock_log_openai_call.assert_called_once()

if __name__ == "__main__":
    unittest.main()
