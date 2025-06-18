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

def test_feedback_api():
    """Test submitting feedback through the API endpoint."""
    
    # Sample feedback data
    test_feedback = {
        "message_id": "test_api_msg_123",
        "feedback_type": "negative",
        "feedback_tags": ["Incomplete"],
        "comment": "This is a test API comment",
        "timestamp": "2025-06-17T17:00:00.000Z",
        "question": "This is a test API user query",
        "response": "This is a test API bot response"
    }
    
    logger.info("Submitting test feedback through API...")
    
    try:
        # Submit feedback through the API
        response = requests.post(
            "http://localhost:5003/api/feedback",
            json=test_feedback,
            headers={"Content-Type": "application/json"}
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info(f"API response: {result}")
            
            if result.get("success"):
                vote_id = result.get("vote_id")
                logger.info(f"Feedback saved with ID: {vote_id}")
                
                # Verify the data was saved correctly
                conn = DatabaseManager.get_connection()
                with conn.cursor() as cursor:
                    cursor.execute("SELECT * FROM votes WHERE vote_id = %s", (vote_id,))
                    db_result = cursor.fetchone()
                    
                    if db_result:
                        logger.info("Database record retrieved successfully")
                        logger.info(f"Vote ID: {db_result[0]}")
                        logger.info(f"User Query: {db_result[1]}")
                        logger.info(f"Bot Response: {db_result[2]}")
                        logger.info(f"Feedback Tags: {db_result[4]}")
                        logger.info(f"Comment: {db_result[5]}")
                        
                        # Check if user query and bot response were saved correctly
                        if db_result[1] == test_feedback["question"] and db_result[2] == test_feedback["response"]:
                            logger.info("✅ API TEST PASSED: User query and bot response were saved correctly")
                        else:
                            logger.error("❌ API TEST FAILED: User query and bot response were not saved correctly")
                            if db_result[1] != test_feedback["question"]:
                                logger.error(f"Expected user query: {test_feedback['question']}")
                                logger.error(f"Actual user query: {db_result[1]}")
                            if db_result[2] != test_feedback["response"]:
                                logger.error(f"Expected bot response: {test_feedback['response']}")
                                logger.error(f"Actual bot response: {db_result[2]}")
                    else:
                        logger.error("❌ API TEST FAILED: No record found with the given vote_id")
                
                conn.close()
            else:
                logger.error(f"❌ API TEST FAILED: API returned error: {result.get('error')}")
        else:
            logger.error(f"❌ API TEST FAILED: API returned status code {response.status_code}")
            logger.error(f"Response: {response.text}")
        
    except Exception as e:
        logger.error(f"Error during API test: {e}")
        logger.error("❌ API TEST FAILED")

if __name__ == "__main__":
    test_feedback_api()
