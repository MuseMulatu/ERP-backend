# project_management/views.py

from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone

from .models import Project, ProjectMember, Task, TaskComment
from .serializers import (
    ProjectSerializer,
    ProjectMemberSerializer,
    TaskSerializer,
    TaskCommentSerializer,
)


class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().select_related("project_manager")
    serializer_class = ProjectSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["status", "priority"]
    search_fields = ["name", "code"]


class ProjectMemberViewSet(viewsets.ModelViewSet):
    queryset = ProjectMember.objects.all().select_related("project", "employee")
    serializer_class = ProjectMemberSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["project", "role", "is_active"]


class TaskViewSet(viewsets.ModelViewSet):
    queryset = Task.objects.all().select_related("project", "assigned_to")
    serializer_class = TaskSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["project", "status", "priority", "assigned_to"]
    search_fields = ["title", "description"]

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user.employee_profile)

    @action(detail=True, methods=["post"])
    def mark_done(self, request, pk=None):
        """Custom action to mark a task as completed."""
        task = self.get_object()
        task.status = "DONE"
        task.completed_at = timezone.now()
        task.save()
        return Response({"status": "task marked as done"}, status=status.HTTP_200_OK)


class TaskCommentViewSet(viewsets.ModelViewSet):
    queryset = TaskComment.objects.all().select_related("author", "task")
    serializer_class = TaskCommentSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["task"]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user.employee_profile)
