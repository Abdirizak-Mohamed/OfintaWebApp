# django
from django.conf import settings
from django.utils.deprecation import MiddlewareMixin

# ofinta
from .models import Request
from apps.core.router import patterns
 
 
class RequestMiddleware(MiddlewareMixin):
    
    def process_request(self, request):
        request._body_to_log = request.body
    
    def process_response(self, request, response):
 
        ignore = patterns(False, *settings.REQUEST_IGNORE_PATHS)
        if ignore.resolve(request.path[1:]):
            return response
 
        r = Request()
        r.from_http_request(request, response)
 
        return response
