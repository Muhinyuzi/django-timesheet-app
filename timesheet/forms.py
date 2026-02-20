from django import forms
from .models import WeeklyTimesheet, DailyEntry
from django.forms import modelformset_factory
from datetime import timedelta


class WeeklyTimesheetForm(forms.ModelForm):
    class Meta:
        model = WeeklyTimesheet
        fields = ["employee", "week_start"]
        widgets = {
            "week_start": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_week_start(self):
        d = self.cleaned_data["week_start"]
        # weekday(): lundi=0 ... dimanche=6
        if d.weekday() != 0:
            raise forms.ValidationError("La date doit être un lundi (début de la semaine).")
        return d

    def clean(self):
        cleaned = super().clean()
        employee = cleaned.get("employee")
        week_start = cleaned.get("week_start")

        if employee and week_start:
            qs = WeeklyTimesheet.objects.filter(employee=employee, week_start=week_start)

            # Important si un jour tu réutilises ce form pour modifier une feuille existante
            if self.instance and self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            if qs.exists():
                raise forms.ValidationError(
                    "Une feuille de temps existe déjà pour cet employé pour cette semaine."
                )

        return cleaned
    

class DailyEntryForm(forms.ModelForm):
    class Meta:
        model = DailyEntry
        fields = [
            "arrival_morning",
            "lunch_departure",
            "lunch_return",
            "arrival_evening",
            "departure_evening",
        ]
        widgets = {
            field: forms.TimeInput(attrs={"type": "time"})
            for field in fields
        }    