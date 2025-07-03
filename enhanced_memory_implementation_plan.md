# Enhanced Memory Management Implementation Plan

## Problem Statement

The current RAG assistant with history has a limitation: when the conversation history grows too large, it simply truncates older messages, potentially losing important context, product information, and citation references. This can lead to inconsistent responses and loss of critical information.

## Solution Overview

Implement a smart context summarization approach that:

1. Preserves key information from older messages
2. Maintains all citation references in their original form
3. Keeps product-specific information intact
4. Reduces token usage while maintaining conversation coherence

## Implementation Details

### 1. Add Summarization Settings

Add configuration options to the `FlaskRAGAssistantWithHistory` class:

```python
# Summarization settings
self.summarization_settings = {
    "enabled": True,                # Whether to use summarization (vs. simple truncation)
    "max_summary_tokens": 800,      # Maximum length of summaries
    "summary_temperature": 0.3,     # Temperature for summary generation
}
```

### 2. Implement Summarization Method

Add a method to summarize conversation history:

```python
def summarize_history(self, messages_to_summarize: List[Dict]) -> Dict:
    """
    Summarize a portion of conversation history while preserving key information.
    
    Args:
        messages_to_summarize: List of message dictionaries to summarize
        
    Returns:
        A single system message containing the summary
    """
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
    
    return {"role": "system", "content": f"Previous conversation summary: {summary_response}"}
```

### 3. Modify the _trim_history Method

Replace the existing `_trim_history` method with an enhanced version that uses summarization:

```python
def _trim_history(self, messages: List[Dict]) -> Tuple[List[Dict], bool]:
    """
    Trim conversation history to the last N turns while preserving key information through summarization.
    
    Args:
        messages: List of message dictionaries
        
    Returns:
        Tuple of (trimmed_messages, was_trimmed)
    """
    # If we're under the limit, no trimming needed
    if len(messages) <= self.max_history_turns*2+1:  # +1 for system message
        self._history_trimmed = False
        return messages, False
    
    # Check if summarization is enabled
    if not self.summarization_settings.get("enabled", True):
        # Fall back to original trimming behavior
        dropped = True
        # Keep system message + last N pairs
        trimmed_messages = [messages[0]] + messages[-self.max_history_turns*2:]
        self._history_trimmed = True
        return trimmed_messages, dropped
    
    # We need to trim with summarization
    dropped = True
    
    # Extract the system message (first message)
    system_message = messages[0]
    
    # Determine which messages to keep and which to summarize
    messages_to_keep = messages[-self.max_history_turns*2:]  # Keep the most recent N turns
    messages_to_summarize = messages[1:-self.max_history_turns*2]  # Summarize older messages (excluding system)
    
    # If there are messages to summarize, generate a summary
    if messages_to_summarize:
        summary_message = self.summarize_history(messages_to_summarize)
        
        # Construct the new message list: system message + summary + recent messages
        trimmed_messages = [system_message, summary_message] + messages_to_keep
    else:
        # If no messages to summarize, just keep system + recent
        trimmed_messages = [system_message] + messages_to_keep
    
    self._history_trimmed = True
    
    return trimmed_messages, dropped
```

### 4. Update Settings Loading

Modify the `_load_settings` method to handle summarization settings:

```python
# Update summarization settings
if "summarization_settings" in settings:
    self.summarization_settings.update(settings.get("summarization_settings", {}))
```

## Testing Plan

1. Create a test script that simulates a conversation with multiple turns
2. Set a low `max_history_turns` value to trigger summarization
3. Verify that:
   - Summarization is triggered when the history exceeds the limit
   - The summary preserves citation references
   - The summary maintains product information
   - The conversation remains coherent after summarization

## Implementation Timeline

1. Add summarization settings and update settings loading (1 hour)
2. Implement the summarization method (2 hours)
3. Modify the _trim_history method (1 hour)
4. Create test script and verify functionality (2 hours)
5. Documentation and code review (1 hour)

Total estimated time: 7 hours

## Benefits

1. Preserves critical information from earlier in the conversation
2. Maintains citation references for proper attribution
3. Keeps product-specific information intact
4. Reduces token usage while maintaining conversation coherence
5. Improves user experience by providing more consistent responses

## Limitations and Considerations

1. Summarization adds an additional API call, which may increase latency
2. There's a trade-off between summary length and information preservation
3. The quality of the summary depends on the LLM's summarization capabilities
4. Summarization may not be needed for all use cases, so it can be disabled
