from django.contrib import admin
from .models import Employee, WeeklyTimesheet, DailyEntry

# Register your models here.



@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    ordering = ("name",)

class DailyEntryInline(admin.TabularInline):
    model = DailyEntry
    extra = 5
    max_num = 7


@admin.register(WeeklyTimesheet)
class WeeklyTimesheetAdmin(admin.ModelAdmin):
    list_display = ("employee", "week_start", "total_hours", "created_at")
    list_filter = ("week_start",)
    search_fields = ("employee__name",)    


@admin.register(DailyEntry)
class DailyEntryAdmin(admin.ModelAdmin):
    list_display = ("timesheet", "day", "total_minutes")
    list_filter = ("day",)
    search_fields = ("timesheet__employee__name",)