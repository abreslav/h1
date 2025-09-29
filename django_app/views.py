from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views.decorators.http import require_http_methods
from .models import Demo
import logging
import json
import time

logger = logging.getLogger('django_app')


def log_request_response(request, response, start_time):
    """Helper function to log request and response details"""
    duration = (time.time() - start_time) * 1000  # Convert to milliseconds

    # Get request headers
    request_headers = dict(request.META.items())
    request_headers = {k: v for k, v in request_headers.items() if k.startswith('HTTP_') or k in ['CONTENT_TYPE', 'CONTENT_LENGTH']}

    # Get response headers
    response_headers = dict(response.items()) if hasattr(response, 'items') else {}

    # Get request body size (handle RawPostDataException for POST requests)
    try:
        request_body_size = len(request.body) if hasattr(request, 'body') else 0
    except Exception:
        # If we can't access body (e.g., after POST data has been read), estimate from headers
        request_body_size = int(request.META.get('CONTENT_LENGTH', 0))

    # Get response body size
    response_body_size = len(response.content) if hasattr(response, 'content') else 0

    log_data = {
        "method": request.method,
        "url": request.build_absolute_uri(),
        "request_headers": request_headers,
        "request_body_size": request_body_size,
        "response_status": response.status_code,
        "response_headers": response_headers,
        "response_body_size": response_body_size,
        "processing_duration_ms": round(duration, 2)
    }

    # Log full response body if not successful
    if response.status_code >= 400 and hasattr(response, 'content'):
        log_data["response_body"] = response.content.decode('utf-8')

    logger.info(json.dumps(log_data))


def home(request):
    """Main page view to display and add demo records"""
    start_time = time.time()

    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        description = request.POST.get('description', '').strip()

        if name and description:
            Demo.objects.create(name=name, description=description)
            response = redirect('home')
        else:
            demos = Demo.objects.all().order_by('-id')
            response = render(request, 'django_app/home.html', {
                'demos': demos,
                'error': 'Both name and description are required.'
            })
    else:
        demos = Demo.objects.all().order_by('-id')
        response = render(request, 'django_app/home.html', {'demos': demos})

    log_request_response(request, response, start_time)
    return response
