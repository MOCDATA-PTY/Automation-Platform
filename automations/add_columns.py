"""Check existing columns and add missing ones."""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'automations.settings'
django.setup()

from django.db import connection

cursor = connection.cursor()
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name = 'useu_contacts' ORDER BY ordinal_position")
cols = [r[0] for r in cursor.fetchall()]
print('Existing columns:', cols)

# New columns to add
new_cols = {
    'title': "VARCHAR(255) DEFAULT ''",
    'mode': "VARCHAR(50) DEFAULT ''",
    'job_title': "VARCHAR(255) DEFAULT ''",
    'address': "VARCHAR(500) DEFAULT ''",
    'branch': "VARCHAR(50) DEFAULT ''",
    'unloco': "VARCHAR(50) DEFAULT ''",
    'city': "VARCHAR(255) DEFAULT ''",
    'fax': "VARCHAR(100) DEFAULT ''",
    'sales_rep': "VARCHAR(100) DEFAULT ''",
    'touchpoint_3': "VARCHAR(50) DEFAULT ''",
    'touchpoint_4': "VARCHAR(50) DEFAULT ''",
    'touchpoint_5': "VARCHAR(50) DEFAULT ''",
    'touchpoint_6': "VARCHAR(50) DEFAULT ''",
    'touchpoint_7': "VARCHAR(50) DEFAULT ''",
    'touchpoint_8': "VARCHAR(50) DEFAULT ''",
    'touchpoint_9': "VARCHAR(50) DEFAULT ''",
    'touchpoint_10': "VARCHAR(50) DEFAULT ''",
    'journey_status': "VARCHAR(50) DEFAULT 'Active'",
    'tp2_sent_on': "VARCHAR(50) DEFAULT ''",
    'tp3_sent_on': "VARCHAR(50) DEFAULT ''",
    'tp4_sent_on': "VARCHAR(50) DEFAULT ''",
    'tp5_sent_on': "VARCHAR(50) DEFAULT ''",
    'tp6_sent_on': "VARCHAR(50) DEFAULT ''",
    'tp7_sent_on': "VARCHAR(50) DEFAULT ''",
    'tp8_sent_on': "VARCHAR(50) DEFAULT ''",
    'tp9_sent_on': "VARCHAR(50) DEFAULT ''",
    'tp10_sent_on': "VARCHAR(50) DEFAULT ''",
}

for col_name, col_type in new_cols.items():
    if col_name not in cols:
        sql = f"ALTER TABLE useu_contacts ADD COLUMN {col_name} {col_type}"
        cursor.execute(sql)
        print(f"  Added: {col_name}")
    else:
        print(f"  Exists: {col_name}")

print("\nDone!")
