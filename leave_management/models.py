# leave_management/models.py

from django.db import models
from django.utils import timezone
from hr.models import Employee


class LeaveType(models.Model):
    """
    Defines a category of leave (e.g. Annual, Sick, Maternity).
    HR administrators create and manage leave types.
    """

    name = models.CharField(
        max_length=100,
        unique=True,
        help_text="Display name shown to employees, e.g. 'Annual Leave'.",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Short code used in reports and exports, e.g. 'AL', 'SL'.",
    )
    max_days_per_year = models.PositiveIntegerField(
        help_text="Maximum days an employee may take of this type in a year."
    )
    requires_approval = models.BooleanField(
        default=True,
        help_text="If True, a manager must approve before leave is confirmed.",
    )
    is_paid = models.BooleanField(
        default=True,
        help_text="Whether the employee receives full pay during this leave.",
    )
    carry_forward = models.BooleanField(
        default=False, help_text="If True, unused days roll over to the following year."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Policy notes and eligibility rules for this leave type.",
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive leave types are hidden from employee applications.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "Leave Type"
        verbose_name_plural = "Leave Types"

    def __str__(self):
        return f"{self.code} {self.name}"


class LeaveRequest(models.Model):
    """
    Represents a leave application submitted by an employee.
    Follows a workflow: PENDING / APPROVED / REJECTED / CANCELLED.
    """

    STATUS_CHOICES = [
        ("PENDING", "Pending Review"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("CANCELLED", "Cancelled by Employee"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_requests",
        help_text="The employee who submitted this leave request.",
    )
    leave_type = models.ForeignKey(
        LeaveType,
        on_delete=models.PROTECT,
        related_name="requests",
        help_text="The category of leave being requested.",
    )
    start_date = models.DateField(
        help_text="First day of the requested leave (inclusive)."
    )
    end_date = models.DateField(
        help_text="Last day of the requested leave (inclusive)."
    )
    total_days = models.PositiveIntegerField(
        editable=False,
        default=0,
        help_text="Automatically calculated number of calendar days. Excludes weekends if configured.",
    )
    reason = models.TextField(
        help_text="Employee's written explanation for this leave request."
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING",
        help_text="Current state in the approval workflow.",
    )
    reviewed_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="reviewed_leaves",
        help_text="Manager who took the approval/rejection action.",
    )
    reviewed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp of when the review decision was made.",
    )
    review_comment = models.TextField(
        blank=True,
        null=True,
        help_text="Optional note from the reviewer explaining the decision.",
    )
    attachment = models.FileField(
        upload_to="leave/attachments/",
        blank=True,
        null=True,
        help_text="Supporting document, e.g. a medical certificate.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Leave Request"
        verbose_name_plural = "Leave Requests"
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["employee", "status"]),
        ]

    def __str__(self):
        return (
            f"{self.employee.full_name} "
            f"{self.leave_type.code} "
            f"({self.start_date} to {self.end_date}) "
            f"[{self.get_status_display()}]"
        )

    def save(self, *args, **kwargs):
        # Auto-calculate total_days before saving
        if self.start_date and self.end_date:
            delta = (self.end_date - self.start_date).days + 1
            self.total_days = max(delta, 0)
        super().save(*args, **kwargs)

    def approve(self, reviewer: Employee, comment: str = ""):
        """Approve this leave request and deduct from employee leave balance."""
        self.status = "APPROVED"
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_comment = comment
        self.save()

        # Deduct from employee leave balance
        self.employee.leave_balance = max(
            0, self.employee.leave_balance - self.total_days
        )
        self.employee.save(update_fields=["leave_balance"])

    def reject(self, reviewer: Employee, comment: str = ""):
        """Reject this leave request."""
        self.status = "REJECTED"
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_comment = comment
        self.save()
