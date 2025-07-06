#!/bin/bash

# Script to run comparison between original and improved RAG implementations

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the comparison
echo "Running comparison between original and improved RAG implementations..."
python compare_rag_implementations.py

# Save the results to a file
echo "Saving comparison results to comparison_results.txt..."
python compare_rag_implementations.py > comparison_results.txt

echo "Comparison complete. Results saved to comparison_results.txt"
