"""
Unit tests for the SalesProcessor class.

Tests cover:
- Sales calculations
- Report generation
- Empty database results
- Error handling
"""

import pytest
from datetime import date
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '../../src/processor'))

from sales import SalesProcessor, SalesError
from database import Database, DatabaseError


@pytest.fixture
def mock_db():
    """Create a mock Database instance."""
    db = MagicMock(spec=Database)
    return db


@pytest.fixture
def sales_processor(mock_db):
    """Create a SalesProcessor instance with mock database."""
    return SalesProcessor(mock_db)


class TestCalculateTotalOrders:
    """Tests for calculate_total_orders method."""

    def test_total_orders_with_data(self, sales_processor, mock_db):
        """Test total orders calculation with data."""
        mock_db.execute_query.return_value = [{'total': 150}]
        
        result = sales_processor.calculate_total_orders(date(2024, 1, 15))
        
        assert result == 150
        mock_db.execute_query.assert_called_once()

    def test_total_orders_empty(self, sales_processor, mock_db):
        """Test total orders with no data."""
        mock_db.execute_query.return_value = [{'total': 0}]
        
        result = sales_processor.calculate_total_orders(date(2024, 1, 15))
        
        assert result == 0

    def test_total_orders_none_result(self, sales_processor, mock_db):
        """Test total orders with None result."""
        mock_db.execute_query.return_value = []
        
        result = sales_processor.calculate_total_orders(date(2024, 1, 15))
        
        assert result == 0

    def test_total_orders_database_error(self, sales_processor, mock_db):
        """Test total orders with database error."""
        mock_db.execute_query.side_effect = DatabaseError("Connection failed")
        
        with pytest.raises(SalesError, match="Failed to calculate total orders"):
            sales_processor.calculate_total_orders(date(2024, 1, 15))


class TestCalculateTotalQuantity:
    """Tests for calculate_total_quantity method."""

    def test_total_quantity_with_data(self, sales_processor, mock_db):
        """Test total quantity calculation with data."""
        mock_db.execute_query.return_value = [{'total': 450}]
        
        result = sales_processor.calculate_total_quantity(date(2024, 1, 15))
        
        assert result == 450

    def test_total_quantity_empty(self, sales_processor, mock_db):
        """Test total quantity with no data."""
        mock_db.execute_query.return_value = [{'total': 0}]
        
        result = sales_processor.calculate_total_quantity(date(2024, 1, 15))
        
        assert result == 0


class TestCalculateTotalRevenue:
    """Tests for calculate_total_revenue method."""

    def test_total_revenue_with_data(self, sales_processor, mock_db):
        """Test total revenue calculation with data."""
        mock_db.execute_query.return_value = [{'total': 12500.50}]
        
        result = sales_processor.calculate_total_revenue(date(2024, 1, 15))
        
        assert result == 12500.50

    def test_total_revenue_empty(self, sales_processor, mock_db):
        """Test total revenue with no data."""
        mock_db.execute_query.return_value = [{'total': 0}]
        
        result = sales_processor.calculate_total_revenue(date(2024, 1, 15))
        
        assert result == 0.0

    def test_total_revenue_decimal(self, sales_processor, mock_db):
        """Test total revenue with decimal value."""
        mock_db.execute_query.return_value = [{'total': 99.99}]
        
        result = sales_processor.calculate_total_revenue(date(2024, 1, 15))
        
        assert result == 99.99


class TestCalculateAverageOrderValue:
    """Tests for calculate_average_order_value method."""

    def test_average_order_value_with_data(self, sales_processor, mock_db):
        """Test average order value calculation with data."""
        mock_db.execute_query.return_value = [{'avg_value': 83.33}]
        
        result = sales_processor.calculate_average_order_value(date(2024, 1, 15))
        
        assert result == 83.33

    def test_average_order_value_empty(self, sales_processor, mock_db):
        """Test average order value with no data."""
        mock_db.execute_query.return_value = [{'avg_value': 0}]
        
        result = sales_processor.calculate_average_order_value(date(2024, 1, 15))
        
        assert result == 0.0


class TestGetTopProduct:
    """Tests for get_top_product method."""

    def test_top_product_with_data(self, sales_processor, mock_db):
        """Test top product retrieval with data."""
        mock_db.execute_query.return_value = [{
            'product_name': 'Wireless Headphones',
            'total_revenue': 500.00,
            'total_quantity': 10
        }]
        
        result = sales_processor.get_top_product(date(2024, 1, 15))
        
        assert result is not None
        assert result['name'] == 'Wireless Headphones'
        assert result['revenue'] == 500.00
        assert result['quantity'] == 10

    def test_top_product_empty(self, sales_processor, mock_db):
        """Test top product with no data."""
        mock_db.execute_query.return_value = []
        
        result = sales_processor.get_top_product(date(2024, 1, 15))
        
        assert result is None


class TestGetTopCategory:
    """Tests for get_top_category method."""

    def test_top_category_with_data(self, sales_processor, mock_db):
        """Test top category retrieval with data."""
        mock_db.execute_query.return_value = [{
            'category': 'Electronics',
            'total_revenue': 5000.00,
            'order_count': 50
        }]
        
        result = sales_processor.get_top_category(date(2024, 1, 15))
        
        assert result is not None
        assert result['name'] == 'Electronics'
        assert result['revenue'] == 5000.00
        assert result['order_count'] == 50

    def test_top_category_empty(self, sales_processor, mock_db):
        """Test top category with no data."""
        mock_db.execute_query.return_value = []
        
        result = sales_processor.get_top_category(date(2024, 1, 15))
        
        assert result is None


class TestGetSalesByCategory:
    """Tests for get_sales_by_category method."""

    def test_sales_by_category_with_data(self, sales_processor, mock_db):
        """Test sales by category retrieval with data."""
        mock_db.execute_query.return_value = [
            {
                'category': 'Electronics',
                'total_revenue': 5000.00,
                'total_quantity': 100,
                'order_count': 50
            },
            {
                'category': 'Clothing',
                'total_revenue': 3000.00,
                'total_quantity': 75,
                'order_count': 30
            }
        ]
        
        result = sales_processor.get_sales_by_category(date(2024, 1, 15))
        
        assert len(result) == 2
        assert result[0]['category'] == 'Electronics'
        assert result[0]['revenue'] == 5000.00
        assert result[1]['category'] == 'Clothing'

    def test_sales_by_category_empty(self, sales_processor, mock_db):
        """Test sales by category with no data."""
        mock_db.execute_query.return_value = []
        
        result = sales_processor.get_sales_by_category(date(2024, 1, 15))
        
        assert result == []


class TestGenerateReport:
    """Tests for generate_report method."""

    def test_generate_report_with_data(self, sales_processor, mock_db):
        """Test report generation with complete data."""
        # Mock all database queries
        mock_db.execute_query.side_effect = [
            [{'total': 100}],  # total_orders
            [{'total': 300}],  # total_quantity
            [{'total': 10000.00}],  # total_revenue
            [{'avg_value': 100.00}],  # avg_order_value
            [{'product_name': 'Widget', 'total_revenue': 2000.00, 'total_quantity': 50}],  # top_product
            [{'category': 'Electronics', 'total_revenue': 5000.00, 'order_count': 40}],  # top_category
            [  # sales_by_category
                {'category': 'Electronics', 'total_revenue': 5000.00, 'total_quantity': 100, 'order_count': 40},
                {'category': 'Clothing', 'total_revenue': 3000.00, 'total_quantity': 80, 'order_count': 30}
            ]
        ]
        
        report = sales_processor.generate_report(date(2024, 1, 15), 'dev')
        
        assert 'DAILY SALES REPORT' in report
        assert '2024-01-15' in report
        assert 'dev' in report
        assert 'Total Orders: 100' in report
        assert 'Total Quantity: 300' in report
        assert 'Total Revenue: $10,000.00' in report
        assert 'Average Order Value: $100.00' in report
        assert 'Top Product: Widget' in report
        assert 'Top Category: Electronics' in report
        assert 'Electronics: $5,000.00' in report
        assert 'Clothing: $3,000.00' in report

    def test_generate_report_empty_data(self, sales_processor, mock_db):
        """Test report generation with no data."""
        mock_db.execute_query.side_effect = [
            [{'total': 0}],  # total_orders
            [{'total': 0}],  # total_quantity
            [{'total': 0}],  # total_revenue
            [{'avg_value': 0}],  # avg_order_value
            [],  # top_product
            [],  # top_category
            []  # sales_by_category
        ]
        
        report = sales_processor.generate_report(date(2024, 1, 15), 'dev')
        
        assert 'DAILY SALES REPORT' in report
        assert 'Total Orders: 0' in report
        assert 'Top Product: N/A' in report
        assert 'Top Category: N/A' in report

    def test_generate_report_database_error(self, sales_processor, mock_db):
        """Test report generation with database error."""
        mock_db.execute_query.side_effect = DatabaseError("Connection failed")
        
        with pytest.raises(SalesError):
            sales_processor.generate_report(date(2024, 1, 15), 'dev')