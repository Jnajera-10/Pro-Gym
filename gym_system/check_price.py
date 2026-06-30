import psycopg2, os
conn = psycopg2.connect(os.environ['DATABASE_URL'].replace('postgresql://','postgres://'), sslmode='require')
cur = conn.cursor()
cur.execute("SELECT name, sale_price, quantity FROM products WHERE name = 'AGUA'")
print(cur.fetchone())
cur.close()
conn.close()
