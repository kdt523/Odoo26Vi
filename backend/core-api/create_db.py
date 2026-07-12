import psycopg2
from psycopg2 import sql

def create_db():
    # Connect to the default 'postgres' database to create a new one
    conn = psycopg2.connect(
        dbname='postgres',
        user='postgres',
        password='optusyes523',
        host='localhost',
        port=5432
    )
    conn.autocommit = True
    cursor = conn.cursor()
    
    # Check if database exists
    cursor.execute("SELECT 1 FROM pg_database WHERE datname='assetflow_db'")
    exists = cursor.fetchone()
    
    if not exists:
        cursor.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier('assetflow_db')))
        print("Database 'assetflow_db' created successfully.")
    else:
        print("Database 'assetflow_db' already exists.")
        
    cursor.close()
    conn.close()

if __name__ == '__main__':
    create_db()
