# project_management/models.py

from django.db import models
from hr.models import Employee


class Project(models.Model):
    """
    Represents a company project or initiative.
    Projects have defined start/end dates, budgets, and status tracking.
    """

    STATUS_CHOICES = [
        ("PLANNING", "Planning"),
        ("IN_PROGRESS", "In Progress"),
        ("ON_HOLD", "On Hold"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]
    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    ]

    name = models.CharField(
        max_length=200,
        help_text="Full project name, e.g. 'Customer Portal Redesign Q3 2024'.",
    )
    code = models.CharField(
        max_length=20,
        unique=True,
        help_text="Unique project code used in task IDs, e.g. 'CPR-2024'.",
    )
    description = models.TextField(
        help_text="Detailed description of the project scope and goals."
    )
    project_manager = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name="managed_projects",
        help_text="The employee responsible for delivering this project.",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PLANNING",
        help_text="Current lifecycle stage of the project.",
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="MEDIUM",
        help_text="Business priority level affecting resource allocation.",
    )
    start_date = models.DateField(help_text="Official project kick-off date.")
    end_date = models.DateField(
        null=True,
        blank=True,
        help_text="Target completion date. Null if not yet defined.",
    )
    budget = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Approved project budget in the company's base currency.",
    )
    spent_budget = models.DecimalField(
        max_digits=14,
        decimal_places=2,
        default=0,
        help_text="Amount of budget spent to date. Updated as costs are logged.",
    )
    github_url = models.URLField(
        blank=True, null=True, help_text="Link to the project's GitHub or repository."
    )
    is_active = models.BooleanField(
        default=True,
        help_text="Inactive projects are archived and hidden from dashboards.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-start_date", "name"]
        verbose_name = "Project"
        verbose_name_plural = "Projects"

    def __str__(self):
        return f"[{self.code}] {self.name}"

    @property
    def completion_percentage(self):
        """Percentage of tasks in DONE status."""
        total = self.tasks.count()
        if total == 0:
            return 0
        done = self.tasks.filter(status="DONE").count()
        return round((done / total) * 100, 1)

    @property
    def remaining_budget(self):
        if self.budget is None:
            return None
        return self.budget - self.spent_budget


class ProjectMember(models.Model):
    """
    Intermediate model linking an Employee to a Project with a role.
    Represents team membership.
    """

    ROLE_CHOICES = [
        ("MANAGER", "Project Manager"),
        ("TECH_LEAD", "Technical Lead"),
        ("DEVELOPER", "Developer"),
        ("DESIGNER", "Designer / UX"),
        ("QA", "Quality Assurance"),
        ("ANALYST", "Business Analyst"),
        ("STAKEHOLDER", "Stakeholder"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="members",
        help_text="The project this membership record belongs to.",
    )
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="project_memberships",
        help_text="The employee who is a member of this project.",
    )
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default="DEVELOPER",
        help_text="The employee's role within this specific project.",
    )
    joined_at = models.DateField(
        auto_now_add=True, help_text="Date the employee was added to this project."
    )
    is_active = models.BooleanField(
        default=True, help_text="Inactive if the employee has left the project team."
    )

    class Meta:
        unique_together = [["project", "employee"]]
        ordering = ["project", "role"]
        verbose_name = "Project Member"
        verbose_name_plural = "Project Members"

    def __str__(self):
        return f"{self.employee.full_name} {self.get_role_display()} on [{self.project.code}]"


class Task(models.Model):
    """
    A single unit of work belonging to a project.
    Can be assigned to a project team member.
    """

    PRIORITY_CHOICES = [
        ("LOW", "Low"),
        ("MEDIUM", "Medium"),
        ("HIGH", "High"),
        ("CRITICAL", "Critical"),
    ]
    STATUS_CHOICES = [
        ("BACKLOG", "Backlog"),
        ("TODO", "To Do"),
        ("IN_PROGRESS", "In Progress"),
        ("IN_REVIEW", "In Review"),
        ("DONE", "Done"),
        ("BLOCKED", "Blocked"),
    ]

    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name="tasks",
        help_text="The project this task belongs to.",
    )
    title = models.CharField(
        max_length=200, help_text="Short descriptive title of the task."
    )
    description = models.TextField(
        blank=True,
        null=True,
        help_text="Detailed description of what needs to be done.",
    )
    assigned_to = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name="assigned_tasks",
        help_text="The employee responsible for completing this task.",
    )
    created_by = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        related_name="created_tasks",
        help_text="The employee who created this task.",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="BACKLOG",
        help_text="Current stage of the task in the workflow.",
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="MEDIUM",
        help_text="Urgency/importance of this task.",
    )
    due_date = models.DateField(
        null=True, blank=True, help_text="Target completion date for this task."
    )
    estimated_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Estimated hours to complete this task.",
    )
    actual_hours = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Actual hours spent on this task (logged by assignee).",
    )
    tags = models.CharField(
        max_length=255,
        blank=True,
        help_text="Comma-separated tags for filtering, e.g. 'backend,api,bug'.",
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Timestamp when the task was moved to DONE status.",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-priority", "due_date", "title"]
        verbose_name = "Task"
        verbose_name_plural = "Tasks"

    def __str__(self):
        return f"[{self.project.code}] {self.title} [{self.status}]"


class TaskComment(models.Model):
    """
    A comment or progress update posted on a task.
    Enables team communication within the context of a specific task.
    """

    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="comments",
        help_text="The task this comment belongs to.",
    )
    author = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="task_comments",
        help_text="The employee who wrote this comment.",
    )
    content = models.TextField(help_text="The text content of the comment or update.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]
        verbose_name = "Task Comment"
        verbose_name_plural = "Task Comments"

    def __str__(self):
        return f"Comment by {self.author.full_name} on [{self.task.title}]"
