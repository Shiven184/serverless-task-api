# tests/test_lambda_functions.py
#
# These are unit tests for your Lambda functions.
# They run locally (no AWS connection needed) by mocking DynamoDB.
#
# The pipeline runs these before every deployment.
# If any test fails, the deployment stops.

import json
import pytest
from unittest.mock import patch, MagicMock
import os

# Set environment variables that Lambda functions expect
os.environ['TABLE_NAME'] = 'tasks-test'
os.environ['LOG_LEVEL']  = 'ERROR'

import sys
sys.path.insert(0, 'src')


class TestCreateTask:

    def _make_event(self, body, user_id='user-test'):
        return {
            'headers': {'X-User-Id': user_id},
            'body': json.dumps(body)
        }

    @patch('create_task.table')
    def test_create_task_success(self, mock_table):
        mock_table.put_item.return_value = {}
        from create_task import handler
        event = self._make_event({'title': 'Test task', 'priority': 'HIGH'})
        result = handler(event, None)
        assert result['statusCode'] == 201
        body = json.loads(result['body'])
        assert body['task']['title'] == 'Test task'
        assert body['task']['status'] == 'PENDING'
        assert body['task']['priority'] == 'HIGH'

    @patch('create_task.table')
    def test_create_task_missing_title(self, mock_table):
        from create_task import handler
        event = self._make_event({'priority': 'LOW'})
        result = handler(event, None)
        assert result['statusCode'] == 400
        body = json.loads(result['body'])
        assert 'title' in body['error']

    @patch('create_task.table')
    def test_create_task_invalid_priority(self, mock_table):
        from create_task import handler
        event = self._make_event({'title': 'Test', 'priority': 'URGENT'})
        result = handler(event, None)
        assert result['statusCode'] == 400

    def test_create_task_missing_user_id(self):
        from create_task import handler
        event = {'headers': {}, 'body': json.dumps({'title': 'Test'})}
        result = handler(event, None)
        assert result['statusCode'] == 400
        assert 'X-User-Id' in json.loads(result['body'])['error']

    @patch('create_task.table')
    def test_create_task_title_too_long(self, mock_table):
        from create_task import handler
        event = self._make_event({'title': 'A' * 201})
        result = handler(event, None)
        assert result['statusCode'] == 400


class TestListTasks:

    def _make_event(self, user_id='user-test', query_params=None):
        return {
            'headers': {'X-User-Id': user_id},
            'queryStringParameters': query_params or {}
        }

    @patch('list_tasks.table')
    def test_list_tasks_success(self, mock_table):
        mock_table.query.return_value = {
            'Items': [
                {'userId': 'user-test', 'taskId': 'abc', 'title': 'Task 1', 'status': 'PENDING'}
            ]
        }
        from list_tasks import handler
        result = handler(self._make_event(), None)
        assert result['statusCode'] == 200
        body = json.loads(result['body'])
        assert body['count'] == 1
        assert body['tasks'][0]['title'] == 'Task 1'

    @patch('list_tasks.table')
    def test_list_tasks_empty(self, mock_table):
        mock_table.query.return_value = {'Items': []}
        from list_tasks import handler
        result = handler(self._make_event(), None)
        assert result['statusCode'] == 200
        assert json.loads(result['body'])['count'] == 0

    def test_list_tasks_invalid_status(self):
        from list_tasks import handler
        event = self._make_event(query_params={'status': 'INVALID'})
        result = handler(event, None)
        assert result['statusCode'] == 400


class TestGetTask:

    def _make_event(self, task_id='task-123', user_id='user-test'):
        return {
            'headers': {'X-User-Id': user_id},
            'pathParameters': {'taskId': task_id}
        }

    @patch('get_task.table')
    def test_get_task_found(self, mock_table):
        mock_table.get_item.return_value = {
            'Item': {'userId': 'user-test', 'taskId': 'task-123', 'title': 'Found task'}
        }
        from get_task import handler
        result = handler(self._make_event(), None)
        assert result['statusCode'] == 200
        assert json.loads(result['body'])['task']['title'] == 'Found task'

    @patch('get_task.table')
    def test_get_task_not_found(self, mock_table):
        mock_table.get_item.return_value = {}
        from get_task import handler
        result = handler(self._make_event(), None)
        assert result['statusCode'] == 404


class TestDeleteTask:

    def _make_event(self, task_id='task-123', user_id='user-test'):
        return {
            'headers': {'X-User-Id': user_id},
            'pathParameters': {'taskId': task_id}
        }

    @patch('delete_task.table')
    def test_delete_task_success(self, mock_table):
        mock_table.delete_item.return_value = {}
        from delete_task import handler
        result = handler(self._make_event(), None)
        assert result['statusCode'] == 200
        assert 'deleted' in json.loads(result['body'])['message'].lower()

    @patch('delete_task.table')
    def test_delete_task_not_found(self, mock_table):
        from botocore.exceptions import ClientError
        mock_table.delete_item.side_effect = ClientError(
            {'Error': {'Code': 'ConditionalCheckFailedException', 'Message': 'Condition failed'}},
            'DeleteItem'
        )
        from delete_task import handler
        result = handler(self._make_event(), None)
        assert result['statusCode'] == 404

    def test_delete_task_missing_user_id(self):
        from delete_task import handler
        event = {'headers': {}, 'pathParameters': {'taskId': 'task-123'}}
        result = handler(event, None)
        assert result['statusCode'] == 400


class TestResponseHeaders:
    """Verify CORS headers are present on all responses."""

    @patch('create_task.table')
    def test_cors_headers_present(self, mock_table):
        mock_table.put_item.return_value = {}
        from create_task import handler
        event = {
            'headers': {'X-User-Id': 'user-test'},
            'body': json.dumps({'title': 'Test'})
        }
        result = handler(event, None)
        assert 'Access-Control-Allow-Origin' in result['headers']
        assert result['headers']['Access-Control-Allow-Origin'] == '*'
