from django.db import models

class TurnoverData(models.Model):
    debtor = models.CharField(max_length=100)
    debtor_name = models.CharField(max_length=255)
    value = models.DecimalField(max_digits=15, decimal_places=2)
    date = models.DateField()
    date_fixed = models.CharField(max_length=20)
    branch = models.CharField(max_length=50)

    class Meta:
        db_table = 'turnover_data'
        managed = False

    def __str__(self):
        return f"{self.debtor} - {self.branch}"
