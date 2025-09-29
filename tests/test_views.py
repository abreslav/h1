import pytest
import json
import time
from unittest.mock import Mock, patch
from django.test import TestCase, Client
from django.http import HttpRequest, HttpResponse
from django.urls import reverse
from django_app.models import Demo
from django_app.views import log_request_response


class TestViews(TestCase):

    def setUp(self):
        self.client = Client()

    @pytest.mark.timeout(30)
    def test_home_get(self):
        """
        Test kind: endpoint_tests
        Original method: home
        """
        # Test GET request to home endpoint
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

        # Verify template content is rendered
        self.assertContains(response, 'HelloDB Demo')
        self.assertContains(response, 'Add New Demo Record')

    @pytest.mark.timeout(30)
    def test_home_post_valid_data(self):
        """
        Test kind: endpoint_tests
        Original method: home
        """
        # Test POST request with valid data
        data = {
            'name': 'Test Demo',
            'description': 'Test Description'
        }
        response = self.client.post(reverse('home'), data)

        # Should redirect after successful creation
        self.assertEqual(response.status_code, 302)

        # Verify demo was created
        demo = Demo.objects.get(name='Test Demo')
        self.assertEqual(demo.description, 'Test Description')

    @pytest.mark.timeout(30)
    def test_home_post_invalid_data(self):
        """
        Test kind: endpoint_tests
        Original method: home
        """
        # Test POST request with missing name
        data = {
            'name': '',
            'description': 'Test Description'
        }
        response = self.client.post(reverse('home'), data)

        # Should return form with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Both name and description are required.')

        # Verify no demo was created
        self.assertEqual(Demo.objects.count(), 0)

        # Test POST request with missing description
        data = {
            'name': 'Test Demo',
            'description': ''
        }
        response = self.client.post(reverse('home'), data)

        # Should return form with error
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Both name and description are required.')

        # Verify no demo was created
        self.assertEqual(Demo.objects.count(), 0)

    @pytest.mark.timeout(30)
    def test_log_request_response(self):
        """
        Test kind: unit_tests
        Original method: log_request_response
        """
        # Create mock request
        request = Mock(spec=HttpRequest)
        request.method = 'GET'
        request.build_absolute_uri.return_value = 'http://example.com/test'
        request.META = {
            'HTTP_USER_AGENT': 'TestAgent',
            'HTTP_ACCEPT': 'text/html',
            'CONTENT_TYPE': 'application/json',
            'CONTENT_LENGTH': '100',
            'SERVER_NAME': 'testserver'
        }
        request.body = b'test body'

        # Create mock response
        response = Mock(spec=HttpResponse)
        response.status_code = 200
        response.content = b'test response'
        response.items.return_value = [('Content-Type', 'text/html')]

        # Mock logger and time
        start_time = time.time() - 0.1  # 100ms ago

        with patch('django_app.views.logger') as mock_logger, \
             patch('django_app.views.time.time', return_value=time.time()):

            log_request_response(request, response, start_time)

            # Verify logger.info was called
            mock_logger.info.assert_called_once()

            # Parse the logged JSON
            logged_data = json.loads(mock_logger.info.call_args[0][0])

            # Verify logged data structure
            self.assertEqual(logged_data['method'], 'GET')
            self.assertEqual(logged_data['url'], 'http://example.com/test')
            self.assertEqual(logged_data['response_status'], 200)
            self.assertEqual(logged_data['request_body_size'], 9)  # len(b'test body')
            self.assertEqual(logged_data['response_body_size'], 13)  # len(b'test response')
            self.assertGreater(logged_data['processing_duration_ms'], 0)

            # Verify request headers filtering
            expected_headers = {
                'HTTP_USER_AGENT': 'TestAgent',
                'HTTP_ACCEPT': 'text/html',
                'CONTENT_TYPE': 'application/json',
                'CONTENT_LENGTH': '100'
            }
            self.assertEqual(logged_data['request_headers'], expected_headers)

    @pytest.mark.timeout(30)
    def test_log_request_response_error(self):
        """
        Test kind: unit_tests
        Original method: log_request_response
        """
        # Create mock request
        request = Mock(spec=HttpRequest)
        request.method = 'POST'
        request.build_absolute_uri.return_value = 'http://example.com/error'
        request.META = {'CONTENT_LENGTH': '50'}
        request.body = b''

        # Create mock response with error status
        response = Mock(spec=HttpResponse)
        response.status_code = 400
        response.content = b'Bad Request Error'
        response.items.return_value = []

        start_time = time.time()

        with patch('django_app.views.logger') as mock_logger:
            log_request_response(request, response, start_time)

            # Verify logger.info was called
            mock_logger.info.assert_called_once()

            # Parse the logged JSON
            logged_data = json.loads(mock_logger.info.call_args[0][0])

            # Verify error response body is logged
            self.assertEqual(logged_data['response_status'], 400)
            self.assertEqual(logged_data['response_body'], 'Bad Request Error')

    @pytest.mark.timeout(30)
    def test_log_request_response_body_exception(self):
        """
        Test kind: unit_tests
        Original method: log_request_response
        """
        # Create mock request that raises exception when accessing body
        request = Mock(spec=HttpRequest)
        request.method = 'POST'
        request.build_absolute_uri.return_value = 'http://example.com/test'
        request.META = {'CONTENT_LENGTH': '100'}
        request.body.side_effect = Exception("Cannot access body")

        # Create mock response
        response = Mock(spec=HttpResponse)
        response.status_code = 200
        response.content = b'test response'
        response.items.return_value = []

        start_time = time.time()

        with patch('django_app.views.logger') as mock_logger:
            log_request_response(request, response, start_time)

            # Verify logger.info was called
            mock_logger.info.assert_called_once()

            # Parse the logged JSON
            logged_data = json.loads(mock_logger.info.call_args[0][0])

            # Verify request body size falls back to CONTENT_LENGTH
            self.assertEqual(logged_data['request_body_size'], 100)