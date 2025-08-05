#!/usr/bin/env python3
"""
Comprehensive tests for main.py

Tests all endpoints, valid and invalid inputs, edge cases, and error scenarios.
"""
import pytest
import json
from datetime import date, datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from main import app, calculate_days_until_birthday

# Test client
client = TestClient(app)

class TestCalculateDaysUntilBirthday:
    """Test the birthday calculation function."""

    def test_birthday_today(self):
        """Test when birthday is today."""
        today = date.today()
        result = calculate_days_until_birthday(today.isoformat())
        assert result == 0

    def test_birthday_tomorrow(self):
        """Test when birthday is tomorrow."""
        tomorrow = date.today() + timedelta(days=1)
        result = calculate_days_until_birthday(tomorrow.isoformat())
        assert result == 1

    def test_birthday_yesterday(self):
        """Test when birthday was yesterday (should calculate for next year)."""
        yesterday = date.today() - timedelta(days=1)
        result = calculate_days_until_birthday(yesterday.isoformat())
        assert result > 360  # Should be close to a year

    def test_birthday_in_5_days(self):
        """Test when birthday is in 5 days."""
        future_date = date.today() + timedelta(days=5)
        result = calculate_days_until_birthday(future_date.isoformat())
        assert result == 5

class TestPutHelloEndpoint:
    """Test the PUT /hello/{username} endpoint."""

    @patch('main.store_birthday')
    def test_valid_birthday(self, mock_store):
        """Test valid birthday input."""
        mock_store.return_value = None
        response = client.put(
            "/hello/john",
            json={"dateOfBirth": "1990-05-15"}
        )
        assert response.status_code == 204
        assert response.content == b''  # No content
        mock_store.assert_called_once_with("john", "1990-05-15")

    def test_missing_request_body(self):
        """Test missing request body."""
        response = client.put("/hello/john")
        assert response.status_code == 422

    def test_invalid_date_format(self):
        """Test invalid date format."""
        response = client.put(
            "/hello/john",
            json={"dateOfBirth": "invalid-date"}
        )
        assert response.status_code == 422

    def test_future_date(self):
        """Test future date (should be rejected)."""
        future_date = date.today().replace(year=date.today().year + 1)
        response = client.put(
            "/hello/john",
            json={"dateOfBirth": future_date.isoformat()}
        )
        assert response.status_code == 422
        assert "dateOfBirth must be a date before today" in response.json()["detail"][0]["msg"]

    def test_today_date(self):
        """Test today's date (should be rejected)."""
        today = date.today()
        response = client.put(
            "/hello/john",
            json={"dateOfBirth": today.isoformat()}
        )
        assert response.status_code == 422
        assert "dateOfBirth must be a date before today" in response.json()["detail"][0]["msg"]

    def test_invalid_username_special_chars(self):
        """Test username with special characters."""
        response = client.put(
            "/hello/john123",
            json={"dateOfBirth": "1990-05-15"}
        )
        assert response.status_code == 422

    def test_invalid_username_numbers(self):
        """Test username with numbers."""
        response = client.put(
            "/hello/john123",
            json={"dateOfBirth": "1990-05-15"}
        )
        assert response.status_code == 422

    def test_invalid_username_empty(self):
        """Test empty username."""
        response = client.put(
            "/hello/",
            json={"dateOfBirth": "1990-05-15"}
        )
        assert response.status_code == 404

    def test_invalid_username_too_long(self):
        """Test username too long."""
        long_username = "a" * 51
        response = client.put(
            f"/hello/{long_username}",
            json={"dateOfBirth": "1990-05-15"}
        )
        assert response.status_code == 422

    def test_invalid_username_too_short(self):
        """Test username too short."""
        response = client.put(
            "/hello/",
            json={"dateOfBirth": "1990-05-15"}
        )
        assert response.status_code == 404

class TestGetHelloEndpoint:
    """Test the GET /hello/{username} endpoint."""

    @patch('main.get_birthday')
    def test_user_exists_birthday_today(self, mock_get):
        """Test user exists and birthday is today."""
        mock_get.return_value = date.today().isoformat()
        response = client.get("/hello/john")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, john! Happy birthday!"}

    @patch('main.get_birthday')
    def test_user_exists_birthday_tomorrow(self, mock_get):
        """Test user exists and birthday is tomorrow."""
        tomorrow = date.today() + timedelta(days=1)
        mock_get.return_value = tomorrow.isoformat()
        response = client.get("/hello/john")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, john! Your birthday is in 1 day"}

    @patch('main.get_birthday')
    def test_user_exists_birthday_in_5_days(self, mock_get):
        """Test user exists and birthday is in 5 days."""
        future_date = date.today() + timedelta(days=5)
        mock_get.return_value = future_date.isoformat()
        response = client.get("/hello/john")
        assert response.status_code == 200
        assert response.json() == {"message": "Hello, john! Your birthday is in 5 days"}

    @patch('main.get_birthday')
    def test_user_not_found(self, mock_get):
        """Test user not found in database."""
        mock_get.return_value = None
        response = client.get("/hello/john")
        assert response.status_code == 200
        assert response.json() == {"message": "user not found"}

    def test_invalid_username_special_chars(self):
        """Test username with special characters."""
        response = client.get("/hello/john123")
        assert response.status_code == 422

    def test_invalid_username_numbers(self):
        """Test username with numbers."""
        response = client.get("/hello/john123")
        assert response.status_code == 422

    def test_invalid_username_empty(self):
        """Test empty username."""
        response = client.get("/hello/")
        assert response.status_code == 404

    def test_invalid_username_too_long(self):
        """Test username too long."""
        long_username = "a" * 51
        response = client.get(f"/hello/{long_username}")
        assert response.status_code == 422

    def test_invalid_username_too_short(self):
        """Test username too short."""
        response = client.get("/hello/")
        assert response.status_code == 404

class TestHealthCheckEndpoint:
    """Test the GET /hello/healthcheck endpoint."""

    @patch('main.table')
    def test_health_check_healthy(self, mock_table):
        """Test health check when everything is working."""
        # Mock successful table.load()
        mock_table.load.return_value = None

        response = client.get("/hello/healthcheck")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["service"] == "revolut-birthday-api"
        assert "timestamp" in data
        assert data["checks"]["application"] == "ok"
        assert data["checks"]["database"] == "ok"
        mock_table.load.assert_called_once()

    @patch('main.table')
    def test_health_check_database_error(self, mock_table):
        """Test health check when DynamoDB is unavailable."""
        from botocore.exceptions import ClientError

        # Mock ClientError from DynamoDB
        mock_table.load.side_effect = ClientError(
            error_response={'Error': {'Code': 'ResourceNotFoundException', 'Message': 'Table not found'}},
            operation_name='DescribeTable'
        )

        response = client.get("/hello/healthcheck")

        assert response.status_code == 503
        data = response.json()["detail"]
        assert data["status"] == "unhealthy"
        assert data["service"] == "revolut-birthday-api"
        assert "timestamp" in data
        assert data["checks"]["application"] == "ok"
        assert data["checks"]["database"] == "error"
        assert "error" in data
        mock_table.load.assert_called_once()

    @patch('main.table')
    def test_health_check_unexpected_error(self, mock_table):
        """Test health check when unexpected error occurs."""
        # Mock unexpected exception
        mock_table.load.side_effect = Exception("Unexpected error")

        response = client.get("/hello/healthcheck")

        assert response.status_code == 503
        data = response.json()["detail"]
        assert data["status"] == "unhealthy"
        assert data["service"] == "revolut-birthday-api"
        assert "timestamp" in data
        assert data["checks"]["application"] == "error"
        assert data["checks"]["database"] == "unknown"
        assert "error" in data
        mock_table.load.assert_called_once()

    def test_health_check_response_format(self):
        """Test that health check response has correct format."""
        with patch('main.table') as mock_table:
            mock_table.load.return_value = None

            response = client.get("/hello/healthcheck")

            assert response.status_code == 200
            data = response.json()

            # Check required fields exist
            required_fields = ["status", "service", "timestamp", "checks"]
            for field in required_fields:
                assert field in data

            # Check checks structure
            assert "application" in data["checks"]
            assert "database" in data["checks"]

            # Check timestamp format (ISO format)
            from datetime import datetime
            try:
                datetime.fromisoformat(data["timestamp"])
            except ValueError:
                pytest.fail("Timestamp is not in valid ISO format")

class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @patch('main.store_birthday')
    def test_username_with_uppercase(self, mock_store):
        """Test username with uppercase letters."""
        mock_store.return_value = None
        response = client.put(
            "/hello/John",
            json={"dateOfBirth": "1990-05-15"}
        )
        assert response.status_code == 204

    @patch('main.get_birthday')
    def test_username_with_uppercase_get(self, mock_get):
        """Test username with uppercase letters in GET."""
        mock_get.return_value = None
        response = client.get("/hello/John")
        assert response.status_code == 200

    @patch('main.store_birthday')
    def test_username_max_length(self, mock_store):
        """Test username at maximum length."""
        mock_store.return_value = None
        max_username = "a" * 50
        response = client.put(
            f"/hello/{max_username}",
            json={"dateOfBirth": "1990-05-15"}
        )
        assert response.status_code == 204

    @patch('main.get_birthday')
    def test_username_max_length_get(self, mock_get):
        """Test username at maximum length in GET."""
        mock_get.return_value = None
        max_username = "a" * 50
        response = client.get(f"/hello/{max_username}")
        assert response.status_code == 200

    @patch('main.store_birthday')
    def test_username_min_length(self, mock_store):
        """Test username at minimum length."""
        mock_store.return_value = None
        response = client.put(
            "/hello/a",
            json={"dateOfBirth": "1990-05-15"}
        )
        assert response.status_code == 204

    @patch('main.get_birthday')
    def test_username_min_length_get(self, mock_get):
        """Test username at minimum length in GET."""
        mock_get.return_value = None
        response = client.get("/hello/a")
        assert response.status_code == 200

    def test_very_old_date(self):
        """Test very old date."""
        response = client.put(
            "/hello/john",
            json={"dateOfBirth": "1900-01-01"}
        )
        assert response.status_code == 204

    @patch('main.get_birthday')
    def test_very_old_date_get(self, mock_get):
        """Test very old date in GET."""
        mock_get.return_value = "1900-01-01"
        response = client.get("/hello/john")
        assert response.status_code == 200
        # Should calculate days until next birthday

if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 