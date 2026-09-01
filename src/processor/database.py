"""
Database module for S214 Sales Platform.

This module handles all database operations including:
- Database connection management
- Query execution
- Connection cleanup

Security: Credentials are retrieved from AWS Secrets Manager at runtime.
No credentials are hardcoded or logged.
"""

import logging
import pymysql
import boto3
import json
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DatabaseError(Exception):
    """Custom exception for database operations."""

    pass


class Database:
    """
    Database connection manager for MySQL RDS.

    Handles connection lifecycle, query execution, and error handling.
    Connections are created on demand and should be closed after use.
    """

    def __init__(self, secret_arn: str, region: str = "us-east-1"):
        """
        Initialize the Database manager.

        Args:
            secret_arn: ARN of the Secrets Manager secret containing credentials
            region: AWS region where the secret is stored
        """
        self.secret_arn = secret_arn
        self.region = region
        self.connection = None
        self.credentials = None

    def _get_credentials(self) -> Dict[str, str]:
        """
        Retrieve database credentials from AWS Secrets Manager.

        Returns:
            Dictionary containing username, password, host, port, dbname

        Raises:
            DatabaseError: If credentials cannot be retrieved
        """
        if self.credentials:
            return self.credentials

        try:
            client = boto3.client("secretsmanager", region_name=self.region)
            response = client.get_secret_value(SecretId=self.secret_arn)
            secret = json.loads(response["SecretString"])

            self.credentials = {
                "username": secret["username"],
                "password": secret["password"],
                "host": secret.get("host", ""),
                "port": secret.get("port", 3306),
                "dbname": secret.get("dbname", "salesdb"),
            }

            logger.info(
                "Successfully retrieved database credentials from Secrets Manager"
            )
            return self.credentials

        except Exception as e:
            logger.error(f"Failed to retrieve database credentials: {str(e)}")
            raise DatabaseError(f"Failed to retrieve credentials: {str(e)}")

    def connect(self) -> None:
        """
        Establish a connection to the MySQL database.

        Raises:
            DatabaseError: If connection cannot be established
        """
        if self.connection and self.connection.open:
            return

        try:
            credentials = self._get_credentials()

            self.connection = pymysql.connect(
                host=credentials["host"],
                user=credentials["username"],
                password=credentials["password"],
                database=credentials["dbname"],
                port=credentials["port"],
                charset="utf8mb4",
                cursorclass=pymysql.cursors.DictCursor,
                connect_timeout=10,
                read_timeout=30,
                write_timeout=30,
            )

            logger.info("Successfully connected to database")

        except Exception as e:
            logger.error(f"Failed to connect to database: {str(e)}")
            raise DatabaseError(f"Failed to connect to database: {str(e)}")

    def disconnect(self) -> None:
        """Close the database connection."""
        if self.connection:
            try:
                self.connection.close()
                logger.info("Database connection closed")
            except Exception as e:
                logger.warning(f"Error closing database connection: {str(e)}")
            finally:
                self.connection = None

    def execute_query(
        self, query: str, params: Optional[tuple] = None
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results.

        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)

        Returns:
            List of dictionaries containing query results

        Raises:
            DatabaseError: If query execution fails
        """
        if not self.connection or not self.connection.open:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                results = cursor.fetchall()
                logger.info(
                    f"Query executed successfully, returned {len(results)} rows"
                )
                return results

        except Exception as e:
            logger.error(f"Query execution failed: {str(e)}")
            raise DatabaseError(f"Query execution failed: {str(e)}")

    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """
        Execute an INSERT, UPDATE, or DELETE query.

        Args:
            query: SQL query string
            params: Query parameters (for parameterized queries)

        Returns:
            Number of affected rows

        Raises:
            DatabaseError: If query execution fails
        """
        if not self.connection or not self.connection.open:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                affected_rows = cursor.rowcount
                logger.info(
                    f"Update executed successfully, affected {affected_rows} rows"
                )
                return affected_rows

        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Update execution failed: {str(e)}")
            raise DatabaseError(f"Update execution failed: {str(e)}")

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
