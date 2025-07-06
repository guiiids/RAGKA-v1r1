# RAG System Improvement Plan

## Overview

This document outlines a phased implementation plan to improve the RAG (Retrieval-Augmented Generation) system's ability to handle procedural content, specifically addressing issues with structured responses like calendar setup instructions.

## Problem Statement

The current RAG system produces responses that lack structure and completeness when handling procedural content. Specifically:
- Responses lack logical step-by-step structure
- Important details from the source documentation are omitted
- The hierarchical nature of procedures is not preserved
- The system doesn't distinguish between procedural and informational queries

## Implementation Strategy

The implementation will follow a phased approach with clear checkpoints to ensure stability and allow for course correction if issues arise. All changes will be implemented in alternate files to prevent disruption to the production system.

### File Structure

- `main_alternate.py` - Clone of main.py with references to alternate RAG implementation
- `rag_assistant_with_history_alternate.py` - Modified RAG implementation with improvements
- `rag_improvement_logs.log` - Dedicated log file for the improvement process

## Phase 1: Improved Chunking Strategy

**Goal**: Implement semantic chunking to better preserve document structure.

### Tasks:
1. Create the `chunk_document` function to split documents by semantic boundaries
2. Implement hierarchical retrieval to maintain document structure
3. Add metadata extraction for procedural content
4. Update the search function to use the new chunking strategy

### Checkpoint 1:
- Test chunking with sample procedural documents
- Verify that document structure is preserved
- Log chunk boundaries and metadata for review

### Test:
```python
def test_semantic_chunking():
    sample_doc = """# Adding a Calendar
    
    ## Basic Information
    1. Enter a name for the calendar
    2. Provide a description
    
    ## Time Settings
    1. Set minimum reservation time
    2. Set maximum reservation time"""
    
    chunks = chunk_document(sample_doc)
    
    # Verify chunks preserve headers and numbered steps
    assert len(chunks) > 0
    assert "# Adding a Calendar" in chunks[0]
    assert any("1. Enter a name" in chunk for chunk in chunks)
    assert any("## Time Settings" in chunk for chunk in chunks)
```

## Phase 2: Context Preparation Enhancements

**Goal**: Enhance context preparation to maintain procedural flow.

### Tasks:
1. Create the `format_procedural_context` function
2. Implement detection of procedural content
3. Update the `_prepare_context` method to use the new formatting
4. Add prioritization of procedural content in context preparation

### Checkpoint 2:
- Test context preparation with procedural content
- Verify that steps and hierarchies are preserved
- Log formatted context for review

### Test:
```python
def test_procedural_context_formatting():
    procedural_text = "1. Enter a name for the calendar\n2. Provide a description"
    formatted = format_procedural_context(procedural_text)
    
    # Verify formatting preserves numbered steps
    assert "1. Enter" in formatted
    assert "2. Provide" in formatted
    
    # Test detection
    assert is_procedural_content(procedural_text) == True
    assert is_procedural_content("General information about calendars") == False
```

## Phase 3: System Prompt Improvements

**Goal**: Update system prompts to include specific instructions for procedural content.

### Tasks:
1. Create the `PROCEDURAL_SYSTEM_PROMPT` with guidelines for handling procedures
2. Implement query type detection
3. Update the system to select appropriate prompts based on query type
4. Modify the conversation manager to handle different prompt types

### Checkpoint 3:
- Test query type detection with sample queries
- Verify that appropriate prompts are selected
- Log prompt selection decisions for review

### Test:
```python
def test_query_type_detection():
    procedural_queries = [
        "how to add a new calendar?",
        "steps to create a calendar",
        "what is the process to set up a calendar?"
    ]
    
    informational_queries = [
        "what is a calendar?",
        "tell me about calendar features",
        "when was the calendar system released?"
    ]
    
    for query in procedural_queries:
        assert detect_query_type(query) == "procedural"
        
    for query in informational_queries:
        assert detect_query_type(query) == "informational"
```

## Phase 4: Response Validation and Post-Processing

**Goal**: Implement validation and enhancement of responses for procedural content.

### Tasks:
1. Create the `validate_procedural_response` function
2. Implement the `enhance_procedural_response` function
3. Update the response generation to include validation and enhancement
4. Add logging for validation results

### Checkpoint 4:
- Test response validation with sample responses
- Verify that procedural responses are properly enhanced
- Log validation results for review

### Test:
```python
def test_procedural_response_validation():
    procedural_query = "how to add a calendar?"
    good_response = "To add a calendar:\n\n1. Navigate to Settings\n2. Click on Add Calendar"
    bad_response = "Adding a calendar is simple. You go to settings and add a calendar."
    
    valid, _ = validate_procedural_response(procedural_query, good_response)
    assert valid == True
    
    valid, enhanced = validate_procedural_response(procedural_query, bad_response)
    assert valid == False
    assert "Note: This response may not include all steps" in enhanced
```

## Phase 5: Metadata-Enhanced Retrieval

**Goal**: Use metadata to improve retrieval and ranking of procedural content.

### Tasks:
1. Implement the `extract_metadata` function for chunks
2. Create the `rank_results_with_metadata` function
3. Update the search function to use metadata-enhanced ranking
4. Add logging for ranking decisions

### Checkpoint 5:
- Test metadata extraction with sample chunks
- Verify that ranking properly prioritizes procedural content
- Log ranking decisions for review

### Test:
```python
def test_metadata_extraction():
    chunk = "## Adding a Calendar\n\n1. Navigate to Settings\n2. Click on Add Calendar"
    metadata = extract_metadata(chunk)
    
    assert metadata["is_procedural"] == True
    assert metadata["steps"] == [1, 2]
    assert metadata["first_step"] == 1
    assert metadata["last_step"] == 2
```

## Phase 6: Integration and Testing

**Goal**: Integrate all improvements and test the complete system.

### Tasks:
1. Ensure all components work together
2. Perform end-to-end testing with real queries
3. Compare responses with the original system
4. Fine-tune parameters based on test results

### Checkpoint 6:
- Test the complete system with a variety of queries
- Verify that procedural responses are properly structured
- Log comparison results for review

### Test:
```python
def test_end_to_end():
    queries = [
        "how to add a new calendar?",
        "what are the steps to configure calendar permissions?",
        "tell me about calendar features"
    ]
    
    for query in queries:
        original_response = original_rag.generate_rag_response(query)[0]
        improved_response = improved_rag.generate_rag_response(query)[0]
        
        # Log both responses for comparison
        logger.info(f"Query: {query}")
        logger.info(f"Original: {original_response[:100]}...")
        logger.info(f"Improved: {improved_response[:100]}...")
        
        # For procedural queries, verify structure
        if detect_query_type(query) == "procedural":
            assert has_numbered_steps(improved_response)
```

## Logging Strategy

All changes and test results will be logged to a dedicated log file (`rag_improvement_logs.log`) with the following structure:

- `[PHASE-X]` prefix for each log entry to indicate the implementation phase
- `[CHECKPOINT-X]` prefix for checkpoint validation logs
- `[TEST]` prefix for test results
- `[COMPARE]` prefix for comparison between original and improved responses

## Rollback Strategy

If issues are encountered during implementation:

1. Identify the phase where the issue was introduced
2. Revert changes in the alternate files to the last working checkpoint
3. Log the issue and the rollback action
4. Modify the approach before proceeding

## Success Criteria

The implementation will be considered successful if:

1. Procedural responses include clear, numbered steps
2. The hierarchical structure of procedures is preserved
3. All critical information from the source documentation is included
4. The system properly distinguishes between procedural and informational queries
5. Response quality is improved as measured by user feedback

## Team Communication

To ensure all team members are aware of changes:

1. Update this document after completing each phase
2. Include a summary of changes, test results, and any issues encountered
3. Highlight any deviations from the original plan
4. Share log excerpts demonstrating improvements
