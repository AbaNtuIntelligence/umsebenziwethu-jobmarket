from rest_framework.views import exception_handler


def _first_message(value):
    if isinstance(value, dict):
        for nested in value.values():
            message = _first_message(nested)
            if message:
                return message
    elif isinstance(value, (list, tuple)):
        for nested in value:
            message = _first_message(nested)
            if message:
                return message
    elif value:
        return str(value)
    return "Request failed."

def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is not None:
        errors = response.data
        response.data = {
            "success": False,
            "code": getattr(exc, "default_code", "request_failed"),
            "detail": _first_message(errors),
            "errors": errors,
        }
    return response
