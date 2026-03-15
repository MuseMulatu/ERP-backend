# project_management/urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ProjectViewSet, ProjectMemberViewSet, TaskViewSet, TaskCommentViewSet

app_name = "project_management"

router = DefaultRouter()
router.register(r"projects", ProjectViewSet, basename="project")
router.register(r"members", ProjectMemberViewSet, basename="project-member")
router.register(r"tasks", TaskViewSet, basename="task")
router.register(r"comments", TaskCommentViewSet, basename="task-comment")

urlpatterns = [
    path("", include(router.urls)),
]
