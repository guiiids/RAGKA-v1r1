"""
Test script for the improved RAG implementation
"""
import logging
import sys
from rag_improvement_logging import setup_improvement_logging, get_test_logger
from rag_assistant_with_history_alternate import (
    chunk_document,
    is_procedural_content,
    extract_metadata,
    format_procedural_context,
    prioritize_procedural_content,
    test_semantic_chunking,
    test_procedural_content_detection,
    test_metadata_extraction,
    test_query_type_detection,
    test_prompt_selection,
    run_phase1_tests,
    run_phase2_tests,
    run_phase3_tests
)

# Set up logging
logger = setup_improvement_logging()
test_logger = get_test_logger()

# Add console handler for test output
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(levelname)s - [%(name)s] - %(message)s')
console_handler.setFormatter(formatter)
test_logger.addHandler(console_handler)

# ─────────── Phase 2 Tests ───────────

def test_procedural_context_formatting():
    """Test the procedural context formatting function"""
    test_logger.info("Running test_procedural_context_formatting")
    
    procedural_text = "1. Enter a name for the calendar\n2. Provide a description"
    formatted = format_procedural_context(procedural_text)
    
    # Verify formatting preserves numbered steps
    assert "1. Enter" in formatted, "Should preserve step 1"
    assert "2. Provide" in formatted, "Should preserve step 2"
    
    # Test with section headers
    header_text = "BASIC INFORMATION: This section contains details about the calendar."
    formatted_header = format_procedural_context(header_text)
    
    # Verify headers are emphasized
    assert "**BASIC INFORMATION:**" in formatted_header, "Should emphasize headers"
    
    test_logger.info("test_procedural_context_formatting passed")
    return True


def test_prioritize_procedural_content():
    """Test the prioritization of procedural content"""
    test_logger.info("Running test_prioritize_procedural_content")
    
    # Create sample results with mixed content
    results = [
        {
            "chunk": "Calendars are used to schedule events and manage time.",
            "title": "Calendar Overview",
            "parent_id": "doc1",
            "relevance": 0.9
        },
        {
            "chunk": "1. Enter a name for the calendar\n2. Provide a description",
            "title": "Adding a Calendar",
            "parent_id": "doc2",
            "relevance": 0.8
        },
        {
            "chunk": "The system supports multiple calendar views.",
            "title": "Calendar Views",
            "parent_id": "doc3",
            "relevance": 0.7
        }
    ]
    
    # Prioritize the results
    prioritized = prioritize_procedural_content(results)
    
    # Verify procedural content is first
    assert "1. Enter" in prioritized[0]["chunk"], "Procedural content should be first"
    assert len(prioritized) == 3, "Should preserve all results"
    
    # Test with multiple procedural chunks
    results.append({
        "chunk": "1. Go to Settings\n2. Select Calendar tab",
        "title": "Accessing Calendar Settings",
        "parent_id": "doc4",
        "relevance": 0.6,
        "metadata": {
            "is_procedural": True,
            "first_step": 1,
            "last_step": 2
        }
    })
    
    # Prioritize again
    prioritized = prioritize_procedural_content(results)
    
    # Verify both procedural chunks are first
    assert len([r for r in prioritized[:2] if is_procedural_content(r["chunk"])]) == 2, "Should have 2 procedural chunks first"
    
    test_logger.info("test_prioritize_procedural_content passed")
    return True


def run_phase2_tests():
    """Run all Phase 2 tests"""
    test_logger.info("Running Phase 2 tests")
    
    tests = [
        test_procedural_context_formatting,
        test_prioritize_procedural_content
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            test_logger.error(f"Test {test.__name__} failed: {e}")
            results.append(False)
    
    success = all(results)
    if success:
        test_logger.info("All Phase 2 tests passed")
    else:
        test_logger.error("Some Phase 2 tests failed")
    
    return success


def main():
    """Run all tests for the improved RAG implementation"""
    print("Running tests for the improved RAG implementation...")
    
    # Run Phase 1 tests
    print("\n=== Phase 1: Improved Chunking Strategy ===")
    phase1_success = run_phase1_tests()
    
    # Run Phase 2 tests
    print("\n=== Phase 2: Context Preparation Enhancements ===")
    phase2_success = run_phase2_tests()
    
    # Run Phase 3 tests
    print("\n=== Phase 3: System Prompt Improvements ===")
    phase3_success = run_phase3_tests()
    
    # Run individual tests
    print("\n=== Individual Tests ===")
    
    # Test semantic chunking
    print("\nTesting semantic chunking...")
    test_semantic_chunking()
    
    # Test procedural content detection
    print("\nTesting procedural content detection...")
    test_procedural_content_detection()
    
    # Test metadata extraction
    print("\nTesting metadata extraction...")
    test_metadata_extraction()
    
    # Test procedural context formatting
    print("\nTesting procedural context formatting...")
    test_procedural_context_formatting()
    
    # Test prioritization of procedural content
    print("\nTesting prioritization of procedural content...")
    test_prioritize_procedural_content()
    
    # Test query type detection
    print("\nTesting query type detection...")
    test_query_type_detection()
    
    # Test prompt selection
    print("\nTesting prompt selection...")
    test_prompt_selection()
    
    # Test with a sample procedural document
    print("\n=== Sample Document Test ===")
    sample_doc = """# Adding a Calendar

## Basic Information
1. Enter a name for the calendar
2. Provide a description of the scheduled resource
3. Select a category for the calendar

## Time Settings
1. Set minimum reservation time
2. Set maximum reservation time
3. Define the time step increment

## User Access
1. Configure who can create reservations
2. Set up permission groups if needed
3. Configure visibility settings"""
    
    print("\nChunking sample document...")
    chunks = chunk_document(sample_doc)
    print(f"Document chunked into {len(chunks)} chunks")
    
    for i, chunk in enumerate(chunks):
        print(f"\nChunk {i+1}:")
        print(f"Length: {len(chunk)} characters")
        print(f"Is procedural: {is_procedural_content(chunk)}")
        metadata = extract_metadata(chunk)
        print(f"Metadata: {metadata}")
        print(f"Content preview: {chunk[:100]}...")
    
    # Print summary
    print("\n=== Test Summary ===")
    if phase1_success:
        print("All Phase 1 tests PASSED")
    else:
        print("Some Phase 1 tests FAILED")
        
    if phase2_success:
        print("All Phase 2 tests PASSED")
    else:
        print("Some Phase 2 tests FAILED")
        
    if phase3_success:
        print("All Phase 3 tests PASSED")
    else:
        print("Some Phase 3 tests FAILED")
    
    print("\nImplementation is ready for testing with real queries.")
    print("To run the improved RAG system, execute: python main_alternate.py")

if __name__ == "__main__":
    main()
