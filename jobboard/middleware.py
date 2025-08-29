import uuid
import threading

_local = threading.local()

def get_request_id() -> str:
    return getattr(_local, "request_id", "")

class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        rid = request.META.get("HTTP_X_REQUEST_ID") or uuid.uuid4().hex
        _local.request_id = rid
        request.request_id = rid
        response = self.get_response(request)
        response["X-Request-ID"] = rid
        return response
