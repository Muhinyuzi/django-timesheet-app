from django.urls import path
from . import views

app_name = "timesheet"

urlpatterns = [
    path("employees/", views.employee_list, name="employee_list"),
    path("timesheets/", views.timesheet_list, name="timesheet_list"),
    path("timesheets/new/", views.timesheet_create, name="timesheet_create"),
    path("timesheets/<int:pk>/", views.timesheet_detail, name="timesheet_detail"),
    path("payroll/summary/", views.payroll_summary, name="payroll_summary"),
]