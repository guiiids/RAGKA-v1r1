#!/bin/bash

# Script to run tests and start the improved RAG system

# Create logs directory if it doesn't exist
mkdir -p logs

# Run the tests
echo "Running tests for the improved RAG implementation..."
python test_rag_improvement.py

# Ask if user wants to start the improved RAG system
echo ""
echo "Do you want to start the improved RAG system? (y/n)"
read answer

if [ "$answer" = "y" ] || [ "$answer" = "Y" ]; then
    echo "Starting the improved RAG system on port 5004..."
    python main_alternate.py
else
    echo "Exiting without starting the improved RAG system."
fi
