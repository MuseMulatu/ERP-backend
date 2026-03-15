# project_management/serializers.py

from rest_framework import serializers
from .models import Project, ProjectMember, Task, TaskComment
from hr.models import Employee


class ProjectSerializer(serializers.ModelSerializer):
    completion_percentage = serializers.ReadOnlyField()
    remaining_budget = serializers.ReadOnlyField()
    manager_name = serializers.ReadOnlyField(source="project_manager.full_name")

    class Meta:
        model = Project
        fields = "__all__"


class ProjectMemberSerializer(serializers.ModelSerializer):
    employee_name = serializers.ReadOnlyField(source="employee.full_name")
    project_name = serializers.ReadOnlyField(source="project.name")
    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = ProjectMember
        fields = "__all__"


class TaskSerializer(serializers.ModelSerializer):
    assigned_to_name = serializers.ReadOnlyField(source="assigned_to.full_name")
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = Task
        fields = "__all__"
        read_only_fields = ["created_by", "created_at", "updated_at", "completed_at"]


class TaskCommentSerializer(serializers.ModelSerializer):
    author_name = serializers.ReadOnlyField(source="author.full_name")

    class Meta:
        model = TaskComment
        fields = "__all__"
        read_only_fields = ["author", "created_at"]
