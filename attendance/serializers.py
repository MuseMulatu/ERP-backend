# attendance/serializers.py

from rest_framework import serializers
from .models import AttendanceRecord


class AttendanceRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for daily attendance records.
    Display of working hours and status.
    """

    employee_name = serializers.ReadOnlyField(source="employee.full_name")
    status_display = serializers.CharField(source="get_status_display", read_only=True)

    class Meta:
        model = AttendanceRecord
        fields = [
            "id",
            "employee",
            "employee_name",
            "date",
            "check_in",
            "check_out",
            "working_hours",
            "overtime_hours",
            "status",
            "status_display",
            "location",
            "ip_address",
            "notes",
            "created_at",
        ]
        read_only_fields = ["id", "working_hours", "overtime_hours", "created_at"]

    def validate(self, attrs):
        """
        check_out must be after check_in if both are provided.
        """
        check_in = attrs.get("check_in")
        check_out = attrs.get("check_out")

        if check_in and check_out and check_out < check_in:
            raise serializers.ValidationError(
                "Check-out time must be after check-in time."
            )
        return attrs
