import os

DATABASE = 'database.db'

def elimina_database():
    if os.path.exists(DATABASE):
        os.remove(DATABASE)
        print(f"Il database '{DATABASE}' è stato eliminato con successo.")
    else:
        print(f"Il database '{DATABASE}' non esiste.")

# Chiamata della funzione per eliminare il database
elimina_database()
