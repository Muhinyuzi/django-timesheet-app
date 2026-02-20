from django.shortcuts import render, redirect
from django.contrib import messages
from django.shortcuts import get_object_or_404
from django.db import IntegrityError
from django.forms import modelformset_factory

# Create your views here.

from .models import Employee, WeeklyTimesheet, DailyEntry
from .forms import WeeklyTimesheetForm, DailyEntryForm


def employee_list(request):
    employees = Employee.objects.filter(is_active=True)
    return render(request, "timesheet/employee_list.html", {
        "employees": employees
    })


def timesheet_list(request):
    timesheets = WeeklyTimesheet.objects.select_related("employee").all()
    return render(request, "timesheet/timesheet_list.html", {"timesheets": timesheets})

def timesheet_create(request):
    if request.method == "POST":
        form = WeeklyTimesheetForm(request.POST)
        if form.is_valid():
            try:
                ts = form.save()
                messages.success(request, "Feuille de temps créée avec succès.")
                # prochaine étape: rediriger vers detail page
                return redirect("timesheet:timesheet_detail", pk=ts.pk)
            except IntegrityError:
                form.add_error(None, "Une feuille existe déjà pour cet employé et cette semaine.")
    else:
        form = WeeklyTimesheetForm()

    return render(request, "timesheet/timesheet_form.html", {"form": form})

def timesheet_detail(request, pk):
    timesheet = get_object_or_404(WeeklyTimesheet, pk=pk)

    # S'assurer que Lun → Ven existent
    for day_code, _ in DailyEntry.Weekday.choices[:5]:
        DailyEntry.objects.get_or_create(
            timesheet=timesheet,
            day=day_code
        )

    queryset = timesheet.entries.all().order_by("day")

    DailyEntryFormSet = modelformset_factory(
        DailyEntry,
        form=DailyEntryForm,
        extra=0
    )

    if request.method == "POST":
        formset = DailyEntryFormSet(request.POST, queryset=queryset)
        if formset.is_valid():
            formset.save()
    else:
        formset = DailyEntryFormSet(queryset=queryset)

    return render(request, "timesheet/timesheet_detail.html", {
        "timesheet": timesheet,
        "formset": formset
    })