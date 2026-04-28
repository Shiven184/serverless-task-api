"""
update_task.py — PUT /tasks/{taskId}
Body: { "title": "...", "status": "IN_PROGRESS", "description": "..." }
"""
import json, os, logging, boto3
from datetime import datetime, timezone
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['TABLE_NAME'])

def build_response(code, body):
    return {'statusCode': code, 'headers': {'Content-Type': 'application/json', 'Access-Control-Allow-Origin': '*'}, 'body': json.dumps(body)}

def handler(event, context):
    headers = event.get('headers') or {}
    user_id = headers.get('X-User-Id') or headers.get('x-user-id')
    if not user_id:
        return build_response(400, {'error': 'Missing header: X-User-Id'})
    task_id = (event.get('pathParameters') or {}).get('taskId')
    try:
        body = json.loads(event.get('body') or '{}')
    except json.JSONDecodeError:
        return build_response(400, {'error': 'Invalid JSON'})

    allowed_statuses = ('PENDING', 'IN_PROGRESS', 'DONE')
    updates, expr_attrs = [], {}

    if 'title' in body:
        updates.append('title = :title')
        expr_attrs[':title'] = body['title']
    if 'description' in body:
        updates.append('description = :desc')
        expr_attrs[':desc'] = body['description']
    if 'status' in body:
        if body['status'].upper() not in allowed_statuses:
            return build_response(400, {'error': f'status must be one of {allowed_statuses}'})
        updates.append('#s = :status')
        expr_attrs[':status'] = body['status'].upper()
    if not updates:
        return build_response(400, {'error': 'No valid fields to update'})

    updates.append('updatedAt = :now')
    expr_attrs[':now'] = datetime.now(timezone.utc).isoformat()

    try:
        resp = table.update_item(
            Key={'userId': user_id, 'taskId': task_id},
            UpdateExpression='SET ' + ', '.join(updates),
            ExpressionAttributeValues=expr_attrs,
            ExpressionAttributeNames={'#s': 'status'} if 'status' in body else {},
            ConditionExpression='attribute_exists(taskId)',
            ReturnValues='ALL_NEW'
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return build_response(404, {'error': f'Task {task_id} not found'})
        return build_response(500, {'error': 'DynamoDB error'})

    return build_response(200, {'message': 'Task updated', 'task': resp['Attributes']})
