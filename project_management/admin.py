from django.contrib import admin
from .models import Project, ProjectMember, Task, TaskComment

admin.site.register(Project)
admin.site.register(ProjectMember)
admin.site.register(Task)
admin.site.register(TaskComment)
