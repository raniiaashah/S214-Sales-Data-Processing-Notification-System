"""CloudFormation custom-resource response helper for zip-based Lambdas."""

import json
import logging

import requests


SUCCESS = "SUCCESS"
FAILED = "FAILED"
logger = logging.getLogger(__name__)


def send(event, context, response_status, response_data, physical_resource_id=None):
    """Send the custom-resource result to CloudFormation's response URL."""
    response_url = event["ResponseURL"]
    physical_id = physical_resource_id or getattr(context, "log_stream_name", "custom-resource")
    response_body = json.dumps(
        {
            "Status": response_status,
            "Reason": f"See details in CloudWatch Log Stream: {physical_id}",
            "PhysicalResourceId": physical_id,
            "StackId": event["StackId"],
            "RequestId": event["RequestId"],
            "LogicalResourceId": event["LogicalResourceId"],
            "Data": response_data,
        }
    )

    response = requests.put(
        response_url,
        data=response_body,
        headers={"content-type": "", "content-length": str(len(response_body))},
        timeout=30,
    )
    response.raise_for_status()
    logger.info("Sent %s response to CloudFormation", response_status)
