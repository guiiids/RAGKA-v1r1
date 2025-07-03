"""
Test script for the Enhanced Memory Management implementation.
This script demonstrates how the smart context summarization works with a mock conversation.
"""
import logging
import sys
import re
from typing import List, Dict, Tuple, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Mock OpenAI service for testing
class MockOpenAIService:
    def get_chat_response(self, messages, temperature=0.3, max_tokens=800, top_p=1.0):
        """Mock implementation that generates a summary"""
        # Extract the prompt from the messages
        prompt = messages[1]["content"] if len(messages) > 1 else ""
        
        # Extract citation references from the prompt
        citation_pattern = r'\[(\d+)\]'
        citations = re.findall(citation_pattern, prompt)
        
        # Extract product mentions (simplified for testing)
        product_pattern = r'(Agilent \d+)'
        products = re.findall(product_pattern, prompt)
        
        # Generate a mock summary that preserves citations and products
        summary = "This is a summary of the conversation. "
        
        # Add product mentions
        if products:
            summary += f"The conversation discussed these products: {', '.join(products)}. "
        
        # Add citation references
        if citations:
            summary += f"Information was cited from sources: {', '.join(['['+c+']' for c in citations])}. "
        
        # Add some generic content
        summary += "The user asked about features, specifications, and maintenance procedures. The assistant provided detailed information about the products and their capabilities."
        
        return summary

# Mock RAG assistant for testing
class MockRAGAssistant:
    def __init__(self, settings=None):
        self.settings = settings or {}
        self.max_history_turns = settings.get("max_history_turns", 3) if settings else 3
        self._history_trimmed = False
        self.openai_service = MockOpenAIService()
        
        # Summarization settings
        self.summarization_settings = {
            "enabled": True,
            "max_summary_tokens": 800,
            "summary_temperature": 0.3
        }
        
        # Update from settings if provided
        if settings and "summarization_settings" in settings:
            self.summarization_settings.update(settings.get("summarization_settings", {}))
        
        # Initialize conversation history
        self.conversation_history = [
            {"role": "system", "content": "You are a helpful assistant."}
        ]
    
    def summarize_history(self, messages_to_summarize: List[Dict]) -> Dict:
        """
        Summarize a portion of conversation history while preserving key information.
        
        Args:
            messages_to_summarize: List of message dictionaries to summarize
            
        Returns:
            A single system message containing the summary
        """
        logger.info(f"Summarizing {len(messages_to_summarize)} messages")
        
        # Extract all citation references from the messages
        citation_pattern = r'\[(\d+)\]'
        all_citations = []
        for msg in messages_to_summarize:
            if msg['role'] == 'assistant':
                citations = re.findall(citation_pattern, msg['content'])
                all_citations.extend(citations)
        
        # Create a prompt that emphasizes preserving citations and product information
        prompt = """
        Summarize the following conversation while:
        1. Preserving ALL mentions of specific products, models, and technical details
        2. Maintaining ALL citation references [X] in their original form
        3. Keeping the key questions and answers
        4. Focusing on technical information rather than conversational elements
        
        Conversation to summarize:
        """
        
        for msg in messages_to_summarize:
            prompt += f"\n\n{msg['role'].upper()}: {msg['content']}"
        
        # If there are citations, add special instructions
        if all_citations:
            prompt += f"\n\nIMPORTANT: Make sure to preserve these citation references in your summary: {', '.join(['['+c+']' for c in all_citations])}"
        
        # Get summary from OpenAI with specific instructions
        summary_messages = [
            {"role": "system", "content": "You create concise summaries that preserve technical details, product information, and citation references exactly as they appear in the original text."},
            {"role": "user", "content": prompt}
        ]
        
        # Use the existing OpenAI service
        summary_response = self.openai_service.get_chat_response(
            messages=summary_messages,
            temperature=self.summarization_settings.get("summary_temperature", 0.3),
            max_tokens=self.summarization_settings.get("max_summary_tokens", 800)
        )
        
        logger.info(f"Generated summary of length {len(summary_response)}")
        return {"role": "system", "content": f"Previous conversation summary: {summary_response}"}
    
    def _trim_history(self, messages: List[Dict]) -> Tuple[List[Dict], bool]:
        """
        Trim conversation history to the last N turns while preserving key information through summarization.
        
        Args:
            messages: List of message dictionaries
            
        Returns:
            Tuple of (trimmed_messages, was_trimmed)
        """
        logger.info(
            f"TRIM_DEBUG: Called with {len(messages)} messages. Cap is {self.max_history_turns*2+1}"
        )
        
        dropped = False
        
        # If we're under the limit, no trimming needed
        if len(messages) <= self.max_history_turns*2+1:  # +1 for system message
            self._history_trimmed = False
            logger.info(f"No trimming needed. History size: {len(messages)}, limit: {self.max_history_turns*2+1}")
            return messages, dropped
        
        # Check if summarization is enabled
        if not self.summarization_settings.get("enabled", True):
            # Fall back to original trimming behavior
            dropped = True
            logger.info(f"Summarization disabled, using simple truncation")
            
            # Keep system message + last N pairs
            trimmed_messages = [messages[0]] + messages[-self.max_history_turns*2:]
            
            # Log after trimming
            logger.info(f"After simple truncation: {len(trimmed_messages)} messages")
            self._history_trimmed = True
            
            return trimmed_messages, dropped
        
        # We need to trim with summarization
        dropped = True
        logger.info(f"History size ({len(messages)}) exceeds limit ({self.max_history_turns*2+1}), trimming with summarization...")
        
        # Extract the system message (first message)
        system_message = messages[0]
        
        # Determine which messages to keep and which to summarize
        messages_to_keep = messages[-self.max_history_turns*2:]  # Keep the most recent N turns
        messages_to_summarize = messages[1:-self.max_history_turns*2]  # Summarize older messages (excluding system)
        
        # If there are messages to summarize, generate a summary
        if messages_to_summarize:
            logger.info(f"Summarizing {len(messages_to_summarize)} messages")
            summary_message = self.summarize_history(messages_to_summarize)
            
            # Construct the new message list: system message + summary + recent messages
            trimmed_messages = [system_message, summary_message] + messages_to_keep
        else:
            # If no messages to summarize, just keep system + recent
            trimmed_messages = [system_message] + messages_to_keep
        
        logger.info(f"After trimming with summarization: {len(trimmed_messages)} messages")
        self._history_trimmed = True
        
        return trimmed_messages, dropped
    
    def add_message(self, role, content):
        """Add a message to the conversation history"""
        self.conversation_history.append({"role": role, "content": content})
        
        # Trim history if needed
        self.conversation_history, _ = self._trim_history(self.conversation_history)
        
        return self.conversation_history

def test_enhanced_memory():
    """Test the enhanced memory management with a mock conversation"""
    # Initialize the mock RAG assistant with a low history limit to trigger summarization
    rag_assistant = MockRAGAssistant(settings={
        "max_history_turns": 2,  # Keep only 2 recent turns
        "summarization_settings": {
            "enabled": True,
            "max_summary_tokens": 500,
            "summary_temperature": 0.3
        }
    })
    
    logger.info("Initialized mock RAG assistant with smart memory management")
    logger.info(f"Settings: max_history_turns={rag_assistant.max_history_turns}")
    logger.info(f"Summarization settings: {rag_assistant.summarization_settings}")
    
    # Simulate a conversation with multiple turns
    conversation = [
        # Turn 1
        {"role": "user", "content": "What are the key features of the Agilent 1290 Infinity II LC System?"},
        {"role": "assistant", "content": "The Agilent 1290 Infinity II LC System offers several key features [1]: high pressure tolerance up to 1300 bar, flow rates up to 5 mL/min, and exceptional retention time precision. It also features modular design for easy maintenance [2]."},
        
        # Turn 2
        {"role": "user", "content": "How does it compare to the Agilent 1260 Infinity II?"},
        {"role": "assistant", "content": "Compared to the Agilent 1260 Infinity II, the 1290 Infinity II offers higher pressure tolerance (1300 bar vs 600 bar), higher flow rates, and better precision [3]. The 1260 is more economical but has fewer advanced features."},
        
        # Turn 3
        {"role": "user", "content": "What maintenance procedures are recommended?"},
        {"role": "assistant", "content": "For the Agilent 1290 Infinity II, recommended maintenance procedures include: regular seal replacement every 6 months, frit cleaning monthly, and detector lamp replacement as needed [4]. Following these procedures ensures optimal performance and longevity."},
        
        # Turn 4
        {"role": "user", "content": "Are there any common troubleshooting issues?"},
        {"role": "assistant", "content": "Common troubleshooting issues with the Agilent 1290 Infinity II include pressure fluctuations, baseline noise, and carryover [5]. Most can be resolved by checking for leaks, purging the system, or replacing worn components as detailed in the maintenance guide."},
        
        # Turn 5
        {"role": "user", "content": "Can you tell me about the warranty options?"},
        {"role": "assistant", "content": "Agilent offers several warranty options for the 1290 Infinity II system [6]: standard 1-year warranty, extended warranties up to 5 years, and service contracts with different coverage levels. Premium service includes on-site support and loaner equipment during repairs."}
    ]
    
    # Process each message in sequence
    print("\n=== Starting conversation simulation ===\n")
    
    for i in range(0, len(conversation), 2):
        if i+1 < len(conversation):
            user_msg = conversation[i]
            assistant_msg = conversation[i+1]
            
            print(f"\n--- Turn {(i//2)+1} ---")
            print(f"User: {user_msg['content']}")
            print(f"Assistant: {assistant_msg['content']}")
            
            # Add messages to conversation history
            rag_assistant.add_message(user_msg['role'], user_msg['content'])
            rag_assistant.add_message(assistant_msg['role'], assistant_msg['content'])
            
            # Print current history length
            print(f"History length: {len(rag_assistant.conversation_history)}")
            
            # Check if summarization was triggered
            if rag_assistant._history_trimmed:
                print("\n*** Summarization was triggered ***")
                
                # Find and print the summary message
                for msg in rag_assistant.conversation_history:
                    if msg['role'] == 'system' and 'Previous conversation summary' in msg['content']:
                        print(f"Summary: {msg['content']}")
                        break
    
    print("\n=== Conversation simulation complete ===\n")
    
    # Print final conversation history
    print("Final conversation history:")
    for i, msg in enumerate(rag_assistant.conversation_history):
        print(f"{i}. {msg['role']}: {msg['content'][:50]}...")

if __name__ == "__main__":
    test_enhanced_memory()
