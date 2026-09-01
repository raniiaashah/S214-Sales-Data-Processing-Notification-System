"""
Database initialization module for S214 Sales Platform Custom Resource.

This module handles:
- Database table creation
- Sample data insertion
- Idempotent operations (safe to run multiple times)
"""

import logging
import pymysql
import boto3
import json
from typing import Dict

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class DatabaseInitializationError(Exception):
    """Custom exception for database initialization operations."""

    pass


class DatabaseInitializer:
    """
    Initializes the database schema and sample data.

    This class is designed to be idempotent - it can be run multiple times
    without creating duplicate data or causing errors.
    """

    def __init__(self, secret_arn: str, region: str = "us-east-1"):
        """
        Initialize the DatabaseInitializer.

        Args:
            secret_arn: ARN of the Secrets Manager secret
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

            return self.credentials

        except Exception as e:
            logger.error(f"Failed to retrieve database credentials: {str(e)}")
            raise DatabaseInitializationError(
                f"Failed to retrieve credentials: {str(e)}"
            )

    def connect(self) -> None:
        """Establish a connection to the MySQL database."""
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
            raise DatabaseInitializationError(
                f"Failed to connect to database: {str(e)}"
            )

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

    def create_tables(self) -> None:
        """
        Create the sales table if it doesn't exist.

        This operation is idempotent - it uses CREATE TABLE IF NOT EXISTS.
        """
        if not self.connection or not self.connection.open:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                # Create sales table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sales (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        order_id VARCHAR(50) NOT NULL,
                        product_name VARCHAR(255) NOT NULL,
                        category VARCHAR(100) NOT NULL,
                        quantity INT NOT NULL,
                        unit_price DECIMAL(10,2) NOT NULL,
                        total_amount DECIMAL(10,2) NOT NULL,
                        sale_date DATE NOT NULL,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        INDEX idx_sale_date (sale_date),
                        INDEX idx_category (category)
                    ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci
                """)

                self.connection.commit()
                logger.info("Sales table created successfully (or already exists)")

        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Failed to create tables: {str(e)}")
            raise DatabaseInitializationError(f"Failed to create tables: {str(e)}")

    def insert_sample_data(self) -> int:
        """
        Insert sample sales data if the table is empty.

        This operation is idempotent - it checks if data exists before inserting.

        Returns:
            Number of records inserted
        """
        if not self.connection or not self.connection.open:
            self.connect()

        try:
            with self.connection.cursor() as cursor:
                # Check if data already exists
                cursor.execute("SELECT COUNT(*) as count FROM sales")
                result = cursor.fetchone()

                if result["count"] > 0:
                    logger.info(
                        f"Sample data already exists ({result['count']} records). Skipping insertion."
                    )
                    return 0

                # Sample sales data
                sample_data = [
                    # Electronics
                    (
                        "ORD-001",
                        "Wireless Headphones",
                        "Electronics",
                        2,
                        79.99,
                        159.98,
                        "2024-01-15",
                    ),
                    (
                        "ORD-002",
                        "Smartphone Case",
                        "Electronics",
                        3,
                        24.99,
                        74.97,
                        "2024-01-15",
                    ),
                    (
                        "ORD-003",
                        "USB-C Cable",
                        "Electronics",
                        5,
                        12.99,
                        64.95,
                        "2024-01-15",
                    ),
                    (
                        "ORD-004",
                        "Bluetooth Speaker",
                        "Electronics",
                        1,
                        49.99,
                        49.99,
                        "2024-01-15",
                    ),
                    (
                        "ORD-005",
                        "Wireless Headphones",
                        "Electronics",
                        1,
                        79.99,
                        79.99,
                        "2024-01-15",
                    ),
                    # Clothing
                    (
                        "ORD-006",
                        "Cotton T-Shirt",
                        "Clothing",
                        4,
                        19.99,
                        79.96,
                        "2024-01-15",
                    ),
                    (
                        "ORD-007",
                        "Denim Jeans",
                        "Clothing",
                        2,
                        59.99,
                        119.98,
                        "2024-01-15",
                    ),
                    (
                        "ORD-008",
                        "Running Shoes",
                        "Clothing",
                        1,
                        89.99,
                        89.99,
                        "2024-01-15",
                    ),
                    (
                        "ORD-009",
                        "Winter Jacket",
                        "Clothing",
                        1,
                        129.99,
                        129.99,
                        "2024-01-15",
                    ),
                    # Home & Garden
                    (
                        "ORD-010",
                        "Coffee Maker",
                        "Home & Garden",
                        1,
                        79.99,
                        79.99,
                        "2024-01-15",
                    ),
                    (
                        "ORD-011",
                        "Plant Pot Set",
                        "Home & Garden",
                        2,
                        29.99,
                        59.98,
                        "2024-01-15",
                    ),
                    (
                        "ORD-012",
                        "Kitchen Scale",
                        "Home & Garden",
                        1,
                        34.99,
                        34.99,
                        "2024-01-15",
                    ),
                    # Sports
                    ("ORD-013", "Yoga Mat", "Sports", 2, 29.99, 59.98, "2024-01-15"),
                    (
                        "ORD-014",
                        "Dumbbells Set",
                        "Sports",
                        1,
                        49.99,
                        49.99,
                        "2024-01-15",
                    ),
                    (
                        "ORD-015",
                        "Resistance Bands",
                        "Sports",
                        3,
                        14.99,
                        44.97,
                        "2024-01-15",
                    ),
                    # Additional data for yesterday
                    (
                        "ORD-016",
                        "Wireless Headphones",
                        "Electronics",
                        1,
                        79.99,
                        79.99,
                        "2024-01-14",
                    ),
                    (
                        "ORD-017",
                        "Cotton T-Shirt",
                        "Clothing",
                        2,
                        19.99,
                        39.98,
                        "2024-01-14",
                    ),
                    (
                        "ORD-018",
                        "Coffee Maker",
                        "Home & Garden",
                        1,
                        79.99,
                        79.99,
                        "2024-01-14",
                    ),
                    ("ORD-019", "Yoga Mat", "Sports", 1, 29.99, 29.99, "2024-01-14"),
                    (
                        "ORD-020",
                        "Smartphone Case",
                        "Electronics",
                        2,
                        24.99,
                        49.98,
                        "2024-01-14",
                    ),
                ]

                insert_query = """
                    INSERT INTO sales 
                    (order_id, product_name, category, quantity, unit_price, total_amount, sale_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """

                cursor.executemany(insert_query, sample_data)
                self.connection.commit()

                inserted_count = len(sample_data)
                logger.info(f"Inserted {inserted_count} sample records")
                return inserted_count

        except Exception as e:
            if self.connection:
                self.connection.rollback()
            logger.error(f"Failed to insert sample data: {str(e)}")
            raise DatabaseInitializationError(f"Failed to insert sample data: {str(e)}")

    def initialize(self) -> Dict[str, int]:
        """
        Perform full database initialization.

        Creates tables and inserts sample data if needed.

        Returns:
            Dictionary with initialization results
        """
        logger.info("Starting database initialization...")

        self.connect()

        try:
            self.create_tables()
            inserted = self.insert_sample_data()

            result = {"tables_created": 1, "records_inserted": inserted}

            logger.info(f"Database initialization completed: {result}")
            return result

        finally:
            self.disconnect()

    def cleanup(self) -> None:
        """
        Clean up sample data (for stack deletion).

        This removes all sample data but keeps the table structure.
        """
        logger.info("Starting database cleanup...")

        self.connect()

        try:
            with self.connection.cursor() as cursor:
                cursor.execute("DELETE FROM sales")
                self.connection.commit()
                logger.info("Sample data cleaned up successfully")

        except Exception as e:
            logger.warning(
                f"Cleanup encountered an issue (table may not exist): {str(e)}"
            )
        finally:
            self.disconnect()

    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.disconnect()
        return False
