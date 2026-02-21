"""
Run from automations/ directory:
  python set_project_names.py
Sets project_name on existing parent tasks based on title prefix.
"""
import os, sys, django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from dashboard.models import ProjectTask

n1 = ProjectTask.objects.filter(title__startswith='[Budget]', parent=None).update(project_name='Budgeting App')
n2 = ProjectTask.objects.filter(title__startswith='[Legal]', parent=None).update(project_name='Legal System')

print(f'Budgeting App: {n1} tasks updated')
print(f'Legal System:  {n2} tasks updated')
print('Done.')
