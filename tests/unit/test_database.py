"""
Unit tests for the Database class.

Tests cover:
- Database connection management
- Query execution
- Credential retrieval
- Error handling
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/processor'))

from database import Database, DatabaseError


@pytest.fixture
def mock_boto3():
    """Mock boto3 client."""
    with patch('boto3.client') as mock:
        yield mock


@pytest.fixture
def mock_pymysql():
    """Mock pymysql module."""
    with patch('database.pymysql') as mock:
        yield mock


@pytest.fixture
def database(mock_boto3):
    """Create a Database instance with mocked boto3."""
    db = Database(
        secret_arn='arn:aws:secretsmanager:us-east-1:123456789012:secret:test',
        region='us-east-1'
    )
    return db


class TestGetCredentials:
    """Tests for _get_credentials method."""

    def test_get_credentials_success(self, database, mock_boto3):
        """Test successful credential retrieval."""
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"username": "admin", "password": "secret123", "host": "rds.amazonaws.com", "port": 3306, "dbname": "salesdb"}'
        }
        
        # Reset credentials to force retrieval
        database.credentials = None
        creds = database._get_credentials()
        
        assert creds['username'] == 'admin'
        assert creds['password'] == 'secret123'
        assert creds['host'] == 'rds.amazonaws.com'
        assert creds['port'] == 3306
        assert creds['dbname'] == 'salesdb'

    def test_get_credentials_cached(self, database, mock_boto3):
        """Test that credentials are cached after first retrieval."""
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"username": "admin", "password": "secret123"}'
        }
        
        # First call
        database.credentials = None
        creds1 = database._get_credentials()
        
        # Second call should use cache
        creds2 = database._get_credentials()
        
        assert creds1 == creds2
        mock_client.get_secret_value.assert_called_once()

    def test_get_credentials_error(self, database, mock_boto3):
        """Test credential retrieval with error."""
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_client.get_secret_value.side_effect = Exception("Access denied")
        
        database.credentials = None
        with pytest.raises(DatabaseError, match="Failed to retrieve credentials"):
            database._get_credentials()


class TestConnect:
    """Tests for connect method."""

    def test_connect_success(self, database, mock_boto3, mock_pymysql):
        """Test successful database connection."""
        # Mock credentials
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"username": "admin", "password": "secret123", "host": "rds.amazonaws.com", "port": 3306, "dbname": "salesdb"}'
        }
        
        database.connect()
        
        mock_pymysql.connect.assert_called_once()
        call_args = mock_pymysql.connect.call_args
        assert call_args[1]['host'] == 'rds.amazonaws.com'
        assert call_args[1]['user'] == 'admin'

    def test_connect_already_connected(self, database, mock_boto3, mock_pymysql):
        """Test connect when already connected."""
        mock_connection = MagicMock()
        mock_connection.open = True
        database.connection = mock_connection
        
        database.connect()
        
        # Should not create new connection
        mock_pymysql.connect.assert_not_called()

    def test_connect_error(self, database, mock_boto3, mock_pymysql):
        """Test connection with error."""
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"username": "admin", "password": "secret123"}'
        }
        mock_pymysql.connect.side_effect = Exception("Connection refused")
        
        with pytest.raises(DatabaseError, match="Failed to connect to database"):
            database.connect()


class TestDisconnect:
    """Tests for disconnect method."""

    def test_disconnect_success(self, database):
        """Test successful disconnection."""
        mock_connection = MagicMock()
        database.connection = mock_connection
        
        database.disconnect()
        
        mock_connection.close.assert_called_once()
        assert database.connection is None

    def test_disconnect_no_connection(self, database):
        """Test disconnect when no connection exists."""
        database.connection = None
        
        # Should not raise error
        database.disconnect()

    def test_disconnect_error(self, database):
        """Test disconnect with error."""
        mock_connection = MagicMock()
        mock_connection.close.side_effect = Exception("Close error")
        database.connection = mock_connection
        
        # Should not raise error
        database.disconnect()
        assert database.connection is None


class TestExecuteQuery:
    """Tests for execute_query method."""

    def test_execute_query_success(self, database, mock_boto3, mock_pymysql):
        """Test successful query execution."""
        # Setup mock connection
        mock_connection = MagicMock()
        mock_connection.open = True
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [
            {'id': 1, 'name': 'Product A'},
            {'id': 2, 'name': 'Product B'}
        ]
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=False)
        database.connection = mock_connection
        
        results = database.execute_query("SELECT * FROM products")
        
        assert len(results) == 2
        assert results[0]['name'] == 'Product A'

    def test_execute_query_with_params(self, database, mock_boto3, mock_pymysql):
        """Test query execution with parameters."""
        mock_connection = MagicMock()
        mock_connection.open = True
        mock_cursor = MagicMock()
        mock_cursor.fetchall.return_value = [{'id': 1}]
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=False)
        database.connection = mock_connection
        
        database.execute_query("SELECT * FROM products WHERE id = %s", (1,))
        
        mock_cursor.execute.assert_called_once_with("SELECT * FROM products WHERE id = %s", (1,))

    def test_execute_query_auto_connect(self, database, mock_boto3, mock_pymysql):
        """Test that query auto-connects if not connected."""
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"username": "admin", "password": "secret123", "host": "rds.amazonaws.com", "port": 3306, "dbname": "salesdb"}'
        }
        
        database.execute_query("SELECT 1")
        
        mock_pymysql.connect.assert_called_once()

    def test_execute_query_error(self, database, mock_boto3, mock_pymysql):
        """Test query execution with error."""
        mock_connection = MagicMock()
        mock_connection.open = True
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Syntax error")
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=False)
        database.connection = mock_connection
        
        with pytest.raises(DatabaseError, match="Query execution failed"):
            database.execute_query("INVALID SQL")


class TestExecuteUpdate:
    """Tests for execute_update method."""

    def test_execute_update_success(self, database, mock_boto3, mock_pymysql):
        """Test successful update execution."""
        mock_connection = MagicMock()
        mock_connection.open = True
        mock_cursor = MagicMock()
        mock_cursor.rowcount = 1
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=False)
        database.connection = mock_connection
        
        affected = database.execute_update("INSERT INTO products VALUES (1, 'Test')")
        
        assert affected == 1
        mock_connection.commit.assert_called_once()

    def test_execute_update_rollback_on_error(self, database, mock_boto3, mock_pymysql):
        """Test rollback on update error."""
        mock_connection = MagicMock()
        mock_connection.open = True
        mock_cursor = MagicMock()
        mock_cursor.execute.side_effect = Exception("Constraint violation")
        mock_connection.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = MagicMock(return_value=False)
        database.connection = mock_connection
        
        with pytest.raises(DatabaseError, match="Update execution failed"):
            database.execute_update("INSERT INTO products VALUES (1, 'Test')")
        
        mock_connection.rollback.assert_called_once()


class TestContextManager:
    """Tests for context manager functionality."""

    def test_context_manager(self, database, mock_boto3, mock_pymysql):
        """Test context manager entry and exit."""
        mock_client = MagicMock()
        mock_boto3.return_value = mock_client
        mock_client.get_secret_value.return_value = {
            'SecretString': '{"username": "admin", "password": "secret123", "host": "rds.amazonaws.com", "port": 3306, "dbname": "salesdb"}'
        }
        
        with database as db:
            assert db is database
        
        # Connection should be closed after context exit
        mock_pymysql.connect.assert_called_once()