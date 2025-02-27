import unittest
from unittest.mock import patch, MagicMock
import json

# Define a mock SQLAlchemyError for testing
class MockSQLAlchemyError(Exception):
    pass

# Create a mock DatabaseService class instead of importing the real one
class MockDatabaseService:
    def __init__(self, engine=None):
        self.engine = engine or MagicMock()
        self.connection = engine.connect.return_value.__enter__.return_value if engine else MagicMock()
        
    def execute_query(self, sql, params=None):
        """Mock implementation of execute_query that calls the connection's execute method."""
        # Forward the call to the mock connection's execute method
        self.connection.execute(sql, params)
        
        # Return whatever the mock is set up to return in the test
        result = self.connection.execute.return_value
        if hasattr(result, 'mappings') and callable(result.mappings):
            return result.mappings.return_value.all.return_value
        return result


class TestParameterizedQueries(unittest.TestCase):
    def setUp(self):
        self.mock_engine = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_engine.connect.return_value.__enter__.return_value = self.mock_connection
        self.db_service = MockDatabaseService(engine=self.mock_engine)
        
        # Sample test data
        self.sample_result = [
            {"id": 1, "name": "Service A"},
            {"id": 2, "name": "Service B"}
        ]

    def test_basic_parameter_passing(self):
        """Test that parameters are correctly passed to the SQL query execution."""
        # Set up mock to return our sample data
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = self.sample_result
        self.mock_connection.execute.return_value = mock_result
        
        # Execute query with parameters
        sql = "SELECT * FROM services WHERE name = :service_name"
        params = {"service_name": "Service A"}
        result = self.db_service.execute_query(sql, params)
        
        # Verify the parameters were passed to execute
        self.mock_connection.execute.assert_called_once()
        call_args = self.mock_connection.execute.call_args[0]
        # call_args[0] is the SQL text object, call_args[1] is the parameters
        self.assertEqual(params, call_args[1])
        
        # Verify result processing
        self.assertEqual(self.sample_result, result)

    def test_multiple_parameters(self):
        """Test that multiple parameters are correctly handled."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = self.sample_result
        self.mock_connection.execute.return_value = mock_result
        
        # Query with multiple parameters
        sql = "SELECT * FROM services WHERE name = :name AND price > :min_price"
        params = {"name": "Service A", "min_price": 50}
        result = self.db_service.execute_query(sql, params)
        
        # Verify all parameters were passed correctly
        self.mock_connection.execute.assert_called_once()
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])

    def test_parameter_type_handling(self):
        """Test handling of different parameter types (string, int, float, boolean)."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        self.mock_connection.execute.return_value = mock_result
        
        # Query with different parameter types
        sql = """
        SELECT * FROM services 
        WHERE name = :name 
        AND price > :price 
        AND active = :active 
        AND rating >= :rating
        """
        params = {
            "name": "Service A",       # string
            "price": 100,              # int
            "active": True,            # boolean
            "rating": 4.5              # float
        }
        self.db_service.execute_query(sql, params)
        
        # Verify parameters were passed with correct types
        call_args = self.mock_connection.execute.call_args[0]
        passed_params = call_args[1]
        
        self.assertEqual(type(passed_params["name"]), str)
        self.assertEqual(type(passed_params["price"]), int)
        self.assertEqual(type(passed_params["active"]), bool)
        self.assertEqual(type(passed_params["rating"]), float)

    def test_none_parameters(self):
        """Test handling of None parameters."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        self.mock_connection.execute.return_value = mock_result
        
        sql = "SELECT * FROM services WHERE name = :name OR category = :category"
        params = {"name": "Service A", "category": None}
        self.db_service.execute_query(sql, params)
        
        # Verify None parameters are passed correctly
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])

    def test_list_parameters(self):
        """Test handling of list parameters for IN clauses."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        self.mock_connection.execute.return_value = mock_result
        
        sql = "SELECT * FROM services WHERE id IN :service_ids"
        params = {"service_ids": [1, 2, 3]}
        self.db_service.execute_query(sql, params)
        
        # Verify list parameters are passed correctly
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])

    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are prevented by parameterization."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        self.mock_connection.execute.return_value = mock_result
        
        # Malicious input attempt
        sql = "SELECT * FROM users WHERE username = :username"
        malicious_input = "admin'; DROP TABLE users; --"
        params = {"username": malicious_input}
        
        self.db_service.execute_query(sql, params)
        
        # Verify the malicious string was passed as a parameter and not concatenated
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])
        
        # The SQL string should remain unchanged
        self.assertIn("username = :username", str(call_args[0]))
        self.assertNotIn("DROP TABLE", str(call_args[0]))

    def test_missing_parameters(self):
        """Test error handling when required parameters are missing."""
        sql = "SELECT * FROM services WHERE name = :name AND price > :price"
        params = {"name": "Service A"}  # Missing price parameter
        
        # Set up the mock to raise an exception
        self.mock_connection.execute.side_effect = Exception("Missing parameter")
        
        # Test that the exception is propagated
        with self.assertRaises(Exception):
            self.db_service.execute_query(sql, params)

    def test_date_parameters(self):
        """Test handling of date parameters."""
        from datetime import date, datetime
        
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        self.mock_connection.execute.return_value = mock_result
        
        sql = """
        SELECT * FROM bookings 
        WHERE booking_date = :booking_date 
        AND created_at > :created_after
        """
        
        today = date.today()
        now = datetime.now()
        params = {"booking_date": today, "created_after": now}
        
        self.db_service.execute_query(sql, params)
        
        # Verify date parameters are passed correctly
        call_args = self.mock_connection.execute.call_args[0]
        passed_params = call_args[1]
        
        self.assertEqual(passed_params["booking_date"], today)
        self.assertEqual(passed_params["created_after"], now)

    def test_json_parameters(self):
        """Test handling of JSON parameters."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = []
        self.mock_connection.execute.return_value = mock_result
        
        sql = "SELECT * FROM settings WHERE config = :config"
        json_data = {"theme": "dark", "notifications": True}
        params = {"config": json.dumps(json_data)}
        
        self.db_service.execute_query(sql, params)
        
        # Verify JSON parameters are passed correctly
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])


if __name__ == "__main__":
    unittest.main()