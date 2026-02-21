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

    def clean(self):
        cleaned = super().clean()

        am = cleaned.get("arrival_morning")
        ld = cleaned.get("lunch_departure")
        lr = cleaned.get("lunch_return")
        ae = cleaned.get("arrival_evening")
        de = cleaned.get("departure_evening")

        # Helper
        def require_pair(a, b, field_a, field_b, message):
            if (a is None) ^ (b is None):
                if a is None:
                    self.add_error(field_a, message)
                if b is None:
                    self.add_error(field_b, message)

        # Bloc matin
        require_pair(
            am, ld,
            "arrival_morning", "lunch_departure",
            "Veuillez compléter le bloc du matin (arrivée + départ dîner)."
        )

        # Bloc dîner
        require_pair(
            ld, lr,
            "lunch_departure", "lunch_return",
            "Veuillez compléter le bloc du dîner (départ + retour)."
        )

        # Bloc soir
        require_pair(
            ae, de,
            "arrival_evening", "departure_evening",
            "Veuillez compléter le bloc du soir (arrivée + départ)."
        )

        # Ordre logique
        if am and ld and not (am < ld):
            self.add_error("lunch_departure", "Le départ dîner doit être après l’arrivée matin.")

        if ld and lr and not (ld < lr):
            self.add_error("lunch_return", "Le retour dîner doit être après le départ dîner.")

        if ae and de and not (ae < de):
            self.add_error("departure_evening", "Le départ soir doit être après l’arrivée soir.")

        # Cohérence globale optionnelle (pro)
        if lr and ae and ae < lr:
            self.add_error("arrival_evening", "L’arrivée soir doit être après le retour dîner.")

        return cleaned