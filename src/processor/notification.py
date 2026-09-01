"""
Notification module for S214 Sales Platform.

This module handles all notification operations including:
- SNS topic publishing
- Email notification formatting
- Error handling for notification failures
"""

import logging
import boto3
from typing import Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class NotificationError(Exception):
    """Custom exception for notification operations."""
    pass


class NotificationService:
    """
    Handles sending notifications via Amazon SNS.
    
    Publishes sales reports to an SNS topic which can be
    configured to send email notifications to subscribers.
    """

    def __init__(self, topic_arn: str, region: str = 'us-east-1'):
        """
        Initialize the NotificationService.
        
        Args:
            topic_arn: ARN of the SNS topic
            region: AWS region where the topic is located
        """
        self.topic_arn = topic_arn
        self.region = region
        self.sns_client = boto3.client('sns', region_name=region)

    def send_report(self, report: str, subject: Optional[str] = None) -> str:
        """
        Send a sales report via SNS.
        
        Args:
            report: The report content to send
            subject: Optional email subject line
            
        Returns:
            Message ID of the published message
            
        Raises:
            NotificationError: If publishing fails
        """
        if not subject:
            subject = "Daily Sales Report"
        
        try:
            response = self.sns_client.publish(
                TopicArn=self.topic_arn,
                Subject=subject[:100],  # SNS subject limit is 100 characters
                Message=report,
                MessageAttributes={
                    'report_type': {
                        'DataType': 'String',
                        'StringValue': 'daily_sales_report'
                    }
                }
            )
            
            message_id = response['MessageId']
            logger.info(f"Report sent successfully. Message ID: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to send report via SNS: {str(e)}")
            raise NotificationError(f"Failed to send report: {str(e)}")

    def send_error_notification(self, error_message: str, environment: str) -> str:
        """
        Send an error notification via SNS.
        
        Args:
            error_message: The error message to send
            environment: Environment where the error occurred
            
        Returns:
            Message ID of the published message
            
        Raises:
            NotificationError: If publishing fails
        """
        subject = f"ALERT: Sales Processing Error - {environment}"
        
        message = f"""
SALES PROCESSING ERROR
======================

Environment: {environment}
Timestamp: {__import__('datetime').datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%SZ')}

Error Details:
{error_message}

Please investigate the issue in CloudWatch Logs.
"""
        
        try:
            response = self.sns_client.publish(
                TopicArn=self.topic_arn,
                Subject=subject[:100],
                Message=message,
                MessageAttributes={
                    'report_type': {
                        'DataType': 'String',
                        'StringValue': 'error_notification'
                    }
                }
            )
            
            message_id = response['MessageId']
            logger.info(f"Error notification sent. Message ID: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"Failed to send error notification: {str(e)}")
            raise NotificationError(f"Failed to send error notification: {str(e)}")