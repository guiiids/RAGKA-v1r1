# Phase 3 Implementation: System Prompt Improvements

## Overview

Phase 3 of the RAG improvement plan focused on enhancing the system prompts and query type detection to better handle procedural content. This phase builds upon the improvements made in Phases 1 and 2, which implemented semantic chunking and context preparation enhancements.

## Implementation Details

### 1. Enhanced Query Type Detection

We improved the `detect_query_type` function to more accurately identify procedural queries:

- Added comprehensive pattern matching for various procedural query formats
- Implemented special case detection for phrases like "guide me through" and "show me how"
- Added context-aware detection for follow-up questions in procedural conversations
- Improved detection of short follow-up queries that continue a procedural conversation

```python
def detect_query_type(self, query: str, conversation_history: List[Dict] = None) -> str:
    """
    Detect if the query is asking for procedural information.
    
    Args:
        query: The user query
        conversation_history: Optional conversation history for context
        
    Returns:
        "procedural" or "informational"
    """
    # Enhanced procedural patterns
    procedural_patterns = [
        # How-to patterns
        r'how (to|do|can|would|should) (i|we|you|one)?\s',
        r'what (is|are) the (steps|procedure|process|way|method) (to|for|of)',
        # ... additional patterns ...
    ]
    
    # Special case for "guide me through" and similar phrases
    if re.search(r'(guide|walk|take) me through', query_lower) or re.search(r'(show|tell) me how', query_lower):
        return "procedural"
        
    # Check conversation context for follow-up questions
    if conversation_history:
        # ... context-aware detection logic ...
    
    return "informational"  # Default to informational
```

### 2. Refined Procedural System Prompt

We enhanced the procedural system prompt to provide better guidance for formatting procedural content:

- Added clear hierarchical organization guidelines using markdown headings
- Provided detailed instructions for step-by-step content formatting
- Added guidelines for ensuring completeness of procedural responses
- Included an improved example format for procedures with clear sections
- Preserved all important rules from the existing system prompts (citations, uncertainty handling, etc.)

```
### Guidelines for Procedural Content:

- Structure your response with clear hierarchical organization:
  * Use markdown headings (## for main sections, ### for subsections)
  * Group related steps under appropriate headings
  * Maintain a logical flow from prerequisites to completion

- For step-by-step instructions:
  * Preserve the original sequence and numbering from the source material
  * Present steps in a clear, logical order from start to finish
  * Number each step explicitly (1, 2, 3, etc.)
  * Include all necessary details for each step
  * Use bullet points for sub-steps or additional details within a step

- Ensure completeness:
  * Include all necessary prerequisites before listing steps
  * Specify where to start the procedure (e.g., which menu, screen, or interface)
  * Include any required materials, permissions, or preconditions
  * Conclude with verification steps or expected outcomes
  * Mention any common issues or troubleshooting tips if available
```

### 3. Prompt Selection Logic

We implemented logic to select the appropriate system prompt based on the query type:

- Procedural queries use the enhanced PROCEDURAL_SYSTEM_PROMPT
- Informational queries use the DEFAULT_SYSTEM_PROMPT
- The system maintains conversation context for follow-up questions

```python
# Select appropriate system prompt based on query type
if query_type == "procedural":
    system_prompt = self.PROCEDURAL_SYSTEM_PROMPT
    logger.info("Using procedural system prompt")
else:
    system_prompt = self.DEFAULT_SYSTEM_PROMPT
    logger.info("Using default system prompt")

# Update the system message with the appropriate prompt
self.conversation_manager.clear_history(preserve_system_message=False)
self.conversation_manager.chat_history = [{"role": "system", "content": system_prompt}]
```

## Testing

We implemented comprehensive tests to verify the Phase 3 implementation:

1. **Query Type Detection Tests**:
   - Tests for various procedural query patterns
   - Tests for informational queries
   - Tests for follow-up questions with conversation context

2. **Prompt Selection Tests**:
   - Tests to verify the correct prompt is selected based on query type
   - Tests to ensure procedural content is handled with the procedural prompt
   - Tests to ensure informational content is handled with the default prompt

## Results

The implementation successfully addresses the key objectives of Phase 3:

1. ✅ Accurately detects when a query is asking for procedural information
2. ✅ Uses specialized prompts for procedural vs. informational queries
3. ✅ Maintains context awareness for follow-up questions
4. ✅ Preserves all important rules from existing system prompts

## Next Steps

With Phase 3 complete, the next steps are:

1. Implement Phase 4: Response Validation and Post-Processing
   - Validate that procedural responses include all necessary steps
   - Enhance formatting of procedural responses
   - Implement post-processing to ensure consistent structure

2. Implement Phase 5: Metadata-Enhanced Retrieval
   - Use extracted metadata to improve search relevance
   - Implement metadata-based ranking of results
   - Add weighting for procedural content in relevant queries
