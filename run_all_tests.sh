#!/bin/bash

# Script to run all tests and comparisons for the improved RAG system

# Create logs directory if it doesn't exist
mkdir -p logs

# Make sure the scripts are executable
chmod +x run_improved_rag.sh run_comparison.sh

echo "===== STEP 1: Running tests for the improved RAG implementation ====="
python test_rag_improvement.py

echo ""
echo "===== STEP 2: Running comparison between original and improved RAG implementations ====="
python compare_rag_implementations.py > comparison_results.txt
echo "Comparison results saved to comparison_results.txt"

echo ""
echo "===== STEP 3: Would you like to start the improved RAG system? (y/n) ====="
read answer

if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    echo "Starting the improved RAG system on port 5004..."
    python main_alternate.py
else
    echo "Exiting without starting the improved RAG system."
fi
