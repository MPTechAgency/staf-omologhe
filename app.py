from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import ssl

app = Flask(__name__)
app.secret_key = 'your_secret_key'

DATABASE = 'database.db'

# Funzione per connettersi al database SQLite
def get_db_connection():
    # Usa 'check_same_thread=False' e il timeout per gestire meglio la concorrenza
    conn = sqlite3.connect(DATABASE, check_same_thread=False, timeout=10)
    conn.row_factory = sqlite3.Row
    # Opzionale: Abilita il WAL per migliorare le performance con molte scritture
    conn.execute('PRAGMA journal_mode=WAL;')
    return conn


# Funzione per verificare se il documento è scaduto
def isExpired(data_scadenza):
    # Converte la data di scadenza in un oggetto datetime
    data_scadenza = datetime.strptime(data_scadenza, '%Y-%m-%d')
    # Verifica se la data di scadenza è nel passato
    return data_scadenza < datetime.now()


# Calcolo automatico della data di scadenza (365 giorni dopo la data di accettazione)
def calcola_data_scadenza(data_accettazione):
    scadenza = datetime.strptime(data_accettazione, '%Y-%m-%d') + timedelta(days=365)
    return scadenza.strftime('%Y-%m-%d')  # Restituisce solo la data nel formato 'YYYY-MM-DD'

# Funzione per inviare l'email di notifica
def send_email(subject, body):
    try:
        sender_email = "test@test.it"
        receiver_email = "test-invio@test.it"
        password = "Password-test"

        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = receiver_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP_SSL('mx.test.it', 465)
        server.login(sender_email, password)
        server.sendmail(sender_email, receiver_email, msg.as_string())
        server.quit()

        print(f"Email inviata a {receiver_email}")
    except Exception as e:
        print(f"Errore durante l'invio dell'email: {e}")

# Homepage
@app.route('/')
def home():
        return render_template('index.html')


# Lista Omologhe: Visualizza tutti i documenti
@app.route('/omologhe')
def lista_omologhe():
    conn = get_db_connection()
    documenti = conn.execute('SELECT * FROM documenti').fetchall()
    conn.close()
    return render_template('lista_omologhe.html', documenti=documenti, isExpired=isExpired)

# Aggiungi Omologa: Modifica o aggiungi un nuovo documento
@app.route('/aggiungi_omologa', methods=['GET', 'POST'])
def aggiungi_omologa():
    conn = get_db_connection()
    
    # Recupera la lista dei produttori
    produttori = conn.execute('SELECT * FROM produttori').fetchall()
    
    # Recupera la lista degli impianti
    impianti = conn.execute('SELECT * FROM impianti').fetchall()
    
    conn.close()

    if request.method == 'POST':
        # Recupera i dati dal form
        document_id = request.form.get('id')  # id del documento, se presente per aggiornare
        nome_produttore = request.form.get('nome_produttore')
        impianto_destinazione = request.form.get('impianto_destinazione')
        codice_eer = request.form.get('codice_eer')
        data_invio = request.form.get('data_invio')
        data_accettazione = request.form.get('data_accettazione')
        indirizzo_cantiere = request.form.get('indirizzo_cantiere')  # Recupera l'indirizzo del cantiere

        # Calcola la data di scadenza in base alla data di accettazione
        data_scadenza = calcola_data_scadenza(data_accettazione)
        
        # Riapri la connessione per l'operazione di aggiornamento o inserimento
        conn = get_db_connection()

        # Se document_id è presente, aggiorniamo il documento esistente
        if document_id:
            conn.execute('''UPDATE documenti 
                            SET nome_produttore = ?, 
                                impianto_destinazione = ?, 
                                codice_eer = ?, 
                                data_invio = ?, 
                                data_accettazione = ?, 
                                data_scadenza = ?, 
                                indirizzo_cantiere = ?  -- Aggiungi indirizzo_cantiere
                            WHERE id = ?''', 
                            (nome_produttore, impianto_destinazione, codice_eer, data_invio, data_accettazione, data_scadenza, indirizzo_cantiere, document_id))
        else:
            # Se document_id non è presente, inseriamo un nuovo documento
            conn.execute('''INSERT INTO documenti (nome_produttore, impianto_destinazione, codice_eer, data_invio, data_accettazione, data_scadenza, indirizzo_cantiere) 
                            VALUES (?, ?, ?, ?, ?, ?, ?)''', 
                            (nome_produttore, impianto_destinazione, codice_eer, data_invio, data_accettazione, data_scadenza, indirizzo_cantiere))

        conn.commit()  # Salviamo le modifiche nel database
        conn.close()   # Chiudiamo la connessione al database
        
        flash('Omologa aggiunta con successo!', 'success')  # Messaggio di successo
        return redirect(url_for('lista_omologhe'))  # Reindirizza alla lista delle omologhe
    
    # Se la richiesta è di tipo GET, renderizza il modulo di aggiunta
    return render_template('aggiungi_omologa.html', produttori=produttori, impianti=impianti)

# Lista Produttori: Visualizza tutti i produttori
@app.route('/lista_produttori')
def lista_produttori():
    conn = get_db_connection()
    # Recupera tutti i produttori dalla tabella 'produttori'
    produttori = conn.execute('SELECT * FROM produttori').fetchall()
    conn.close()
    # Passa i dati alla template 'lista_produttori.html' per la visualizzazione
    return render_template('lista_produttori.html', produttori=produttori)


# Usa con 'with' per gestire automaticamente la connessione
@app.route('/aggiungi_produttore', methods=['GET', 'POST'])
def aggiungi_produttore():
    if request.method == 'POST':
        nome_produttore = request.form['nome_produttore']
        indirizzo_produttore = request.form['indirizzo_produttore']

        with get_db_connection() as conn:
            conn.execute('INSERT INTO produttori (nome_produttore, indirizzo_produttore) VALUES (?, ?)', (nome_produttore, indirizzo_produttore))
            conn.commit()

        flash('Produttore aggiunto con successo!', 'success')
        return redirect(url_for('lista_produttori'))
    
    return render_template('aggiungi_produttore.html') 


# Lista Impianti: Visualizza tutti gli impianti
@app.route('/impianti')
def lista_impianti():
    conn = get_db_connection()
    impianti = conn.execute('SELECT * FROM impianti').fetchall()
    conn.close()
    return render_template('lista_impianti.html', impianti=impianti)


# Aggiungi Impianto: Modifica o aggiungi un nuovo impianto
@app.route('/aggiungi_impianto', methods=['GET', 'POST'])
def aggiungi_impianto():
    if request.method == 'POST':
        nome_impianto = request.form['nome_impianto']
        indirizzo_impianto = request.form['indirizzo_impianto'] 

        with get_db_connection() as conn:
            conn.execute('INSERT INTO impianti (nome_impianto, indirizzo_impianto) VALUES (?, ?)',
                         (nome_impianto, indirizzo_impianto))
            conn.commit()

        flash('Impianto aggiunto con successo!', 'success')


        return redirect(url_for('lista_impianti'))

    return render_template('aggiungi_impianto.html')

# Modifica un documento esistente
@app.route('/edit/<int:document_id>', methods=['GET', 'POST'])
def edit_document(document_id):
    conn = get_db_connection()

    # Recupera il documento dal database
    documento = conn.execute('SELECT * FROM documenti WHERE id = ?', (document_id,)).fetchone()

    # Se il documento non esiste, rimanda alla lista delle omologhe
    if documento is None:
        flash('Documento non trovato', 'danger')
        return redirect(url_for('lista_omologhe'))

    if request.method == 'POST':
        # Recupera i dati dal form di modifica
        nome_produttore = request.form['nome_produttore']
        impianto_destinazione = request.form['impianto_destinazione']
        codice_eer = request.form['codice_eer']
        data_invio = request.form['data_invio']
        data_accettazione = request.form['data_accettazione']
        indirizzo_cantiere = request.form['indirizzo_cantiere']

        # Calcola la data di scadenza in base alla data di accettazione
        data_scadenza = calcola_data_scadenza(data_accettazione)

        # Esegui l'update del documento nel database
        conn.execute('''
            UPDATE documenti
            SET nome_produttore = ?,
                impianto_destinazione = ?,
                codice_eer = ?,
                data_invio = ?,
                data_accettazione = ?,
                data_scadenza = ?,
                indirizzo_cantiere = ?
            WHERE id = ?
        ''', (nome_produttore, impianto_destinazione, codice_eer, data_invio, data_accettazione, data_scadenza, indirizzo_cantiere, document_id))
        conn.commit()
        conn.close()

        flash('Omologa modificata con successo!', 'success')
        return redirect(url_for('lista_omologhe'))

    conn.close()

    # Recupera la lista dei produttori e degli impianti per precompilare i select
    conn = get_db_connection()
    produttori = conn.execute('SELECT * FROM produttori').fetchall()
    impianti = conn.execute('SELECT * FROM impianti').fetchall()
    conn.close()

    # Passa il documento da modificare e i dati di riferimento (produttori e impianti) alla pagina di modifica
    return render_template('edit_documento.html', documento=documento, produttori=produttori, impianti=impianti)


# Ricerca documenti
@app.route('/search', methods=['GET'])
def search():
    query = request.args.get('query') or ""
    conn = get_db_connection()
    documenti = conn.execute('''SELECT * FROM documenti WHERE
        nome_produttore LIKE ? OR impianto_destinazione LIKE ? OR indirizzo_cantiere LIKE ? OR codice_eer LIKE ?''',
        ('%' + query + '%',) * 4).fetchall()
    conn.close()
    return render_template('search.html', documenti=documenti)

# Eliminazione dei documenti selezionati
@app.route('/delete', methods=['POST'])
def delete_documents():
    # Recuperiamo gli ID dei documenti selezionati
    selected_ids = request.form.getlist('document_ids')

    if selected_ids:
        try:
            conn = get_db_connection()
            conn.execute(f"DELETE FROM documenti WHERE id IN ({','.join('?' for _ in selected_ids)})", selected_ids)
            conn.commit()
            conn.close()

            # Invia un'email di notifica (opzionale)
            documenti_eliminati = ', '.join(selected_ids)
            subject = "Notifica di Eliminazione Documenti"
            body = f"I seguenti documenti sono stati eliminati: {documenti_eliminati}"
            send_email(subject, body)

            flash('Documenti eliminati con successo!', 'success')
        except Exception as e:
            flash(f"Errore durante l'eliminazione: {str(e)}", 'danger')
    else:
        flash('Nessun documento selezionato per l\'eliminazione', 'warning')

    return redirect(url_for('lista_omologhe'))

@app.route('/delete_impianti', methods=['POST'])
def delete_impianti():
    # Ottieni gli ID degli impianti selezionati dal form
    impianto_ids = request.form.getlist('impianto_ids')
    conn = get_db_connection()
    if impianto_ids:
        for id in impianto_ids:
            conn.execute('DELETE FROM impianti WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        flash('Impianti eliminati con successo!', 'success')
    else:
        flash('Nessun impianto selezionato per l\'eliminazione', 'warning')

    return redirect(url_for('lista_impianti'))

@app.route('/delete_produttori', methods=['POST'])
def delete_produttori():
    # Ottieni gli ID dei produttori selezionati dal form
    produttore_ids = request.form.getlist('produttore_ids')
    conn = get_db_connection()
    
    if produttore_ids:
        for id in produttore_ids:
            conn.execute('DELETE FROM produttori WHERE id = ?', (id,))
        conn.commit()
        conn.close()
        flash('Produttori eliminati con successo!', 'success')
    else:
        flash('Nessun produttore selezionato per l\'eliminazione', 'warning')

    return redirect(url_for('lista_produttori'))


if __name__ == '__main__':
    # Utilizzo di HTTPS con un certificato autofirmato
    context = ('cert.pem', 'key.pem')  # Assicurati di avere questi file
    app.run(host='0.0.0.0', port=5000, debug=True, ssl_context=context)
