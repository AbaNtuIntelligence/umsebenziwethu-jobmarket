from django.urls import include, path
from rest_framework.routers import DefaultRouter
from .views import ApplicationCVReplaceView, ApplicationDetailView, ApplicationDocumentCreateView, ApplicationDocumentDownloadView, ApplicationListCreateView, ApplicationStatusView, ApplicationWithdrawView, FeedbackCreateView, InterviewViewSet, JobLocationReportCreateView, JobMediaCreateView, JobMediaDeleteView, JobReportCreateView, JobViewSet, LocationAnalyticsView, NotificationListView, NotificationReadAllView, NotificationReadView, RecruitmentSessionViewSet, SavedJobDeleteView, SavedJobListCreateView, SubmitApplicationView

router = DefaultRouter()
router.register("jobs", JobViewSet, basename="job")
router.register("interviews", InterviewViewSet, basename="interview")
router.register("recruitment-sessions", RecruitmentSessionViewSet, basename="recruitment-session")
urlpatterns = [
    path("", include(router.urls)),
    path("applications/", ApplicationListCreateView.as_view(), name="applications"),
    path("applications/submit/", SubmitApplicationView.as_view(), name="application-submit"),
    path("applications/<int:pk>/", ApplicationDetailView.as_view(), name="application-detail"),
    path("applications/<int:pk>/status/", ApplicationStatusView.as_view(), name="application-status"),
    path("applications/<int:pk>/withdraw/", ApplicationWithdrawView.as_view(), name="application-withdraw"),
    path("applications/<int:pk>/cv/", ApplicationCVReplaceView.as_view(), name="application-cv-replace"),
    path("saved-jobs/", SavedJobListCreateView.as_view(), name="saved-jobs"),
    path("saved-jobs/<int:job_id>/", SavedJobDeleteView.as_view(), name="saved-job-delete"),
    path("jobs/<int:job_id>/media/", JobMediaCreateView.as_view(), name="job-media-create"),
    path("job-media/<int:pk>/", JobMediaDeleteView.as_view(), name="job-media-delete"),
    path("applications/<int:application_id>/documents/", ApplicationDocumentCreateView.as_view(), name="application-document-create"),
    path("application-documents/<int:pk>/download/", ApplicationDocumentDownloadView.as_view(), name="application-document-download"),
    path("notifications/", NotificationListView.as_view(), name="notifications"),
    path("notifications/read-all/", NotificationReadAllView.as_view(), name="notifications-read-all"),
    path("notifications/<int:pk>/read/", NotificationReadView.as_view(), name="notification-read"),
    path("job-reports/", JobReportCreateView.as_view(), name="job-report-create"),
    path("job-location-reports/", JobLocationReportCreateView.as_view(), name="job-location-report-create"),
    path("analytics/locations/", LocationAnalyticsView.as_view(), name="location-analytics"),
    path("feedback/", FeedbackCreateView.as_view(), name="feedback-create"),
]
