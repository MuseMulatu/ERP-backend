# leave_management/views.py

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from .models import LeaveRequest, LeaveType
from .serializers import LeaveRequestSerializer, LeaveTypeSerializer
from hr.models import Employee


class LeaveTypeViewSet(viewsets.ModelViewSet):
    """
    CRUD for leave types (Annual, Sick, etc.).
    Only active leave types are shown to non-staff by default.
    """

    queryset = LeaveType.objects.filter(is_active=True)
    serializer_class = LeaveTypeSerializer
    permission_classes = [IsAuthenticated]


class LeaveRequestViewSet(viewsets.ModelViewSet):
    """
    Manage leave requests.
    Custom actions:
    POST /api/leaves/{id}/approve/ manager approves
    POST /api/leaves/{id}/reject/  manager rejects
    """

    serializer_class = LeaveRequestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_staff:
            return LeaveRequest.objects.all().select_related(
                "employee", "leave_type", "reviewed_by"
            )
        try:
            employee = user.employee_profile
            return LeaveRequest.objects.filter(employee=employee).select_related(
                "leave_type"
            )
        except Employee.DoesNotExist:
            return LeaveRequest.objects.none()

    def perform_create(self, serializer):
        employee = self.request.user.employee_profile
        serializer.save(employee=employee)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        leave = self.get_object()
        if leave.status != "PENDING":
            return Response(
                {"error": "Only PENDING requests can be approved."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reviewer = request.user.employee_profile
        comment = request.data.get("comment", "")
        leave.approve(reviewer=reviewer, comment=comment)
        return Response({"detail": "Leave request approved."})

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        leave = self.get_object()
        if leave.status != "PENDING":
            return Response(
                {"error": "Only PENDING requests can be rejected."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        reviewer = request.user.employee_profile
        comment = request.data.get("comment", "")
        leave.reject(reviewer=reviewer, comment=comment)
        return Response({"detail": "Leave request rejected."})
