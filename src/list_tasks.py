"""
list_tasks.py — GET /tasks
Returns all tasks for a user, with optional status filter.

Query parameters:
  status   (optional): PENDING | IN_PROGRESS | DONE
  limit    (optional): max items to return (default 50)

Headers:
  X-User-Id: user123   (required)
"""

import json
import os
import logging
from boto3.dynamodb.conditions import Key, Attr
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])


def build_response(status_code, body):
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*',
        },
        'body': json.dumps(body)
    }


def handler(event, context):
    headers = event.get('headers') or {}
    user_id = headers.get('X-User-Id') or headers.get('x-user-id')
    if not user_id:
        return build_response(400, {'error': 'Missing required header: X-User-Id'})

    params = event.get('queryStringParameters') or {}
    status_filter = params.get('status', '').upper()
    limit = min(int(params.get('limit', 50)), 100)

    valid_statuses = ('PENDING', 'IN_PROGRESS', 'DONE')
    if status_filter and status_filter not in valid_statuses:
        return build_response(400, {
            'error': f'status must be one of: {", ".join(valid_statuses)}'
        })

    try:
        kwargs = {
            'KeyConditionExpression': Key('userId').eq(user_id),
            'Limit': limit,
            'ScanIndexForward': False  # newest first
        }
        if status_filter:
            kwargs['FilterExpression'] = Attr('status').eq(status_filter)

        response = table.query(**kwargs)
        tasks = response.get('Items', [])

    except ClientError as e:
        logger.error("DynamoDB error: %s", e.response['Error']['Message'])
        return build_response(500, {'error': 'Failed to list tasks'})

    return build_response(200, {
        'tasks': tasks,
        'count': len(tasks),
        'userId': user_id
    })
