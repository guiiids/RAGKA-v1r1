# RAG Consistency Testing Plan with LLM-Based Evaluation

## Overview

This document outlines a comprehensive approach for testing the consistency of our Retrieval-Augmented Generation (RAG) system. The plan incorporates both traditional phrase-based validation and advanced LLM-based semantic evaluation to ensure thorough assessment of response quality and consistency.

## Testing Approach

### 1. Test Case Selection

We use a set of predefined test cases from the UAT document, covering multiple domains:
- Genomics
- GC (Gas Chromatography)
- LC (Liquid Chromatography)
- iLab
- OpenLab CDS

Each domain includes:
- An initial query
- A follow-up query that builds on the context of the initial query
- Expected responses for both queries
- Required phrases that must be present in the responses

### 2. Two-Tier Evaluation

#### Tier 1: Phrase-Based Validation
- Automated checking for required phrases in responses
- Ensures critical information is included
- Fast and deterministic

#### Tier 2: LLM-Based Semantic Evaluation
- Uses an LLM to compare actual vs. expected responses
- Evaluates semantic similarity beyond exact phrase matching
- Provides scores for:
  - Overall similarity
  - Information completeness
  - Accuracy
  - Structure
  - Clarity

### 3. Visualization and Reporting

- Generate visualizations of performance metrics
- Create detailed reports with domain-specific analysis
- Provide actionable recommendations for improvement

## Implementation

### Step 1: Run Consistency Tests

Execute `test_rag_consistency.py` to:
- Run each test case through the RAG system
- Log responses and comparison data
- Generate comparison files for human review
- Create a basic summary of test results

### Step 2: Analyze Results with LLM

Execute `analyze_rag_consistency.py` to:
- Process the test results
- Use LLM to evaluate semantic similarity
- Generate visualizations
- Create a comprehensive analysis report

### Step 3: Review and Iterate

- Review the analysis report and visualizations
- Identify areas for improvement
- Make necessary adjustments to the RAG system
- Re-run tests to verify improvements

## Execution

The entire process can be executed using the `run_rag_consistency_tests.sh` script, which:
1. Sets up necessary directories
2. Runs the consistency tests
3. Analyzes the results
4. Generates reports and visualizations

## Benefits of LLM-Based Evaluation

Traditional testing approaches often rely on exact phrase matching, which can miss semantically equivalent responses that use different phrasing. By incorporating LLM-based evaluation, we can:

1. **Capture Semantic Equivalence**: Recognize when responses convey the same information using different words
2. **Evaluate Response Quality**: Assess structure, clarity, and completeness beyond simple phrase matching
3. **Provide Nuanced Feedback**: Generate detailed explanations of strengths and weaknesses
4. **Identify Subtle Inconsistencies**: Detect minor variations that might be missed by simpler methods

## Limitations and Mitigations

### Limitations

1. **LLM Evaluation Subjectivity**: LLM evaluations may have some inherent variability
2. **Computational Overhead**: LLM-based evaluation requires more resources than simple phrase matching
3. **Reference Dependency**: Evaluation quality depends on the quality of expected responses

### Mitigations

1. **Multiple Evaluation Criteria**: Use multiple metrics to reduce impact of subjectivity
2. **Batch Processing**: Run evaluations in batches to manage computational load
3. **Human Verification**: Maintain human review for critical test cases
4. **Continuous Refinement**: Regularly update expected responses based on expert feedback

## Conclusion

This hybrid approach combines the reliability of phrase-based validation with the nuanced understanding of LLM-based semantic evaluation. By implementing this testing plan, we can ensure our RAG system delivers consistent, high-quality responses across different domains and query types.
