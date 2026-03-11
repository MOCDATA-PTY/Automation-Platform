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


class USEUContact(models.Model):
    STATUS_CHOICES = [
        ('Active', 'Active'),
        ('Inactive', 'Inactive'),
        ('Faulty Data', 'Faulty Data'),
    ]

    title = models.CharField(max_length=255, blank=True, default='')
    org_name = models.CharField(max_length=500, blank=True, default='')
    default = models.CharField(max_length=10, blank=True, default='')
    contact_name = models.CharField(max_length=255, blank=True, default='')
    mode = models.CharField(max_length=50, blank=True, default='')
    attach = models.CharField(max_length=50, blank=True, default='')
    job_title = models.CharField(max_length=255, blank=True, default='')
    address = models.CharField(max_length=500, blank=True, default='')
    branch = models.CharField(max_length=50, blank=True, default='')
    unloco = models.CharField(max_length=50, blank=True, default='')
    city = models.CharField(max_length=255, blank=True, default='')
    phone = models.CharField(max_length=100, blank=True, default='')
    fax = models.CharField(max_length=100, blank=True, default='')
    email = models.CharField(max_length=255, blank=True, default='')
    sales_rep = models.CharField(max_length=100, blank=True, default='')
    touchpoint_1 = models.CharField(max_length=50, blank=True, default='')
    touchpoint_2 = models.CharField(max_length=50, blank=True, default='')
    touchpoint_3 = models.CharField(max_length=50, blank=True, default='')
    touchpoint_4 = models.CharField(max_length=50, blank=True, default='')
    touchpoint_5 = models.CharField(max_length=50, blank=True, default='')
    touchpoint_6 = models.CharField(max_length=50, blank=True, default='')
    touchpoint_7 = models.CharField(max_length=50, blank=True, default='')
    touchpoint_8 = models.CharField(max_length=50, blank=True, default='')
    touchpoint_9 = models.CharField(max_length=50, blank=True, default='')
    touchpoint_10 = models.CharField(max_length=50, blank=True, default='')
    last_touch = models.CharField(max_length=50, blank=True, default='')
    journey_status = models.CharField(max_length=50, blank=True, default='Active')
    tp1_sent_on = models.CharField(max_length=50, blank=True, default='')
    tp2_sent_on = models.CharField(max_length=50, blank=True, default='')
    tp3_sent_on = models.CharField(max_length=50, blank=True, default='')
    tp4_sent_on = models.CharField(max_length=50, blank=True, default='')
    tp5_sent_on = models.CharField(max_length=50, blank=True, default='')
    tp6_sent_on = models.CharField(max_length=50, blank=True, default='')
    tp7_sent_on = models.CharField(max_length=50, blank=True, default='')
    tp8_sent_on = models.CharField(max_length=50, blank=True, default='')
    tp9_sent_on = models.CharField(max_length=50, blank=True, default='')
    tp10_sent_on = models.CharField(max_length=50, blank=True, default='')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='Active')
    tp1_processing_id = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'useu_contacts'
        ordering = ['id']

    def __str__(self):
        return self.org_name


class TouchpointTemplate(models.Model):
    """Email template for each touchpoint (1-10). One template per touchpoint number."""
    touchpoint_number = models.IntegerField(unique=True)
    subject = models.CharField(max_length=500, default='')
    body = models.TextField(default='')
    body_html = models.TextField(default='', blank=True)
    signature = models.TextField(default='', blank=True)
    attachment = models.FileField(upload_to='touchpoint_attachments/', blank=True, null=True)
    days_after_previous = models.IntegerField(default=7, help_text='Days after previous touchpoint to send this one')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'touchpoint_templates'
        ordering = ['touchpoint_number']

    def __str__(self):
        return f'Touchpoint {self.touchpoint_number}'


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
