import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'].replace('postgresql://','postgres://'), sslmode='require')
cur = conn.cursor()
cur.execute("ALTER TABLE sales ADD COLUMN IF NOT EXISTS payment_status VARCHAR(20) NOT NULL DEFAULT 'pagado'")
conn.commit()
print('Migracion sales lista')
cur.close()
conn.close()
