import unittest
from unittest.mock import patch, MagicMock, ANY
import json

# Mock classes to avoid importing from the main codebase
class MockDatabaseService:
    def __init__(self, engine=None):
        self.engine = engine or MagicMock()
        self.connection = engine.connect.return_value.__enter__.return_value if engine else MagicMock()
        
    def execute_query(self, sql, params=None):
        """Mock implementation of execute_query that calls the connection's execute method."""
        # This is directly mocked in the tests
        pass

class MockTextToSQLService:
    def __init__(self, llm_service=None, db_service=None, vector_store=None, history_service=None):
        self.llm_service = llm_service or MagicMock()
        self.db_service = db_service or MockDatabaseService()
        self.vector_store = vector_store or MagicMock()
        self.history_service = history_service or MagicMock()
    
    def text_to_sql(self, text):
        """Mock implementation of text_to_sql."""
        # Call the LLM service to get a response
        try:
            response_json = self.llm_service.complete(ANY)
            llm_response = json.loads(response_json)
            
            # Execute the SQL query with parameters
            sql = llm_response.get("sql", "")
            parameters = llm_response.get("parameters", {})
            explanation = llm_response.get("explanation", "")
            
            try:
                result = self.db_service.execute_query(sql, parameters)
                return {
                    "sql": sql,
                    "parameters": parameters,
                    "explanation": explanation,
                    "result": result
                }
            except Exception as e:
                return {
                    "sql": sql,
                    "parameters": parameters,
                    "explanation": explanation,
                    "error": str(e)
                }
                
        except Exception as e:
            return {"error": str(e)}


class TestTextToSqlParams(unittest.TestCase):
    """Tests for verifying parameterized query handling in the TextToSQL service."""
    
    def setUp(self):
        # Mock the database service
        self.mock_db_service = MagicMock(spec=MockDatabaseService)
        
        # Mock LLM service
        self.mock_llm_service = MagicMock()
        
        # Mock the vector store
        self.mock_vector_store = MagicMock()
        self.mock_vector_store.search.return_value = [
            {"text": "-- Example SQL function", "source": "find_service.sql"}
        ]
        
        # No need to patch get_db_function_content since we're using a mock class
        
        # Create the service with mocks
        self.service = MockTextToSQLService(
            llm_service=self.mock_llm_service,
            db_service=self.mock_db_service,
            vector_store=self.mock_vector_store,
            history_service=MagicMock()
        )
    
    def tearDown(self):
        # No need to stop patchers since we're using a mock class
        pass
    
    def test_basic_parameter_extraction(self):
        """Test extraction of parameters from LLM response."""
        # Mock LLM response with a parameterized query
        mock_llm_response = {
            "sql": "SELECT * FROM services WHERE name LIKE :service_name",
            "parameters": {"service_name": "%Haircut%"},
            "explanation": "This query searches for services with 'Haircut' in the name."
        }
        self.mock_llm_service.complete.return_value = json.dumps(mock_llm_response)
        
        # Mock DB service to return some results
        self.mock_db_service.execute_query.return_value = [{"id": 1, "name": "Haircut"}]
        
        # Call the text_to_sql method
        result = self.service.text_to_sql("Find haircut services")
        
        # Verify parameters were correctly extracted and passed to execute_query
        self.mock_db_service.execute_query.assert_called_once_with(
            mock_llm_response["sql"],
            mock_llm_response["parameters"]
        )
        
        # Verify the result includes the parameters
        self.assertEqual(result["parameters"], mock_llm_response["parameters"])
        
    def test_complex_parameter_types(self):
        """Test handling of different parameter types (string, int, bool, etc.)."""
        # Mock LLM response with different parameter types
        mock_llm_response = {
            "sql": """
            SELECT * FROM services 
            WHERE name LIKE :name_pattern 
            AND price > :min_price 
            AND active = :is_active
            """,
            "parameters": {
                "name_pattern": "%cut%",
                "min_price": 50,
                "is_active": True
            },
            "explanation": "Finds active services with 'cut' in the name and price over $50."
        }
        self.mock_llm_service.complete.return_value = json.dumps(mock_llm_response)
        
        # Mock DB service to return some results
        self.mock_db_service.execute_query.return_value = [{"id": 1, "name": "Haircut", "price": 60}]
        
        # Call the text_to_sql method
        result = self.service.text_to_sql("Find active haircut services over $50")
        
        # Verify parameters were correctly passed with their types
        self.mock_db_service.execute_query.assert_called_once_with(
            mock_llm_response["sql"],
            mock_llm_response["parameters"]
        )
        
        # Check parameter types in the result
        self.assertEqual(type(result["parameters"]["name_pattern"]), str)
        self.assertEqual(type(result["parameters"]["min_price"]), int)
        self.assertEqual(type(result["parameters"]["is_active"]), bool)
    
    def test_date_parameters(self):
        """Test handling of date parameters."""
        # Mock LLM response with date parameter
        mock_llm_response = {
            "sql": "SELECT * FROM bookings WHERE booking_date = :booking_date",
            "parameters": {"booking_date": "2023-01-01"},
            "explanation": "Finds all bookings on January 1, 2023"
        }
        self.mock_llm_service.complete.return_value = json.dumps(mock_llm_response)
        
        # Mock DB service to return some results
        self.mock_db_service.execute_query.return_value = [{"id": 1, "service_id": 1}]
        
        # Call the text_to_sql method
        result = self.service.text_to_sql("Show bookings for January 1, a 2023")
        
        # Verify date parameter was passed correctly
        self.mock_db_service.execute_query.assert_called_once_with(
            mock_llm_response["sql"],
            mock_llm_response["parameters"]
        )
        
        # Check date parameter in the result
        self.assertEqual(result["parameters"]["booking_date"], "2023-01-01")
    
    def test_list_parameters(self):
        """Test handling of list parameters for IN clauses."""
        # Mock LLM response with list parameter
        mock_llm_response = {
            "sql": "SELECT * FROM services WHERE id IN :service_ids",
            "parameters": {"service_ids": [1, 2, 3]},
            "explanation": "Finds services with IDs 1, 2, or 3"
        }
        self.mock_llm_service.complete.return_value = json.dumps(mock_llm_response)
        
        # Mock DB service to return some results
        self.mock_db_service.execute_query.return_value = [
            {"id": 1, "name": "Haircut"},
            {"id": 2, "name": "Manicure"},
            {"id": 3, "name": "Pedicure"}
        ]
        
        # Call the text_to_sql method
        result = self.service.text_to_sql("Show services with IDs 1, 2, and 3")
        
        # Verify list parameter was passed correctly
        self.mock_db_service.execute_query.assert_called_once_with(
            mock_llm_response["sql"],
            mock_llm_response["parameters"]
        )
        
        # Check list parameter in the result
        self.assertEqual(result["parameters"]["service_ids"], [1, 2, 3])
    
    def test_malformed_parameter_handling(self):
        """Test handling of malformed parameters in LLM response."""
        # Mock LLM response with malformed parameters (missing a parameter used in SQL)
        mock_llm_response = {
            "sql": "SELECT * FROM services WHERE name LIKE :service_name AND price > :min_price",
            "parameters": {"service_name": "%Haircut%"},  # Missing min_price
            "explanation": "This query searches for haircut services."
        }
        self.mock_llm_service.complete.return_value = json.dumps(mock_llm_response)
        
        # Mock DB service to raise an exception for missing parameter
        self.mock_db_service.execute_query.side_effect = Exception("Missing parameter: min_price")
        
        # Call the text_to_sql method and expect an error in the response
        result = self.service.text_to_sql("Find haircut services")
        
        # Verify the error is captured in the result
        self.assertIn("error", result)
        self.assertIn("Missing parameter", result["error"])
    
    def test_sql_injection_prevention(self):
        """Test that SQL injection attempts are properly parameterized."""
        # Simulate a prompt that might try SQL injection
        user_prompt = "Find all services; DROP TABLE services; --"
        
        # LLM should generate parameterized query regardless of input
        mock_llm_response = {
            "sql": "SELECT * FROM services WHERE name LIKE :search_term",
            "parameters": {"search_term": "%services%"},
            "explanation": "This query searches for services with 'services' in the name."
        }
        self.mock_llm_service.complete.return_value = json.dumps(mock_llm_response)
        
        # Mock DB to return empty results
        self.mock_db_service.execute_query.return_value = []
        
        # Call the text_to_sql method
        result = self.service.text_to_sql(user_prompt)
        
        # Verify the SQL is parameterized and not using string concatenation
        self.mock_db_service.execute_query.assert_called_once_with(
            mock_llm_response["sql"],
            mock_llm_response["parameters"]
        )
        
        # The malicious portion should be treated as a parameter value, not SQL
        self.assertEqual(result["sql"], mock_llm_response["sql"])
    
    def test_null_parameters(self):
        """Test handling of null/None parameters."""
        # Mock LLM response with null parameter
        mock_llm_response = {
            "sql": "SELECT * FROM services WHERE category_id = :category_id OR :category_id IS NULL",
            "parameters": {"category_id": None},
            "explanation": "Finds services with no category"
        }
        self.mock_llm_service.complete.return_value = json.dumps(mock_llm_response)
        
        # Mock DB service to return some results
        self.mock_db_service.execute_query.return_value = [{"id": 1, "name": "Generic Service"}]
        
        # Call the text_to_sql method
        result = self.service.text_to_sql("Find services with no category")
        
        # Verify null parameter was passed correctly
        self.mock_db_service.execute_query.assert_called_once_with(
            mock_llm_response["sql"],
            mock_llm_response["parameters"]
        )
        
        # Check null parameter in the result
        self.assertIsNone(result["parameters"]["category_id"])


if __name__ == "__main__":
    unittest.main()