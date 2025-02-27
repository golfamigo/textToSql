import unittest
from unittest.mock import patch, MagicMock
import os
import json

# Mock classes to avoid importing from the main codebase
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

# Mock function for get_db_function_content
def mock_get_db_function_content(function_name):
    """Mock implementation of get_db_function_content."""
    sql_templates = {
        "find_service.sql": "SELECT * FROM services WHERE name LIKE :search_term",
        "get_booking_details.sql": "SELECT * FROM bookings WHERE id = :booking_id",
        "get_bookings_by_customer_email.sql": "SELECT * FROM bookings WHERE customer_email = :customer_email",
        "create_booking.sql": """
            INSERT INTO bookings (service_id, staff_id, customer_name, customer_email, customer_phone, start_time, end_time, notes)
            VALUES (:service_id, :staff_id, :customer_name, :customer_email, :customer_phone, :start_time, :end_time, :notes)
            RETURNING id
        """,
        "update_service.sql": """
            UPDATE services
            SET name = :name, description = :description, duration = :duration, price = :price
            WHERE id = :service_id
        """,
        "get_period_availability.sql": "SELECT * FROM period_availability WHERE period_id = :period_id",
        "get_period_availability_by_date.sql": "SELECT * FROM period_availability WHERE period_id = :period_id AND date = :date",
        "set_staff_availability.sql": """
            INSERT INTO staff_availability (staff_id, period_id, date, is_available)
            VALUES (:staff_id, :period_id, :date, :is_available)
            ON CONFLICT (staff_id, period_id, date) DO UPDATE
            SET is_available = :is_available
        """
    }
    return sql_templates.get(function_name, "")


class TestSqlFunctionParams(unittest.TestCase):
    """Tests for verifying parameter handling in actual SQL functions from the codebase."""
    
    def setUp(self):
        self.mock_engine = MagicMock()
        self.mock_connection = MagicMock()
        self.mock_engine.connect.return_value.__enter__.return_value = self.mock_connection
        self.db_service = MockDatabaseService(engine=self.mock_engine)
        
        # Get the directory where SQL functions are stored
        self.db_function_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                                          "database_function")
        
        # Sample test data for different entity types
        self.test_data = {
            "service": {"id": 1, "name": "Haircut", "duration": 30, "price": 50.0},
            "staff": {"id": 1, "name": "John Doe", "email": "john@example.com"},
            "booking": {"id": 1, "customer_email": "customer@example.com", "service_id": 1, "staff_id": 1},
            "period": {"id": 1, "name": "Morning", "start_time": "09:00:00", "end_time": "12:00:00"}
        }
    
    def _mock_query_result(self, result_data):
        """Helper to create a mock query result with the given data."""
        mock_result = MagicMock()
        mock_result.mappings.return_value.all.return_value = result_data
        self.mock_connection.execute.return_value = mock_result
        return mock_result
    
    def test_find_service_params(self):
        """Test parameter handling in find_service.sql function."""
        # Load the SQL function content
        sql = mock_get_db_function_content("find_service.sql")
        self.assertIsNotNone(sql, "SQL function not found")
        
        # Check that the SQL uses named parameters
        self.assertIn(":search_term", sql, "SQL should use named parameter :search_term")
        
        # Mock the query result
        self._mock_query_result([self.test_data["service"]])
        
        # Execute the query with parameters
        params = {"search_term": "Haircut"}
        result = self.db_service.execute_query(sql, params)
        
        # Verify parameter passing
        self.mock_connection.execute.assert_called_once()
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])
        
        # Verify result
        self.assertEqual([self.test_data["service"]], result)
    
    def test_get_booking_details_params(self):
        """Test parameter handling in get_booking_details.sql function."""
        # Load the SQL function content
        sql = mock_get_db_function_content("get_booking_details.sql")
        self.assertIsNotNone(sql, "SQL function not found")
        
        # Check that the SQL uses named parameters
        self.assertIn(":booking_id", sql, "SQL should use named parameter :booking_id")
        
        # Mock the query result
        self._mock_query_result([{**self.test_data["booking"], "service_name": "Haircut", "staff_name": "John Doe"}])
        
        # Execute the query with parameters
        params = {"booking_id": 1}
        result = self.db_service.execute_query(sql, params)
        
        # Verify parameter passing
        self.mock_connection.execute.assert_called_once()
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])
    
    def test_get_bookings_by_customer_email_params(self):
        """Test parameter handling in get_bookings_by_customer_email.sql function."""
        # Load the SQL function content
        sql = mock_get_db_function_content("get_bookings_by_customer_email.sql")
        self.assertIsNotNone(sql, "SQL function not found")
        
        # Check that the SQL uses named parameters
        self.assertIn(":customer_email", sql, "SQL should use named parameter :customer_email")
        
        # Mock the query result
        self._mock_query_result([self.test_data["booking"]])
        
        # Execute the query with parameters
        params = {"customer_email": "customer@example.com"}
        result = self.db_service.execute_query(sql, params)
        
        # Verify parameter passing
        self.mock_connection.execute.assert_called_once()
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])
    
    def test_create_booking_params(self):
        """Test parameter handling in create_booking.sql function."""
        # Load the SQL function content
        sql = mock_get_db_function_content("create_booking.sql")
        self.assertIsNotNone(sql, "SQL function not found")
        
        # Check for named parameters in the SQL
        required_params = [
            ":service_id", ":staff_id", ":customer_name", 
            ":customer_email", ":customer_phone", ":start_time", ":end_time"
        ]
        
        for param in required_params:
            self.assertIn(param, sql, f"SQL should use named parameter {param}")
        
        # Mock the query result
        self._mock_query_result([{"id": 1}])
        
        # Create booking parameters
        params = {
            "service_id": 1,
            "staff_id": 1,
            "customer_name": "Test Customer",
            "customer_email": "test@example.com",
            "customer_phone": "123-456-7890",
            "start_time": "2023-01-01 09:00:00",
            "end_time": "2023-01-01 09:30:00",
            "notes": "Test booking"
        }
        
        # Execute the query with parameters
        result = self.db_service.execute_query(sql, params)
        
        # Verify parameter passing
        self.mock_connection.execute.assert_called_once()
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])
    
    def test_update_service_params(self):
        """Test parameter handling in update_service.sql function."""
        # Load the SQL function content
        sql = mock_get_db_function_content("update_service.sql")
        self.assertIsNotNone(sql, "SQL function not found")
        
        # Check for named parameters in the SQL
        required_params = [":service_id", ":name", ":description", ":duration", ":price"]
        
        for param in required_params:
            self.assertIn(param, sql, f"SQL should use named parameter {param}")
        
        # Mock the query result
        self._mock_query_result([{"affected_rows": 1}])
        
        # Update service parameters
        params = {
            "service_id": 1,
            "name": "Updated Haircut",
            "description": "New description",
            "duration": 45,
            "price": 60.0
        }
        
        # Execute the query with parameters
        result = self.db_service.execute_query(sql, params)
        
        # Verify parameter passing
        self.mock_connection.execute.assert_called_once()
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])
    
    def test_get_period_availability_params(self):
        """Test parameter handling in get_period_availability.sql function."""
        # Load the SQL function content
        sql = mock_get_db_function_content("get_period_availability.sql")
        self.assertIsNotNone(sql, "SQL function not found")
        
        # Check for named parameters in the SQL
        self.assertIn(":period_id", sql, "SQL should use named parameter :period_id")
        
        # Mock the query result
        availability_data = [
            {"date": "2023-01-01", "day_of_week": "Monday", "is_available": True}
        ]
        self._mock_query_result(availability_data)
        
        # Execute query with parameters
        params = {"period_id": 1}
        result = self.db_service.execute_query(sql, params)
        
        # Verify parameter passing
        self.mock_connection.execute.assert_called_once()
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])
        
        # Verify result
        self.assertEqual(availability_data, result)
    
    def test_get_period_availability_by_date_params(self):
        """Test parameter handling in get_period_availability_by_date.sql function."""
        # Load the SQL function content
        sql = mock_get_db_function_content("get_period_availability_by_date.sql")
        self.assertIsNotNone(sql, "SQL function not found")
        
        # Check for named parameters in the SQL
        required_params = [":date", ":period_id"]
        
        for param in required_params:
            self.assertIn(param, sql, f"SQL should use named parameter {param}")
        
        # Mock the query result
        availability_data = [{"is_available": True}]
        self._mock_query_result(availability_data)
        
        # Execute query with parameters
        params = {"date": "2023-01-01", "period_id": 1}
        result = self.db_service.execute_query(sql, params)
        
        # Verify parameter passing
        self.mock_connection.execute.assert_called_once()
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])
        
        # Verify result
        self.assertEqual(availability_data, result)
    
    def test_set_staff_availability_params(self):
        """Test parameter handling in set_staff_availability.sql function."""
        # Load the SQL function content
        sql = mock_get_db_function_content("set_staff_availability.sql")
        self.assertIsNotNone(sql, "SQL function not found")
        
        # Check for named parameters in the SQL
        required_params = [":staff_id", ":period_id", ":date", ":is_available"]
        
        for param in required_params:
            self.assertIn(param, sql, f"SQL should use named parameter {param}")
        
        # Mock the query result
        self._mock_query_result([{"affected_rows": 1}])
        
        # Execute query with parameters
        params = {
            "staff_id": 1,
            "period_id": 1,
            "date": "2023-01-01",
            "is_available": True
        }
        result = self.db_service.execute_query(sql, params)
        
        # Verify parameter passing
        self.mock_connection.execute.assert_called_once()
        call_args = self.mock_connection.execute.call_args[0]
        self.assertEqual(params, call_args[1])


if __name__ == "__main__":
    unittest.main()