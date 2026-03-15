# attendance/views.py

from rest_framework import viewsets, filters
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from .models import AttendanceRecord
from .serializers import AttendanceRecordSerializer
from hr.models import Employee


class AttendanceRecordViewSet(viewsets.ModelViewSet):
    """
    Employees can see their own records, while staff can see all records.
    """

    serializer_class = AttendanceRecordSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ["date", "status", "location"]
    ordering_fields = ["date", "check_in"]
    ordering = ["-date"]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return AttendanceRecord.objects.all().select_related("employee")

        try:
            employee = user.employee_profile
            return AttendanceRecord.objects.filter(employee=employee)
        except Employee.DoesNotExist:
            return AttendanceRecord.objects.none()

    def perform_create(self, serializer):
        """
        capture the IP address and set the employee on check-in.
        """
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = self.request.META.get("REMOTE_ADDR")

        employee = self.request.user.employee_profile
        serializer.save(employee=employee, ip_address=ip)
