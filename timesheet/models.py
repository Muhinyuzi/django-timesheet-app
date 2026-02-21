from __future__ import annotations

from datetime import datetime, date, time, timedelta
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import models


class Employee(models.Model):
    name = models.CharField("Nom de l’employé", max_length=150)
    is_active = models.BooleanField("Actif", default=True)
    hourly_rate = models.DecimalField("Taux horaire", max_digits=8, decimal_places=2, default=Decimal("0.00"))
    weekly_regular_hours = models.DecimalField("Heures normales/semaine", max_digits=5, decimal_places=2, default=Decimal("40.00"))
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class WeeklyTimesheet(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="timesheets",
    )
    week_start = models.DateField("Début de la semaine (lundi)")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Feuille de temps"
        verbose_name_plural = "Feuilles de temps"
        unique_together = ("employee", "week_start")
        ordering = ["-week_start"]

    def __str__(self) -> str:
        return f"{self.employee.name} - {self.week_start}"

    # ✅ Validation stricte : week_start doit être lundi
    def clean(self):
        super().clean()
        if self.week_start.weekday() != 0:
            raise ValidationError({
                "week_start": "La date doit être un lundi (début de la semaine)."
            })

    # ✅ Force validation même via admin
    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    # ✅ Calcul fiable basé sur minutes (pas de float)
    @property
    def total_minutes(self) -> int:
        return sum(e.total_minutes for e in self.entries.all())

    @property
    def total_hours_decimal(self) -> Decimal:
        return (Decimal(self.total_minutes) / Decimal(60)).quantize(Decimal("0.01"))

    @property
    def total_hours(self) -> float:
        return float(self.total_hours_decimal)

    @property
    def regular_hours(self) -> Decimal:
        cap = self.employee.weekly_regular_hours
        return min(self.total_hours_decimal, cap)

    @property
    def banked_hours(self) -> Decimal:
        cap = self.employee.weekly_regular_hours
        extra = self.total_hours_decimal - cap
        return extra if extra > 0 else Decimal("0.00")
    
    @property
    def week_end(self):
        return self.week_start + timedelta(days=6)


class DailyEntry(models.Model):
    class Weekday(models.TextChoices):
        MONDAY = "MON", "Lundi"
        TUESDAY = "TUE", "Mardi"
        WEDNESDAY = "WED", "Mercredi"
        THURSDAY = "THU", "Jeudi"
        FRIDAY = "FRI", "Vendredi"
        SATURDAY = "SAT", "Samedi"
        SUNDAY = "SUN", "Dimanche"

    timesheet = models.ForeignKey(
        WeeklyTimesheet,
        on_delete=models.CASCADE,
        related_name="entries",
    )
    day = models.CharField("Jour", max_length=3, choices=Weekday.choices)

    arrival_morning = models.TimeField("Heure d’arrivée (matin)", null=True, blank=True)
    lunch_departure = models.TimeField("Départ dîner", null=True, blank=True)
    lunch_return = models.TimeField("Retour dîner", null=True, blank=True)

    arrival_evening = models.TimeField("Heure d’arrivée (soir)", null=True, blank=True)
    departure_evening = models.TimeField("Heure de départ (soir)", null=True, blank=True)

    class Meta:
        verbose_name = "Entrée journalière"
        verbose_name_plural = "Entrées journalières"
        unique_together = ("timesheet", "day")
        ordering = ["timesheet_id", "day"]

    def __str__(self) -> str:
        return f"{self.timesheet} - {self.get_day_display()}"

    def clean(self):
        """
        Validation simple:
        - si une heure est fournie, les heures liées doivent aussi être fournies (par bloc)
        - ordre logique des heures
        """
        def _lt(a: time | None, b: time | None) -> bool:
            return a is not None and b is not None and a < b

        # Matin: si l'un existe, l'autre doit exister
        if (self.arrival_morning is None) ^ (self.lunch_departure is None):
            raise ValidationError("Pour le matin, veuillez fournir l’arrivée et le départ dîner.")

        # Dîner: si l'un existe, l'autre doit exister
        if (self.lunch_departure is None) ^ (self.lunch_return is None):
            raise ValidationError("Pour le dîner, veuillez fournir le départ et le retour.")

        # Soir: si l'un existe, l'autre doit exister
        if (self.arrival_evening is None) ^ (self.departure_evening is None):
            raise ValidationError("Pour le soir, veuillez fournir l’arrivée soir et le départ soir.")

        # Ordres
        if self.arrival_morning and self.lunch_departure and not _lt(self.arrival_morning, self.lunch_departure):
            raise ValidationError("Le départ dîner doit être après l’arrivée matin.")
        if self.lunch_departure and self.lunch_return and not _lt(self.lunch_departure, self.lunch_return):
            raise ValidationError("Le retour dîner doit être après le départ dîner.")
        if self.arrival_evening and self.departure_evening and not _lt(self.arrival_evening, self.departure_evening):
            raise ValidationError("Le départ soir doit être après l’arrivée soir.")

    @staticmethod
    def _duration(start: time | None, end: time | None) -> timedelta:
        if start is None or end is None:
            return timedelta(0)

        dt0 = datetime.combine(date.today(), start)
        dt1 = datetime.combine(date.today(), end)

        if dt1 < dt0:
            return timedelta(0)  # v1: pas de quart de nuit
        return dt1 - dt0

    @property
    def total_duration(self) -> timedelta:
        morning = self._duration(self.arrival_morning, self.lunch_departure)
        evening = self._duration(self.arrival_evening, self.departure_evening)
        return morning + evening

    @property
    def total_minutes(self) -> int:
        return int(self.total_duration.total_seconds() // 60)
    
    @property
    def total_hours(self) -> float:
        return round(self.total_minutes / 60, 2)