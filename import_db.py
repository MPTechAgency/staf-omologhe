import sqlite3
import json
import os

NEW_DATABASE = 'new_database.db'
IMPORT_FILE = 'database_export.json'

def import_db():
    # Verifica che il file di importazione esista
    if not os.path.exists(IMPORT_FILE):
        print(f"File {IMPORT_FILE} non trovato.")
        return

    # Connessione al nuovo database
    conn = sqlite3.connect(NEW_DATABASE)
    cursor = conn.cursor()

    # Carica i dati dal file JSON
    with open(IMPORT_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # Inserisci i dati nelle tabelle
    for table, rows in data.items():
        if not rows:
            continue  # Salta tabelle vuote
        columns = ', '.join(rows[0].keys())
        placeholders = ', '.join(['?'] * len(rows[0]))
        for row in rows:
            values = tuple(row.values())
            cursor.execute(f"INSERT INTO {table} ({columns}) VALUES ({placeholders})")

    conn.commit()
    conn.close()
    print(f"I dati sono stati importati con successo in {NEW_DATABASE}")

if __name__ == "__main__":
    import_db()
