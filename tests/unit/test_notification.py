"""
Unit tests for the NotificationService class.

Tests cover:
- SNS report publishing
- Error notification sending
- Error handling
"""

import pytest
from unittest.mock import MagicMock, patch
import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../src/processor"))

from notification import NotificationService, NotificationError


@pytest.fixture
def mock_sns_client():
    """Create a mock SNS client."""
    with patch("boto3.client") as mock_boto:
        mock_client = MagicMock()
        mock_boto.return_value = mock_client
        yield mock_client


@pytest.fixture
def notification_service(mock_sns_client):
    """Create a NotificationService instance with mock SNS client."""
    with patch("boto3.client", return_value=mock_sns_client):
        service = NotificationService(
            topic_arn="arn:aws:sns:us-east-1:123456789012:test-topic",
            region="us-east-1",
        )
        yield service


class TestSendReport:
    """Tests for send_report method."""

    def test_send_report_success(self, notification_service, mock_sns_client):
        """Test successful report sending."""
        mock_sns_client.publish.return_value = {"MessageId": "test-message-id-123"}

        report = "Test sales report content"
        message_id = notification_service.send_report(report)

        assert message_id == "test-message-id-123"
        mock_sns_client.publish.assert_called_once()

    def test_send_report_with_custom_subject(
        self, notification_service, mock_sns_client
    ):
        """Test report sending with custom subject."""
        mock_sns_client.publish.return_value = {"MessageId": "test-message-id-456"}

        report = "Test report"
        subject = "Custom Subject Line"
        message_id = notification_service.send_report(report, subject=subject)

        assert message_id == "test-message-id-456"

        # Verify subject was passed
        call_args = mock_sns_client.publish.call_args
        assert call_args[1]["Subject"] == subject

    def test_send_report_default_subject(self, notification_service, mock_sns_client):
        """Test report sending with default subject."""
        mock_sns_client.publish.return_value = {"MessageId": "test-message-id-789"}

        notification_service.send_report("Test report")

        # Verify default subject was used
        call_args = mock_sns_client.publish.call_args
        assert call_args[1]["Subject"] == "Daily Sales Report"

    def test_send_report_long_subject_truncated(
        self, notification_service, mock_sns_client
    ):
        """Test that long subjects are truncated to 100 characters."""
        mock_sns_client.publish.return_value = {"MessageId": "test-message-id-012"}

        long_subject = "A" * 150
        notification_service.send_report("Test report", subject=long_subject)

        # Verify subject was truncated
        call_args = mock_sns_client.publish.call_args
        assert len(call_args[1]["Subject"]) == 100

    def test_send_report_sns_error(self, notification_service, mock_sns_client):
        """Test report sending with SNS error."""
        mock_sns_client.publish.side_effect = Exception("SNS service unavailable")

        with pytest.raises(NotificationError, match="Failed to send report"):
            notification_service.send_report("Test report")

    def test_send_report_includes_message_attributes(
        self, notification_service, mock_sns_client
    ):
        """Test that report includes message attributes."""
        mock_sns_client.publish.return_value = {"MessageId": "test-message-id-345"}

        notification_service.send_report("Test report")

        # Verify message attributes
        call_args = mock_sns_client.publish.call_args
        assert "MessageAttributes" in call_args[1]
        assert (
            call_args[1]["MessageAttributes"]["report_type"]["StringValue"]
            == "daily_sales_report"
        )


class TestSendErrorNotification:
    """Tests for send_error_notification method."""

    def test_send_error_notification_success(
        self, notification_service, mock_sns_client
    ):
        """Test successful error notification sending."""
        mock_sns_client.publish.return_value = {"MessageId": "error-message-id-123"}

        error_message = "Database connection failed"
        message_id = notification_service.send_error_notification(error_message, "dev")

        assert message_id == "error-message-id-123"
        mock_sns_client.publish.assert_called_once()

    def test_send_error_notification_includes_environment(
        self, notification_service, mock_sns_client
    ):
        """Test that error notification includes environment."""
        mock_sns_client.publish.return_value = {"MessageId": "error-message-id-456"}

        notification_service.send_error_notification("Test error", "staging")

        # Verify environment is in the message
        call_args = mock_sns_client.publish.call_args
        assert "staging" in call_args[1]["Message"]

    def test_send_error_notification_includes_error_details(
        self, notification_service, mock_sns_client
    ):
        """Test that error notification includes error details."""
        mock_sns_client.publish.return_value = {"MessageId": "error-message-id-789"}

        error_details = "Connection timeout after 30 seconds"
        notification_service.send_error_notification(error_details, "prod")

        # Verify error details are in the message
        call_args = mock_sns_client.publish.call_args
        assert error_details in call_args[1]["Message"]

    def test_send_error_notification_sns_error(
        self, notification_service, mock_sns_client
    ):
        """Test error notification with SNS error."""
        mock_sns_client.publish.side_effect = Exception("SNS service unavailable")

        with pytest.raises(
            NotificationError, match="Failed to send error notification"
        ):
            notification_service.send_error_notification("Test error", "dev")

    def test_send_error_notification_subject_format(
        self, notification_service, mock_sns_client
    ):
        """Test error notification subject format."""
        mock_sns_client.publish.return_value = {"MessageId": "error-message-id-012"}

        notification_service.send_error_notification("Test error", "dev")

        # Verify subject format
        call_args = mock_sns_client.publish.call_args
        assert "ALERT" in call_args[1]["Subject"]
        assert "dev" in call_args[1]["Subject"]
