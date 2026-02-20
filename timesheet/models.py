from django.db import models

# Create your models here.


class Employee(models.Model):
    name = models.CharField("Nom de l’employé", max_length=150)
    is_active = models.BooleanField("Actif", default=True)
    created_at = models.DateTimeField("Créé le", auto_now_add=True)

    class Meta:
        verbose_name = "Employé"
        verbose_name_plural = "Employés"
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name
