#!/bin/bash

# Run All RAG Tests
# This script runs all RAG tests, including consistency tests, improvement tests, and comparison tests

# Set up directories
mkdir -p logs
mkdir -p comparison_results
mkdir -p analysis_results

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=========================================================${NC}"
echo -e "${BLUE}                 RAG Test Suite                          ${NC}"
echo -e "${BLUE}=========================================================${NC}"

# Function to run a test and check its result
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -e "\n${YELLOW}Running $test_name...${NC}"
    eval $test_command
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}$test_name completed successfully.${NC}"
        return 0
    else
        echo -e "${RED}$test_name failed. Check logs for details.${NC}"
        return 1
    fi
}

# Create a summary file
summary_file="test_suite_summary.txt"
echo "RAG TEST SUITE SUMMARY" > $summary_file
echo "====================" >> $summary_file
echo "Test run at: $(date)" >> $summary_file
echo "" >> $summary_file

# Run RAG Consistency Tests
echo -e "\n${BLUE}1. RAG Consistency Tests${NC}"
echo -e "${BLUE}------------------------${NC}"
run_test "RAG Consistency Tests" "./run_rag_consistency_tests.sh"
consistency_result=$?

if [ $consistency_result -eq 0 ]; then
    echo "1. RAG Consistency Tests: PASSED" >> $summary_file
else
    echo "1. RAG Consistency Tests: FAILED" >> $summary_file
fi

# Run RAG Improvement Tests (if available)
echo -e "\n${BLUE}2. RAG Improvement Tests${NC}"
echo -e "${BLUE}------------------------${NC}"
if [ -f "run_improved_rag.sh" ]; then
    run_test "RAG Improvement Tests" "./run_improved_rag.sh"
    improvement_result=$?
    
    if [ $improvement_result -eq 0 ]; then
        echo "2. RAG Improvement Tests: PASSED" >> $summary_file
    else
        echo "2. RAG Improvement Tests: FAILED" >> $summary_file
    fi
else
    echo -e "${YELLOW}RAG Improvement Tests script not found. Skipping.${NC}"
    echo "2. RAG Improvement Tests: SKIPPED (script not found)" >> $summary_file
    improvement_result=0
fi

# Run RAG Comparison Tests (if available)
echo -e "\n${BLUE}3. RAG Comparison Tests${NC}"
echo -e "${BLUE}------------------------${NC}"
if [ -f "run_comparison.sh" ]; then
    run_test "RAG Comparison Tests" "./run_comparison.sh"
    comparison_result=$?
    
    if [ $comparison_result -eq 0 ]; then
        echo "3. RAG Comparison Tests: PASSED" >> $summary_file
    else
        echo "3. RAG Comparison Tests: FAILED" >> $summary_file
    fi
else
    echo -e "${YELLOW}RAG Comparison Tests script not found. Skipping.${NC}"
    echo "3. RAG Comparison Tests: SKIPPED (script not found)" >> $summary_file
    comparison_result=0
fi

# Run Unit Tests (if available)
echo -e "\n${BLUE}4. Unit Tests${NC}"
echo -e "${BLUE}------------------------${NC}"
unit_tests=("test_conversation_manager.py" "test_db_manager.py" "test_openai_service.py")
unit_test_results=()

echo "4. Unit Tests:" >> $summary_file

for test in "${unit_tests[@]}"; do
    if [ -f "$test" ]; then
        run_test "Unit Test: $test" "python $test"
        result=$?
        unit_test_results+=($result)
        
        if [ $result -eq 0 ]; then
            echo "   - $test: PASSED" >> $summary_file
        else
            echo "   - $test: FAILED" >> $summary_file
        fi
    else
        echo -e "${YELLOW}Unit Test $test not found. Skipping.${NC}"
        echo "   - $test: SKIPPED (file not found)" >> $summary_file
    fi
done

# Calculate overall result
overall_result=0
if [ $consistency_result -ne 0 ] || [ $improvement_result -ne 0 ] || [ $comparison_result -ne 0 ]; then
    overall_result=1
fi

for result in "${unit_test_results[@]}"; do
    if [ $result -ne 0 ]; then
        overall_result=1
        break
    fi
done

# Print summary
echo -e "\n${BLUE}=========================================================${NC}"
echo -e "${BLUE}                 Test Suite Summary                      ${NC}"
echo -e "${BLUE}=========================================================${NC}"
cat $summary_file

echo -e "\n${BLUE}Overall Result:${NC}"
if [ $overall_result -eq 0 ]; then
    echo -e "${GREEN}All tests passed successfully!${NC}"
    echo -e "\nOverall Result: PASSED" >> $summary_file
else
    echo -e "${RED}Some tests failed. Check the logs for details.${NC}"
    echo -e "\nOverall Result: FAILED" >> $summary_file
fi

echo -e "\n${YELLOW}Test summary saved to: $summary_file${NC}"
echo -e "${YELLOW}Detailed logs available in the logs directory${NC}"

exit $overall_result
