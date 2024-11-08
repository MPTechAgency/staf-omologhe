import sqlite3

# Path al database
DATABASE = 'database.db'

def create_db():
    # Connettiamo al database (verrà creato se non esiste)
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Creiamo la tabella 'documenti' con i campi necessari
    c.execute('''
    CREATE TABLE IF NOT EXISTS documenti (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_produttore TEXT NOT NULL,
        impianto_destinazione TEXT NOT NULL,
        indirizzo_cantiere TEXT NOT NULL,
        codice_eer TEXT NOT NULL,
        data_invio DATE NOT NULL,
        data_accettazione DATE NOT NULL,
        data_scadenza DATE NOT NULL
    )
    ''')

    # Commit delle modifiche e chiusura della connessione
    conn.commit()
    conn.close()

def insert_sample_data():
    # Connessione al database
    conn = sqlite3.connect(DATABASE)
    c = conn.cursor()

    # Inseriamo alcuni dati di esempio
    c.executemany('''
    INSERT INTO documenti (nome_produttore, impianto_destinazione, indirizzo_cantiere, codice_eer, data_invio, data_accettazione, data_scadenza)
    VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', [
        ('Produttore A', 'Impianto A', 'Indirizzo A', 'EER001', '2024-01-01', '2024-01-01', '2025-01-01'),
        ('Produttore B', 'Impianto B', 'Indirizzo B', 'EER002', '2024-02-01', '2024-02-01', '2025-02-01'),
        ('Produttore C', 'Impianto C', 'Indirizzo C', 'EER003', '2024-03-01', '2024-03-01', '2025-03-01'),
        ('Produttore D', 'Impianto D', 'Indirizzo D', 'EER004', '2024-04-01', '2024-04-01', '2025-04-01')
    ])

    # Commit delle modifiche e chiusura della connessione
    conn.commit()
    conn.close()

if __name__ == '__main__':
    create_db()  # Crea la tabella
    insert_sample_data()  # Inserisce alcuni dati di esempio
    print("Database e dati di esempio creati con successo.")
