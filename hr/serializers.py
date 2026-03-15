# hr/serializers.py

from rest_framework import serializers
from .models import Department, Position, Employee


class DepartmentSerializer(serializers.ModelSerializer):
    headcount = serializers.ReadOnlyField()

    class Meta:
        model = Department
        fields = [
            "id",
            "name",
            "code",
            "description",
            "manager",
            "headcount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PositionSerializer(serializers.ModelSerializer):
    department_name = serializers.CharField(source="department.name", read_only=True)

    class Meta:
        model = Position
        fields = [
            "id",
            "title",
            "department",
            "department_name",
            "level",
            "min_salary",
            "max_salary",
            "description",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate(self, attrs):
        if attrs.get("min_salary") and attrs.get("max_salary"):
            if attrs["min_salary"] > attrs["max_salary"]:
                raise serializers.ValidationError(
                    "Minimum salary must not exceed maximum salary."
                )
        return attrs


class EmployeeListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for list views excludes sensitive fields."""

    full_name = serializers.ReadOnlyField()
    department_name = serializers.CharField(source="department.name", read_only=True)
    position_title = serializers.CharField(source="position.title", read_only=True)

    class Meta:
        model = Employee
        fields = [
            "id",
            "employee_id",
            "full_name",
            "email",
            "department_name",
            "position_title",
            "employment_type",
            "status",
            "hire_date",
        ]


class EmployeeDetailSerializer(serializers.ModelSerializer):
    """Full serializer for create/update/retrieve includes all fields."""

    full_name = serializers.ReadOnlyField()
    years_of_service = serializers.ReadOnlyField()

    class Meta:
        model = Employee
        fields = "__all__"
        read_only_fields = [
            "id",
            "employee_id",
            "created_at",
            "updated_at",
            "full_name",
            "years_of_service",
        ]

    def validate_email(self, value):
        """Ensure email uniqueness on update (exclude current instance)."""
        qs = Employee.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError(
                "An employee with this email already exists."
            )
        return value
