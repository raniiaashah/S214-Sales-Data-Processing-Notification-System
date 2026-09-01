"""
Main Lambda handler for S214 Sales Platform.

This module orchestrates the sales processing workflow:
1. Retrieve database credentials from Secrets Manager
2. Connect to RDS and fetch sales data
3. Calculate business metrics
4. Generate sales report
5. Send report via SNS

Environment Variables:
    SECRET_ARN: ARN of the Secrets Manager secret
    SNS_TOPIC_ARN: ARN of the SNS topic
    ENVIRONMENT: Environment name (dev, staging, prod)
    AWS_REGION: AWS region (default: us-east-1)
"""

import logging
import os
from datetime import date, timedelta

from database import Database, DatabaseError
from sales import SalesProcessor, SalesError
from notification import NotificationService, NotificationError

# Configure logging
log_level = os.environ.get('LOG_LEVEL', 'INFO')
logger = logging.getLogger()
logger.setLevel(getattr(logging, log_level))

# Environment variables
SECRET_ARN = os.environ.get('SECRET_ARN')
SNS_TOPIC_ARN = os.environ.get('SNS_TOPIC_ARN')
ENVIRONMENT = os.environ.get('ENVIRONMENT', 'dev')
AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')


def validate_environment() -> None:
    """
    Validate that all required environment variables are set.
    
    Raises:
        ValueError: If required environment variables are missing
    """
    required_vars = {
        'SECRET_ARN': SECRET_ARN,
        'SNS_TOPIC_ARN': SNS_TOPIC_ARN,
        'ENVIRONMENT': ENVIRONMENT
    }
    
    missing = [key for key, value in required_vars.items() if not value]
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")


def lambda_handler(event: dict, context: dict) -> dict:
    """
    Main Lambda handler function.
    
    Processes daily sales data and sends a report via SNS.
    
    Args:
        event: EventBridge event (scheduled trigger)
        context: Lambda context object
        
    Returns:
        Dictionary with processing results
        
    Raises:
        Exception: If processing fails
    """
    logger.info("=" * 60)
    logger.info("Sales Processor Lambda - Starting execution")
    logger.info(f"Environment: {ENVIRONMENT}")
    logger.info(f"Region: {AWS_REGION}")
    logger.info("=" * 60)
    
    # Validate environment
    try:
        validate_environment()
    except ValueError as e:
        logger.error(f"Environment validation failed: {str(e)}")
        raise
    
    # Determine report date (default to yesterday)
    report_date = date.today() - timedelta(days=1)
    if event and 'date' in event:
        try:
            report_date = date.fromisoformat(event['date'])
        except (ValueError, TypeError):
            logger.warning(f"Invalid date in event, using default: {report_date}")
    
    logger.info(f"Generating report for: {report_date}")
    
    # Initialize services
    db = Database(SECRET_ARN, AWS_REGION)
    notification_service = NotificationService(SNS_TOPIC_ARN, AWS_REGION)
    
    try:
        # Connect to database and process sales
        with db:
            sales_processor = SalesProcessor(db)
            
            # Generate the sales report
            logger.info("Generating sales report...")
            report = sales_processor.generate_report(report_date, ENVIRONMENT)
            
            # Log report summary
            logger.info("Report generated successfully")
            logger.info(f"Report length: {len(report)} characters")
        
        # Send report via SNS (outside DB context to free connection)
        logger.info("Sending report via SNS...")
        subject = f"Daily Sales Report - {report_date.strftime('%Y-%m-%d')} - {ENVIRONMENT}"
        message_id = notification_service.send_report(report, subject)
        
        logger.info(f"Report sent successfully. Message ID: {message_id}")
        logger.info("=" * 60)
        logger.info("Sales Processor Lambda - Execution completed successfully")
        logger.info("=" * 60)
        
        return {
            'statusCode': 200,
            'body': {
                'message': 'Sales report generated and sent successfully',
                'date': report_date.isoformat(),
                'messageId': message_id,
                'environment': ENVIRONMENT
            }
        }
        
    except DatabaseError as e:
        error_msg = f"Database error: {str(e)}"
        logger.error(error_msg)
        
        # Attempt to send error notification
        try:
            notification_service.send_error_notification(error_msg, ENVIRONMENT)
        except NotificationError:
            logger.error("Failed to send error notification")
        
        raise
        
    except SalesError as e:
        error_msg = f"Sales processing error: {str(e)}"
        logger.error(error_msg)
        
        # Attempt to send error notification
        try:
            notification_service.send_error_notification(error_msg, ENVIRONMENT)
        except NotificationError:
            logger.error("Failed to send error notification")
        
        raise
        
    except NotificationError as e:
        error_msg = f"Notification error: {str(e)}"
        logger.error(error_msg)
        raise
        
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Attempt to send error notification
        try:
            notification_service.send_error_notification(error_msg, ENVIRONMENT)
        except NotificationError:
            logger.error("Failed to send error notification")
        
        raise


if __name__ == '__main__':
    # Local testing
    test_event = {
        'date': (date.today() - timedelta(days=1)).isoformat()
    }
    test_context = {}
    
    result = lambda_handler(test_event, test_context)
    print(result)