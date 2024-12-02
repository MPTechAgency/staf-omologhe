import sqlite3
import json
import os

DATABASE = 'database.db'
EXPORT_FILE = 'database_export.json'

def export_db():
    # Connessione al database
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()

    # Ottieni i dati dalle tabelle
    data = {}
    for table in ['documenti', 'cassoni', 'produttori', 'impianti']:
        cursor.execute(f"SELECT * FROM {table}")
        columns = [column[0] for column in cursor.description]
        rows = cursor.fetchall()
        data[table] = [dict(zip(columns, row)) for row in rows]

    # Salva i dati in un file JSON
    with open(EXPORT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    conn.close()
    print(f"I dati sono stati esportati con successo in {EXPORT_FILE}")

if __name__ == "__main__":
    export_db()

