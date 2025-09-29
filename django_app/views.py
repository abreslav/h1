from django.shortcuts import render
import logging
import json
import time
from django.http import HttpResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.views import View

logger = logging.getLogger('django_app')

class RequestLoggingMixin:
    def dispatch(self, request, *args, **kwargs):
        start_time = time.time()

        # Log request
        request_data = {
            'method': request.method,
            'url': request.build_absolute_uri(),
            'headers': dict(request.headers),
            'body_size': len(request.body) if hasattr(request, 'body') else 0
        }

        response = super().dispatch(request, *args, **kwargs)

        # Log response
        end_time = time.time()
        processing_time = end_time - start_time

        response_data = {
            'status': response.status_code,
            'headers': dict(response.items()) if hasattr(response, 'items') else {},
            'body_size': len(response.content) if hasattr(response, 'content') else 0,
            'processing_duration': f"{processing_time:.4f}s"
        }

        log_entry = {
            'request': request_data,
            'response': response_data
        }

        if response.status_code >= 400:
            log_entry['response']['body'] = response.content.decode('utf-8') if hasattr(response, 'content') else ''

        logger.info(json.dumps(log_entry))

        return response

class HomeView(RequestLoggingMixin, View):
    def get(self, request):
        return render(request, 'django_app/home.html')
