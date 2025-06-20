import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime, timedelta
from db_manager import DatabaseManager

class TestDatabaseMethods(unittest.TestCase):
    """Test cases for the database methods."""

    @patch('psycopg2.connect')
    def test_get_feedback_summary(self, mock_connect):
        """Test the get_feedback_summary method."""
        # Set up mock cursor
        mock_cursor = MagicMock()
        mock_cursor.fetchone.side_effect = [{'total_feedback': 100}, {'positive_feedback': 75}]
        mock_cursor.fetchall.return_value = [{'vote_id': 1, 'user_query': 'Test', 'feedback_tags': ['Looks Good'], 'comment': '', 'timestamp': datetime.now()}]
        
        # Set up mock connection
        mock_conn = MagicMock()
        mock_conn.__enter__.return_value = mock_cursor
        mock_connect.return_value = mock_conn
        
        # Call the method without date filters
        result = DatabaseManager.get_feedback_summary()
        
        # Verify result keys
        self.assertIn('total_feedback', result)
        self.assertIn('positive_feedback', result)
        self.assertIn('negative_feedback', result)
        self.assertIn('recent_feedback', result)
        
        # Call the method with date filters
        start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
        result_with_dates = DatabaseManager.get_feedback_summary(start_date=start_date, end_date=end_date)
        
        # Verify result keys again
        self.assertIn('total_feedback', result_with_dates)
        self.assertIn('positive_feedback', result_with_dates)
        self.assertIn('negative_feedback', result_with_dates)
        self.assertIn('recent_feedback', result_with_dates)

if __name__ == '__main__':
    unittest.main()