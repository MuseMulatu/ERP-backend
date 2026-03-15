# leave_management/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import LeaveRequestViewSet, LeaveTypeViewSet

app_name = "leave_management"

router = DefaultRouter()
router.register(r"types", LeaveTypeViewSet, basename="leave-type")
router.register(r"requests", LeaveRequestViewSet, basename="leave-request")

urlpatterns = [
    path("", include(router.urls)),
]
