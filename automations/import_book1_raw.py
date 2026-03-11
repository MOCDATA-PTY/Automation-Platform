"""Import Book1 1.xlsx into useu_contacts using raw SQL."""
import openpyxl
import psycopg2

EXCEL_PATH = r'C:\Users\berna\OneDrive\Desktop\Automation-Platform-master\Automation-Platform-master\automations\templates\Book1 1.xlsx'

conn = psycopg2.connect(
    dbname='turnover_data',
    user='powerbi',
    password='your_secure_password',
    host='167.88.43.168',
    port='5432'
)
conn.autocommit = True
cur = conn.cursor()

# Clear existing data
cur.execute("DELETE FROM useu_contacts")
print("Cleared existing data")

wb = openpyxl.load_workbook(EXCEL_PATH, read_only=True)
ws = wb.active

def safe(val):
    if val is None:
        return ''
    s = str(val).strip().lstrip('\t')
    return s

INSERT_SQL = """INSERT INTO useu_contacts (
    title, org_name, "default", contact_name, mode, attach, job_title,
    address, branch, unloco, city, phone, fax, email, sales_rep,
    touchpoint_1, touchpoint_2, touchpoint_3, touchpoint_4, touchpoint_5,
    touchpoint_6, touchpoint_7, touchpoint_8, touchpoint_9, touchpoint_10,
    last_touch, journey_status, tp1_sent_on, tp2_sent_on, tp3_sent_on,
    tp5_sent_on, tp4_sent_on, tp6_sent_on, tp7_sent_on, tp8_sent_on,
    tp9_sent_on, tp10_sent_on, status
) VALUES (
    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,
    %s,%s,%s,%s,%s,%s,%s,%s
)"""

count = 0
errors = 0
for row in ws.iter_rows(min_row=2, values_only=True):
    email_val = safe(row[13] if len(row) > 13 else '')
    status = safe(row[26] if len(row) > 26 else 'Active')
    if '<' in email_val and '>' in email_val:
        status = 'Faulty Data'
    if not status:
        status = 'Active'

    vals = (
        safe(row[0])[:255],   # title
        safe(row[1])[:500],   # org_name
        safe(row[2])[:10],    # default
        safe(row[3])[:255],   # contact_name
        safe(row[4])[:50],    # mode
        safe(row[5])[:50],    # attach
        safe(row[6])[:255],   # job_title
        safe(row[7])[:500],   # address
        safe(row[8])[:50],    # branch
        safe(row[9])[:50],    # unloco
        safe(row[10])[:255],  # city
        safe(row[11])[:100],  # phone
        safe(row[12])[:100],  # fax
        email_val[:255],      # email
        safe(row[14])[:100],  # sales_rep
        safe(row[15])[:50],   # touchpoint_1
        safe(row[16])[:50],   # touchpoint_2
        safe(row[17])[:50],   # touchpoint_3
        safe(row[18])[:50],   # touchpoint_4
        safe(row[19])[:50],   # touchpoint_5
        safe(row[20])[:50],   # touchpoint_6
        safe(row[21])[:50],   # touchpoint_7
        safe(row[22])[:50],   # touchpoint_8
        safe(row[23])[:50],   # touchpoint_9
        safe(row[24])[:50],   # touchpoint_10
        safe(row[25])[:50],   # last_touch
        status[:50],          # journey_status
        safe(row[27])[:50],   # tp1_sent_on
        safe(row[28])[:50],   # tp2_sent_on
        safe(row[29])[:50],   # tp3_sent_on
        safe(row[30])[:50],   # tp5_sent_on
        safe(row[31])[:50],   # tp4_sent_on
        safe(row[32])[:50],   # tp6_sent_on
        safe(row[33])[:50],   # tp7_sent_on
        safe(row[34])[:50],   # tp8_sent_on
        safe(row[35])[:50],   # tp9_sent_on
        safe(row[36])[:50],   # tp10_sent_on
        status[:20],          # status
    )
    try:
        cur.execute(INSERT_SQL, vals)
        count += 1
    except Exception as e:
        errors += 1
        if errors <= 5:
            print(f"  Error row {count + errors}: {e}")
    
    if count % 5000 == 0 and count > 0:
        print(f"  Inserted {count} rows...")

wb.close()
cur.close()
conn.close()

print(f"\nDone! Inserted {count} rows, {errors} errors.")
