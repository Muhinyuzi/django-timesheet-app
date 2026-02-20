from django.contrib import admin
from .models import Employee

# Register your models here.



@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)
