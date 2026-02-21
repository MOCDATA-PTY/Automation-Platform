"""
Run from automations/ directory:
  python add_sample_subtasks.py
Adds 2-3 subtasks per existing parent task.
"""
import os, sys, django
from datetime import date

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'automations.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from dashboard.models import ProjectTask

def get(title):
    try:
        return ProjectTask.objects.get(title=title)
    except ProjectTask.DoesNotExist:
        print(f'  !! Parent not found: {title}')
        return None

def sub(parent, title, desc, status, priority, start, end):
    if ProjectTask.objects.filter(title=title, parent=parent).exists():
        print(f'  ~ skip: {title}')
        return
    ProjectTask.objects.create(
        title=title, description=desc, status=status, priority=priority,
        parent=parent, start_date=start, end_date=end,
    )
    print(f'  + {title}')

subtasks = [
    # ── Budgeting App ──────────────────────────────────────────────────
    ('[Budget] Requirements & Scoping', [
        ('Stakeholder interviews & workshops',     'Conduct sessions with all stakeholders to gather functional requirements.', 'done', 'high',   date(2026,1,5),  date(2026,1,10)),
        ('User story documentation',               'Write and prioritise user stories in Jira; define acceptance criteria.',    'done', 'medium', date(2026,1,11), date(2026,1,17)),
    ]),
    ('[Budget] Database Schema Design', [
        ('ER diagram & table definitions',         'Draft entity-relationship diagram; define all columns and data types.',     'done', 'high',   date(2026,1,13), date(2026,1,20)),
        ('Indexing & migration strategy',          'Define indexes for performance; plan zero-downtime migration strategy.',   'done', 'medium', date(2026,1,21), date(2026,1,27)),
    ]),
    ('[Budget] Backend API — Auth & Accounts', [
        ('JWT auth endpoints',                     'Implement /register, /login, /refresh, /logout with JWT tokens.',          'in_progress', 'critical', date(2026,1,26), date(2026,2,7)),
        ('Account CRUD & password reset',          'Account create/update/deactivate endpoints; email-based password reset.',  'in_progress', 'high',     date(2026,2,8),  date(2026,2,20)),
    ]),
    ('[Budget] Backend API — Transactions & Categories', [
        ('Transaction CRUD endpoints',             'Create/read/update/delete transaction records with pagination and filters.','in_progress', 'high',   date(2026,2,10), date(2026,2,24)),
        ('CSV/Excel bulk import',                  'Parse uploaded CSV/Excel, validate, and bulk-insert transaction rows.',    'todo',        'medium', date(2026,2,25), date(2026,3,7)),
    ]),
    ('[Budget] Budget Rules & Alerts Engine', [
        ('Budget threshold configuration',         'API to define per-category monthly budget caps with rollover logic.',      'todo', 'high',   date(2026,3,2),  date(2026,3,14)),
        ('Alert dispatch service',                 'Background job to check budgets hourly; send email/push on breach.',       'todo', 'medium', date(2026,3,15), date(2026,3,27)),
    ]),
    ('[Budget] Reporting & Analytics Module', [
        ('Monthly summary reports',                'Generate PDF/Excel summary of income vs spend per category per month.',    'todo', 'medium', date(2026,3,16), date(2026,3,28)),
        ('Year-on-year comparison charts',         'API endpoints returning chart data for multi-year spend comparisons.',     'todo', 'low',    date(2026,3,29), date(2026,4,10)),
    ]),
    ('[Budget] Frontend UI — Dashboard & Charts', [
        ('Balance overview widget',                'Current balance, income vs spend cards with sparkline trend chart.',       'todo', 'high',   date(2026,3,23), date(2026,4,5)),
        ('Category breakdown chart',               'Pie/donut chart with drill-down; monthly filter; top-5 categories list.', 'todo', 'medium', date(2026,4,6),  date(2026,4,24)),
    ]),
    ('[Budget] Frontend UI — Transaction Management', [
        ('Transaction list & filters',             'Sortable table with search, date range, category, and amount filters.',   'backlog', 'medium', date(2026,4,14), date(2026,4,28)),
        ('Bulk edit & category assignment',        'Multi-select rows; bulk-assign category; split transaction flow.',        'backlog', 'low',    date(2026,4,29), date(2026,5,9)),
    ]),
    ('[Budget] QA & Integration Testing', [
        ('Automated E2E test suite',               'Playwright tests covering all critical user flows end-to-end.',           'backlog', 'high',   date(2026,5,4),  date(2026,5,14)),
        ('Load & security testing',                'k6 load tests at 500 RPS; OWASP ZAP security scan; remediate findings.', 'backlog', 'high',   date(2026,5,15), date(2026,5,22)),
    ]),
    ('[Budget] Staging Deploy & UAT', [
        ('Deploy to staging environment',          'Docker/K8s staging deploy; smoke tests; seeded demo data.',               'backlog', 'critical', date(2026,5,19), date(2026,5,26)),
        ('UAT with pilot users',                   '5 pilot users run scripted scenarios; capture and prioritise feedback.',  'backlog', 'high',     date(2026,5,27), date(2026,6,6)),
    ]),
    ('[Budget] Production Launch', [
        ('Production deployment & monitoring',     'Blue-green deploy to production; Sentry, uptime, and alerting configured.','backlog', 'critical', date(2026,6,9),  date(2026,6,14)),
        ('Launch comms & hypercare',               'Announce to users; monitor closely for 5 days; rapid-response support.',  'backlog', 'high',     date(2026,6,15), date(2026,6,20)),
    ]),

    # ── Legal System ──────────────────────────────────────────────────
    ('[Legal] Legal Requirements Analysis', [
        ('POPIA/GDPR compliance mapping',          'Map all data flows to POPIA and GDPR obligations; produce gap analysis.', 'done', 'critical', date(2026,1,8),  date(2026,1,16)),
        ('Document retention rules',               'Define retention periods per document type; audit trail requirements.',   'done', 'high',     date(2026,1,17), date(2026,1,24)),
    ]),
    ('[Legal] System Architecture & Data Model', [
        ('Entity design & RBAC model',             'Define Matter, Client, Document, Task entities; role-permission matrix.', 'done', 'high',   date(2026,1,20), date(2026,1,30)),
        ('Infrastructure architecture',            'AWS/Azure topology; DB replication; backup and DR strategy.',             'done', 'medium', date(2026,1,31), date(2026,2,7)),
    ]),
    ('[Legal] Matter & Case Management Module', [
        ('Matter lifecycle & status workflow',     'Create/assign matters; status machine (open→active→review→closed).',     'in_progress', 'critical', date(2026,2,3),  date(2026,2,21)),
        ('Linked parties & conflict check',        'Associate clients, opponents, counsel to matters; conflict-of-interest.', 'todo',        'high',     date(2026,2,22), date(2026,3,14)),
    ]),
    ('[Legal] Document Management & Version Control', [
        ('Upload, preview & version history',      'Secure S3 upload; version chain; in-browser PDF/Word preview.',          'todo', 'high',   date(2026,2,24), date(2026,3,20)),
        ('Full-text search & expiry tracking',     'Elasticsearch indexing of documents; expiry alerts per retention policy.','todo', 'medium', date(2026,3,21), date(2026,4,4)),
    ]),
    ('[Legal] Client Portal & Secure Messaging', [
        ('Client dashboard & matter status',       'Portal showing matter status, documents, next steps; 2FA login.',        'todo', 'high',   date(2026,3,17), date(2026,4,6)),
        ('Encrypted messaging per matter',         'End-to-end encrypted chat thread per matter; read receipts; audit log.',  'todo', 'medium', date(2026,4,7),  date(2026,4,25)),
    ]),
    ('[Legal] Time Tracking & Billing Engine', [
        ('Time entry & billable classification',   'Attorney time entry with matter, rate, and billable/non-billable flag.',  'todo', 'medium', date(2026,4,1),  date(2026,4,16)),
        ('Invoice generation & trust accounting',  'Generate itemised invoices; trust account ledger; payment reconciliation.','todo', 'medium', date(2026,4,17), date(2026,5,2)),
    ]),
    ('[Legal] Compliance & Audit Logs', [
        ('Immutable audit trail',                  'Append-only log of all data access, mutations, and exports.',            'todo', 'critical', date(2026,4,14), date(2026,4,25)),
        ('Compliance reporting dashboard',         'Dashboard showing data access stats, outstanding retention actions.',    'todo', 'high',     date(2026,4,26), date(2026,5,9)),
    ]),
    ('[Legal] Calendar & Deadline Management', [
        ('Court date & statute tracking',          'Add court dates to matters; statute-of-limitations countdown widget.',   'backlog', 'high',   date(2026,4,27), date(2026,5,10)),
        ('Automated reminders & iCal feed',        'Email/push reminders T-7, T-3, T-1 days; iCal subscription feed.',      'backlog', 'medium', date(2026,5,11), date(2026,5,23)),
    ]),
    ('[Legal] Security Hardening & Pen Test', [
        ('Penetration testing engagement',         'Engage third-party pen testers; provide test environment and scope.',    'backlog', 'critical', date(2026,5,18), date(2026,5,28)),
        ('Vulnerability remediation',              'Triage findings; patch critical/high within SLA; re-test.',              'backlog', 'critical', date(2026,5,29), date(2026,6,6)),
    ]),
    ('[Legal] User Training & Go-Live', [
        ('Staff training & user manual',           'Deliver 3 training sessions; publish user manual and video walkthroughs.','backlog', 'high',   date(2026,6,8),  date(2026,6,20)),
        ('Production go-live & hypercare',         'Go-live deployment; 30-day hypercare with dedicated support channel.',   'backlog', 'high',   date(2026,6,21), date(2026,7,4)),
    ]),
]

created = 0
for parent_title, subs in subtasks:
    parent = get(parent_title)
    if not parent:
        continue
    for title, desc, status, priority, start, end in subs:
        sub(parent, title, desc, status, priority, start, end)
        created += 1

print(f'\nDone — {created} subtasks created.')
