from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class ProjectTask(models.Model):
    STATUS_CHOICES = [
        ('backlog', 'Backlog'),
        ('todo', 'To Do'),
        ('in_progress', 'In Progress'),
        ('review', 'Review'),
        ('done', 'Done'),
    ]
    PRIORITY_CHOICES = [
        ('critical', 'Critical'),
        ('high', 'High'),
        ('medium', 'Medium'),
        ('low', 'Low'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='backlog')
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    project_name = models.CharField(max_length=100, blank=True, default='')
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL, related_name='subtasks')
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']

    def __str__(self):
        return self.title


class PowerBIEmbed(models.Model):
    page_name = models.CharField(max_length=50, unique=True)
    embed_url = models.TextField(blank=True, default='')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'powerbi_embed'

    def __str__(self):
        return self.page_name


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    dark_mode = models.BooleanField(default=False)

    class Meta:
        db_table = 'user_profile'

    def __str__(self):
        return self.user.username


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.get_or_create(user=instance)


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
