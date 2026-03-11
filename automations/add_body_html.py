import psycopg2

conn = psycopg2.connect(
    host='167.88.43.168', port=5432,
    dbname='turnover_data', user='powerbi', password='Hrhk@2025!'
)
cur = conn.cursor()
cur.execute("ALTER TABLE touchpoint_templates ADD COLUMN IF NOT EXISTS body_html TEXT DEFAULT ''")
conn.commit()
print('body_html column added')
cur.close()
conn.close()
