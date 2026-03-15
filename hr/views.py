# hr/views.py

from datetime import date
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from drf_spectacular.utils import extend_schema, extend_schema_view

from .models import Department, Position, Employee
from .serializers import (
    DepartmentSerializer,
    PositionSerializer,
    EmployeeListSerializer,
    EmployeeDetailSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="List all departments"),
    create=extend_schema(summary="Create a new department"),
    retrieve=extend_schema(summary="Get department details"),
    update=extend_schema(summary="Update a department"),
    destroy=extend_schema(summary="Delete a department"),
)
class DepartmentViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Departments.
    GET    /api/departments/       list all
    POST   /api/departments/       create
    GET    /api/departments/{id}/  retrieve
    PUT    /api/departments/{id}/  full update
    PATCH  /api/departments/{id}/  partial update
    DELETE /api/departments/{id}/  delete
    """

    queryset = Department.objects.all().select_related("manager")
    serializer_class = DepartmentSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ["name", "code"]
    ordering_fields = ["name", "created_at"]
    ordering = ["name"]


class PositionViewSet(viewsets.ModelViewSet):
    queryset = Position.objects.all().select_related("department")
    serializer_class = PositionSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["department", "level", "is_active"]
    search_fields = ["title", "description"]


class EmployeeViewSet(viewsets.ModelViewSet):
    """
    Full CRUD for Employees with additional custom actions.
    Custom actions:
    GET  /api/employees/{id}/profile/        full profile
    GET  /api/employees/{id}/direct_reports/ subordinates
    POST /api/employees/{id}/deactivate/     deactivate employee
    """

    permission_classes = [IsAuthenticated]
    filter_backends = [
        DjangoFilterBackend,
        filters.SearchFilter,
        filters.OrderingFilter,
    ]
    filterset_fields = ["department", "status", "employment_type"]
    search_fields = ["first_name", "last_name", "email", "employee_id"]
    ordering_fields = ["hire_date", "last_name", "salary"]

    def get_queryset(self):
        return Employee.objects.all().select_related(
            "user", "department", "position", "manager"
        )

    def get_serializer_class(self):
        if self.action == "list":
            return EmployeeListSerializer
        return EmployeeDetailSerializer

    @action(detail=True, methods=["get"])
    def profile(self, request, pk=None):
        """Return the full employee profile including related data."""
        employee = self.get_object()
        serializer = EmployeeDetailSerializer(employee, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["get"])
    def direct_reports(self, request, pk=None):
        """Return all employees who report to this employee."""
        employee = self.get_object()
        reports = employee.direct_reports.filter(status="ACTIVE")
        serializer = EmployeeListSerializer(reports, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def deactivate(self, request, pk=None):
        """Set employee status to TERMINATED."""
        employee = self.get_object()
        employee.status = "TERMINATED"
        employee.end_date = date.today()
        employee.save(update_fields=["status", "end_date"])
        return Response(
            {"detail": f"{employee.full_name} has been deactivated."},
            status=status.HTTP_200_OK,
        )
