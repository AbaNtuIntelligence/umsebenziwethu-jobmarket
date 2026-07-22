from django.contrib import admin
from django.urls import include, path, re_path
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError
from django.views.static import serve
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.response import Response
from rest_framework.views import APIView

class HealthView(APIView):
    permission_classes = []
    def get(self, request):
        return Response({"status": "ok", "service": "AbaNtu Job Centre API"})

class ReadinessView(APIView):
    permission_classes = []

    def get(self, request):
        try:
            with connections["default"].cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()
        except OperationalError:
            return Response({"status": "unavailable", "database": "unavailable"}, status=503)
        return Response({"status": "ready", "database": "ok"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view()),
    path("api/ready/", ReadinessView.as_view()),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("jobs.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
    # Uploaded media lives outside the application slug on Render. Unlike the
    # static() helper, this route remains available when DEBUG is False.
    re_path(
        r"^media/(?P<path>.*)$",
        serve,
        {"document_root": settings.MEDIA_ROOT},
    ),
]
