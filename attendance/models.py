# attendance/models.py

from datetime import time
from decimal import Decimal
from django.db import models
from django.utils import timezone
from hr.models import Employee


class AttendanceRecord(models.Model):
    """
    Records daily attendance for an employee.
    One record per employee per calendar day.
    Tracks check-in/check-out timestamps and computes working hours.
    """

    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LATE", "Late Arrival"),
        ("HALF_DAY", "Half Day"),
        ("ON_LEAVE", "On Approved Leave"),
    ]
    LOCATION_CHOICES = [
        ("OFFICE", "Office"),
        ("REMOTE", "Remote / Work From Home"),
        ("FIELD", "Field / On-Site"),
    ]

    STANDARD_HOURS = Decimal("8.00")  # Standard working day length in hours

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="attendance_records",
        help_text="The employee this attendance record belongs to.",
    )
    date = models.DateField(
        help_text="Calendar date of this attendance entry. Only one record per employee per day is allowed."
    )
    check_in = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Exact timestamp when the employee clocked in for the day.",
    )
    check_out = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Exact timestamp when the employee clocked out. Null if the employee has not yet checked out.",
    )
    working_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        help_text="Computed hours worked (check_out - check_in). Calculated automatically on save.",
    )
    overtime_hours = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        editable=False,
        help_text="Hours worked beyond STANDARD_HOURS (8 hrs). Calculated automatically.",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PRESENT",
        help_text="Attendance status for the day.",
    )
    location = models.CharField(
        max_length=20,
        choices=LOCATION_CHOICES,
        blank=True,
        null=True,
        help_text="Where the employee was working from.",
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address captured at check-in for audit purposes.",
    )
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional comments from the employee or HR manager.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-date", "employee"]
        verbose_name = "Attendance Record"
        verbose_name_plural = "Attendance Records"
        unique_together = [["employee", "date"]]
        indexes = [
            models.Index(fields=["employee", "date"]),
            models.Index(fields=["date", "status"]),
        ]

    def __str__(self):
        return f"{self.employee.full_name} {self.date} [{self.get_status_display()}]"

    def save(self, *args, **kwargs):
        # Recompute working and overtime hours whenever the record is saved
        if self.check_in and self.check_out:
            if self.check_out > self.check_in:
                duration = self.check_out - self.check_in
                total = Decimal(str(round(duration.total_seconds() / 3600, 2)))
                self.working_hours = total
                overtime = total - self.STANDARD_HOURS
                self.overtime_hours = max(Decimal("0"), overtime)

        # Auto-set LATE status if check-in is after 09:00
        if (
            self.check_in
            and self.check_in.time() > time(9, 0)
            and self.status == "PRESENT"
        ):
            self.status = "LATE"

        super().save(*args, **kwargs)

    @property
    def is_complete(self):
        """Returns True if both check-in and check-out are recorded."""
        return self.check_in is not None and self.check_out is not None
