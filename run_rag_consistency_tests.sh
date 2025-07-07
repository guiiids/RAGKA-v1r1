#!/bin/bash

# RAG Consistency Tests
# This script runs the RAG consistency tests and analyzes the results

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
echo -e "${BLUE}           RAG Consistency Test Suite                    ${NC}"
echo -e "${BLUE}=========================================================${NC}"

# Run the consistency tests
echo -e "\n${YELLOW}Running RAG consistency tests...${NC}"
python test_rag_consistency.py

# Check if the tests were successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}RAG consistency tests completed successfully.${NC}"
else
    echo -e "${RED}RAG consistency tests failed. Check logs for details.${NC}"
    # Don't exit on test failure, continue with analysis
    # exit 1
fi

# Analyze the results
echo -e "\n${YELLOW}Analyzing test results...${NC}"
python analyze_rag_consistency.py --log-file logs/rag_consistency_results.log --comparison-dir comparison_results

# Check if the analysis was successful
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Analysis completed successfully.${NC}"
else
    echo -e "${RED}Analysis failed. Check logs for details.${NC}"
    exit 1
fi

# Generate a summary
echo -e "\n${YELLOW}Generating summary...${NC}"

# Count the number of test cases
total_tests=$(grep -c "DOMAIN:" logs/rag_consistency_results.log)
successful_tests=$(grep -c "All required phrases found" logs/rag_consistency_results.log)
failed_tests=$((total_tests - successful_tests))
success_rate=$((successful_tests * 100 / total_tests))

# Create a summary file
summary_file="rag_consistency_summary.txt"
echo "RAG CONSISTENCY TEST SUMMARY" > $summary_file
echo "==========================" >> $summary_file
echo "Test run at: $(date)" >> $summary_file
echo "" >> $summary_file
echo "Total Test Cases: $total_tests" >> $summary_file
echo "Successful Tests: $successful_tests" >> $summary_file
echo "Failed Tests: $failed_tests" >> $summary_file
echo "Success Rate: $success_rate%" >> $summary_file
echo "" >> $summary_file
echo "Detailed analysis available in: analysis_results/analysis_report.md" >> $summary_file
echo "Visualizations available in: analysis_results/visualizations/" >> $summary_file
echo "Comparison files available in: comparison_results/" >> $summary_file

echo -e "${GREEN}Summary generated and saved to $summary_file${NC}"

# Print summary
echo -e "\n${BLUE}=========================================================${NC}"
echo -e "${BLUE}                 Test Summary                            ${NC}"
echo -e "${BLUE}=========================================================${NC}"
echo -e "Total Test Cases: ${YELLOW}$total_tests${NC}"
echo -e "Successful Tests: ${GREEN}$successful_tests${NC}"
echo -e "Failed Tests: ${RED}$failed_tests${NC}"
echo -e "Success Rate: ${YELLOW}$success_rate%${NC}"
echo -e "\n${BLUE}Detailed analysis available in:${NC} analysis_results/analysis_report.md"
echo -e "${BLUE}Visualizations available in:${NC} analysis_results/visualizations/"
echo -e "${BLUE}Comparison files available in:${NC} comparison_results/"

# Determine exit code based on success rate
if [ $success_rate -ge 80 ]; then
    echo -e "\n${GREEN}Tests PASSED with success rate >= 80%${NC}"
    exit 0
else
    echo -e "\n${RED}Tests FAILED with success rate < 80%${NC}"
    exit 1
fi
