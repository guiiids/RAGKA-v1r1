from dotenv import load_dotenv
from pathlib import Path
load_dotenv(dotenv_path=Path(__file__).resolve().parent / ".env")
import psycopg2
from psycopg2.extras import RealDictCursor, Json
import logging
from datetime import datetime, timezone
from config import (
    POSTGRES_HOST,
    POSTGRES_PORT,
    POSTGRES_DB,
    POSTGRES_USER,
    POSTGRES_PASSWORD,
    POSTGRES_SSL_MODE
)

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Handles database connections and operations for the feedback system."""
    
    @staticmethod
    def get_connection():
        """Create and return a database connection."""
        try:
            logger.debug(f"Connecting to PostgreSQL: {POSTGRES_USER}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}")
            conn = psycopg2.connect(
                host=POSTGRES_HOST,
                port=POSTGRES_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
                sslmode=POSTGRES_SSL_MODE
            )
            return conn
        except Exception as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    @staticmethod
    def save_feedback(feedback_data):
        """Save feedback to the PostgreSQL database."""
        conn = None
        try:
            # Log the incoming feedback data for debugging
            logger.debug(f"Saving feedback data: {feedback_data}")
            
            # Extract the user query and bot response
            # The frontend might be sending different keys than what we expect
            user_query = feedback_data.get("question", "")
            bot_response = feedback_data.get("response", "")
            
            # If user_query and bot_response are empty, try to get them from other fields
            # This is a fallback mechanism to handle different data structures
            if not user_query and "user_query" in feedback_data:
                user_query = feedback_data["user_query"]
            
            if not bot_response and "bot_response" in feedback_data:
                bot_response = feedback_data["bot_response"]
            
            citations = feedback_data.get("citations", [])
            
            conn = DatabaseManager.get_connection()
            with conn.cursor() as cursor:
                cursor.execute(
                    """
                    INSERT INTO votes 
                    (user_query, bot_response, evaluation_json, feedback_tags, comment, citations)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    RETURNING vote_id
                    """,
                    (
                        user_query,
                        bot_response,
                        Json(feedback_data.get("evaluation_json", {})),
                        feedback_data["feedback_tags"],
                        feedback_data.get("comment", ""),
                        Json(citations)
                    )
                )
                vote_id = cursor.fetchone()[0]
                conn.commit()
                logger.info(f"Feedback saved successfully with ID: {vote_id}")
                return vote_id
        except Exception as e:
            logger.error(f"Error saving feedback to database: {e}")
            raise
        finally:
            if conn is not None:
                conn.close()
    
    @staticmethod
    def get_feedback_summary():
        """Get summary statistics of collected feedback."""
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Count total feedback entries
                cursor.execute("SELECT COUNT(*) as total_feedback FROM votes")
                total_feedback = cursor.fetchone()["total_feedback"]
                
                # Count positive feedback (contains "Looks Good")
                cursor.execute(
                    "SELECT COUNT(*) as positive_feedback FROM votes WHERE 'Looks Good / Accurate & Clear' = ANY(feedback_tags)"
                )
                positive_feedback = cursor.fetchone()["positive_feedback"]
                
                # Get recent feedback (last 5 entries)
                cursor.execute(
                    """
                    SELECT vote_id, user_query, feedback_tags, comment, timestamp
                    FROM votes
                    ORDER BY timestamp DESC
                    LIMIT 5
                    """
                )
                recent_feedback = cursor.fetchall()
                
                summary = {
                    'total_feedback': total_feedback,
                    'positive_feedback': positive_feedback,
                    'negative_feedback': total_feedback - positive_feedback,
                    'recent_feedback': recent_feedback
                }
                
                return summary
        except Exception as e:
            logger.error(f"Error generating feedback summary: {e}")
            return {
                'total_feedback': 0,
                'positive_feedback': 0,
                'negative_feedback': 0,
                'recent_feedback': []
            }
        finally:
            if conn is not None:
                conn.close()
    
    @staticmethod
    def get_query_analytics():
        """Analyze query patterns and generate statistics."""
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                # Count total unique queries
                cursor.execute("SELECT COUNT(DISTINCT user_query) as total_queries FROM votes")
                total_queries = cursor.fetchone()["total_queries"]
                
                # Count total feedback entries
                cursor.execute("SELECT COUNT(*) as queries_with_feedback FROM votes")
                queries_with_feedback = cursor.fetchone()["queries_with_feedback"]
                
                # Count successful queries (with "Looks Good" tag)
                cursor.execute(
                    "SELECT COUNT(*) as successful_queries FROM votes WHERE 'Looks Good / Accurate & Clear' = ANY(feedback_tags)"
                )
                successful_queries = cursor.fetchone()["successful_queries"]
                
                # Get recent queries
                cursor.execute(
                    """
                    SELECT user_query, timestamp
                    FROM votes
                    ORDER BY timestamp DESC
                    LIMIT 5
                    """
                )
                recent_queries = cursor.fetchall()
                
                analytics = {
                    'total_queries': total_queries,
                    'queries_with_feedback': queries_with_feedback,
                    'successful_queries': successful_queries,
                    'recent_queries': recent_queries
                }
                
                return analytics
        except Exception as e:
            logger.error(f"Error generating query analytics: {e}")
            return {
                'total_queries': 0,
                'queries_with_feedback': 0,
                'successful_queries': 0,
                'recent_queries': []
            }
        finally:
            if conn is not None:
                conn.close()
    
    @staticmethod
    def get_tag_distribution():
        """Get distribution of feedback tags."""
        conn = None
        try:
            conn = DatabaseManager.get_connection()
            with conn.cursor(cursor_factory=RealDictCursor) as cursor:
                cursor.execute(
                    """
                    SELECT unnest(feedback_tags) as tag, COUNT(*) as count
                    FROM votes
                    GROUP BY tag
                    ORDER BY count DESC
                    """
                )
                tag_distribution = cursor.fetchall()
                return tag_distribution
        except Exception as e:
            logger.error(f"Error getting tag distribution: {e}")
            return []
        finally:
            if conn is not None:
                conn.close()
