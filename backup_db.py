import sqlite3
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from apscheduler.schedulers.background import BackgroundScheduler
import os

DATABASE = 'database.db'
EXPORT_FILE = 'database_export.json'

# Configurazione email
EMAIL_SENDER = 'your_email@example.com'
EMAIL_RECEIVER = 'receiver_email@example.com'
EMAIL_PASSWORD = 'your_password'
SMTP_SERVER = 'smtp.example.com'
SMTP_PORT = 587

# Funzione per esportare i dati dal database
def export_db():
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
    print(f"Dati esportati con successo in {EXPORT_FILE}")

# Funzione per inviare il file via email
def send_email():
    export_db()  # Assicurati che il file di export sia aggiornato

    try:
        # Configurazione email
        msg = MIMEMultipart()
        msg['From'] = EMAIL_SENDER
        msg['To'] = EMAIL_RECEIVER
        msg['Subject'] = 'Backup Database Export'

        # Corpo del messaggio
        body = 'In allegato trovi l\'export del database.'
        msg.attach(MIMEText(body, 'plain'))

        # Aggiungi allegato
        with open(EXPORT_FILE, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename={os.path.basename(EXPORT_FILE)}',
        )
        msg.attach(part)

        # Invio email
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(EMAIL_SENDER, EMAIL_PASSWORD)
            server.send_message(msg)

        print(f"Email inviata a {EMAIL_RECEIVER} con successo.")
    except Exception as e:
        print(f"Errore nell'invio dell'email: {e}")

# Scheduler per eseguire il backup e l'invio email ogni 12 ore
def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(send_email, 'interval', hours=12)  # Ogni 12 ore
    scheduler.start()
    print("Scheduler avviato. Il backup e l'email saranno inviati ogni 12 ore.")

if __name__ == '__main__':
    start_scheduler()

    # Mantieni il programma in esecuzione
    try:
        while True:
            pass
    except (KeyboardInterrupt, SystemExit):
        print("Scheduler interrotto.")
