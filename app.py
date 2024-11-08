from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'database.db'

# Funzione per connettersi al database SQLite
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

# Calcolo automatico della data di scadenza (365 giorni dopo la data di accettazione)
def calcola_data_scadenza(data_accettazione):
    return datetime.strptime(data_accettazione, '%Y-%m-%d') + timedelta(days=365)

# Funzione per inviare l'email di notifica
def send_email(subject, body):
    try:
        # Configurazione del server SMTP (Gmail come esempio)
        sender_email = "test@test.it"  # Email mittente
        receiver_email = "test-invio@test.it"  # Email destinatario
        password = "Password-test"  # Password dell'app (non quella dell'account Google)

        # Creazione del messaggio
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'plain'))

        # Connessione al server SMTP di Gmail
        server = smtplib.SMTP_SSL('mx.test.it', 465)
        server.login(sender_email, password)

        # Inviare l'email
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        print(f"Email inviata a {receiver_email}")
    except Exception as e:
        print(f"Errore durante l'invio dell'email: {e}")

# Homepage che mostra tutti i documenti
@app.route('/')
def index():
    conn = get_db_connection()
    documenti = conn.execute('SELECT * FROM documenti').fetchall()
    conn.close()
    return render_template('index.html', documenti=documenti)

# Aggiungere un nuovo documento
@app.route('/add', methods=['GET', 'POST'])
def add_document():
    if request.method == 'POST':
        nome_produttore = request.form['nome_produttore']
        impianto_destinazione = request.form['impianto_destinazione']
        indirizzo_cantiere = request.form['indirizzo_cantiere']
        codice_eer = request.form['codice_eer']
        data_invio = request.form['data_invio']
        data_accettazione = request.form['data_accettazione']
        data_scadenza = calcola_data_scadenza(data_accettazione)

        conn = get_db_connection()
        conn.execute('INSERT INTO documenti (nome_produttore, impianto_destinazione, indirizzo_cantiere, codice_eer, data_invio, data_accettazione, data_scadenza) VALUES (?, ?, ?, ?, ?, ?, ?)', 
                     (nome_produttore, impianto_destinazione, indirizzo_cantiere, codice_eer, data_invio, data_accettazione, data_scadenza))
        conn.commit()
        conn.close()
        flash('Documento aggiunto con successo!', 'success')
        return redirect(url_for('index'))
    
    return render_template('form.html')

# Ricerca documenti
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query')

    # Verifica se query è None o vuota
    if not query:
        query = ""  # Imposta query come stringa vuota se non è definita o è vuota

    conn = get_db_connection()
    documenti = conn.execute('''
        SELECT * FROM documenti 
        WHERE nome_produttore LIKE ? 
        OR impianto_destinazione LIKE ? 
        OR indirizzo_cantiere LIKE ? 
        OR codice_eer LIKE ?
    ''', ('%' + query + '%', '%' + query + '%', '%' + query + '%', '%' + query + '%')).fetchall()
    conn.close()

    return render_template('search.html', documenti=documenti)

# Eliminazione dei documenti selezionati
@app.route('/delete', methods=['POST'])
def delete_documents():
    # Recuperiamo gli ID dei documenti selezionati
    selected_ids = request.form.getlist('document_ids')
    
    # Verifica che siano stati selezionati degli ID
    if selected_ids:
        try:
            # Connettiamo al database e prepariamo la query per eliminare i documenti
            conn = get_db_connection()
            # Eseguiamo una DELETE dove gli ID corrispondono a quelli selezionati
            conn.execute(f"DELETE FROM documenti WHERE id IN ({','.join('?' for _ in selected_ids)})", selected_ids)
            conn.commit()  # Commit delle modifiche
            conn.close()

            # Creiamo il corpo dell'email
            documenti_eliminati = ', '.join(selected_ids)
            subject = "Notifica di Eliminazione Documenti"
            body = f"I seguenti documenti sono stati eliminati: {documenti_eliminati}"

            # Invio dell'email di notifica
            send_email(subject, body)

            flash('Documenti eliminati con successo!', 'success')
        except Exception as e:
            flash(f"Errore durante l'eliminazione: {str(e)}", 'danger')
    else:
        flash('Nessun documento selezionato per l\'eliminazione', 'warning')

    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)

