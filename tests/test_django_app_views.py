import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from django.test import TestCase, RequestFactory, Client
from django.http import HttpResponse
from django.views import View
from django.contrib.auth.models import User
from django.urls import reverse

from django_app.views import RequestLoggingMixin, HomeView


class TestRequestLoggingMixin(TestCase):
    """Unit tests for RequestLoggingMixin.dispatch method"""

    def setUp(self):
        self.factory = RequestFactory()

        # Create a test view class that uses the mixin
        class TestView(RequestLoggingMixin, View):
            def get(self, request, *args, **kwargs):
                return HttpResponse("Test response", status=200)

            def post(self, request, *args, **kwargs):
                # Always return error for POST to test error logging
                return HttpResponse("Error response", status=400)

        self.test_view = TestView()

    @pytest.mark.timeout(30)
    @patch('django_app.views.logger')
    @patch('time.time')
    def test_dispatch_logs_successful_request_and_response(self, mock_time, mock_logger):
        """
        Test kind: unit_tests
        Original method FQN: RequestLoggingMixin.dispatch
        """
        # Setup time mocking
        mock_time.side_effect = [1000.0, 1000.5]  # 0.5 second processing time

        # Create GET request (successful case)
        request = self.factory.get('/test/', HTTP_USER_AGENT='TestAgent')
        request.build_absolute_uri = Mock(return_value='http://testserver/test/')

        # Execute dispatch
        response = self.test_view.dispatch(request)

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"Test response")

        # Verify logging was called
        mock_logger.info.assert_called_once()

        # Verify log content
        log_call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call_args)

        # Check request data
        self.assertEqual(log_data['request']['method'], 'GET')
        self.assertEqual(log_data['request']['url'], 'http://testserver/test/')
        self.assertEqual(log_data['request']['body_size'], 0)  # GET has no body
        self.assertIn('User-Agent', log_data['request']['headers'])

        # Check response data
        self.assertEqual(log_data['response']['status'], 200)
        self.assertEqual(log_data['response']['body_size'], 13)  # len(b"Test response")
        self.assertEqual(log_data['response']['processing_duration'], '0.5000s')

        # Should not have error body for successful response
        self.assertNotIn('body', log_data['response'])

    @pytest.mark.timeout(30)
    @patch('django_app.views.logger')
    @patch('time.time')
    def test_dispatch_logs_error_response_with_body(self, mock_time, mock_logger):
        """
        Test kind: unit_tests
        Original method FQN: RequestLoggingMixin.dispatch
        """
        # Setup time mocking
        mock_time.side_effect = [1000.0, 1000.25]  # 0.25 second processing time

        # Create request
        request = self.factory.post('/test/')
        request.build_absolute_uri = Mock(return_value='http://testserver/test/')

        # Execute dispatch
        response = self.test_view.dispatch(request)

        # Verify response
        self.assertEqual(response.status_code, 400)

        # Verify logging was called
        mock_logger.info.assert_called_once()

        # Verify log content
        log_call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call_args)

        # Check request data
        self.assertEqual(log_data['request']['method'], 'POST')
        # POST request created by factory has some default body content
        self.assertGreaterEqual(log_data['request']['body_size'], 0)

        # Check response data
        self.assertEqual(log_data['response']['status'], 400)
        self.assertEqual(log_data['response']['processing_duration'], '0.2500s')

        # Should have error body for error response
        self.assertEqual(log_data['response']['body'], 'Error response')

    @pytest.mark.timeout(30)
    @patch('django_app.views.logger')
    def test_dispatch_handles_missing_attributes_gracefully(self, mock_logger):
        """
        Test kind: unit_tests
        Original method FQN: RequestLoggingMixin.dispatch
        """
        # Create minimal request without body
        request = Mock()
        request.method = 'GET'
        request.headers = {}
        request.build_absolute_uri.return_value = 'http://testserver/test/'
        # Remove body attribute to test hasattr check
        if hasattr(request, 'body'):
            delattr(request, 'body')

        # Create minimal response without content
        mock_response = Mock()
        mock_response.status_code = 200
        if hasattr(mock_response, 'content'):
            delattr(mock_response, 'content')
        if hasattr(mock_response, 'items'):
            delattr(mock_response, 'items')

        # Mock the super().dispatch to return our mock response
        with patch.object(View, 'dispatch', return_value=mock_response):
            response = self.test_view.dispatch(request)

        # Verify the method handled missing attributes gracefully
        self.assertEqual(response, mock_response)

        # Verify logging was called
        mock_logger.info.assert_called_once()

        # Verify log content handles missing attributes
        log_call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call_args)

        self.assertEqual(log_data['request']['body_size'], 0)  # Default when no body
        self.assertEqual(log_data['response']['headers'], {})  # Default when no items()
        self.assertEqual(log_data['response']['body_size'], 0)  # Default when no content


class TestHomeViewEndpoint(TestCase):
    """Endpoint tests for HomeView.get method"""

    def setUp(self):
        self.client = Client()

    @pytest.mark.timeout(30)
    @patch('django_app.views.logger')
    def test_home_view_get_returns_correct_template(self, mock_logger):
        """
        Test kind: endpoint_tests
        Original method FQN: HomeView.get
        """
        # Make GET request to home view
        response = self.client.get('/')

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_app/home.html')

        # Verify content contains expected elements
        self.assertContains(response, 'Hello from')
        self.assertContains(response, 'CodeSpeak!')
        self.assertContains(response, 'Django')
        self.assertContains(response, 'Tailwind CSS')

        # Verify logging was called (due to RequestLoggingMixin)
        mock_logger.info.assert_called_once()

        # Verify log shows successful response
        log_call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call_args)
        self.assertEqual(log_data['response']['status'], 200)
        self.assertEqual(log_data['request']['method'], 'GET')

    @pytest.mark.timeout(30)
    @patch('django_app.views.logger')
    def test_home_view_get_with_query_parameters(self, mock_logger):
        """
        Test kind: endpoint_tests
        Original method FQN: HomeView.get
        """
        # Make GET request with query parameters
        response = self.client.get('/?test=value&param=123')

        # Verify response
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'django_app/home.html')

        # Verify logging captured the URL with parameters
        log_call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call_args)
        self.assertIn('test=value', log_data['request']['url'])
        self.assertIn('param=123', log_data['request']['url'])

    @pytest.mark.timeout(30)
    @patch('django_app.views.logger')
    def test_home_view_get_with_custom_headers(self, mock_logger):
        """
        Test kind: endpoint_tests
        Original method FQN: HomeView.get
        """
        # Make GET request with custom headers
        response = self.client.get('/', HTTP_X_CUSTOM_HEADER='custom-value', HTTP_USER_AGENT='TestAgent')

        # Verify response
        self.assertEqual(response.status_code, 200)

        # Verify logging captured the custom headers
        log_call_args = mock_logger.info.call_args[0][0]
        log_data = json.loads(log_call_args)
        self.assertIn('X-Custom-Header', log_data['request']['headers'])
        self.assertEqual(log_data['request']['headers']['X-Custom-Header'], 'custom-value')
        self.assertEqual(log_data['request']['headers']['User-Agent'], 'TestAgent')