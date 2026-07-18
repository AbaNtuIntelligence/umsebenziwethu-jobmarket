from django.contrib import admin
from django.urls import include, path
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework.response import Response
from rest_framework.views import APIView

class HealthView(APIView):
    permission_classes = []
    def get(self, request):
        return Response({"status": "ok", "service": "AbaNtu Job Centre API"})

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/health/", HealthView.as_view()),
    path("api/auth/", include("accounts.urls")),
    path("api/", include("jobs.urls")),
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="docs"),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
