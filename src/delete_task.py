"""
delete_task.py — DELETE /tasks/{taskId}
"""
import json, os, logging, boto3
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
    if not task_id:
        return build_response(400, {'error': 'Missing path parameter: taskId'})
    try:
        table.delete_item(
            Key={'userId': user_id, 'taskId': task_id},
            ConditionExpression='attribute_exists(taskId)'
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
            return build_response(404, {'error': f'Task {task_id} not found'})
        return build_response(500, {'error': 'DynamoDB error'})
    logger.info("Task deleted: userId=%s taskId=%s", user_id, task_id)
    return build_response(200, {'message': f'Task {task_id} deleted successfully'})
