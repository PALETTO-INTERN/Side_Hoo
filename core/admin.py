from django.contrib import admin

# Register your models here.
# core/admin.py

from django.contrib import admin
from .models import UserProfile, Task, TaskApplication

# 1. UserProfile 모델 등록
@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'points', 'tasks_completed')
    search_fields = ('user__username', 'bio')
    list_filter = ('tasks_completed',)
    
# 2. Task 모델 등록
@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'registrant', 'reward_points', 'status', 'due_date', 'assigned_to')
    list_filter = ('status', 'created_at', 'due_date')
    search_fields = ('title', 'content', 'registrant__username')
    raw_id_fields = ('registrant', 'assigned_to') # 사용자 검색을 쉽게

# 3. TaskApplication 모델 등록
@admin.register(TaskApplication)
class TaskApplicationAdmin(admin.ModelAdmin):
    list_display = ('task', 'applicant', 'status', 'applied_at')
    list_filter = ('status', 'applied_at')
    search_fields = ('task__title', 'applicant__username')
    raw_id_fields = ('task', 'applicant')