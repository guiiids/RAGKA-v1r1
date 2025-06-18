#!/usr/bin/env python3
import json
import requests
import logging
from dotenv import load_dotenv
import os
from db_manager import DatabaseManager

# Configure logging
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def test_feedback_submission():
    """Test submitting feedback and verify it's stored correctly in the database."""
    
    # Sample feedback data
    test_feedback = {
        "message_id": "test_msg_123",
        "feedback_type": "positive",
        "feedback_tags": ["Looks Good / Accurate & Clear"],
        "comment": "This is a test comment",
        "timestamp": "2025-06-17T16:58:00.000Z",
        "question": "This is a test user query",
        "response": "This is a test bot response"
    }
    
    logger.info("Submitting test feedback...")
    
    try:
        # Submit feedback directly to the database
        vote_id = DatabaseManager.save_feedback(test_feedback)
        logger.info(f"Feedback saved with ID: {vote_id}")
        
        # Verify the data was saved correctly
        conn = DatabaseManager.get_connection()
        with conn.cursor() as cursor:
            cursor.execute("SELECT * FROM votes WHERE vote_id = %s", (vote_id,))
            result = cursor.fetchone()
            
            if result:
                logger.info("Database record retrieved successfully")
                logger.info(f"Vote ID: {result[0]}")
                logger.info(f"User Query: {result[1]}")
                logger.info(f"Bot Response: {result[2]}")
                logger.info(f"Feedback Tags: {result[4]}")
                logger.info(f"Comment: {result[5]}")
                
                # Check if user query and bot response were saved correctly
                if result[1] == test_feedback["question"] and result[2] == test_feedback["response"]:
                    logger.info("✅ TEST PASSED: User query and bot response were saved correctly")
                else:
                    logger.error("❌ TEST FAILED: User query and bot response were not saved correctly")
                    if result[1] != test_feedback["question"]:
                        logger.error(f"Expected user query: {test_feedback['question']}")
                        logger.error(f"Actual user query: {result[1]}")
                    if result[2] != test_feedback["response"]:
                        logger.error(f"Expected bot response: {test_feedback['response']}")
                        logger.error(f"Actual bot response: {result[2]}")
            else:
                logger.error("❌ TEST FAILED: No record found with the given vote_id")
        
        conn.close()
        
    except Exception as e:
        logger.error(f"Error during test: {e}")
        logger.error("❌ TEST FAILED")

if __name__ == "__main__":
    test_feedback_submission()
