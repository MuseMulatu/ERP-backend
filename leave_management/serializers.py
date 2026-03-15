# leave_management/serializers.py

from rest_framework import serializers
from .models import LeaveRequest, LeaveType
from hr.models import Employee


class LeaveTypeSerializer(serializers.ModelSerializer):
    """
    Serializer for managing different categories of leave.
    """

    class Meta:
        model = LeaveType
        fields = "__all__"


class LeaveRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for leave applications.
    """

    employee_name = serializers.ReadOnlyField(source="employee.full_name")
    leave_type_name = serializers.ReadOnlyField(source="leave_type.name")
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = [
            "id",
            "employee",
            "employee_name",
            "leave_type",
            "leave_type_name",
            "start_date",
            "end_date",
            "total_days",
            "reason",
            "status",
            "status_display",
            "reviewed_by",
            "reviewed_at",
            "review_comment",
            "attachment",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "employee",
            "total_days",
            "status",
            "reviewed_by",
            "reviewed_at",
            "created_at",
        ]

    def validate(self, attrs):
        """
        Check to see the start date is before the end date.
        """
        start = attrs.get("start_date")
        end = attrs.get("end_date")

        if start and end and start > end:
            raise serializers.ValidationError(
                "The start date must be before the end date."
            )
        return attrs
