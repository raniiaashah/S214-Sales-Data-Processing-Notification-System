"""
CloudFormation Custom Resource Lambda for S214 Sales Platform.

This Lambda function handles CloudFormation custom resource lifecycle events:
- Create: Initialize database schema and insert sample data
- Update: Re-initialize if configuration changes
- Delete: Clean up sample data

The custom resource ensures the database is ready before the stack completes deployment.

Why use a Custom Resource?
- CloudFormation doesn't natively support database initialization
- RDS creation doesn't include schema setup
- Sample data needs to be inserted after RDS is available
- This provides a way to run initialization code as part of stack deployment
"""

import logging
import os
import json
import cfnresponse
from database import DatabaseInitializer, DatabaseInitializationError

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Environment variables
SECRET_ARN = os.environ.get("SECRET_ARN")
AWS_REGION = os.environ.get("AWS_REGION", "us-east-1")


def lambda_handler(event: dict, context: dict) -> None:
    """
    Handle CloudFormation custom resource events.

    Args:
        event: CloudFormation custom resource event
        context: Lambda context object
    """
    logger.info("=" * 60)
    logger.info("Custom Resource Lambda - Event received")
    logger.info(f"Request Type: {event.get('RequestType')}")
    logger.info(
        f"Resource Properties: {json.dumps(event.get('ResourceProperties', {}))}"
    )
    logger.info("=" * 60)

    request_type = event["RequestType"]
    resource_properties = event.get("ResourceProperties", {})
    physical_resource_id = event.get("PhysicalResourceId", "")

    response_data = {}
    physical_id = physical_resource_id

    try:
        if request_type == "Create":
            response_data, physical_id = handle_create(resource_properties)

        elif request_type == "Update":
            response_data, physical_id = handle_update(
                resource_properties, physical_resource_id
            )

        elif request_type == "Delete":
            response_data = handle_delete(resource_properties)

        else:
            raise ValueError(f"Unknown request type: {request_type}")

        # Send success response to CloudFormation
        cfnresponse.send(
            event, context, cfnresponse.SUCCESS, response_data, physical_id
        )
        logger.info(f"Custom resource {request_type} completed successfully")

    except Exception as e:
        logger.error(f"Custom resource {request_type} failed: {str(e)}", exc_info=True)

        # Send failure response to CloudFormation
        cfnresponse.send(
            event, context, cfnresponse.FAILED, {"Error": str(e)}, physical_id
        )


def handle_create(resource_properties: dict) -> tuple:
    """
    Handle Create request - initialize database.

    Args:
        resource_properties: Custom resource properties

    Returns:
        Tuple of (response_data, physical_resource_id)
    """
    logger.info("Handling Create request - initializing database")

    initializer = DatabaseInitializer(
        SECRET_ARN,
        AWS_REGION,
        host=resource_properties["DatabaseHost"],
        port=int(resource_properties.get("DatabasePort", 3306)),
    )
    result = initializer.initialize()

    response_data = {
        "Message": "Database initialized successfully",
        "TablesCreated": str(result["tables_created"]),
        "RecordsInserted": str(result["records_inserted"]),
    }

    physical_id = f"s214-db-init-{result['records_inserted']}-records"

    logger.info(f"Create completed: {response_data}")
    return response_data, physical_id


def handle_update(resource_properties: dict, physical_resource_id: str) -> tuple:
    """
    Handle Update request - re-initialize database if needed.

    Args:
        resource_properties: Custom resource properties
        physical_resource_id: Current physical resource ID

    Returns:
        Tuple of (response_data, physical_resource_id)
    """
    logger.info("Handling Update request - re-initializing database")

    initializer = DatabaseInitializer(
        SECRET_ARN,
        AWS_REGION,
        host=resource_properties["DatabaseHost"],
        port=int(resource_properties.get("DatabasePort", 3306)),
    )
    result = initializer.initialize()

    response_data = {
        "Message": "Database re-initialized successfully",
        "TablesCreated": str(result["tables_created"]),
        "RecordsInserted": str(result["records_inserted"]),
    }

    physical_id = f"s214-db-init-{result['records_inserted']}-records"

    logger.info(f"Update completed: {response_data}")
    return response_data, physical_id


def handle_delete(resource_properties: dict) -> dict:
    """
    Handle Delete request - clean up sample data.

    Args:
        resource_properties: Custom resource properties

    Returns:
        Response data dictionary
    """
    logger.info("Handling Delete request - cleaning up database")

    initializer = DatabaseInitializer(
        SECRET_ARN,
        AWS_REGION,
        host=resource_properties["DatabaseHost"],
        port=int(resource_properties.get("DatabasePort", 3306)),
    )
    initializer.cleanup()

    response_data = {"Message": "Database cleanup completed successfully"}

    logger.info(f"Delete completed: {response_data}")
    return response_data
