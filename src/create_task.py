"""
create_task.py — POST /tasks
Creates a new task item in DynamoDB.

Request body:
  {
    "title": "Buy groceries",
    "description": "Milk, eggs, bread",  (optional)
    "priority": "HIGH"                   (optional: LOW | MEDIUM | HIGH)
  }

Headers:
  X-User-Id: user123   (required - identifies the user)
"""

import json
import os
import uuid
import logging
from datetime import datetime, timezone

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError

# ── Logging setup ────────────────────────────────────────────────────────────
logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

# ── DynamoDB client (reused across warm Lambda invocations) ──────────────────
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])


def build_response(status_code: int, body: dict) -> dict:
    """Build a standard API Gateway response with CORS headers."""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type,X-User-Id',
        },
        'body': json.dumps(body)
    }


def handler(event: dict, context) -> dict:
    """
    Lambda handler for POST /tasks.
    Creates a new task and stores it in DynamoDB.
    """
    logger.info("CreateTask invoked: %s", json.dumps(event))

    # ── Extract user ID from header ──────────────────────────────────────────
    headers = event.get('headers') or {}
    user_id = headers.get('X-User-Id') or headers.get('x-user-id')

    if not user_id:
        return build_response(400, {
            'error': 'Missing required header: X-User-Id'
        })

    # ── Parse and validate request body ─────────────────────────────────────
    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return build_response(400, {'error': 'Invalid JSON body'})

    title = body.get('title', '').strip()
    if not title:
        return build_response(400, {'error': 'Missing required field: title'})

    if len(title) > 200:
        return build_response(400, {'error': 'title must be 200 characters or fewer'})

    priority = body.get('priority', 'MEDIUM').upper()
    if priority not in ('LOW', 'MEDIUM', 'HIGH'):
        return build_response(400, {'error': 'priority must be LOW, MEDIUM, or HIGH'})

    # ── Build DynamoDB item ──────────────────────────────────────────────────
    now = datetime.now(timezone.utc).isoformat()
    task_id = str(uuid.uuid4())

    item = {
        'userId':      user_id,
        'taskId':      task_id,
        'title':       title,
        'description': body.get('description', ''),
        'status':      'PENDING',
        'priority':    priority,
        'createdAt':   now,
        'updatedAt':   now,
    }

    # ── Write to DynamoDB ────────────────────────────────────────────────────
    try:
        table.put_item(
            Item=item,
            ConditionExpression='attribute_not_exists(taskId)'  # prevent overwrite
        )
    except ClientError as e:
        logger.error("DynamoDB error: %s", e.response['Error']['Message'])
        return build_response(500, {'error': 'Failed to create task'})

    logger.info("Task created: userId=%s taskId=%s", user_id, task_id)

    return build_response(201, {
        'message': 'Task created successfully',
        'task': item
    })
