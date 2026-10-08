from django.db import connection
from django.http import HttpRequest, JsonResponse


def health(_request: HttpRequest) -> JsonResponse:
    return JsonResponse({"status": "ok"})


def readiness(_request: HttpRequest) -> JsonResponse:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
    except Exception as exc:
        return JsonResponse(
            {"status": "unavailable", "detail": str(exc)}, status=503
        )
    return JsonResponse({"status": "ok"})
