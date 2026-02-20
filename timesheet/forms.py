from django import forms
from .models import WeeklyTimesheet, DailyEntry
from django.forms import modelformset_factory


class WeeklyTimesheetForm(forms.ModelForm):
    class Meta:
        model = WeeklyTimesheet
        fields = ["employee", "week_start"]
        widgets = {
            "week_start": forms.DateInput(attrs={"type": "date"}),
        }

    def clean_week_start(self):
        week_start = self.cleaned_data["week_start"]
        # optionnel: ici on pourrait valider que c’est un lundi
        return week_start
    

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