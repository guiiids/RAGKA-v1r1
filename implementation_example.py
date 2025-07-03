"""
Implementation example for the Enhanced Memory Management solution.
This file shows how to integrate the smart context summarization into the existing codebase.
"""
import re
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def enhance_rag_assistant_with_history(rag_assistant_class):
    """
    Enhance the RAGAssistantWithHistory class with smart context summarization.
    This function adds the necessary methods to the class to enable smart context summarization.
    
    Args:
        rag_assistant_class: The RAGAssistantWithHistory class to enhance
        
    Returns:
        The enhanced class
    """
    # Add summarization method
    def summarize_history(self, messages_to_summarize):
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
    
    # Override the _trim_history method
    def enhanced_trim_history(self, messages):
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
            logger.info("Summarization disabled, using original trimming method")
            return self._original_trim_history(messages)
        
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
    
    # Add the methods to the class
    setattr(rag_assistant_class, 'summarize_history', summarize_history)
    
    # Store the original _trim_history method
    original_trim_history = rag_assistant_class._trim_history
    setattr(rag_assistant_class, '_original_trim_history', original_trim_history)
    
    # Replace the _trim_history method
    setattr(rag_assistant_class, '_trim_history', enhanced_trim_history)
    
    # Modify the __init__ method to add summarization settings
    original_init = rag_assistant_class.__init__
    
    def enhanced_init(self, *args, **kwargs):
        # Call the original __init__
        original_init(self, *args, **kwargs)
        
        # Add summarization settings
        self.summarization_settings = {
            "enabled": True,                # Whether to use summarization (vs. simple truncation)
            "max_summary_tokens": 800,      # Maximum length of summaries
            "summary_temperature": 0.3,     # Temperature for summary generation
        }
        
        # Update from settings if provided
        if hasattr(self, 'settings') and self.settings and "summarization_settings" in self.settings:
            self.summarization_settings.update(self.settings.get("summarization_settings", {}))
            logger.info(f"Updated summarization settings: {self.summarization_settings}")
    
    # Replace the __init__ method
    setattr(rag_assistant_class, '__init__', enhanced_init)
    
    return rag_assistant_class

# Example usage
def main():
    """Example of how to use the enhanced RAG assistant"""
    from rag_assistant_with_history_copy import FlaskRAGAssistantWithHistory
    
    # Enhance the class with smart context summarization
    EnhancedFlaskRAGAssistantWithHistory = enhance_rag_assistant_with_history(FlaskRAGAssistantWithHistory)
    
    # Create an instance with custom settings
    rag_assistant = EnhancedFlaskRAGAssistantWithHistory(settings={
        "max_history_turns": 3,
        "summarization_settings": {
            "enabled": True,
            "max_summary_tokens": 1000,
            "summary_temperature": 0.3
        }
    })
    
    # Use the enhanced RAG assistant as usual
    # The smart context summarization will be applied automatically when the history grows too large
    print("Enhanced RAG assistant created with smart context summarization")
    print(f"Settings: {rag_assistant.summarization_settings}")
    
    # Example of how to use it
    user_query = "What are the key features of the Agilent 1290 Infinity II LC System?"
    print(f"\nProcessing query: {user_query}")
    
    answer, cited_sources, _, _, _ = rag_assistant.generate_rag_response(user_query)
    print(f"Response generated with {len(cited_sources)} citations")
    
    # After several queries, the history will be summarized automatically
    print("\nAfter several queries, older messages will be summarized automatically")
    print("This preserves important information while keeping the context size manageable")

if __name__ == "__main__":
    main()
