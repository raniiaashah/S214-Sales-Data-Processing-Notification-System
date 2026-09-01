"""
Sales processing module for S214 Sales Platform.

This module handles all sales-related operations including:
- Sales data retrieval
- Business metrics calculation
- Report generation
"""

import logging
from datetime import datetime, date
from typing import Dict, List, Any, Optional
from database import Database, DatabaseError

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class SalesError(Exception):
    """Custom exception for sales processing operations."""
    pass


class SalesProcessor:
    """
    Processes sales data and generates business metrics.
    
    Calculates key performance indicators including:
    - Total orders, quantity, and revenue
    - Average order value
    - Top-selling products and categories
    - Daily and category-based sales breakdowns
    """

    def __init__(self, db: Database):
        """
        Initialize the SalesProcessor.
        
        Args:
            db: Database instance for querying sales data
        """
        self.db = db

    def get_daily_sales(self, sale_date: date) -> List[Dict[str, Any]]:
        """
        Retrieve all sales records for a specific date.
        
        Args:
            sale_date: Date to query sales for
            
        Returns:
            List of sales records
            
        Raises:
            SalesError: If data retrieval fails
        """
        try:
            query = """
                SELECT 
                    id,
                    order_id,
                    product_name,
                    category,
                    quantity,
                    unit_price,
                    total_amount,
                    sale_date
                FROM sales
                WHERE sale_date = %s
                ORDER BY total_amount DESC
            """
            results = self.db.execute_query(query, (sale_date,))
            logger.info(f"Retrieved {len(results)} sales records for {sale_date}")
            return results
            
        except DatabaseError as e:
            logger.error(f"Failed to retrieve daily sales: {str(e)}")
            raise SalesError(f"Failed to retrieve daily sales: {str(e)}")

    def calculate_total_orders(self, sale_date: date) -> int:
        """
        Calculate total number of orders for a date.
        
        Args:
            sale_date: Date to calculate for
            
        Returns:
            Total number of orders
        """
        try:
            query = "SELECT COUNT(DISTINCT order_id) as total FROM sales WHERE sale_date = %s"
            results = self.db.execute_query(query, (sale_date,))
            total = results[0]['total'] if results else 0
            logger.info(f"Total orders for {sale_date}: {total}")
            return total
            
        except DatabaseError as e:
            logger.error(f"Failed to calculate total orders: {str(e)}")
            raise SalesError(f"Failed to calculate total orders: {str(e)}")

    def calculate_total_quantity(self, sale_date: date) -> int:
        """
        Calculate total quantity sold for a date.
        
        Args:
            sale_date: Date to calculate for
            
        Returns:
            Total quantity sold
        """
        try:
            query = "SELECT COALESCE(SUM(quantity), 0) as total FROM sales WHERE sale_date = %s"
            results = self.db.execute_query(query, (sale_date,))
            total = results[0]['total'] if results else 0
            logger.info(f"Total quantity for {sale_date}: {total}")
            return total
            
        except DatabaseError as e:
            logger.error(f"Failed to calculate total quantity: {str(e)}")
            raise SalesError(f"Failed to calculate total quantity: {str(e)}")

    def calculate_total_revenue(self, sale_date: date) -> float:
        """
        Calculate total revenue for a date.
        
        Args:
            sale_date: Date to calculate for
            
        Returns:
            Total revenue
        """
        try:
            query = "SELECT COALESCE(SUM(total_amount), 0) as total FROM sales WHERE sale_date = %s"
            results = self.db.execute_query(query, (sale_date,))
            total = float(results[0]['total']) if results else 0.0
            logger.info(f"Total revenue for {sale_date}: ${total:.2f}")
            return total
            
        except DatabaseError as e:
            logger.error(f"Failed to calculate total revenue: {str(e)}")
            raise SalesError(f"Failed to calculate total revenue: {str(e)}")

    def calculate_average_order_value(self, sale_date: date) -> float:
        """
        Calculate average order value for a date.
        
        Args:
            sale_date: Date to calculate for
            
        Returns:
            Average order value
        """
        try:
            query = """
                SELECT 
                    COALESCE(AVG(order_total), 0) as avg_value
                FROM (
                    SELECT 
                        order_id,
                        SUM(total_amount) as order_total
                    FROM sales
                    WHERE sale_date = %s
                    GROUP BY order_id
                ) as order_totals
            """
            results = self.db.execute_query(query, (sale_date,))
            avg_value = float(results[0]['avg_value']) if results else 0.0
            logger.info(f"Average order value for {sale_date}: ${avg_value:.2f}")
            return avg_value
            
        except DatabaseError as e:
            logger.error(f"Failed to calculate average order value: {str(e)}")
            raise SalesError(f"Failed to calculate average order value: {str(e)}")

    def get_top_product(self, sale_date: date) -> Optional[Dict[str, Any]]:
        """
        Get the top-selling product by revenue for a date.
        
        Args:
            sale_date: Date to query
            
        Returns:
            Dictionary with product name and revenue, or None if no sales
        """
        try:
            query = """
                SELECT 
                    product_name,
                    SUM(total_amount) as total_revenue,
                    SUM(quantity) as total_quantity
                FROM sales
                WHERE sale_date = %s
                GROUP BY product_name
                ORDER BY total_revenue DESC
                LIMIT 1
            """
            results = self.db.execute_query(query, (sale_date,))
            
            if results:
                top_product = {
                    'name': results[0]['product_name'],
                    'revenue': float(results[0]['total_revenue']),
                    'quantity': int(results[0]['total_quantity'])
                }
                logger.info(f"Top product for {sale_date}: {top_product['name']}")
                return top_product
            
            logger.info(f"No sales data for {sale_date}")
            return None
            
        except DatabaseError as e:
            logger.error(f"Failed to get top product: {str(e)}")
            raise SalesError(f"Failed to get top product: {str(e)}")

    def get_top_category(self, sale_date: date) -> Optional[Dict[str, Any]]:
        """
        Get the top-selling category by revenue for a date.
        
        Args:
            sale_date: Date to query
            
        Returns:
            Dictionary with category name and revenue, or None if no sales
        """
        try:
            query = """
                SELECT 
                    category,
                    SUM(total_amount) as total_revenue,
                    COUNT(DISTINCT order_id) as order_count
                FROM sales
                WHERE sale_date = %s
                GROUP BY category
                ORDER BY total_revenue DESC
                LIMIT 1
            """
            results = self.db.execute_query(query, (sale_date,))
            
            if results:
                top_category = {
                    'name': results[0]['category'],
                    'revenue': float(results[0]['total_revenue']),
                    'order_count': int(results[0]['order_count'])
                }
                logger.info(f"Top category for {sale_date}: {top_category['name']}")
                return top_category
            
            logger.info(f"No sales data for {sale_date}")
            return None
            
        except DatabaseError as e:
            logger.error(f"Failed to get top category: {str(e)}")
            raise SalesError(f"Failed to get top category: {str(e)}")

    def get_sales_by_category(self, sale_date: date) -> List[Dict[str, Any]]:
        """
        Get sales breakdown by category for a date.
        
        Args:
            sale_date: Date to query
            
        Returns:
            List of category sales data
        """
        try:
            query = """
                SELECT 
                    category,
                    SUM(total_amount) as total_revenue,
                    SUM(quantity) as total_quantity,
                    COUNT(DISTINCT order_id) as order_count
                FROM sales
                WHERE sale_date = %s
                GROUP BY category
                ORDER BY total_revenue DESC
            """
            results = self.db.execute_query(query, (sale_date,))
            
            categories = []
            for row in results:
                categories.append({
                    'category': row['category'],
                    'revenue': float(row['total_revenue']),
                    'quantity': int(row['total_quantity']),
                    'order_count': int(row['order_count'])
                })
            
            logger.info(f"Retrieved sales for {len(categories)} categories")
            return categories
            
        except DatabaseError as e:
            logger.error(f"Failed to get sales by category: {str(e)}")
            raise SalesError(f"Failed to get sales by category: {str(e)}")

    def generate_report(self, sale_date: date, environment: str) -> str:
        """
        Generate a comprehensive daily sales report.
        
        Args:
            sale_date: Date to generate report for
            environment: Environment name (dev, staging, prod)
            
        Returns:
            Formatted report string
        """
        logger.info(f"Generating sales report for {sale_date} in {environment}")
        
        try:
            # Calculate all metrics
            total_orders = self.calculate_total_orders(sale_date)
            total_quantity = self.calculate_total_quantity(sale_date)
            total_revenue = self.calculate_total_revenue(sale_date)
            avg_order_value = self.calculate_average_order_value(sale_date)
            top_product = self.get_top_product(sale_date)
            top_category = self.get_top_category(sale_date)
            sales_by_category = self.get_sales_by_category(sale_date)
            
            # Build report
            report_lines = [
                "=" * 50,
                "       DAILY SALES REPORT",
                "=" * 50,
                f"Date: {sale_date.strftime('%Y-%m-%d')}",
                f"Environment: {environment}",
                "",
                "SUMMARY",
                "-" * 50,
                f"Total Orders: {total_orders}",
                f"Total Quantity: {total_quantity}",
                f"Total Revenue: ${total_revenue:,.2f}",
                f"Average Order Value: ${avg_order_value:,.2f}",
                "",
                "TOP PERFORMERS",
                "-" * 50,
            ]
            
            if top_product:
                report_lines.append(f"Top Product: {top_product['name']} (${top_product['revenue']:,.2f})")
            else:
                report_lines.append("Top Product: N/A")
            
            if top_category:
                report_lines.append(f"Top Category: {top_category['name']} (${top_category['revenue']:,.2f})")
            else:
                report_lines.append("Top Category: N/A")
            
            if sales_by_category:
                report_lines.extend([
                    "",
                    "SALES BY CATEGORY",
                    "-" * 50,
                ])
                for cat in sales_by_category:
                    report_lines.append(
                        f"{cat['category']}: ${cat['revenue']:,.2f} ({cat['quantity']} units)"
                    )
            
            report_lines.extend([
                "",
                "=" * 50,
                f"Generated by: AWS Lambda",
                f"Timestamp: {datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}",
                "=" * 50,
            ])
            
            report = "\n".join(report_lines)
            logger.info("Sales report generated successfully")
            return report
            
        except SalesError as e:
            logger.error(f"Failed to generate sales report: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error generating report: {str(e)}")
            raise SalesError(f"Failed to generate report: {str(e)}")