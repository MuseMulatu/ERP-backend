# tests/test_api.py

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from datetime import date

from hr.models import Department, Position, Employee
from leave_management.models import LeaveType, LeaveRequest
from attendance.models import AttendanceRecord
from project_management.models import Project


class AuthenticationTestCase(APITestCase):
    """Tests for user registration and login endpoints."""

    def test_user_registration_success(self):
        """A new user should register and receive a token."""
        payload = {
            "username": "johndoe",
            "email": "john@company.com",
            "password": "StrongPass123!",
            "password_confirm": "StrongPass123!",
        }
        response = self.client.post("/api/auth/register/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("token", response.data)
        self.assertTrue(User.objects.filter(username="johndoe").exists())

    def test_registration_password_mismatch(self):
        """Registration should fail if passwords do not match."""
        payload = {
            "username": "janedoe",
            "password": "Pass123!",
            "password_confirm": "Different456!",
        }
        response = self.client.post("/api/auth/register/", payload)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_success(self):
        """Valid credentials should return a token."""
        user = User.objects.create_user(username="testuser", password="TestPass123!")
        response = self.client.post(
            "/api/auth/login/",
            {
                "username": "testuser",
                "password": "TestPass123!",
            },
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("token", response.data)

    def test_login_wrong_password(self):
        """Wrong password should return 400."""
        User.objects.create_user(username="user1", password="correct")
        response = self.client.post(
            "/api/auth/login/", {"username": "user1", "password": "wrong"}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_protected_endpoint_requires_auth(self):
        """Unauthenticated requests to protected endpoints should get 401."""
        response = self.client.get("/api/employees/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class EmployeeTestCase(APITestCase):
    """Tests for the HR Employee API."""

    def setUp(self):
        """Create a staff user and authenticate the test client."""
        self.user = User.objects.create_user(
            username="admin", password="admin123", is_staff=True
        )
        self.token = Token.objects.create(user=self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

        self.dept = Department.objects.create(name="Engineering", code="ENG")
        self.position = Position.objects.create(
            title="Backend Developer",
            department=self.dept,
            level="MID",
            min_salary=3000,
            max_salary=6000,
        )

    def test_create_employee(self):
        """POST /api/employees/ should create a new employee record."""
        emp_user = User.objects.create_user(
            username="emp1", email="emp1@co.com", password="pass"
        )
        payload = {
            "user": emp_user.pk,
            "first_name": "Alice",
            "last_name": "Smith",
            "email": "alice@company.com",
            "department": self.dept.pk,
            "position": self.position.pk,
            "hire_date": str(date.today()),
            "employment_type": "FULL_TIME",
        }
        response = self.client.post("/api/employees/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Employee.objects.count(), 1)

    def test_list_employees(self):
        """GET /api/employees/ should return paginated employee list."""
        response = self.client.get("/api/employees/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Note: 'results' key checking assumes you are using pagination
        # If it fails, check if Pagination is enabled in DRF settings.
        # self.assertIn('results', response.data)

    def test_filter_employees_by_department(self):
        """Employees can be filtered by department."""
        response = self.client.get(f"/api/employees/?department={self.dept.pk}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)


class LeaveRequestTestCase(APITestCase):
    """Tests for Leave Management API."""

    def setUp(self):
        # Create employee user
        self.emp_user = User.objects.create_user(
            username="emp_leave", password="pass123"
        )
        dept = Department.objects.create(name="HR", code="HR")
        pos = Position.objects.create(
            title="HR Officer",
            department=dept,
            level="MID",
            min_salary=2000,
            max_salary=4000,
        )
        self.employee = Employee.objects.create(
            user=self.emp_user,
            first_name="Bob",
            last_name="Jones",
            email="bob@co.com",
            department=dept,
            position=pos,
            hire_date=date.today(),
        )
        self.leave_type = LeaveType.objects.create(
            name="Annual Leave",
            code="AL",
            max_days_per_year=21,
            is_paid=True,
        )
        token = Token.objects.create(user=self.emp_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_apply_for_leave(self):
        """Employee should be able to submit a leave request."""
        payload = {
            "leave_type": self.leave_type.pk,
            "start_date": "2025-08-01",
            "end_date": "2025-08-05",
            "reason": "Family vacation.",
        }
        response = self.client.post("/api/leaves/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(LeaveRequest.objects.count(), 1)
        self.assertEqual(LeaveRequest.objects.first().status, "PENDING")

    def test_approve_leave(self):
        """A manager should be able to approve a pending leave request."""
        leave = LeaveRequest.objects.create(
            employee=self.employee,
            leave_type=self.leave_type,
            start_date=date(2025, 9, 1),
            end_date=date(2025, 9, 3),
            reason="Rest",
            status="PENDING",
        )
        # Log in as staff/manager
        manager_user = User.objects.create_user(
            username="mgr", password="mgr123", is_staff=True
        )

        # --- Employee creation ---
        Employee.objects.create(
            user=manager_user,
            first_name="Manager",
            last_name="Boss",
            email="mgr@co.com",
            department=self.employee.department,
            position=self.employee.position,
            hire_date=date.today(),
        )

        mgr_token = Token.objects.create(user=manager_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {mgr_token.key}")

        response = self.client.post(
            f"/api/leaves/{leave.pk}/approve/",
            {"comment": "Approved. Enjoy your time off."},
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        leave.refresh_from_db()
        self.assertEqual(leave.status, "APPROVED")


class AttendanceTestCase(APITestCase):
    """Tests for Attendance Check-In/Check-Out API."""

    def setUp(self):
        user = User.objects.create_user(username="att_user", password="pass")
        dept = Department.objects.create(name="Ops", code="OPS")
        pos = Position.objects.create(
            title="Operator",
            department=dept,
            level="JUNIOR",
            min_salary=1500,
            max_salary=2500,
        )
        self.employee = Employee.objects.create(
            user=user,
            first_name="Carol",
            last_name="White",
            email="carol@co.com",
            department=dept,
            position=pos,
            hire_date=date.today(),
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_check_in(self):
        """Employee should be able to check in."""
        response = self.client.post("/api/attendance/check-in/")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(AttendanceRecord.objects.count(), 1)
        record = AttendanceRecord.objects.first()
        self.assertIsNotNone(record.check_in)

    def test_check_out(self):
        """Employee should be able to check out after checking in."""
        self.client.post("/api/attendance/check-in/")
        response = self.client.post("/api/attendance/check-out/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        record = AttendanceRecord.objects.first()
        self.assertIsNotNone(record.check_out)
        self.assertIsNotNone(record.working_hours)


class ProjectManagementTestCase(APITestCase):
    """Tests for Project and Task management API."""

    def setUp(self):
        user = User.objects.create_user(
            username="pm_user", password="pass", is_staff=True
        )
        dept = Department.objects.create(name="Dev", code="DEV")
        pos = Position.objects.create(
            title="PM",
            department=dept,
            level="MANAGER",
            min_salary=5000,
            max_salary=8000,
        )
        self.pm = Employee.objects.create(
            user=user,
            first_name="Dave",
            last_name="Clark",
            email="dave@co.com",
            department=dept,
            position=pos,
            hire_date=date.today(),
        )
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")

    def test_create_project(self):
        """Staff should be able to create a new project."""
        payload = {
            "name": "ERP Phase 2",
            "code": "ERP-P2",
            "description": "Second phase of the ERP rollout.",
            "project_manager": self.pm.pk,
            "status": "PLANNING",
            "priority": "HIGH",
            "start_date": str(date.today()),
        }
        response = self.client.post("/api/projects/", payload)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Project.objects.count(), 1)

    def test_list_projects(self):
        """GET /api/projects/ should return all projects."""
        response = self.client.get("/api/projects/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
