import os
DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://tiendita_app:AppPass123@localhost:5432/tiendita_db')
SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-me')
import psycopg2
from config import DATABASE_URL

try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("Conexión exitosa:", cur.fetchone())
    cur.close()
    conn.close()
except Exception as e:
    print("Error al conectar:", e)
