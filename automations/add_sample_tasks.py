"""
Run from automations/ directory:
  python add_sample_tasks.py
"""
import os
import sys
import django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from dashboard.models import ProjectTask

sample_tasks = [
    # ── Budgeting App ─────────────────────────────────────────────────────
    {
        'title': '[Budget] Requirements & Scoping',
        'description': 'Gather stakeholder requirements, define feature scope, document user stories and acceptance criteria for the budgeting application.',
        'status': 'done',
        'priority': 'high',
        'start_date': date(2026, 1, 5),
        'end_date':   date(2026, 1, 17),
    },
    {
        'title': '[Budget] Database Schema Design',
        'description': 'Design tables for accounts, transactions, categories, budgets, forecasts. Define relationships and indexing strategy.',
        'status': 'done',
        'priority': 'high',
        'start_date': date(2026, 1, 13),
        'end_date':   date(2026, 1, 27),
    },
    {
        'title': '[Budget] Backend API — Auth & Accounts',
        'description': 'Build JWT authentication, user registration/login, account management endpoints (create, update, deactivate).',
        'status': 'in_progress',
        'priority': 'critical',
        'start_date': date(2026, 1, 26),
        'end_date':   date(2026, 2, 20),
    },
    {
        'title': '[Budget] Backend API — Transactions & Categories',
        'description': 'CRUD endpoints for transactions, bulk import via CSV/Excel, automatic category detection via keyword rules.',
        'status': 'in_progress',
        'priority': 'high',
        'start_date': date(2026, 2, 10),
        'end_date':   date(2026, 3, 7),
    },
    {
        'title': '[Budget] Budget Rules & Alerts Engine',
        'description': 'Implement configurable budget thresholds, over-budget triggers, email/push alert dispatch service.',
        'status': 'todo',
        'priority': 'high',
        'start_date': date(2026, 3, 2),
        'end_date':   date(2026, 3, 27),
    },
    {
        'title': '[Budget] Reporting & Analytics Module',
        'description': 'Monthly summaries, category breakdowns, year-on-year comparisons, export to PDF/Excel.',
        'status': 'todo',
        'priority': 'medium',
        'start_date': date(2026, 3, 16),
        'end_date':   date(2026, 4, 10),
    },
    {
        'title': '[Budget] Frontend UI — Dashboard & Charts',
        'description': 'React/Vue dashboard with spending charts, balance overview, recent transactions widget, month-selector.',
        'status': 'todo',
        'priority': 'high',
        'start_date': date(2026, 3, 23),
        'end_date':   date(2026, 4, 24),
    },
    {
        'title': '[Budget] Frontend UI — Transaction Management',
        'description': 'Transaction list with filtering, bulk edit, category assignment, split transactions, receipt upload.',
        'status': 'backlog',
        'priority': 'medium',
        'start_date': date(2026, 4, 14),
        'end_date':   date(2026, 5, 9),
    },
    {
        'title': '[Budget] QA & Integration Testing',
        'description': 'End-to-end test suite covering all critical paths, load testing, security penetration testing.',
        'status': 'backlog',
        'priority': 'high',
        'start_date': date(2026, 5, 4),
        'end_date':   date(2026, 5, 22),
    },
    {
        'title': '[Budget] Staging Deploy & UAT',
        'description': 'Deploy to staging environment, run user acceptance testing with 5 pilot users, collect and action feedback.',
        'status': 'backlog',
        'priority': 'critical',
        'start_date': date(2026, 5, 19),
        'end_date':   date(2026, 6, 6),
    },
    {
        'title': '[Budget] Production Launch',
        'description': 'Production deployment, monitoring setup (Sentry, uptime), launch communications, hypercare support window.',
        'status': 'backlog',
        'priority': 'critical',
        'start_date': date(2026, 6, 9),
        'end_date':   date(2026, 6, 20),
    },

    # ── Legal System ──────────────────────────────────────────────────────
    {
        'title': '[Legal] Legal Requirements Analysis',
        'description': 'Map jurisdiction-specific compliance requirements, POPIA/GDPR obligations, document retention rules, audit trail needs.',
        'status': 'done',
        'priority': 'critical',
        'start_date': date(2026, 1, 8),
        'end_date':   date(2026, 1, 24),
    },
    {
        'title': '[Legal] System Architecture & Data Model',
        'description': 'Define entities: matters, clients, contacts, documents, tasks, billing entries. Design role-based access control model.',
        'status': 'done',
        'priority': 'high',
        'start_date': date(2026, 1, 20),
        'end_date':   date(2026, 2, 7),
    },
    {
        'title': '[Legal] Matter & Case Management Module',
        'description': 'Create, assign and track legal matters. Status workflow (open → in-progress → review → closed). Linked documents and parties.',
        'status': 'in_progress',
        'priority': 'critical',
        'start_date': date(2026, 2, 3),
        'end_date':   date(2026, 3, 14),
    },
    {
        'title': '[Legal] Document Management & Version Control',
        'description': 'Secure document upload/download, version history, check-in/check-out, full-text search, expiry tracking.',
        'status': 'todo',
        'priority': 'high',
        'start_date': date(2026, 2, 24),
        'end_date':   date(2026, 4, 4),
    },
    {
        'title': '[Legal] Client Portal & Secure Messaging',
        'description': 'Client-facing portal for document sharing, matter status visibility, encrypted messaging thread per matter.',
        'status': 'todo',
        'priority': 'high',
        'start_date': date(2026, 3, 17),
        'end_date':   date(2026, 4, 25),
    },
    {
        'title': '[Legal] Time Tracking & Billing Engine',
        'description': 'Attorney time entry, billable/non-billable classification, invoice generation, trust account management.',
        'status': 'todo',
        'priority': 'medium',
        'start_date': date(2026, 4, 1),
        'end_date':   date(2026, 5, 2),
    },
    {
        'title': '[Legal] Compliance & Audit Logs',
        'description': 'Immutable audit trail for all data access and mutations, compliance reporting dashboard, automated retention-expiry alerts.',
        'status': 'todo',
        'priority': 'critical',
        'start_date': date(2026, 4, 14),
        'end_date':   date(2026, 5, 9),
    },
    {
        'title': '[Legal] Calendar & Deadline Management',
        'description': 'Court date tracking, statute-of-limitations countdown, automated reminders, iCal feed integration.',
        'status': 'backlog',
        'priority': 'high',
        'start_date': date(2026, 4, 27),
        'end_date':   date(2026, 5, 23),
    },
    {
        'title': '[Legal] Security Hardening & Pen Test',
        'description': 'Third-party penetration testing, vulnerability remediation, OWASP compliance review, data-at-rest encryption audit.',
        'status': 'backlog',
        'priority': 'critical',
        'start_date': date(2026, 5, 18),
        'end_date':   date(2026, 6, 6),
    },
    {
        'title': '[Legal] User Training & Go-Live',
        'description': 'Staff training sessions, user manual, production deployment, 30-day hypercare support, success metrics baseline.',
        'status': 'backlog',
        'priority': 'high',
        'start_date': date(2026, 6, 8),
        'end_date':   date(2026, 7, 4),
    },
]

created = 0
for t in sample_tasks:
    # Skip if already exists (avoid duplicates on re-run)
    if not ProjectTask.objects.filter(title=t['title']).exists():
        ProjectTask.objects.create(**t)
        print(f"  + {t['title']}")
        created += 1
    else:
        print(f"  ~ skip (exists): {t['title']}")

print(f"\nDone — {created} tasks created.")
