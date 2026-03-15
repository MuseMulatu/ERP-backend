from rest_framework import viewsets, filters, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
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

    @action(detail=False, methods=["post"], url_path="check-in")
    def check_in(self, request):
        employee = request.user.employee_profile
        today = timezone.now().date()

        # no check in twice in one day
        if AttendanceRecord.objects.filter(employee=employee, date=today).exists():
            return Response(
                {"error": "Already checked in today."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        record = AttendanceRecord.objects.create(
            employee=employee, date=today, check_in=timezone.now()
        )
        return Response({"status": "Checked in"}, status=status.HTTP_201_CREATED)

    @action(detail=False, methods=["post"], url_path="check-out")
    def check_out(self, request):
        employee = request.user.employee_profile
        today = timezone.now().date()
        record = AttendanceRecord.objects.filter(employee=employee, date=today).first()

        if record and not record.check_out:
            record.check_out = timezone.now()
            record.save()
            return Response({"status": "Checked out"}, status=status.HTTP_200_OK)

        return Response(
            {"error": "Cannot check out. No active check-in found."},
            status=status.HTTP_400_BAD_REQUEST,
        )
